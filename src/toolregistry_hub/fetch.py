"""Fetch and extract content from URLs."""

from __future__ import annotations

import os
import re
import threading
import time
import types
import unicodedata
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Literal, NamedTuple, TypedDict, cast
from urllib.parse import urljoin, urlsplit

from ._vendor.httpclient import (
    HttpConnectionError,
    HTTPError,
    HttpTimeoutError,
    Response,
    ResponseTooLargeError,
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
from .url_policy import (
    URLPolicyError,
    validate_fetch_request,
    validate_target_url,
)

if TYPE_CHECKING:
    from .utils.api_key_parser import APIKeyParser

logger = get_logger()

TIMEOUT_DEFAULT = 30.0

# Largest response body fetch buffers by default, in bytes.  Text extraction
# never needs more, and the cap stops one request from exhausting process
# memory before the content-type check can reject it.  ``Fetch`` accepts an
# override and reads ``FETCH_MAX_RESPONSE_SIZE`` when the argument is omitted.
_DEFAULT_MAX_RESPONSE_SIZE = 10 * 1024 * 1024

#: Environment variable that overrides the default cap when ``Fetch`` is
#: constructed without ``max_response_size``.
_MAX_RESPONSE_SIZE_ENV = "FETCH_MAX_RESPONSE_SIZE"

# Redirect hops fetch follows itself.  Matches the vendored client's default;
# each hop is validated before the next request is sent.
_MAX_REDIRECTS = 10
_REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})

StrategyName = Literal[
    "auto",
    "markdown",
    "readability",
    "soup",
    "veilrender",
    "cdp",
    "jina",
]


class FetchResult(TypedDict):
    """Structured result returned by Fetch.fetch_content."""

    content: str
    url: str
    strategy: str
    quality: str
    content_type: str
    cached: bool
    elapsed_ms: int
    metadata: dict[str, object]


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

    content: FetchResult
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

    def get(self, url: str) -> FetchResult | None:
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

    def put(self, url: str, content: FetchResult) -> None:
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


class FetchPolicyError(FetchError):
    """Raised when a target, proxy or redirect violates the outbound policy.

    A policy refusal aborts the whole fetch: falling back to the next
    strategy would hide the block and, for a redirect, could still return
    content from the refused destination.
    """


def _log_policy_refusal(exc: URLPolicyError, *, stage: str, url: str) -> None:
    """Log a refused destination without the resolved address."""
    logger.warning(
        f"fetch_content blocked ({stage}): reason={exc.reason} host={_url_host(url)!r}"
    )


def _enforce_request_policy(
    url: str,
    proxy: str | None,
    *,
    allow_private_hosts: bool,
) -> None:
    """Validate the caller-supplied target and proxy before any I/O."""
    try:
        validate_fetch_request(url, proxy, allow_private_hosts=allow_private_hosts)
    except URLPolicyError as exc:
        _log_policy_refusal(exc, stage="request", url=url)
        raise FetchPolicyError(str(exc)) from exc


def _enforce_final_url_policy(
    response: Response,
    *,
    allow_private_hosts: bool,
    stage: str,
) -> None:
    """Refuse a response whose final URL left the allowed address space.

    The manual redirect loop validates every hop before the request is sent.
    This check is the backstop for the response that actually produced the
    body: with ``follow_redirects=False`` its URL is the last request URL, so
    a bug in the loop still cannot return content from a refused address.
    """
    final_url = getattr(response, "url", None)
    if not isinstance(final_url, str) or not final_url:
        # A real Response always carries a string URL; only test doubles
        # that omit it reach this branch.
        return
    try:
        validate_target_url(final_url, allow_private_hosts=allow_private_hosts)
    except URLPolicyError as exc:
        _log_policy_refusal(exc, stage=stage, url=final_url)
        raise FetchPolicyError(f"redirect target refused: {exc}") from exc


def _url_host(url: str | None) -> str:
    """Return the host of *url*, or ``""`` when it is missing or unparsable."""
    if not url:
        return ""
    try:
        return urlsplit(url).hostname or ""
    except ValueError:
        return ""


def _request_with_redirects(
    method: str,
    url: str,
    send: Callable[[str, str], Response],
    *,
    allow_private_hosts: bool,
    stage: str,
) -> Response:
    """Issue a request, validating every redirect hop before dialing it.

    The vendored client is called with ``follow_redirects=False``, so a 3xx
    response never opens a connection on its own.  Each ``Location`` is
    resolved against the current URL and checked with the same outbound
    policy, which rejects non-http(s) schemes and non-public addresses before
    the next request is sent.

    Args:
        method: ``"GET"`` or ``"POST"`` for the first request.
        url: First request URL.
        send: Callable ``(url, method) -> Response`` that performs exactly one
            request with the caller's headers, timeout and proxy.
        allow_private_hosts: Skip the address-class checks for every hop.
        stage: Log category for a refused hop.

    Returns:
        The first non-redirect response, or a redirect without ``Location``.

    Raises:
        FetchPolicyError: If a hop violates the outbound policy.
        FetchError: If the chain exceeds ``_MAX_REDIRECTS``.

    Note:
        The connection is not pinned to the validated address: the vendored
        client resolves the name again when it dials, so a DNS rebinding
        between the check and the connect is still possible (zerodep #305).
    """
    current_url = url
    current_method = method
    for _ in range(_MAX_REDIRECTS + 1):
        response = send(current_url, current_method)
        if response.status_code not in _REDIRECT_STATUSES:
            return response
        location = response.headers.get("location")
        if not location:
            return response
        next_url = urljoin(current_url, location)
        try:
            validate_target_url(next_url, allow_private_hosts=allow_private_hosts)
        except URLPolicyError as exc:
            _log_policy_refusal(exc, stage=f"{stage}-redirect", url=next_url)
            raise FetchPolicyError(f"redirect target refused: {exc}") from exc
        # 303 always switches to GET; 301/302 do so for a POST.  307/308
        # preserve the method, and fetch sends no body on its GET paths.
        if response.status_code == 303 or (
            response.status_code in (301, 302) and current_method == "POST"
        ):
            current_method = "GET"
        current_url = next_url
    raise FetchError(
        f"too many redirects for host {_url_host(url)!r} (limit {_MAX_REDIRECTS})"
    )


def _response_too_large_error(url: str, exc: ResponseTooLargeError) -> FetchError:
    """Map a capped body to ``FetchError`` naming the host and the limit.

    ``exc.url`` is the address that produced the body, after any redirect
    and for a reader endpoint as well as the page itself.  When its host is
    not the host being fetched, the message names both so the reader does
    not infer that the target host answered.

    The vendored exception message contains the full URL; rebuilding it here
    keeps the error text to hostnames and never includes a resolved address.
    Call sites raise the result with ``from None`` so a traceback cannot
    reach that message either: a URL may carry userinfo.
    """
    target = _url_host(url)
    source = _url_host(exc.url)
    if source and source != target:
        return FetchError(
            f"response from {source!r} for {target!r} exceeds the "
            f"{exc.max_size}-byte fetch limit"
        )
    return FetchError(
        f"response from {(target or source)!r} exceeds the "
        f"{exc.max_size}-byte fetch limit"
    )


def _resolve_max_response_size(value: int | None) -> int:
    """Return the response cap from *value*, the environment, or the default.

    Args:
        value: The constructor argument, or ``None`` to fall back to the
            ``FETCH_MAX_RESPONSE_SIZE`` environment variable and then
            :data:`_DEFAULT_MAX_RESPONSE_SIZE`.

    Returns:
        A positive byte limit.

    Raises:
        ValueError: If the argument or the environment value is not a
            positive integer.
    """
    name = "max_response_size"
    if value is None:
        raw = os.environ.get(_MAX_RESPONSE_SIZE_ENV, "").strip()
        if not raw:
            return _DEFAULT_MAX_RESPONSE_SIZE
        name = _MAX_RESPONSE_SIZE_ENV
        try:
            value = int(raw)
        except ValueError:
            raise ValueError(
                f"{_MAX_RESPONSE_SIZE_ENV} must be a positive integer, got {raw!r}"
            ) from None
    # ``bool`` is an ``int`` subclass, so ``True`` would otherwise count as 1.
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer, got {value!r}")
    return value


def _cdp_too_large_error(url: str, max_response_size: int) -> FetchError:
    """Refuse a CDP-rendered page larger than the configured fetch limit.

    The browser-side probe counts UTF-16 code units, so the message calls
    the same numeric cap a character limit.  Like
    :func:`_response_too_large_error`, it names the caller-supplied host and
    never the rendered content or a resolved address.
    """
    try:
        host = urlsplit(url).hostname or ""
    except ValueError:
        host = ""
    return FetchError(
        f"CDP-rendered page from {host!r} exceeds the "
        f"{max_response_size}-character fetch limit"
    )


def _make_result(
    *,
    content: str,
    url: str,
    strategy: str,
    quality: str = "high",
    content_type: str = "",
    cached: bool = False,
    started_at: float,
    metadata: dict[str, object] | None = None,
) -> FetchResult:
    """Build a structured fetch result."""
    return {
        "content": content,
        "url": url,
        "strategy": strategy,
        "quality": quality,
        "content_type": content_type,
        "cached": cached,
        "elapsed_ms": int((time.monotonic() - started_at) * 1000),
        "metadata": metadata or {},
    }


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
        veilrender_endpoint: str | None = None,
        veilrender_token: str | None = None,
        cache_ttl: float = _CACHE_TTL_DEFAULT,
        cache_maxsize: int = _CACHE_MAXSIZE_DEFAULT,
        allow_private_hosts: bool | None = None,
        max_response_size: int | None = None,
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
            veilrender_endpoint: Base URL of a VeilRender instance
                (e.g. ``https://oaklight-veilrender.hf.space``).  Falls
                back to ``VEILRENDER_ENDPOINT`` env var.  Used as a
                browser-rendering fallback via REST API when CDP is
                unavailable.
            veilrender_token: Bearer token for VeilRender auth.  Falls
                back to ``VEILRENDER_TOKEN`` env var.
            cache_ttl: Time-to-live in seconds for cached URL results.
                Set to ``0`` to disable caching.  Defaults to 300 (5 min).
            cache_maxsize: Maximum number of entries in the URL cache.
                Defaults to 128.
            allow_private_hosts: Allow the target URL and proxy to use
                private addresses.  Defaults to ``False``; when ``None``,
                the ``FETCH_ALLOW_PRIVATE_HOSTS`` environment variable is
                read (``1``, ``true``, ``yes`` or ``on`` enables it).  The
                scheme restriction to http/https always applies.
            max_response_size: Largest response body, in bytes, that any
                request buffers.  Must be a positive integer.  When
                ``None``, the ``FETCH_MAX_RESPONSE_SIZE`` environment
                variable is read; without that, 10 MiB.  The same value
                bounds markdown negotiation, the raw fetch, Jina Reader and
                VeilRender.

        Raises:
            ValueError: If *max_response_size* (or the environment value
                behind it) is not a positive integer.
        """
        from .utils.api_key_parser import APIKeyParser

        parser = APIKeyParser(
            api_keys=api_keys,
            env_var_name="JINA_API_KEY",
            rate_limit_delay=0.0,
        )
        self.api_key_parser: APIKeyParser | None = parser if parser.api_keys else None
        self.cdp_endpoint: str | None = cdp_endpoint or os.environ.get("CDP_ENDPOINT")
        self.veilrender_endpoint: str | None = veilrender_endpoint or os.environ.get(
            "VEILRENDER_ENDPOINT"
        )
        self.veilrender_token: str | None = veilrender_token or os.environ.get(
            "VEILRENDER_TOKEN"
        )
        if allow_private_hosts is None:
            raw_flag = os.environ.get("FETCH_ALLOW_PRIVATE_HOSTS", "").strip().lower()
            allow_private_hosts = raw_flag in {"1", "true", "yes", "on"}
            if raw_flag and not allow_private_hosts:
                logger.warning(
                    "FETCH_ALLOW_PRIVATE_HOSTS is set but not recognised "
                    f"({raw_flag!r}); private destinations stay blocked"
                )
        self._allow_private_hosts: bool = bool(allow_private_hosts)
        self.max_response_size: int = _resolve_max_response_size(max_response_size)
        self._cache: _URLCache | None = (
            _URLCache(ttl=cache_ttl, maxsize=cache_maxsize) if cache_ttl > 0 else None
        )
        self._narrow_strategy_annotation()

    def _available_strategies(self) -> tuple[str, ...]:
        """Return strategies available in this instance."""
        strategies = ["auto", "markdown", "readability", "soup", "jina"]
        if self.veilrender_endpoint:
            strategies.append("veilrender")
        if self.cdp_endpoint:
            strategies.append("cdp")
        return tuple(strategies)

    def _narrow_strategy_annotation(self) -> None:
        """Narrow strategy Literal to strategies available in this instance."""
        original = type(self).fetch_content
        new_func = types.FunctionType(
            original.__code__,
            original.__globals__,
            name=original.__name__,
            argdefs=original.__defaults__,
            closure=original.__closure__,
        )
        new_func.__doc__ = original.__doc__
        new_func.__qualname__ = original.__qualname__
        new_func.__kwdefaults__ = original.__kwdefaults__
        new_func.__annotations__ = dict(original.__annotations__)
        new_func.__annotations__["strategy"] = Literal.__getitem__(
            self._available_strategies()
        )
        self.fetch_content = types.MethodType(new_func, self)  # type: ignore[method-assign]

    def _is_configured(self) -> bool:
        """Check if Fetch is configured.

        Always returns True because Jina API keys are optional.
        Fetch works without keys (unauthenticated requests).
        """
        return True

    def _clear_cache(self) -> None:
        """Remove all cached URL results (internal, not exposed as a tool)."""
        if self._cache is not None:
            self._cache.clear()

    def fetch_content(
        self,
        url: str,
        timeout: float = TIMEOUT_DEFAULT,
        proxy: str | None = None,
        strategy: StrategyName = "auto",
    ) -> FetchResult:
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
            strategy: Strategy to use. Leave as ``"auto"`` for normal use.
                Auto already tries the best available fallback chain. Only set
                a specific strategy when retrying after auto returned low-quality
                or unsuitable content.

                Retry hints:
                - ``"markdown"``: fast check for sites that support Markdown
                  content negotiation.
                - ``"readability"``: local article extraction for normal HTML.
                - ``"soup"``: local fallback when readability misses content.
                - ``"veilrender"`` / ``"cdp"``: JS-heavy pages or SPA shells.
                - ``"jina"``: external reader fallback when local/browser
                  rendering is poor.

                Available choices are narrowed at runtime; ``veilrender`` and
                ``cdp`` appear only when configured.

        Returns:
            Structured result with content, strategy, quality, cache status,
            elapsed time, and metadata.

        Raises:
            FetchError: If every extraction strategy fails or the deadline
                is exceeded before any content can be retrieved.
            FetchPolicyError: If the URL, the proxy or a redirect target is
                refused by the outbound address policy.
        """
        started_at = time.monotonic()
        strategy = strategy.lower().strip()  # type: ignore[assignment]
        if strategy not in self._available_strategies():
            raise ValueError(
                f"Strategy {strategy!r} is not available. "
                f"Available: {self._available_strategies()}"
            )

        # The address policy runs before the cache: a URL blocked by the
        # current policy must not be served from an entry stored earlier.
        _enforce_request_policy(
            url,
            proxy,
            allow_private_hosts=self._allow_private_hosts,
        )

        cache_key = f"{strategy}:{url}"
        if self._cache is not None:
            cached = self._cache.get(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit for {cache_key}")
                cached = dict(cached)
                cached["cached"] = True
                cached["elapsed_ms"] = int((time.monotonic() - started_at) * 1000)
                return cast(FetchResult, cached)

        try:
            result = _extract(
                url,
                timeout=timeout,
                proxy=proxy,
                api_key_parser=self.api_key_parser,
                cdp_endpoint=self.cdp_endpoint,
                veilrender_endpoint=self.veilrender_endpoint,
                veilrender_token=self.veilrender_token,
                strategy=strategy,
                started_at=started_at,
                allow_private_hosts=self._allow_private_hosts,
                max_response_size=self.max_response_size,
            )
            if self._cache is not None:
                self._cache.put(cache_key, result)
            return result
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


def _has_spa_indicators(text: str) -> bool:
    """Check whether *text* contains SPA shell indicator phrases.

    Strict indicators (e.g. ``"please enable javascript"``) are always
    checked.  Broader indicators (e.g. ``"loading..."``) are only checked
    when the text is shorter than ``_SPA_SHORT_TEXT_THRESHOLD`` characters,
    because they appear legitimately in long articles.

    Args:
        text: Lowercased text to scan.

    Returns:
        True if any indicator was found.
    """
    for indicator in _SPA_SHELL_INDICATORS:
        if indicator in text:
            return True
    if len(text) < _SPA_SHORT_TEXT_THRESHOLD:
        for indicator in _SPA_SHELL_INDICATORS_SHORT:
            if indicator in text:
                return True
    return False


def _is_navigation_only(text: str) -> bool:
    """Detect pages that consist mostly of short navigation links.

    Returns True when the text has many lines, most of them are short
    (menu items / breadcrumbs), and there are fewer than
    ``_NAV_MIN_LONG_LINES`` real paragraph-length lines.

    Args:
        text: The extracted text content.

    Returns:
        True if the text looks like navigation-only content.
    """
    lines = [line for line in text.split("\n") if line.strip()]
    if len(lines) <= _NAV_MIN_LINES:
        return False
    short_lines = sum(
        1 for line in lines if len(line.strip()) < _NAV_SHORT_LINE_THRESHOLD
    )
    short_ratio = short_lines / len(lines)
    if short_ratio <= _NAV_SHORT_LINE_RATIO:
        return False
    long_lines = sum(
        1 for line in lines if len(line.strip()) >= _NAV_LONG_LINE_THRESHOLD
    )
    return long_lines < _NAV_MIN_LONG_LINES


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
    if readability_score < _READABILITY_SCORE_THRESHOLD and _has_spa_indicators(
        text.lower()
    ):
        return False

    return not _is_navigation_only(text)


def _pick_local_content(
    readability_content: str,
    readability_score: float,
    soup_content: str,
    url: str,
) -> tuple[str, str, float]:
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
        if not candidate or not _is_content_sufficient(
            candidate, readability_score=score
        ):
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
        return candidate, strategy, score
    return "", "", 0.0


def _validate_cdp_final_url(final_url: object, *, allow_private_hosts: bool) -> None:
    """Refuse a CDP page whose final address is missing or not public."""
    if not isinstance(final_url, str) or not final_url:
        raise FetchPolicyError(
            "CDP page address could not be confirmed; refusing content"
        )
    try:
        validate_target_url(final_url, allow_private_hosts=allow_private_hosts)
    except URLPolicyError as exc:
        _log_policy_refusal(exc, stage="cdp", url=final_url)
        raise FetchPolicyError(f"CDP redirect target refused: {exc}") from exc


def _cdp_page_size(client: Any, target_id: str) -> int | None:
    """Return the rendered page length in UTF-16 code units, or ``None``.

    A page with a document element answers with a number; a missing element
    or an unexpected result is reported as ``None`` so the caller refuses
    the content instead of transferring an unbounded string.
    """
    size = client.evaluate(target_id, "document.documentElement.outerHTML.length")
    if isinstance(size, bool) or not isinstance(size, int):
        return None
    return size


def _render_with_cdp(
    url: str,
    cdp_endpoint: str,
    timeout: float = 15.0,
    *,
    allow_private_hosts: bool = False,
    max_response_size: int = _DEFAULT_MAX_RESPONSE_SIZE,
) -> str:
    """Render a page via CDP and return the rendered HTML.

    Connects to a CDP-compatible browser, navigates to the URL,
    waits for page load, and extracts the fully-rendered HTML
    (post-JavaScript execution).

    The browser follows redirects itself, so the final page address is
    read from ``document.location.href`` before any HTML is returned.  If
    that address cannot be read, or it violates the outbound policy, the
    content is refused (fail closed).

    The page size is probed before the HTML crosses the wire:
    ``document.documentElement.outerHTML.length`` is read first, and a
    value above *max_response_size* raises ``FetchError`` without
    evaluating ``outerHTML``, so an over-size page is normally never
    transferred.  The probe counts UTF-16 code units, and the received
    string is measured again in Python after the read: the DOM can grow
    between the two calls (timers, ``MutationObserver``, SPA hydration),
    and that second check is what guarantees an over-cap string is never
    returned.  Neither measurement is byte-exact; the probe bounds the
    transfer in the normal case, and the returned string always stays
    within the cap.  A probe that does not return an integer is treated as
    an unknown size and the content is refused.

    Args:
        url: The URL to render.
        cdp_endpoint: WebSocket URL of the CDP browser
            (e.g. ``ws://localhost:9222``).
        timeout: Maximum time in seconds to wait for page load.
        allow_private_hosts: Allow a private final address.
        max_response_size: Largest page the probe accepts, in UTF-16 code
            units.  Defaults to the configured response cap.

    Returns:
        Rendered HTML string, or empty string on any failure.

    Raises:
        FetchPolicyError: If the final address is missing or refused.
        FetchError: If the rendered page exceeds the size limit.
    """
    try:
        from ._vendor.cdp import CDPClient

        with CDPClient(cdp_endpoint, timeout=timeout) as client:
            target_id = client.create_target()
            try:
                client.navigate(target_id, url, timeout=timeout)
                final_url = client.evaluate(target_id, "document.location.href")
                _validate_cdp_final_url(
                    final_url, allow_private_hosts=allow_private_hosts
                )
                size = _cdp_page_size(client, target_id)
                if size is None:
                    return ""
                if size > max_response_size:
                    raise _cdp_too_large_error(url, max_response_size)
                html = client.evaluate(target_id, "document.documentElement.outerHTML")
                if not isinstance(html, str) or not html:
                    return ""
                if len(html) > max_response_size:
                    # The DOM can grow between the probe and the read, so the
                    # received string is measured again: an over-cap page must
                    # not be returned even though it crossed the wire once.
                    raise _cdp_too_large_error(url, max_response_size)
                logger.debug(f"CDP rendered {url}: {len(html)} chars of HTML")
                return html
            finally:
                client.close_target(target_id)
    except FetchError:
        raise
    except Exception as e:
        logger.debug(f"CDP rendering failed for {url}: {e}")
        return ""


def _try_cdp_extraction(
    url: str,
    cdp_endpoint: str,
    timeout: float,
    *,
    allow_private_hosts: bool = False,
    max_response_size: int = _DEFAULT_MAX_RESPONSE_SIZE,
) -> tuple[str, str]:
    """Render a page with CDP and attempt readability/soup extraction.

    Args:
        url: The URL to render.
        cdp_endpoint: WebSocket endpoint for the CDP browser.
        timeout: Budget in seconds for the CDP render.
        allow_private_hosts: Allow a private final address.
        max_response_size: Largest rendered page the probe accepts.

    Returns:
        A ``(best_content, local_content)`` tuple.  ``best_content`` is non-empty
        when extraction produced sufficient content; ``local_content`` is the best
        partial result for final-fallback stashing.

    Raises:
        FetchError: If the rendered page exceeds the size limit.
    """
    rendered_html = _render_with_cdp(
        url,
        cdp_endpoint,
        timeout=timeout,
        allow_private_hosts=allow_private_hosts,
        max_response_size=max_response_size,
    )
    if not rendered_html:
        return "", ""

    cdp_readability, cdp_score = _extract_with_readability(rendered_html, url)
    if _should_skip_soup(cdp_readability, cdp_score, url):
        cdp_soup = ""
    else:
        cdp_soup = _extract_with_soup(rendered_html)
    cdp_best, _strategy, _score = _pick_local_content(
        cdp_readability, cdp_score, cdp_soup, url
    )
    if cdp_best:
        logger.info(f"Successfully fetched {url} using strategy: cdp")
        return cdp_best, ""
    return "", cdp_readability or cdp_soup or ""


def _render_with_veilrender(
    url: str,
    endpoint: str,
    token: str | None = None,
    timeout: float = 30.0,
    *,
    allow_private_hosts: bool = False,
    max_response_size: int = _DEFAULT_MAX_RESPONSE_SIZE,
) -> str:
    """Render a page via VeilRender REST API and return the HTML.

    VeilRender reports the page's final URL in ``metadata.url``; it is
    checked before the HTML is returned.  A response that omits it is
    refused (fail closed), because the remote browser may have followed a
    redirect the hub cannot otherwise see.

    The HTML arrives inside the capped JSON response body, so it is bounded
    by *max_response_size* before it is parsed: a JSON string is never
    shorter than the characters it encodes, and the body cap rejects a
    larger document.  No separate length check is needed; a response over
    the cap raises ``FetchError``.

    Args:
        url: The URL to render.
        endpoint: Base URL of the VeilRender instance.
        token: Optional Bearer token for authentication.
        timeout: Maximum time in seconds for the request.
        allow_private_hosts: Allow a private final address.
        max_response_size: Largest VeilRender body to buffer, in bytes.

    Returns:
        Rendered HTML string, or empty string on any failure.

    Raises:
        FetchPolicyError: If the final address is missing or refused.
    """
    try:
        import json

        render_url = f"{endpoint.rstrip('/')}/render"
        payload = json.dumps(
            {
                "url": url,
                "formats": ["html"],
                "timeout": int(timeout * 1000),
            }
        ).encode()

        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        def send(target_url: str, method: str) -> Response:
            """Send one VeilRender request without following redirects."""
            if method == "POST":
                return cast(
                    Response,
                    _http_post(
                        target_url,
                        data=payload,
                        headers=headers,
                        timeout=timeout,
                        max_response_size=max_response_size,
                        follow_redirects=False,
                    ),
                )
            return cast(
                Response,
                _http_get(
                    target_url,
                    headers=headers,
                    timeout=timeout,
                    max_response_size=max_response_size,
                    follow_redirects=False,
                ),
            )

        resp = _request_with_redirects(
            "POST",
            render_url,
            send,
            allow_private_hosts=allow_private_hosts,
            stage="veilrender",
        )

        data = resp.json()
        html = data.get("content", {}).get("html", "")
        if not html:
            return ""
        final_url = (data.get("metadata") or {}).get("url")
        if not isinstance(final_url, str) or not final_url:
            raise FetchPolicyError(
                "VeilRender did not report the final page address; refusing content"
            )
        try:
            validate_target_url(final_url, allow_private_hosts=allow_private_hosts)
        except URLPolicyError as exc:
            _log_policy_refusal(exc, stage="veilrender", url=final_url)
            raise FetchPolicyError(
                f"VeilRender redirect target refused: {exc}"
            ) from exc
        logger.debug(f"VeilRender rendered {url}: {len(html)} chars of HTML")
        return html
    except FetchPolicyError:
        raise
    except FetchError:
        # Too many redirects must reach the caller, not become an empty
        # strategy result.
        raise
    except ResponseTooLargeError as e:
        raise _response_too_large_error(url, e) from None
    except Exception as e:
        logger.debug(f"VeilRender rendering failed for {url}: {e}")
        return ""


def _try_veilrender_extraction(
    url: str,
    endpoint: str,
    token: str | None,
    timeout: float,
    *,
    allow_private_hosts: bool = False,
    max_response_size: int = _DEFAULT_MAX_RESPONSE_SIZE,
) -> tuple[str, str]:
    """Render a page with VeilRender and attempt readability/soup extraction.

    Args:
        url: The URL to render.
        endpoint: Base URL of the VeilRender instance.
        token: Optional Bearer token for authentication.
        timeout: Budget in seconds for the VeilRender request.
        allow_private_hosts: Allow a private final address.
        max_response_size: Largest VeilRender body to buffer, in bytes.

    Returns:
        A ``(best_content, local_content)`` tuple.
    """
    rendered_html = _render_with_veilrender(
        url,
        endpoint,
        token,
        timeout=timeout,
        allow_private_hosts=allow_private_hosts,
        max_response_size=max_response_size,
    )
    if not rendered_html:
        return "", ""

    vr_readability, vr_score = _extract_with_readability(rendered_html, url)
    if _should_skip_soup(vr_readability, vr_score, url):
        vr_soup = ""
    else:
        vr_soup = _extract_with_soup(rendered_html)
    vr_best, _strategy, _score = _pick_local_content(
        vr_readability, vr_score, vr_soup, url
    )
    if vr_best:
        logger.info(f"Successfully fetched {url} using strategy: veilrender")
        return vr_best, ""
    return "", vr_readability or vr_soup or ""


def _try_jina_extraction(
    url: str,
    *,
    local_content: str,
    timeout: float,
    remaining: float,
    proxy: str | None,
    api_key_parser: APIKeyParser | None,
    deadline: float,
    max_response_size: int = _DEFAULT_MAX_RESPONSE_SIZE,
    allow_private_hosts: bool = False,
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
        max_response_size: Largest body to buffer from Jina, in bytes.
        allow_private_hosts: Allow a private redirect target.

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
        max_response_size=max_response_size,
        allow_private_hosts=allow_private_hosts,
    )

    if jina_content and _is_content_sufficient(jina_content):
        logger.info(
            f"Successfully fetched {url} using strategy: jina_reader "
            f"(local reason: {reason})"
        )
        return jina_content
    return ""


def _fetch_body(
    url: str,
    timeout: float,
    proxy: str | None,
    deadline: float,
    *,
    allow_private_hosts: bool = False,
    max_response_size: int = _DEFAULT_MAX_RESPONSE_SIZE,
) -> tuple[str, str]:
    """Fetch the raw body for *url*, trying markdown negotiation first.

    Returns:
        ``(body, content_type)`` tuple.  Both may be empty if every
        attempt failed or the deadline was exceeded.
    """

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
            allow_private_hosts=allow_private_hosts,
            max_response_size=max_response_size,
        )
        if md_content:
            logger.info(
                f"Successfully fetched {url} using strategy: markdown_negotiation"
            )
            return md_content, "_markdown"
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
            allow_private_hosts=allow_private_hosts,
            max_response_size=max_response_size,
        )

    return body, content_type


def _try_local_extraction(html: str, url: str) -> tuple[str, str, str, float]:
    """Run readability and (optionally) soup on *html*.

    Returns:
        ``(best, local_content)`` — *best* is non-empty when a
        sufficient result was found; *local_content* is the best
        partial result for final-fallback stashing.
    """
    readability_content, readability_score = _extract_with_readability(html, url)

    if _should_skip_soup(readability_content, readability_score, url):
        soup_content = ""
    else:
        soup_content = _extract_with_soup(html)

    best, strategy, score = _pick_local_content(
        readability_content,
        readability_score,
        soup_content,
        url,
    )
    local_content = readability_content or soup_content or ""
    return best, local_content, strategy, score


def _strategy_markdown(
    url: str,
    timeout: float,
    proxy: str | None,
    remaining: float,
    started_at: float,
    allow_private_hosts: bool = False,
    max_response_size: int = _DEFAULT_MAX_RESPONSE_SIZE,
    **_kw: object,
) -> FetchResult:
    md_content, _fb, _ct = _try_markdown_negotiation(
        url,
        timeout=min(timeout, remaining),
        proxy=proxy,
        allow_private_hosts=allow_private_hosts,
        max_response_size=max_response_size,
    )
    if not md_content:
        raise FetchError(f"Markdown negotiation did not return content for {url}")
    content = _format_text(md_content)
    return _make_result(
        content=content,
        url=url,
        strategy="markdown",
        content_type="text/markdown",
        started_at=started_at,
        metadata={"content_length": len(content)},
    )


def _strategy_local(
    url: str,
    strategy: str,
    timeout: float,
    proxy: str | None,
    deadline: float,
    remaining: float,
    started_at: float,
    allow_private_hosts: bool = False,
    max_response_size: int = _DEFAULT_MAX_RESPONSE_SIZE,
    **_kw: object,
) -> FetchResult:
    body, content_type = _fetch_raw(
        url,
        timeout=min(timeout, remaining),
        proxy=proxy,
        deadline=deadline,
        allow_private_hosts=allow_private_hosts,
        max_response_size=max_response_size,
    )
    if content_type and _is_binary_content_type(content_type):
        raise FetchError(f"Unsupported binary content type for {url}: {content_type}")
    if strategy == "readability":
        text, score = _extract_with_readability(body, url)
        content = _format_text(text)
        quality = "high" if _is_content_sufficient(text, score) else "low"
        return _make_result(
            content=content,
            url=url,
            strategy="readability",
            quality=quality,
            content_type=content_type,
            started_at=started_at,
            metadata={"readability_score": score, "content_length": len(content)},
        )
    text = _extract_with_soup(body)
    content = _format_text(text)
    quality = "high" if _is_content_sufficient(text) else "low"
    return _make_result(
        content=content,
        url=url,
        strategy="soup",
        quality=quality,
        content_type=content_type,
        started_at=started_at,
        metadata={"content_length": len(content)},
    )


def _strategy_browser(
    url: str,
    strategy: str,
    remaining: float,
    started_at: float,
    cdp_endpoint: str | None = None,
    veilrender_endpoint: str | None = None,
    veilrender_token: str | None = None,
    allow_private_hosts: bool = False,
    max_response_size: int = _DEFAULT_MAX_RESPONSE_SIZE,
    **_kw: object,
) -> FetchResult:
    if strategy == "veilrender":
        if not veilrender_endpoint:
            raise FetchError("VeilRender is not configured")
        result, local = _try_veilrender_extraction(
            url,
            veilrender_endpoint,
            veilrender_token,
            min(remaining, 30.0),
            allow_private_hosts=allow_private_hosts,
            max_response_size=max_response_size,
        )
    else:
        if not cdp_endpoint:
            raise FetchError("CDP is not configured")
        result, local = _try_cdp_extraction(
            url,
            cdp_endpoint,
            min(remaining, 15.0),
            allow_private_hosts=allow_private_hosts,
            max_response_size=max_response_size,
        )
    content = _format_text(result or local)
    return _make_result(
        content=content,
        url=url,
        strategy=strategy,
        quality="high" if result else "low",
        content_type="text/html",
        started_at=started_at,
        metadata={"content_length": len(content)},
    )


def _strategy_jina(
    url: str,
    timeout: float,
    proxy: str | None,
    api_key_parser: APIKeyParser | None,
    deadline: float,
    remaining: float,
    started_at: float,
    max_response_size: int = _DEFAULT_MAX_RESPONSE_SIZE,
    allow_private_hosts: bool = False,
    **_kw: object,
) -> FetchResult:
    content = _try_jina_extraction(
        url,
        local_content="",
        timeout=timeout,
        remaining=remaining,
        proxy=proxy,
        api_key_parser=api_key_parser,
        deadline=deadline,
        max_response_size=max_response_size,
        allow_private_hosts=allow_private_hosts,
    )
    if not content:
        raise FetchError(f"Jina Reader did not return content for {url}")
    formatted = _format_text(content)
    return _make_result(
        content=formatted,
        url=url,
        strategy="jina",
        content_type="text/markdown",
        started_at=started_at,
        metadata={"content_length": len(formatted)},
    )


def _extract_with_strategy(
    url: str,
    *,
    strategy: str,
    timeout: float,
    proxy: str | None,
    api_key_parser: APIKeyParser | None,
    cdp_endpoint: str | None,
    veilrender_endpoint: str | None,
    veilrender_token: str | None,
    deadline: float,
    started_at: float,
    allow_private_hosts: bool = False,
    max_response_size: int = _DEFAULT_MAX_RESPONSE_SIZE,
) -> FetchResult:
    """Run one explicit fetch strategy."""
    remaining = max(0.0, deadline - time.monotonic())
    kwargs = {
        "url": url,
        "strategy": strategy,
        "timeout": timeout,
        "proxy": proxy,
        "api_key_parser": api_key_parser,
        "cdp_endpoint": cdp_endpoint,
        "veilrender_endpoint": veilrender_endpoint,
        "veilrender_token": veilrender_token,
        "deadline": deadline,
        "remaining": remaining,
        "started_at": started_at,
        "allow_private_hosts": allow_private_hosts,
        "max_response_size": max_response_size,
    }
    dispatch = {
        "markdown": _strategy_markdown,
        "readability": _strategy_local,
        "soup": _strategy_local,
        "veilrender": _strategy_browser,
        "cdp": _strategy_browser,
        "jina": _strategy_jina,
    }
    handler = dispatch.get(strategy)
    if handler is None:
        raise ValueError(f"Unknown strategy: {strategy}")
    return handler(**kwargs)


def _extract(
    url: str,
    timeout: float = TIMEOUT_DEFAULT,
    proxy: str | None = None,
    api_key_parser: APIKeyParser | None = None,
    cdp_endpoint: str | None = None,
    veilrender_endpoint: str | None = None,
    veilrender_token: str | None = None,
    strategy: str = "auto",
    started_at: float | None = None,
    allow_private_hosts: bool = False,
    max_response_size: int = _DEFAULT_MAX_RESPONSE_SIZE,
) -> FetchResult:
    """Extract content from a given URL using available methods.

    Strategies are tried in order:
    1. Cloudflare Content Negotiation (zero-cost markdown attempt)
    2. Readability extraction (intelligent article scoring, local)
    3. Simple soup extraction (CSS selector fallback, local)
    4. VeilRender (remote browser rendering via REST API)
    5. CDP rendering (self-hosted browser, re-parsed with readability/soup)
    6. Jina Reader (external API fallback for SPA / JS-heavy pages)

    HTML is fetched once and reused by stages 2 and 3.  ``timeout`` is a
    wall-clock budget for the *whole* operation; strategies are skipped once
    the deadline is exceeded.

    Args:
        url: The URL to extract content from.
        timeout: Total wall-clock timeout in seconds. Defaults to TIMEOUT_DEFAULT.
        proxy: Proxy to use for the request. Defaults to None.
        api_key_parser: Optional API key parser for Jina Reader authentication.
        allow_private_hosts: Allow private target and proxy addresses.
        max_response_size: Largest response body any request buffers, in
            bytes.  Applies to every strategy that performs a request.

    Returns:
        Extracted content.

    Raises:
        FetchError: If every extraction strategy fails or the deadline is
            exceeded before any content is retrieved.
    """
    started_at = started_at or time.monotonic()
    deadline = time.monotonic() + max(0.0, timeout)
    # Private callers (tests, other modules) reach the pipeline here too, so
    # the policy is enforced again rather than only at ``fetch_content``.
    _enforce_request_policy(url, proxy, allow_private_hosts=allow_private_hosts)

    if strategy != "auto":
        return _extract_with_strategy(
            url,
            strategy=strategy,
            timeout=timeout,
            proxy=proxy,
            api_key_parser=api_key_parser,
            cdp_endpoint=cdp_endpoint,
            veilrender_endpoint=veilrender_endpoint,
            veilrender_token=veilrender_token,
            deadline=deadline,
            started_at=started_at,
            allow_private_hosts=allow_private_hosts,
            max_response_size=max_response_size,
        )

    return _extract_auto(
        url,
        timeout=timeout,
        proxy=proxy,
        api_key_parser=api_key_parser,
        cdp_endpoint=cdp_endpoint,
        veilrender_endpoint=veilrender_endpoint,
        veilrender_token=veilrender_token,
        deadline=deadline,
        started_at=started_at,
        allow_private_hosts=allow_private_hosts,
        max_response_size=max_response_size,
    )


def _try_browser_rendering(
    url: str,
    *,
    local_content: str,
    veilrender_endpoint: str | None,
    veilrender_token: str | None,
    cdp_endpoint: str | None,
    remaining: float,
    started_at: float,
    allow_private_hosts: bool = False,
    max_response_size: int = _DEFAULT_MAX_RESPONSE_SIZE,
) -> tuple[FetchResult | None, str]:
    """Try VeilRender then CDP; return (result, updated_local_content)."""
    if veilrender_endpoint and remaining > _MIN_STRATEGY_BUDGET:
        vr_result, vr_local = _try_veilrender_extraction(
            url,
            veilrender_endpoint,
            veilrender_token,
            min(remaining, 30.0),
            allow_private_hosts=allow_private_hosts,
            max_response_size=max_response_size,
        )
        if vr_result:
            content = _format_text(vr_result)
            return _make_result(
                content=content,
                url=url,
                strategy="veilrender",
                content_type="text/html",
                started_at=started_at,
                metadata={"content_length": len(content)},
            ), local_content
        if len(vr_local) > len(local_content):
            local_content = vr_local

    if cdp_endpoint and remaining > _MIN_STRATEGY_BUDGET:
        cdp_result, cdp_local = _try_cdp_extraction(
            url,
            cdp_endpoint,
            min(remaining, 15.0),
            allow_private_hosts=allow_private_hosts,
            max_response_size=max_response_size,
        )
        if cdp_result:
            content = _format_text(cdp_result)
            return _make_result(
                content=content,
                url=url,
                strategy="cdp",
                content_type="text/html",
                started_at=started_at,
                metadata={"content_length": len(content)},
            ), local_content
        if len(cdp_local) > len(local_content):
            local_content = cdp_local

    return None, local_content


def _extract_auto(
    url: str,
    *,
    timeout: float,
    proxy: str | None,
    api_key_parser: APIKeyParser | None,
    cdp_endpoint: str | None,
    veilrender_endpoint: str | None,
    veilrender_token: str | None,
    deadline: float,
    started_at: float,
    allow_private_hosts: bool = False,
    max_response_size: int = _DEFAULT_MAX_RESPONSE_SIZE,
) -> FetchResult:
    """Auto pipeline: try strategies in order."""

    def _remaining() -> float:
        return max(0.0, deadline - time.monotonic())

    # 1. Fetch body (tries markdown negotiation, then raw fetch).
    body, content_type = _fetch_body(
        url,
        timeout,
        proxy,
        deadline,
        allow_private_hosts=allow_private_hosts,
        max_response_size=max_response_size,
    )

    # Markdown negotiation succeeded — return directly.
    if content_type == "_markdown":
        content = _format_text(body)
        return _make_result(
            content=content,
            url=url,
            strategy="markdown",
            content_type="text/markdown",
            started_at=started_at,
            metadata={"content_length": len(content)},
        )

    # Short-circuit: binary content types (images, PDFs, archives, etc.)
    if body and content_type and _is_binary_content_type(content_type):
        raise FetchError(f"Unsupported binary content type for {url}: {content_type}")

    # Short-circuit: non-HTML content types (JSON, plain text, XML, etc.)
    if body and content_type in _NON_HTML_CONTENT_TYPES:
        logger.info(
            f"Successfully fetched {url} using strategy: direct "
            f"(content_type: {content_type})"
        )
        content = _format_text(body)
        return _make_result(
            content=content,
            url=url,
            strategy="direct",
            content_type=content_type,
            started_at=started_at,
            metadata={"content_length": len(content)},
        )

    # 2-3. Local extraction (readability + optional soup).
    local_content = ""
    if body:
        best, local_content, local_strategy, local_score = _try_local_extraction(
            body, url
        )
        if best:
            content = _format_text(best)
            return _make_result(
                content=content,
                url=url,
                strategy=local_strategy,
                quality="high",
                content_type=content_type,
                started_at=started_at,
                metadata={
                    "readability_score": local_score,
                    "content_length": len(content),
                },
            )

    # 4-5. Try browser rendering (VeilRender, then CDP).
    browser_result, local_content = _try_browser_rendering(
        url,
        local_content=local_content,
        veilrender_endpoint=veilrender_endpoint,
        veilrender_token=veilrender_token,
        cdp_endpoint=cdp_endpoint,
        remaining=_remaining(),
        started_at=started_at,
        allow_private_hosts=allow_private_hosts,
        max_response_size=max_response_size,
    )
    if browser_result is not None:
        return browser_result

    # 6. Local extraction insufficient — try Jina Reader.
    jina_content = _try_jina_extraction(
        url,
        local_content=local_content,
        timeout=timeout,
        remaining=_remaining(),
        proxy=proxy,
        api_key_parser=api_key_parser,
        deadline=deadline,
        max_response_size=max_response_size,
        allow_private_hosts=allow_private_hosts,
    )
    if jina_content:
        content = _format_text(jina_content)
        return _make_result(
            content=content,
            url=url,
            strategy="jina",
            content_type="text/markdown",
            started_at=started_at,
            metadata={"content_length": len(content)},
        )

    # 6. Fall back to best local result if available.
    if local_content:
        logger.info(
            f"Successfully fetched {url} using strategy: local_fallback "
            f"(low_quality, length: {len(local_content)})"
        )
        content = _format_text(local_content)
        return _make_result(
            content=content,
            url=url,
            strategy="local_fallback",
            quality="low",
            content_type=content_type,
            started_at=started_at,
            metadata={"content_length": len(content)},
        )

    logger.warning(f"All extraction strategies failed for {url}")
    raise FetchError(f"Unable to fetch content from {url}")


def _try_markdown_negotiation(
    url: str,
    timeout: float = TIMEOUT_DEFAULT,
    proxy: str | None = None,
    *,
    allow_private_hosts: bool = False,
    max_response_size: int = _DEFAULT_MAX_RESPONSE_SIZE,
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
        allow_private_hosts: Allow a private redirect target.
        max_response_size: Largest body to buffer, in bytes.

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

        def send(target_url: str, _method: str) -> Response:
            """Send one markdown probe without following redirects."""
            return cast(
                Response,
                _http_get(
                    target_url,
                    headers=headers,
                    timeout=timeout,
                    proxy=proxy,
                    max_response_size=max_response_size,
                    follow_redirects=False,
                ),
            )

        response = _request_with_redirects(
            "GET",
            url,
            send,
            allow_private_hosts=allow_private_hosts,
            stage="markdown",
        )
        # Final-URL backstop: every hop was already validated above.
        _enforce_final_url_policy(
            response,
            allow_private_hosts=allow_private_hosts,
            stage="markdown",
        )

        # Capture body and content-type before status check so we can
        # return them on non-markdown 2xx responses.
        body = response.text
        raw_ct = response.headers.get("content-type") or ""
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
            f"Markdown negotiation not supported for {url} (Content-Type: {raw_ct})"
        )
        return "", body, ct
    except FetchPolicyError:
        raise
    except FetchError:
        raise
    except ResponseTooLargeError as e:
        raise _response_too_large_error(url, e) from None
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
    max_response_size: int = _DEFAULT_MAX_RESPONSE_SIZE,
    *,
    allow_private_hosts: bool = False,
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
        max_response_size: Largest body to buffer from Jina, in bytes.
        allow_private_hosts: Allow a private redirect target.

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
            max_response_size=max_response_size,
            allow_private_hosts=allow_private_hosts,
        )
        if content and _is_content_sufficient(content):
            return content
        if engine != _JINA_ENGINES[-1]:
            logger.debug(
                f"Jina Reader engine '{engine}' returned insufficient content "
                f"for {url}, retrying with next engine"
            )
    return content  # may be empty or low-quality; caller decides


def _record_jina_http_failure(
    status: int,
    api_key: str | None,
    api_key_parser: APIKeyParser | None,
) -> None:
    """Mark a Jina API key failed for the statuses that indicate it."""
    if not (api_key and api_key_parser):
        return
    if status in (401, 403):
        api_key_parser.mark_key_failed(api_key, f"HTTP {status}", ttl=3600.0)
    elif status == 429:
        api_key_parser.mark_key_failed(api_key, "rate limited", ttl=300.0)


def _jina_reader_request(
    url: str,
    engine: str = "browser",
    return_format: Literal["markdown", "text", "html"] = "markdown",
    timeout: float = TIMEOUT_DEFAULT,
    proxy: str | None = None,
    api_key: str | None = None,
    api_key_parser: APIKeyParser | None = None,
    deadline: float | None = None,
    max_response_size: int = _DEFAULT_MAX_RESPONSE_SIZE,
    *,
    allow_private_hosts: bool = False,
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
        max_response_size: Largest body to buffer from Jina, in bytes.
        allow_private_hosts: Allow a private redirect target.

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

        def send(target_url: str, method: str) -> Response:
            """Send one Jina request without following redirects."""
            if method == "POST":
                return cast(
                    Response,
                    _http_post(
                        target_url,
                        json={"url": url},
                        headers=headers,
                        timeout=transport_timeout,
                        proxy=proxy,
                        max_response_size=max_response_size,
                        follow_redirects=False,
                    ),
                )
            return cast(
                Response,
                _http_get(
                    target_url,
                    headers=headers,
                    timeout=transport_timeout,
                    proxy=proxy,
                    max_response_size=max_response_size,
                    follow_redirects=False,
                ),
            )

        response = _request_with_redirects(
            "POST",
            jina_reader_url,
            send,
            allow_private_hosts=allow_private_hosts,
            stage="jina",
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
        _record_jina_http_failure(status, api_key, api_key_parser)
        return ""
    except FetchError:
        # Too many redirects must reach the caller, not become an empty
        # strategy result.
        raise
    except ResponseTooLargeError as e:
        raise _response_too_large_error(url, e) from None
    except Exception as e:
        logger.debug(f"Jina Reader ({engine}) error: {e}")
        return ""


def _fetch_raw(
    url: str,
    timeout: float = TIMEOUT_DEFAULT,
    proxy: str | None = None,
    deadline: float | None = None,
    *,
    allow_private_hosts: bool = False,
    max_response_size: int = _DEFAULT_MAX_RESPONSE_SIZE,
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
        allow_private_hosts: Allow a private redirect target.
        max_response_size: Largest body to buffer per attempt, in bytes.

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

            request_headers = ua.headers.get()
            attempt_timeout = per_attempt_timeout

            def send(
                target_url: str,
                _method: str,
                headers: dict[str, str] = request_headers,
                timeout: float = attempt_timeout,
            ) -> Response:
                """Send one raw-fetch request without following redirects."""
                return cast(
                    Response,
                    _http_get(
                        target_url,
                        headers=headers,
                        timeout=timeout,
                        proxy=proxy,
                        max_response_size=max_response_size,
                        follow_redirects=False,
                    ),
                )

            response = _request_with_redirects(
                "GET",
                url,
                send,
                allow_private_hosts=allow_private_hosts,
                stage="http",
            )
            # Final-URL backstop: every hop was already validated above.
            _enforce_final_url_policy(
                response,
                allow_private_hosts=allow_private_hosts,
                stage="http",
            )
            response.raise_for_status()
            # Extract the MIME type (drop charset and parameters).
            raw_ct = response.headers.get("content-type") or ""
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
        except FetchPolicyError:
            # A refused destination must abort the fetch, not retry or fall
            # through to another strategy.
            raise
        except FetchError:
            # Too many redirects is definitive; retrying the chain would
            # repeat the same hops.
            raise
        except ResponseTooLargeError as e:
            # The cap is not transient; retrying would read the same body.
            raise _response_too_large_error(url, e) from None
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
