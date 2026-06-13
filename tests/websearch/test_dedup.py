"""Tests for BM25-based deduplication and re-ranking."""

from toolregistry_hub.websearch.dedup import (
    _bm25_score,
    _tokenize,
    deduplicate_results,
)
from toolregistry_hub.websearch.search_result import SearchResult


def _r(title="t", url="https://example.com", content="c", score=1.0):
    return SearchResult(title=title, url=url, content=content, score=score)


# ── Tokenizer ────────────────────────────────────────────────────────────


class TestTokenize:
    def test_basic(self):
        assert _tokenize("Hello World") == ["hello", "world"]

    def test_punctuation_stripped(self):
        assert _tokenize("python 3.12 release!") == ["python", "3", "12", "release"]

    def test_empty(self):
        assert _tokenize("") == []

    def test_unicode(self):
        tokens = _tokenize("Python 发布 3.12")
        assert "python" in tokens
        assert "发布" in tokens


# ── BM25 scoring ─────────────────────────────────────────────────────────


class TestBM25Score:
    def test_matching_terms_score_positive(self):
        score = _bm25_score(
            query_tokens=["python"],
            doc_tokens=["python", "is", "great"],
            avg_dl=3.0,
            df={"python": 1, "is": 2, "great": 1},
            n_docs=3,
        )
        assert score > 0

    def test_no_matching_terms_score_zero(self):
        score = _bm25_score(
            query_tokens=["rust"],
            doc_tokens=["python", "is", "great"],
            avg_dl=3.0,
            df={"python": 1},
            n_docs=3,
        )
        assert score == 0.0

    def test_rarer_terms_score_higher(self):
        # "python" appears in 1/10 docs vs "the" in 9/10 docs
        score_rare = _bm25_score(
            query_tokens=["python"],
            doc_tokens=["python", "tutorial"],
            avg_dl=5.0,
            df={"python": 1, "the": 9},
            n_docs=10,
        )
        score_common = _bm25_score(
            query_tokens=["the"],
            doc_tokens=["the", "tutorial"],
            avg_dl=5.0,
            df={"python": 1, "the": 9},
            n_docs=10,
        )
        assert score_rare > score_common


# ── Deduplication ────────────────────────────────────────────────────────


class TestDeduplicateResults:
    def test_empty_input(self):
        assert deduplicate_results([], "python") == []

    def test_single_result(self):
        results = [_r(content="Python tutorial")]
        deduped = deduplicate_results(results, "python")
        assert len(deduped) == 1

    def test_url_dedup_keeps_longest_content(self):
        results = [
            _r(url="https://a.com", content="short"),
            _r(url="https://a.com", content="much longer content here"),
        ]
        deduped = deduplicate_results(results, "test")
        assert len(deduped) == 1
        assert deduped[0].content == "much longer content here"

    def test_url_dedup_normalizes_trailing_slash(self):
        results = [
            _r(url="https://a.com/path/", content="with slash"),
            _r(url="https://a.com/path", content="without slash but longer text"),
        ]
        deduped = deduplicate_results(results, "test")
        assert len(deduped) == 1

    def test_different_urls_preserved(self):
        results = [
            _r(url="https://a.com", content="content a about python"),
            _r(url="https://b.com", content="content b about python"),
        ]
        deduped = deduplicate_results(results, "python")
        assert len(deduped) == 2

    def test_bm25_reranks_by_relevance(self):
        results = [
            _r(
                url="https://irrelevant.com",
                title="Cooking recipes",
                content="Best pasta recipes for dinner tonight",
            ),
            _r(
                url="https://relevant.com",
                title="Python tutorial",
                content="Learn Python programming with examples",
            ),
        ]
        deduped = deduplicate_results(results, "python programming")
        assert deduped[0].url == "https://relevant.com"

    def test_empty_query_preserves_order(self):
        results = [
            _r(url="https://a.com", content="first"),
            _r(url="https://b.com", content="second"),
        ]
        deduped = deduplicate_results(results, "   ")
        # Empty query can't score — should still return deduped results
        assert len(deduped) == 2

    def test_mixed_engines_deduplicated(self):
        """Simulate two engines returning overlapping results."""
        engine_a = [
            _r(url="https://shared.com", title="Shared", content="short"),
            _r(url="https://only-a.com", title="Only A", content="unique to a"),
        ]
        engine_b = [
            _r(
                url="https://shared.com",
                title="Shared Result",
                content="longer version from engine b",
            ),
            _r(url="https://only-b.com", title="Only B", content="unique to b"),
        ]
        combined = engine_a + engine_b
        deduped = deduplicate_results(combined, "test query")
        urls = {r.url for r in deduped}
        assert len(deduped) == 3
        assert urls == {
            "https://shared.com",
            "https://only-a.com",
            "https://only-b.com",
        }
        # Shared URL should keep the longer content
        shared = next(r for r in deduped if "shared" in r.url)
        assert shared.content == "longer version from engine b"
