"""Fetch and extract content from URLs."""

from __future__ import annotations

import os
import re
import threading
import time
import unicodedata
from typing import TYPE_CHECKING, Literal, NamedTuple, cast

from ._vendor.httpclient import (
    HttpConnectionError,
    HTTPError,
    HttpTimeoutError,
    Response,
)
from ._vendor.httpclient import (
    get as _http_get,
)
from ._vendor.httpclient import (
    post as _http_post,
)
from ._vendor.readability import extract as readability_extract
from ._vendor.soup import Soup
from ._vendor.structlog import get_logger
from ._vendor.useragent import generate

if TYPE_CHECKING:
    from .utils.api_key_parser import APIKeyParser

logger = get_logger()

TIMEOUT_DEFAULT = 30.0

# Minimum remaining budget (in seconds) before attempting another network
# strategy.  Strategies are skipped when the deadline is closer than this so
# callers with very small ``timeout`` values get an answer quickly.
_MIN_STRATEGY_BUDGET = 0.05

# Default TTL (in seconds) for the per-instance URL result cache.
_CACHE_TTL_DEFAULT = 300.0  # 5 minutes

# Default maximum number of cached entries.
_CACHE_MAXSIZE_DEFAULT = 128


class _CacheEntry(NamedTuple):
    """A cached extraction result with its expiry timestamp."""

    content: str
    expires_at: float  # time.monotonic() deadline


class _URLCache:
    """Simple thread-safe TTL + LRU cache keyed by URL.

    Uses an ``OrderedDict``-style approach with a plain ``dict`` (Python 3.7+
    dicts are insertion-ordered).  On hit the entry is moved to the end so
    that eviction always removes the least-recently-used item.

    Only successful extraction results are cached; ``FetchError`` outcomes
    are never stored.
    """

    def __init__(
        self,
        ttl: float = _CACHE_TTL_DEFAULT,
        maxsize: int = _CACHE_MAXSIZE_DEFAULT,
    ) -> None:
        self._ttl = ttl
        self._maxsize = maxsize
        self._data: dict[str, _CacheEntry] = {}
        self._lock = threading.Lock()

    # ── public API ───────────────────────────────────────────────────────

    def get(self, url: str) -> str | None:
        """Return cached content for *url*, or ``None`` on miss/expiry."""
        with self._lock:
            entry = self._data.get(url)
            if entry is None:
                return None
            if time.monotonic() > entry.expires_at:
                del self._data[url]
                return None
            # Move to end (most-recently-used).
            self._data[url] = self._data.pop(url)
            return entry.content

    def put(self, url: str, content: str) -> None:
        """Store *content* for *url* with the configured TTL."""
        with self._lock:
            # Remove first so re-insertion lands at the end.
            self._data.pop(url, None)
            self._data[url] = _CacheEntry(
                content=content,
                expires_at=time.monotonic() + self._ttl,
            )
            # Evict oldest entries if over capacity.
            while len(self._data) > self._maxsize:
                oldest_key = next(iter(self._data))
                del self._data[oldest_key]

    def clear(self) -> None:
        """Remove all cached entries."""
        with self._lock:
            self._data.clear()

    def __len__(self) -> int:
        """Return the number of cached entries (including expired)."""
        return len(self._data)


class FetchError(RuntimeError):
    """Raised when ``Fetch.fetch_content`` cannot retrieve any usable content.

    Surfacing this as an exception (rather than returning a sentinel string)
    lets MCP and other tool harnesses set the ``isError`` flag on the
    response automatically.
    """


# Minimum content length (in characters) to consider extraction sufficient.
# Content shorter than this triggers the next fallback strategy.
_MIN_CONTENT_LENGTH = 100

# Common indicators of SPA shell pages that lack real content.
# If any of these appear in the extracted text, the content is considered
# insufficient and Jina Reader (with browser engine) will be tried.
# SPA shell indicators that reliably signal a JavaScript app shell.
# These are checked against the *entire* lowercased text.  Indicators
# like "loading..." that frequently appear in legitimate long-form
# content have been removed to avoid false positives.  Short content
# (< _SPA_SHORT_TEXT_THRESHOLD chars) is checked against a broader
# set of indicators via _SPA_SHELL_INDICATORS_SHORT.
_SPA_SHELL_INDICATORS = [
    "please enable javascript",
    "you need to enable javascript",
    "this app requires javascript",
    "we're sorry but",
    "doesn't work properly without javascript",
    "requires a modern browser",
]

# Additional indicators checked only when extracted text is short.
# Short SPA shells often contain only boilerplate phrases; in long
# articles the same words may appear legitimately.
_SPA_SHELL_INDICATORS_SHORT = [
    "loading...",
    "noscript",
    "enable cookies",
]

# Text shorter than this threshold is checked against both indicator
# lists; longer text is only checked against the strict list.
_SPA_SHORT_TEXT_THRESHOLD = 500

# Readability score above this value is considered a strong signal of
# real article content.  When the score exceeds this threshold, SPA
# indicator matching is skipped entirely — a high score means
# readability found a substantive candidate container.
_READABILITY_SCORE_THRESHOLD = 20.0

# Maximum number of retry attempts for transient HTTP failures in _fetch_html.
_FETCH_MAX_RETRIES = 3

# Base delay (in seconds) for exponential backoff between retries.
_FETCH_RETRY_BASE_DELAY = 1.0

# Navigation-only content detection thresholds.
# These are used by _is_content_sufficient() to detect pages that consist
# mostly of short navigation links/menu items rather than real content.
_NAV_MIN_LINES = 5  # Minimum lines before applying structure analysis
_NAV_SHORT_LINE_THRESHOLD = 30  # Characters; lines shorter are "short"
_NAV_SHORT_LINE_RATIO = 0.7  # Fraction of short lines to trigger check
_NAV_LONG_LINE_THRESHOLD = (
    80  # Characters; lines at least this long are "real paragraphs"
)
_NAV_MIN_LONG_LINES = 2  # Minimum long lines required to pass the check

# Soup-skip thresholds for P3 optimisation.  When readability produces a
# result that exceeds *both* thresholds we skip the soup extraction pass
# entirely, saving 30-180 ms depending on document size.  Values chosen
# conservatively: profiling showed that readability scores >= 170 always
# yielded content within 16% of soup output, so 100 leaves comfortable
# margin.  2 000 chars guards against high-score stubs (sidebar, summary).
_SOUP_SKIP_SCORE_THRESHOLD: float = 100.0
_SOUP_SKIP_MIN_LENGTH: int = 2_000

# Content types that should be returned directly without HTML extraction.
# When the server responds with one of these MIME types, the body is already
# usable text/data — running it through readability or soup would be wasteful
# or destructive.
_NON_HTML_CONTENT_TYPES: frozenset[str] = frozenset(
    {
        "text/plain",
        "text/csv",
        "text/markdown",
        "application/json",
        "application/xml",
        "text/xml",
        "application/x-yaml",
        "text/yaml",
    }
)

# Content-type prefixes that indicate binary data.  These cannot be
# meaningfully extracted as text; attempting to do so wastes CPU on
# garbage and may cause encoding errors.
_BINARY_CONTENT_TYPE_PREFIXES: tuple[str, ...] = (
    "image/",
    "audio/",
    "video/",
    "font/",
)

# Exact binary MIME types that should also be rejected early.
_BINARY_CONTENT_TYPES: frozenset[str] = frozenset(
    {
        "application/pdf",
        "application/zip",
        "application/gzip",
        "application/x-tar",
        "application/x-7z-compressed",
        "application/x-rar-compressed",
        "application/octet-stream",
        "application/wasm",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
)


def _is_binary_content_type(content_type: str) -> bool:
    """Check whether a MIME type represents binary (non-extractable) content."""
    return (
        content_type.startswith(_BINARY_CONTENT_TYPE_PREFIXES)
        or content_type in _BINARY_CONTENT_TYPES
    )

# CSS selectors tried in order by _extract_with_soup to locate the main
# content container.  Each entry is a ``(tag, attrs)`` tuple compatible
# with ``Soup.find(tag, attrs)``.  The first match wins.
_SOUP_CONTENT_SELECTORS: list[tuple[str, dict[str, str | bool] | None]] = [
    ("main", None),
    ("article", None),
    ("div", {"class": "content"}),
    ("div", {"class": "post-content"}),
    ("div", {"class": "entry-content"}),
    ("div", {"class": "article-body"}),
    ("div", {"class": "article-content"}),
    ("div", {"id": "content"}),
    ("section", {"class": "content"}),
    ("div", {"class": "markdown-body"}),
    ("div", {"class": "post"}),
    ("div", {"class": "entry"}),
    ("div", {"class": "page-content"}),
    ("div", {"class": "main-content"}),
    ("div", {"id": "main-content"}),
    ("div", {"role": "main"}),
    ("div", {"class": "blog-post"}),
    ("div", {"class": "post-body"}),
    ("div", {"class": "story-body"}),
]


class Fetch:
    """Fetch and extract content from URLs.

    Supports optional Jina Reader API keys for higher rate limits.
    Multiple keys are rotated automatically via round-robin with
    failure tracking.
    """

    def __init__(
        self,
        api_keys: str | None = None,
        cdp_endpoint: str | None = None,
        cache_ttl: float = _CACHE_TTL_DEFAULT,
        cache_maxsize: int = _CACHE_MAXSIZE_DEFAULT,
    ):
        """Initialize Fetch with optional Jina Reader API keys and CDP endpoint.

        Args:
            api_keys: Comma-separated Jina API keys. Falls back to
                the ``JINA_API_KEY`` environment variable if not provided.
                When set, requests to the Jina Reader API include an
                ``Authorization: Bearer <key>`` header.
            cdp_endpoint: WebSocket URL of a CDP-compatible browser
                (e.g. ``ws://localhost:9222``).  Falls back to the
                ``CDP_ENDPOINT`` environment variable.  When set, SPA
                pages are rendered via CDP before falling back to Jina.
            cache_ttl: Time-to-live in seconds for cached URL results.
                Set to ``0`` to disable caching.  Defaults to 300 (5 min).
            cache_maxsize: Maximum number of entries in the URL cache.
                Defaults to 128.
        """
        from .utils.api_key_parser import APIKeyParser

        parser = APIKeyParser(
            api_keys=api_keys,
            env_var_name="JINA_API_KEY",
            rate_limit_delay=0.0,
        )
        self.api_key_parser: APIKeyParser | None = parser if parser.api_keys else None
        self.cdp_endpoint: str | None = cdp_endpoint or os.environ.get("CDP_ENDPOINT")
        self._cache: _URLCache | None = (
            _URLCache(ttl=cache_ttl, maxsize=cache_maxsize)
            if cache_ttl > 0
            else None
        )

    def _is_configured(self) -> bool:
        """Check if Fetch is configured.

        Always returns True because Jina API keys are optional.
        Fetch works without keys (unauthenticated requests).
        """
        return True

    def clear_cache(self) -> None:
        """Remove all cached URL results."""
        if self._cache is not None:
            self._cache.clear()

    def fetch_content(
        self,
        url: str,
        timeout: float = TIMEOUT_DEFAULT,
        proxy: str | None = None,
    ) -> str:
        """Fetch and extract content from a given URL.

        The ``timeout`` is treated as a wall-clock budget for the whole
        operation, including internal retries and fallback strategies.
        Calls that exceed the budget abort early instead of running on
        for many multiples of the requested timeout.

        Args:
            url (str): The URL to fetch content from.
            timeout (float, optional): Total wall-clock timeout in seconds.
                Defaults to TIMEOUT_DEFAULT.
            proxy (str, optional): Proxy to use for the request. Defaults to None.

        Returns:
            str: Extracted content from the URL.

        Raises:
            FetchError: If every extraction strategy fails or the deadline
                is exceeded before any content can be retrieved.
        """
        # Check cache first.
        if self._cache is not None:
            cached = self._cache.get(url)
            if cached is not None:
                logger.debug(f"Cache hit for {url}")
                return cached

        try:
            content = _extract(
                url,
                timeout=timeout,
                proxy=proxy,
                api_key_parser=self.api_key_parser,
                cdp_endpoint=self.cdp_endpoint,
            )
            # Cache successful results only.
            if self._cache is not None:
                self._cache.put(url, content)
            return content
        except FetchError:
            raise
        except Exception as e:
            logger.error(f"Failed to fetch content from {url}: {e}")
            raise FetchError(f"Failed to fetch content from {url}: {e}") from e


def _should_skip_soup(
    readability_content: str,
    readability_score: float,
    url: str,
) -> bool:
    """Decide whether to skip soup extraction.

    When readability produced a high-confidence result with enough content,
    running the soup pass adds little value (profiling shows <16% extra
    content) but costs 30-180 ms.  Skipping is logged at DEBUG level so
    the decision can be audited later.

    Args:
        readability_content: Text returned by readability.
        readability_score: Readability score of the best candidate.
        url: URL being processed (for logging).

    Returns:
        True if soup extraction should be skipped.
    """
    if (
        readability_score >= _SOUP_SKIP_SCORE_THRESHOLD
        and len(readability_content) >= _SOUP_SKIP_MIN_LENGTH
    ):
        logger.debug(
            f"Skipping soup extraction for {url} "
            f"(readability sufficient: score={readability_score:.1f}, "
            f"len={len(readability_content)})"
        )
        return True
    return False


def _is_content_sufficient(
    text: str,
    readability_score: float = 0.0,
) -> bool:
    """Evaluate whether extracted content has sufficient quality.

    Checks for minimum length, SPA shell indicators, and navigation-only
    structure to determine if the content is meaningful.

    When *readability_score* exceeds ``_READABILITY_SCORE_THRESHOLD``,
    SPA indicator matching is skipped entirely — a high score means the
    readability algorithm found a substantive candidate container, so
    phrases like ``"loading..."`` in the body text are not false
    positives.

    Args:
        text: The extracted text content to evaluate.
        readability_score: Score from :func:`readability_extract`.
            Defaults to 0.0 (unknown / not from readability).

    Returns:
        True if content appears sufficient, False otherwise.
    """
    if len(text) < _MIN_CONTENT_LENGTH:
        return False

    # High readability score → readability found real content,
    # skip SPA indicator heuristics to avoid false positives.
    if readability_score < _READABILITY_SCORE_THRESHOLD:
        text_lower = text.lower()
        # Always check the strict indicator list.
        for indicator in _SPA_SHELL_INDICATORS:
            if indicator in text_lower:
                return False
        # Short text gets checked against the broader list too.
        if len(text) < _SPA_SHORT_TEXT_THRESHOLD:
            for indicator in _SPA_SHELL_INDICATORS_SHORT:
                if indicator in text_lower:
                    return False

    # Text structure analysis: detect navigation-only content.
    lines = [line for line in text.split("\n") if line.strip()]
    if len(lines) > _NAV_MIN_LINES:
        short_lines = sum(
            1 for line in lines if len(line.strip()) < _NAV_SHORT_LINE_THRESHOLD
        )
        short_ratio = short_lines / len(lines)
        if short_ratio > _NAV_SHORT_LINE_RATIO:
            # Mostly short lines — check for real paragraphs
            long_lines = sum(
                1 for line in lines if len(line.strip()) >= _NAV_LONG_LINE_THRESHOLD
            )
            if long_lines < _NAV_MIN_LONG_LINES:
                return False

    return True


def _pick_local_content(
    readability_content: str,
    readability_score: float,
    soup_content: str,
    url: str,
) -> str:
    """Choose the best local extraction result.

    Prefers readability unless soup produced substantially more content
    (> 2x). Falls back to the next candidate if the preferred one is
    insufficient.

    Args:
        readability_content: Text from readability extraction.
        readability_score: Readability score of the best candidate.
        soup_content: Text from soup extraction.
        url: URL being processed (for logging).

    Returns:
        Best sufficient content string, or empty string if neither qualifies.
    """
    candidates = [
        (readability_content, "readability", readability_score),
        (soup_content, "soup", 0.0),
    ]
    for candidate, strategy, score in candidates:
        if not candidate or not _is_content_sufficient(candidate, readability_score=score):
            continue
        if (
            strategy == "readability"
            and soup_content
            and len(soup_content) > len(candidate) * 2
        ):
            logger.debug(
                f"Readability result shorter than soup "
                f"({len(candidate)} vs {len(soup_content)}), trying soup"
            )
            continue
        logger.info(f"Successfully fetched {url} using strategy: {strategy}")
        return candidate
    return ""


def _render_with_cdp(
    url: str,
    cdp_endpoint: str,
    timeout: float = 15.0,
) -> str:
    """Render a page via CDP and return the rendered HTML.

    Connects to a CDP-compatible browser, navigates to the URL,
    waits for page load, and extracts the fully-rendered HTML
    (post-JavaScript execution).

    Args:
        url: The URL to render.
        cdp_endpoint: WebSocket URL of the CDP browser
            (e.g. ``ws://localhost:9222``).
        timeout: Maximum time in seconds to wait for page load.

    Returns:
        Rendered HTML string, or empty string on any failure.
    """
    try:
        from ._vendor.cdp import CDPClient

        with CDPClient(cdp_endpoint, timeout=timeout) as client:
            html = client.get_rendered_html(url, timeout=timeout)
            if html:
                logger.debug(f"CDP rendered {url}: {len(html)} chars of HTML")
            return html or ""
    except Exception as e:
        logger.debug(f"CDP rendering failed for {url}: {e}")
        return ""


def _try_cdp_extraction(
    url: str,
    cdp_endpoint: str,
    timeout: float,
) -> tuple[str, str]:
    """Render a page with CDP and attempt readability/soup extraction.

    Args:
        url: The URL to render.
        cdp_endpoint: WebSocket endpoint for the CDP browser.
        timeout: Budget in seconds for the CDP render.

    Returns:
        A ``(best_content, local_content)`` tuple.  ``best_content`` is non-empty
        when extraction produced sufficient content; ``local_content`` is the best
        partial result for final-fallback stashing.
    """
    rendered_html = _render_with_cdp(url, cdp_endpoint, timeout=timeout)
    if not rendered_html:
        return "", ""

    cdp_readability, cdp_score = _extract_with_readability(rendered_html, url)
    if _should_skip_soup(cdp_readability, cdp_score, url):
        cdp_soup = ""
    else:
        cdp_soup = _extract_with_soup(rendered_html)
    cdp_best = _pick_local_content(cdp_readability, cdp_score, cdp_soup, url)
    if cdp_best:
        logger.info(f"Successfully fetched {url} using strategy: cdp")
        return cdp_best, ""
    return "", cdp_readability or cdp_soup or ""


def _try_jina_extraction(
    url: str,
    *,
    local_content: str,
    timeout: float,
    remaining: float,
    proxy: str | None,
    api_key_parser: APIKeyParser | None,
    deadline: float,
) -> str:
    """Attempt Jina Reader extraction as the final network strategy.

    Args:
        url: The URL to extract content from.
        local_content: Best local extraction result so far (for logging).
        timeout: Original total timeout.
        remaining: Time remaining in the budget.
        proxy: Proxy to use for the request.
        api_key_parser: Optional API key parser for Jina Reader.
        deadline: Absolute wall-clock deadline.

    Returns:
        Sufficient Jina content, or empty string on failure.
    """
    reason = "low_quality_content" if local_content else "no_content"
    if remaining <= _MIN_STRATEGY_BUDGET:
        logger.debug(
            f"Skipping Jina Reader for {url}: deadline exceeded "
            f"(reason: {reason}, length: {len(local_content)})"
        )
        return ""

    logger.debug(
        f"Local extraction insufficient for {url} (reason: {reason}, "
        f"length: {len(local_content)}), trying Jina Reader"
    )

    jina_content = _get_content_with_jina_reader(
        url,
        timeout=min(timeout, remaining),
        proxy=proxy,
        api_key_parser=api_key_parser,
        deadline=deadline,
    )

    if jina_content and _is_content_sufficient(jina_content):
        logger.info(
            f"Successfully fetched {url} using strategy: jina_reader "
            f"(local reason: {reason})"
        )
        return jina_content
    return ""


def _extract(
    url: str,
    timeout: float = TIMEOUT_DEFAULT,
    proxy: str | None = None,
    api_key_parser: APIKeyParser | None = None,
    cdp_endpoint: str | None = None,
) -> str:
    """Extract content from a given URL using available methods.

    Strategies are tried in order:
    1. Cloudflare Content Negotiation (zero-cost markdown attempt)
    2. Readability extraction (intelligent article scoring, local)
    3. Simple soup extraction (CSS selector fallback, local)
    4. CDP rendering (self-hosted browser, re-parsed with readability/soup)
    5. Jina Reader (external API fallback for SPA / JS-heavy pages)

    HTML is fetched once and reused by stages 2 and 3.  ``timeout`` is a
    wall-clock budget for the *whole* operation; strategies are skipped once
    the deadline is exceeded.

    Args:
        url: The URL to extract content from.
        timeout: Total wall-clock timeout in seconds. Defaults to TIMEOUT_DEFAULT.
        proxy: Proxy to use for the request. Defaults to None.
        api_key_parser: Optional API key parser for Jina Reader authentication.

    Returns:
        Extracted content.

    Raises:
        FetchError: If every extraction strategy fails or the deadline is
            exceeded before any content is retrieved.
    """
    deadline = time.monotonic() + max(0.0, timeout)

    def _remaining() -> float:
        return max(0.0, deadline - time.monotonic())

    body, content_type = "", ""

    # 1. Try Cloudflare Content Negotiation (zero-cost, high quality if supported)
    #    On non-markdown 2xx responses the body is preserved for reuse,
    #    avoiding a redundant HTTP round-trip in step 2.
    if _remaining() > _MIN_STRATEGY_BUDGET:
        md_content, fallback_body, fallback_ct = _try_markdown_negotiation(
            url,
            timeout=min(timeout, _remaining()),
            proxy=proxy,
        )
        if md_content:
            logger.info(
                f"Successfully fetched {url} using strategy: markdown_negotiation"
            )
            return _format_text(md_content)
        if fallback_body:
            body, content_type = fallback_body, fallback_ct

    # Fetch content if markdown negotiation didn't produce a reusable body
    # (e.g. network error, 4xx/5xx, or negotiation was skipped).
    if not body and _remaining() > _MIN_STRATEGY_BUDGET:
        body, content_type = _fetch_raw(
            url,
            timeout=min(timeout, _remaining()),
            proxy=proxy,
            deadline=deadline,
        )

    # Short-circuit: binary content types (images, PDFs, archives, etc.)
    # cannot be meaningfully extracted as text.
    if body and content_type and _is_binary_content_type(content_type):
        raise FetchError(
            f"Unsupported binary content type for {url}: {content_type}"
        )

    # Short-circuit: non-HTML content types (JSON, plain text, XML, etc.)
    # can be returned directly without running HTML extraction.
    if body and content_type in _NON_HTML_CONTENT_TYPES:
        logger.info(
            f"Successfully fetched {url} using strategy: direct "
            f"(content_type: {content_type})"
        )
        return _format_text(body)

    html = body  # treat as HTML for remaining extraction stages
    local_content = ""
    if html:
        # 2. Try Readability extraction (intelligent article detection)
        readability_content, readability_score = _extract_with_readability(html, url)

        # 3. Try simple soup extraction (CSS selector fallback)
        #    Skipped when readability already produced a high-confidence,
        #    substantive result (P3 optimisation).
        if _should_skip_soup(readability_content, readability_score, url):
            soup_content = ""
        else:
            soup_content = _extract_with_soup(html)

        # Pick the best local result
        best = _pick_local_content(
            readability_content, readability_score, soup_content, url,
        )
        if best:
            return _format_text(best)

        # Stash best local result for final fallback
        local_content = readability_content or soup_content or ""

    # 4. Try CDP rendering (self-hosted browser) if configured
    if cdp_endpoint and _remaining() > _MIN_STRATEGY_BUDGET:
        cdp_budget = min(_remaining(), 15.0)
        cdp_result, cdp_local = _try_cdp_extraction(url, cdp_endpoint, cdp_budget)
        if cdp_result:
            return _format_text(cdp_result)
        if len(cdp_local) > len(local_content):
            local_content = cdp_local

    # 5. Local extraction insufficient — try Jina Reader
    jina_content = _try_jina_extraction(
        url,
        local_content=local_content,
        timeout=timeout,
        remaining=_remaining(),
        proxy=proxy,
        api_key_parser=api_key_parser,
        deadline=deadline,
    )
    if jina_content:
        return _format_text(jina_content)

    # 6. Fall back to best local result if available
    if local_content:
        logger.info(
            f"Successfully fetched {url} using strategy: local_fallback "
            f"(low_quality, length: {len(local_content)})"
        )
        return _format_text(local_content)

    logger.warning(f"All extraction strategies failed for {url}")
    raise FetchError(f"Unable to fetch content from {url}")


def _try_markdown_negotiation(
    url: str,
    timeout: float = TIMEOUT_DEFAULT,
    proxy: str | None = None,
) -> tuple[str, str, str]:
    """Attempt to fetch markdown content via Cloudflare Content Negotiation.

    Sends a standard HTTP GET request with ``Accept: text/markdown`` header.
    If the origin server (or Cloudflare) supports content negotiation and
    returns markdown, the markdown content is returned.  Otherwise, the
    response body is preserved so the caller can reuse it for local
    extraction (avoiding a redundant HTTP round-trip).

    Args:
        url: The URL to fetch content from.
        timeout: Timeout for the HTTP request.  Defaults to TIMEOUT_DEFAULT.
        proxy: Proxy to use for the HTTP request.  Defaults to None.

    Returns:
        A ``(md_content, fallback_body, fallback_ct)`` tuple.

        - When the server returns markdown: ``(markdown_text, "", "")``.
        - When the server returns a non-markdown 2xx response:
          ``("", response_body, content_type)`` so the caller can reuse
          the body for readability/soup extraction.
        - On any error (network failure, 4xx/5xx): ``("", "", "")``.
    """
    try:
        ua = generate(browser=["chrome", "edge"])
        ua.headers.accept_ch("Sec-CH-UA-Platform-Version, Sec-CH-UA-Full-Version-List")
        headers = ua.headers.get()
        headers["Accept"] = "text/markdown"
        response = cast(
            Response,
            _http_get(
                url,
                headers=headers,
                timeout=timeout,
                proxy=proxy,
            ),
        )

        # Capture body and content-type before status check so we can
        # return them on non-markdown 2xx responses.
        body = response.text
        raw_ct = response.headers.get("content-type", "")
        ct = raw_ct.split(";")[0].strip().lower()

        # On error status, don't reuse — let _fetch_raw handle retries.
        if response.status_code >= 400:
            logger.debug(
                f"Markdown negotiation got HTTP {response.status_code} for {url}"
            )
            return "", "", ""

        if "text/markdown" in raw_ct:
            # Log markdown token count if provided by Cloudflare
            md_tokens = response.headers.get("x-markdown-tokens")
            if md_tokens:
                logger.debug(f"Markdown tokens for {url}: {md_tokens}")
            return body, "", ""

        # Non-markdown success — return body for reuse.
        logger.debug(
            f"Markdown negotiation not supported for {url} "
            f"(Content-Type: {raw_ct})"
        )
        return "", body, ct
    except Exception as e:
        logger.debug(f"Markdown negotiation failed for {url}: {e}")
        return "", "", ""


# Buffer (in seconds) added to the Jina X-Timeout to derive the httpx
# transport timeout.  This ensures the HTTP client does not time out before
# Jina finishes rendering the page.
_JINA_TIMEOUT_BUFFER = 10.0

# Jina Reader engines tried in order.  ``browser`` is the default; if it
# returns insufficient content we retry with ``cf-browser-rendering`` which
# is specifically designed for JS-heavy websites.
_JINA_ENGINES: list[str] = ["browser", "cf-browser-rendering"]

# Common CSS selectors for main content areas.  Used with the Jina
# ``X-Wait-For-Selector`` header so the reader waits until at least one of
# these elements is present before capturing the page.
_JINA_WAIT_SELECTORS = (
    "main, article, .content, #content, .main-content, #main-content, [role='main']"
)


def _get_content_with_jina_reader(
    url: str,
    return_format: Literal["markdown", "text", "html"] = "markdown",
    timeout: float = TIMEOUT_DEFAULT,
    proxy: str | None = None,
    api_key_parser: APIKeyParser | None = None,
    deadline: float | None = None,
) -> str:
    """Fetch parsed content from Jina AI Reader for a given URL.

    Tries the ``browser`` engine first.  If the result is empty or
    insufficient, retries with the ``cf-browser-rendering`` engine which
    is optimised for JS-heavy / SPA websites.

    The Jina ``X-Timeout`` header is set to *timeout* while the httpx
    transport timeout is set to ``timeout + _JINA_TIMEOUT_BUFFER`` so
    that the HTTP client never races against the Jina rendering deadline.
    When ``deadline`` is supplied, engine iteration stops once the deadline
    has been reached.

    Args:
        url: The URL to fetch content from.
        return_format: The format of the returned content.
            Defaults to ``"markdown"``.
        timeout: Maximum seconds Jina should spend rendering the page.
            Defaults to TIMEOUT_DEFAULT.
        proxy: Proxy to use for the HTTP request.  Defaults to ``None``.
        api_key_parser: Optional API key parser for authentication.
        deadline: Optional shared ``time.monotonic()`` deadline.

    Returns:
        Parsed content from Jina AI, or empty string on failure.
    """
    content = ""
    for engine in _JINA_ENGINES:
        if deadline is not None and time.monotonic() >= deadline:
            logger.debug(f"Deadline exceeded before Jina engine '{engine}' for {url}")
            break
        # Get next valid API key for this attempt (if available)
        api_key: str | None = None
        if api_key_parser:
            try:
                api_key = api_key_parser.get_next_valid_key()
            except ValueError:
                logger.debug(
                    "All Jina API keys currently failed, proceeding without key"
                )

        content = _jina_reader_request(
            url,
            engine=engine,
            return_format=return_format,
            timeout=timeout,
            proxy=proxy,
            api_key=api_key,
            api_key_parser=api_key_parser,
            deadline=deadline,
        )
        if content and _is_content_sufficient(content):
            return content
        if engine != _JINA_ENGINES[-1]:
            logger.debug(
                f"Jina Reader engine '{engine}' returned insufficient content "
                f"for {url}, retrying with next engine"
            )
    return content  # may be empty or low-quality; caller decides


def _jina_reader_request(
    url: str,
    engine: str = "browser",
    return_format: Literal["markdown", "text", "html"] = "markdown",
    timeout: float = TIMEOUT_DEFAULT,
    proxy: str | None = None,
    api_key: str | None = None,
    api_key_parser: APIKeyParser | None = None,
    deadline: float | None = None,
) -> str:
    """Send a single request to the Jina Reader API.

    Args:
        url: The URL to fetch content from.
        engine: Jina rendering engine (``"browser"``,
            ``"cf-browser-rendering"``, or ``"direct"``).
        return_format: Desired output format.
        timeout: Maximum seconds Jina should spend rendering the page.
        proxy: Optional HTTP proxy URL.
        api_key: Optional Jina API key for the ``Authorization`` header.
        api_key_parser: Optional parser for marking failed keys.
        deadline: Optional ``time.monotonic()`` deadline.  When provided,
            both the X-Timeout header and the httpx transport timeout
            are clamped so the request cannot run past the deadline.

    Returns:
        Extracted content string, or empty string on failure.
    """
    try:
        if deadline is not None:
            remaining = max(0.0, deadline - time.monotonic())
            if remaining <= 0:
                return ""
            effective_timeout = min(timeout, remaining)
            transport_timeout = min(effective_timeout + _JINA_TIMEOUT_BUFFER, remaining)
        else:
            effective_timeout = timeout
            # httpx timeout must exceed Jina's rendering timeout so we don't
            # abort the HTTP connection before Jina finishes.
            transport_timeout = timeout + _JINA_TIMEOUT_BUFFER

        headers: dict[str, str] = {
            "Accept": "application/json",
            "X-Return-Format": return_format,
            "X-Engine": engine,
            "X-Timeout": str(max(1, int(effective_timeout))),
            "X-Remove-Selector": "header, footer, nav, aside",
            "X-Wait-For-Selector": _JINA_WAIT_SELECTORS,
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        jina_reader_url = "https://r.jina.ai/"
        logger.debug(f"Jina Reader request for {url} (engine: {engine})")
        response = cast(
            Response,
            _http_post(
                jina_reader_url,
                json={"url": url},
                headers=headers,
                timeout=transport_timeout,
                proxy=proxy,
            ),
        )
        response.raise_for_status()

        data = response.json()
        content = data.get("data", {}).get("content", "")
        if content:
            logger.debug(
                f"Jina Reader ({engine}) returned {len(content)} chars for {url}"
            )
        else:
            logger.debug(f"Jina Reader ({engine}) returned empty content for {url}")
        return content
    except HTTPError as e:
        status = e.status_code
        logger.debug(f"Jina Reader ({engine}) HTTP Error [{status}]: {e}")
        if api_key and api_key_parser:
            if status in (401, 403):
                api_key_parser.mark_key_failed(api_key, f"HTTP {status}", ttl=3600.0)
            elif status == 429:
                api_key_parser.mark_key_failed(api_key, "rate limited", ttl=300.0)
        return ""
    except Exception as e:
        logger.debug(f"Jina Reader ({engine}) error: {e}")
        return ""


def _fetch_raw(
    url: str,
    timeout: float = TIMEOUT_DEFAULT,
    proxy: str | None = None,
    deadline: float | None = None,
) -> tuple[str, str]:
    """Fetch raw content from a URL with retry for transient failures.

    Retries up to ``_FETCH_MAX_RETRIES`` times with exponential backoff
    for server errors (5xx), timeouts, and network errors.  Client errors
    (4xx) are considered definitive and are not retried.  When ``deadline``
    is provided, both the per-attempt HTTP timeout and the backoff sleep
    are capped so the total wall-clock time never exceeds the caller's
    budget.

    Args:
        url: The URL to fetch.
        timeout: Per-attempt request timeout in seconds.  Also used as the
            implicit deadline when ``deadline`` is ``None``.
        proxy: Optional proxy URL.
        deadline: Optional ``time.monotonic()`` value past which no further
            attempts or backoff sleeps should be made.  When ``None``, a
            deadline equal to ``time.monotonic() + timeout`` is assumed so
            standalone callers also get bounded behaviour.

    Returns:
        A ``(body, content_type)`` tuple.  ``content_type`` is the MIME
        type portion of the ``Content-Type`` header (e.g. ``"text/html"``),
        lowercased.  On failure both elements are empty strings.
    """
    effective_deadline = (
        deadline if deadline is not None else time.monotonic() + max(0.0, timeout)
    )
    last_exception: Exception | None = None
    for attempt in range(_FETCH_MAX_RETRIES):
        remaining = max(0.0, effective_deadline - time.monotonic())
        if remaining <= 0:
            logger.debug(f"Deadline exceeded before attempt {attempt + 1} for {url}")
            break
        per_attempt_timeout = min(timeout, remaining)
        try:
            ua = generate(browser=["chrome", "edge"])
            ua.headers.accept_ch(
                "Sec-CH-UA-Platform-Version, Sec-CH-UA-Full-Version-List"
            )
            response = cast(
                Response,
                _http_get(
                    url,
                    headers=ua.headers.get(),
                    timeout=per_attempt_timeout,
                    proxy=proxy,
                ),
            )
            response.raise_for_status()
            # Extract the MIME type (drop charset and parameters).
            raw_ct = response.headers.get("content-type", "")
            content_type = raw_ct.split(";")[0].strip().lower()
            return response.text, content_type
        except HTTPError as e:
            status = e.status_code
            if 400 <= status < 500:
                # Client errors are definitive — do not retry.
                logger.debug(f"HTTP Error [{status}]: {e}")
                return "", ""
            # 5xx server error — retryable
            last_exception = e
            logger.debug(
                f"HTTP Error [{status}] on attempt {attempt + 1}/{_FETCH_MAX_RETRIES} "
                f"for {url}: {e}"
            )
        except (HttpTimeoutError, HttpConnectionError) as e:
            last_exception = e
            logger.debug(
                f"Transient error on attempt {attempt + 1}/{_FETCH_MAX_RETRIES} "
                f"for {url}: {e}"
            )
        except Exception as e:
            # Unexpected errors are not retried.
            logger.debug(f"Error fetching {url}: {e}")
            return "", ""

        # Exponential backoff before next retry, capped by remaining budget.
        if attempt < _FETCH_MAX_RETRIES - 1:
            delay = _FETCH_RETRY_BASE_DELAY * (2**attempt)
            remaining_after = max(0.0, effective_deadline - time.monotonic())
            if remaining_after <= 0:
                logger.debug(
                    f"Deadline exceeded after attempt {attempt + 1} for {url}; "
                    f"skipping backoff"
                )
                break
            sleep_for = min(delay, remaining_after)
            logger.debug(f"Retrying {url} in {sleep_for:.1f}s")
            time.sleep(sleep_for)

    logger.debug(
        f"All {_FETCH_MAX_RETRIES} attempts failed for {url}: {last_exception}"
    )
    return "", ""


def _extract_with_readability(html: str, url: str) -> tuple[str, float]:
    """Extract content using the Readability algorithm.

    Uses Mozilla Readability-style scoring to identify and extract the
    main article content from arbitrary web pages.

    Args:
        html: Raw HTML string.
        url: Original URL (passed to readability for link resolution).

    Returns:
        ``(text, score)`` tuple.  *text* is the plain text of the main
        article (empty string on failure); *score* is the readability
        score of the best candidate (0.0 on failure or when the result
        was too short).
    """
    try:
        result = readability_extract(html, url=url)
        if result.length >= _MIN_CONTENT_LENGTH:
            return result.text, result.score
        logger.debug(f"Readability extraction too short ({result.length} chars)")
        return "", 0.0
    except Exception as e:
        logger.debug(f"Readability extraction failed: {e}")
        return "", 0.0


def _extract_with_soup(html: str) -> str:
    """Simple content extraction using zerodep soup.

    Fallback for when readability fails. Decomposes non-content tags,
    then walks ``_SOUP_CONTENT_SELECTORS`` to find the main content
    container.

    Args:
        html: Raw HTML string.

    Returns:
        Extracted text, or empty string.
    """
    try:
        soup = Soup(html)
        for element in soup.find_all(
            ["script", "style", "nav", "footer", "iframe", "noscript"]
        ):
            element.decompose()

        main_content = None
        for tag, attrs in _SOUP_CONTENT_SELECTORS:
            main_content = soup.find(tag, attrs)
            if main_content:
                break

        content_source = main_content if main_content else soup.find("body")
        if not content_source:
            return ""
        return content_source.get_text(separator=" ", strip=True)
    except Exception as e:
        logger.debug(f"Soup extraction failed: {e}")
        return ""


def _format_text(text: str) -> str:
    """
    Format text content.

    Args:
        text (str): The input text.

    Returns:
        str: Formatted text.
    """
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[^\S\n]+", " ", text)
    text = re.sub(r"\n+", "\n", text)
    text = text.strip()
    return text
