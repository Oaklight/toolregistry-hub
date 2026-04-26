import random
import re
import unicodedata
from typing import Literal

import httpx
import ua_generator

from ._vendor.readability import extract as readability_extract
from ._vendor.soup import Soup
from ._vendor.structlog import get_logger

logger = get_logger()

TIMEOUT_DEFAULT = 30.0

# Minimum content length (in characters) to consider extraction sufficient.
# Content shorter than this triggers the next fallback strategy.
_MIN_CONTENT_LENGTH = 100

# Common indicators of SPA shell pages that lack real content.
# If any of these appear in the extracted text, the content is considered
# insufficient and Jina Reader (with browser engine) will be tried.
_SPA_SHELL_INDICATORS = [
    "please enable javascript",
    "you need to enable javascript",
    "this app requires javascript",
    "loading...",
    "noscript",
    "we're sorry but",
    "doesn't work properly without javascript",
    "requires a modern browser",
    "enable cookies",
]


def _get_lynx_useragent():
    """
    Generates a random user agent string mimicking the format of various software versions.

    The user agent string is composed of:
    - Lynx version: Lynx/x.y.z where x is 2-3, y is 8-9, and z is 0-2
    - libwww version: libwww-FM/x.y where x is 2-3 and y is 13-15
    - SSL-MM version: SSL-MM/x.y where x is 1-2 and y is 3-5
    - OpenSSL version: OpenSSL/x.y.z where x is 1-3, y is 0-4, and z is 0-9

    Returns:
        str: A randomly generated user agent string.
    """
    lynx_version = (
        f"Lynx/{random.randint(2, 3)}.{random.randint(8, 9)}.{random.randint(0, 2)}"
    )
    libwww_version = f"libwww-FM/{random.randint(2, 3)}.{random.randint(13, 15)}"
    ssl_mm_version = f"SSL-MM/{random.randint(1, 2)}.{random.randint(3, 5)}"
    openssl_version = (
        f"OpenSSL/{random.randint(1, 3)}.{random.randint(0, 4)}.{random.randint(0, 9)}"
    )
    return f"{lynx_version} {libwww_version} {ssl_mm_version} {openssl_version}"


HEADERS_LYNX = {
    "User-Agent": _get_lynx_useragent(),
    "Accept": "*/*",
}


class Fetch:
    """
    A class to handle fetching and extracting content from URLs.
    """

    @staticmethod
    def fetch_content(
        url: str,
        timeout: float = TIMEOUT_DEFAULT,
        proxy: str | None = None,
    ) -> str:
        """
        Fetch and extract content from a given URL.

        Args:
            url (str): The URL to fetch content from.
            timeout (float, optional): Request timeout in seconds. Defaults to TIMEOUT_DEFAULT.
            proxy (str, optional): Proxy to use for the request. Defaults to None.

        Returns:
            str: Extracted content from the URL, or a message indicating failure if extraction fails.
        """
        try:
            content = _extract(url, timeout=timeout, proxy=proxy)
            return content
        except Exception as e:
            logger.error(f"Failed to fetch content from {url}: {e}")
            return "Unable to fetch content"


def _is_content_sufficient(text: str) -> bool:
    """Evaluate whether extracted content has sufficient quality.

    Checks for minimum length and SPA shell indicators to determine
    if the content is meaningful or just a JavaScript app shell.

    Args:
        text: The extracted text content to evaluate.

    Returns:
        True if content appears sufficient, False otherwise.
    """
    if len(text) < _MIN_CONTENT_LENGTH:
        return False

    text_lower = text.lower()
    for indicator in _SPA_SHELL_INDICATORS:
        if indicator in text_lower:
            return False

    return True


def _extract(
    url: str,
    timeout: float = TIMEOUT_DEFAULT,
    proxy: str | None = None,
) -> str:
    """Extract content from a given URL using available methods.

    Strategies are tried in order:
    1. Cloudflare Content Negotiation (zero-cost markdown attempt)
    2. Readability extraction (intelligent article scoring, local)
    3. Simple soup extraction (CSS selector fallback, local)
    4. Jina Reader (external API fallback for SPA / JS-heavy pages)

    HTML is fetched once and reused by stages 2 and 3.

    Args:
        url: The URL to extract content from.
        timeout: Request timeout in seconds. Defaults to TIMEOUT_DEFAULT.
        proxy: Proxy to use for the request. Defaults to None.

    Returns:
        Extracted content, or ``"Unable to fetch content"`` if all strategies fail.
    """
    # 1. Try Cloudflare Content Negotiation (zero-cost, high quality if supported)
    content = _get_content_with_markdown_negotiation(
        url,
        timeout=timeout,
        proxy=proxy,
    )
    if content:
        logger.info(f"Successfully fetched {url} using strategy: markdown_negotiation")
        return _format_text(content)

    # Fetch HTML once for local extraction strategies
    html = _fetch_html(url, timeout=timeout, proxy=proxy)

    local_content = ""
    if html:
        # 2. Try Readability extraction (intelligent article detection)
        readability_content = _extract_with_readability(html, url)

        # 3. Try simple soup extraction (CSS selector fallback)
        soup_content = _extract_with_soup(html)

        # Pick the best local result: prefer whichever is longer and sufficient.
        # Readability produces cleaner article text; soup captures more structural
        # content.  When readability returns only a short skeleton (e.g. SPA pages),
        # soup's broader extraction is usually more useful.
        for candidate, strategy in [
            (readability_content, "readability"),
            (soup_content, "soup"),
        ]:
            if candidate and _is_content_sufficient(candidate):
                # Prefer readability if it extracted substantially more or equal
                # content; otherwise fall through to soup.
                if strategy == "readability" and soup_content and len(soup_content) > len(candidate) * 2:
                    logger.debug(
                        f"Readability result shorter than soup "
                        f"({len(candidate)} vs {len(soup_content)}), trying soup"
                    )
                    continue
                logger.info(f"Successfully fetched {url} using strategy: {strategy}")
                return _format_text(candidate)

        # Stash best local result for final fallback
        local_content = readability_content or soup_content or ""

    # 4. Local extraction insufficient — try Jina Reader
    reason = "low_quality_content" if local_content else "no_content"
    logger.debug(
        f"Local extraction insufficient for {url} (reason: {reason}, "
        f"length: {len(local_content)}), trying Jina Reader"
    )

    jina_content = _get_content_with_jina_reader(
        url,
        timeout=timeout,
        proxy=proxy,
    )

    if jina_content and _is_content_sufficient(jina_content):
        logger.info(
            f"Successfully fetched {url} using strategy: jina_reader "
            f"(local reason: {reason})"
        )
        return _format_text(jina_content)

    # 5. Fall back to best local result if available
    if local_content:
        logger.info(
            f"Successfully fetched {url} using strategy: local_fallback "
            f"(low_quality, length: {len(local_content)})"
        )
        return _format_text(local_content)

    logger.warning(f"All extraction strategies failed for {url}")
    return "Unable to fetch content"


def _get_content_with_markdown_negotiation(
    url: str,
    timeout: float = TIMEOUT_DEFAULT,
    proxy: str | None = None,
) -> str:
    """
    Attempt to fetch markdown content via Cloudflare Content Negotiation.

    Sends a standard HTTP GET request with ``Accept: text/markdown`` header.
    If the origin server (or Cloudflare) supports content negotiation and
    returns markdown, the content is used directly. Otherwise, returns an
    empty string so that subsequent strategies can handle the URL.

    Args:
        url (str): The URL to fetch content from.
        timeout (float, optional): Timeout for the HTTP request. Defaults to TIMEOUT_DEFAULT.
        proxy (str, optional): Proxy to use for the HTTP request. Defaults to None.

    Returns:
        str: Markdown content if the server supports it, otherwise empty string.
    """
    try:
        ua = ua_generator.generate(browser=["chrome", "edge"])
        ua.headers.accept_ch("Sec-CH-UA-Platform-Version, Sec-CH-UA-Full-Version-List")
        headers = ua.headers.get()
        headers["Accept"] = "text/markdown"
        response = httpx.get(
            url,
            headers=headers,
            timeout=timeout,
            follow_redirects=True,
            proxy=proxy,
        )
        response.raise_for_status()

        content_type = response.headers.get("content-type", "")
        if "text/markdown" not in content_type:
            logger.debug(
                f"Markdown negotiation not supported for {url} "
                f"(Content-Type: {content_type})"
            )
            return ""

        # Log markdown token count if provided by Cloudflare
        md_tokens = response.headers.get("x-markdown-tokens")
        if md_tokens:
            logger.debug(f"Markdown tokens for {url}: {md_tokens}")

        return response.text
    except Exception as e:
        logger.debug(f"Markdown negotiation failed for {url}: {e}")
        return ""


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
) -> str:
    """Fetch parsed content from Jina AI Reader for a given URL.

    Tries the ``browser`` engine first.  If the result is empty or
    insufficient, retries with the ``cf-browser-rendering`` engine which
    is optimised for JS-heavy / SPA websites.

    The Jina ``X-Timeout`` header is set to *timeout* while the httpx
    transport timeout is set to ``timeout + _JINA_TIMEOUT_BUFFER`` so
    that the HTTP client never races against the Jina rendering deadline.

    Args:
        url: The URL to fetch content from.
        return_format: The format of the returned content.
            Defaults to ``"markdown"``.
        timeout: Maximum seconds Jina should spend rendering the page.
            Defaults to TIMEOUT_DEFAULT.
        proxy: Proxy to use for the HTTP request.  Defaults to ``None``.

    Returns:
        Parsed content from Jina AI, or empty string on failure.
    """
    for engine in _JINA_ENGINES:
        content = _jina_reader_request(
            url,
            engine=engine,
            return_format=return_format,
            timeout=timeout,
            proxy=proxy,
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
) -> str:
    """Send a single request to the Jina Reader API.

    Args:
        url: The URL to fetch content from.
        engine: Jina rendering engine (``"browser"``,
            ``"cf-browser-rendering"``, or ``"direct"``).
        return_format: Desired output format.
        timeout: Maximum seconds Jina should spend rendering the page.
        proxy: Optional HTTP proxy URL.

    Returns:
        Extracted content string, or empty string on failure.
    """
    try:
        headers: dict[str, str] = {
            "Accept": "application/json",
            "X-Return-Format": return_format,
            "X-Engine": engine,
            "X-Timeout": str(int(timeout)),
            "X-Remove-Selector": "header, footer, nav, aside",
            "X-Wait-For-Selector": _JINA_WAIT_SELECTORS,
        }
        jina_reader_url = "https://r.jina.ai/"
        # httpx timeout must exceed Jina's rendering timeout so we don't
        # abort the HTTP connection before Jina finishes.
        transport_timeout = timeout + _JINA_TIMEOUT_BUFFER
        logger.debug(f"Jina Reader request for {url} (engine: {engine})")
        response = httpx.post(
            jina_reader_url,
            json={"url": url},
            headers=headers,
            timeout=transport_timeout,
            proxy=proxy,
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
    except httpx.HTTPStatusError as e:
        logger.debug(
            f"Jina Reader ({engine}) HTTP Error [{e.response.status_code}]: {e}"
        )
        return ""
    except Exception as e:
        logger.debug(f"Jina Reader ({engine}) error: {e}")
        return ""


def _fetch_html(
    url: str,
    timeout: float = TIMEOUT_DEFAULT,
    proxy: str | None = None,
) -> str:
    """Fetch raw HTML from a URL.

    Args:
        url: The URL to fetch.
        timeout: Request timeout in seconds.
        proxy: Optional proxy URL.

    Returns:
        HTML string, or empty string on failure.
    """
    try:
        ua = ua_generator.generate(browser=["chrome", "edge"])
        ua.headers.accept_ch("Sec-CH-UA-Platform-Version, Sec-CH-UA-Full-Version-List")
        response = httpx.get(
            url,
            headers=ua.headers.get(),
            timeout=timeout,
            follow_redirects=True,
            proxy=proxy,
        )
        response.raise_for_status()
        return response.text
    except httpx.HTTPStatusError as e:
        logger.debug(f"HTTP Error [{e.response.status_code}]: {e}")
        return ""
    except Exception as e:
        logger.debug(f"Error fetching {url}: {e}")
        return ""


def _extract_with_readability(html: str, url: str) -> str:
    """Extract content using the Readability algorithm.

    Uses Mozilla Readability-style scoring to identify and extract the
    main article content from arbitrary web pages.

    Args:
        html: Raw HTML string.
        url: Original URL (passed to readability for link resolution).

    Returns:
        Plain text of the main article, or empty string on failure.
    """
    try:
        result = readability_extract(html, url=url)
        if result.length >= _MIN_CONTENT_LENGTH:
            return result.text
        logger.debug(f"Readability extraction too short ({result.length} chars)")
        return ""
    except Exception as e:
        logger.debug(f"Readability extraction failed: {e}")
        return ""


def _extract_with_soup(html: str) -> str:
    """Simple content extraction using zerodep soup.

    Fallback for when readability fails. Decomposes non-content tags,
    then looks for main/article/div.content landmarks.

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
        main_content = (
            soup.find("main")
            or soup.find("article")
            or soup.find("div", {"class": "content"})
        )
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
    # text = _remove_emojis(text)
    return text


def _remove_emojis(text: str) -> str:
    """
    Remove emoji expressions from text.

    Args:
        text (str): The input text.

    Returns:
        str: Text with emojis removed.
    """
    return "".join(c for c in text if not unicodedata.category(c).startswith("So"))
