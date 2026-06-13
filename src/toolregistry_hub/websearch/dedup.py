"""BM25-based deduplication and re-ranking for multi-engine search results.

When multiple search engines return results for the same query, duplicates
(same URL) are collapsed and the remaining results are re-ranked using
BM25 scoring against the original query.  This produces a single, high-quality
result list from heterogeneous provider outputs.

The implementation is zero-dependency — only ``math``, ``re``, and
``collections`` from the standard library are used.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

from .search_result import SearchResult

# Query parameters injected by analytics / ad platforms.  Stripping these
# prevents the same page from appearing as two different URLs when engines
# return different tracking suffixes.
_TRACKING_PARAMS: frozenset[str] = frozenset(
    {
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_term",
        "utm_content",
        "ref",
        "fbclid",
        "gclid",
        "msclkid",
        "mc_cid",
        "mc_eid",
    }
)


def _normalize_url(url: str) -> str:
    """Normalize a URL for deduplication purposes.

    Applies the following transformations:
        1. Strip trailing slashes from the path.
        2. Remove ``www.`` prefix from the hostname.
        3. Strip common tracking query parameters (utm_*, fbclid, etc.).

    The original URL stored in the ``SearchResult`` is never modified —
    this function is only used to build the dedup key.

    Args:
        url: Raw URL string.

    Returns:
        Normalized URL string suitable for equality comparison.
    """
    parts = urlsplit(url)

    # Remove www. prefix
    host = parts.hostname or ""
    if host.startswith("www."):
        host = host[4:]
    # Reconstruct netloc (preserve port if present)
    netloc = host
    if parts.port:
        netloc = f"{host}:{parts.port}"

    # Strip trailing slashes from path
    path = parts.path.rstrip("/")

    # Remove tracking query parameters
    if parts.query:
        params = parse_qs(parts.query, keep_blank_values=True)
        cleaned = {k: v for k, v in params.items() if k not in _TRACKING_PARAMS}
        query = urlencode(cleaned, doseq=True)
    else:
        query = ""

    return urlunsplit((parts.scheme, netloc, path, query, ""))


# BM25 tuning constants (standard Okapi BM25 defaults).
_BM25_K1 = 1.5
_BM25_B = 0.75

# Simple word-boundary tokenizer.  Good enough for search-result snippets
# in Latin, CJK, and mixed scripts.
_TOKEN_RE = re.compile(r"\w+", re.UNICODE)


def _tokenize(text: str) -> list[str]:
    """Split *text* into lowercase word tokens.

    Args:
        text: Input text.

    Returns:
        List of lowercase tokens.
    """
    return _TOKEN_RE.findall(text.lower())


def _bm25_score(
    query_tokens: list[str],
    doc_tokens: list[str],
    avg_dl: float,
    df: dict[str, int],
    n_docs: int,
) -> float:
    """Compute the BM25 score of a single document against a query.

    Args:
        query_tokens: Tokenized query.
        doc_tokens: Tokenized document (title + content).
        avg_dl: Average document length across the corpus.
        df: Document-frequency map (token → count of docs containing it).
        n_docs: Total number of documents in the corpus.

    Returns:
        BM25 relevance score (higher is better).
    """
    tf = Counter(doc_tokens)
    dl = len(doc_tokens)
    score = 0.0

    for term in query_tokens:
        if term not in tf:
            continue
        term_tf = tf[term]
        term_df = df.get(term, 0)
        # IDF with smoothing (avoid log(0) and negative IDF)
        idf = math.log(1.0 + (n_docs - term_df + 0.5) / (term_df + 0.5))
        # TF normalization
        numerator = term_tf * (_BM25_K1 + 1.0)
        denominator = term_tf + _BM25_K1 * (1.0 - _BM25_B + _BM25_B * dl / avg_dl)
        score += idf * numerator / denominator

    return score


def deduplicate_results(
    results: list[SearchResult],
    query: str,
) -> list[SearchResult]:
    """Deduplicate and re-rank search results using BM25 scoring.

    Steps:
        1. **URL dedup** — when multiple results share the same URL, keep only
           the one with the longest ``content`` (richest snippet).
        2. **BM25 re-rank** — score each remaining result's ``title + content``
           against the *query* tokens and sort descending.

    Args:
        results: Combined results from multiple engines (may contain dupes).
        query: The original search query string.

    Returns:
        Deduplicated results sorted by BM25 relevance (best first).
    """
    if not results:
        return []

    # ── Step 1: URL dedup (keep longest content per URL) ─────────────────
    best_by_url: dict[str, SearchResult] = {}
    for r in results:
        url = _normalize_url(r.url)
        existing = best_by_url.get(url)
        if existing is None or len(r.content) > len(existing.content):
            best_by_url[url] = r

    unique = list(best_by_url.values())

    if len(unique) <= 1:
        return unique

    # ── Step 2: BM25 re-rank ─────────────────────────────────────────────
    query_tokens = _tokenize(query)
    if not query_tokens:
        return unique  # can't score without query tokens

    # Tokenize all documents
    doc_token_lists = [_tokenize(f"{r.title} {r.content}") for r in unique]

    # Corpus statistics
    n_docs = len(unique)
    avg_dl = sum(len(dt) for dt in doc_token_lists) / n_docs

    # Document frequency
    df: dict[str, int] = {}
    for dt in doc_token_lists:
        for term in set(dt):
            df[term] = df.get(term, 0) + 1

    # Score and sort
    scored = [
        (r, _bm25_score(query_tokens, dt, avg_dl, df, n_docs))
        for r, dt in zip(unique, doc_token_lists, strict=True)
    ]
    scored.sort(key=lambda x: x[1], reverse=True)

    return [r for r, _score in scored]
