import random
import re
import unicodedata
from typing import Literal, Optional

import httpx
import ua_generator
from bs4 import BeautifulSoup
from loguru import logger

TIMEOUT_DEFAULT = 10.0


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
        proxy: Optional[str] = None,
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


def _extract(
    url: str,
    timeout: float = TIMEOUT_DEFAULT,
    proxy: Optional[str] = None,
) -> str:
    """
    Extract content from a given URL using available methods.

    Args:
        url (str): The URL to extract content from.
        timeout (float, optional): Request timeout in seconds. Defaults to TIMEOUT_DEFAULT (10). Usually not needed.
        proxy (str, optional): Proxy to use for the request. Defaults to None.

    Returns:
        str: Extracted content from the URL, or empty string if extraction fails.
    """
    # First try BeautifulSoup method
    content = _get_content_with_bs4(
        url,
        timeout=timeout,
        proxy=proxy,
    )
    if not content:
        # Fallback to Jina Reader if BeautifulSoup fails
        content = _get_content_with_jina_reader(
            url,
            timeout=timeout,
            proxy=proxy,
        )

    formatted_content = _format_text(content) if content else "Unable to fetch content"
    return formatted_content


def _get_content_with_jina_reader(
    url: str,
    return_format: Literal["markdown", "text", "html"] = "text",
    timeout: float = TIMEOUT_DEFAULT,
    proxy: Optional[str] = None,
) -> str:
    """
    Fetch parsed content from Jina AI for a given URL.

    Args:
        url (str): The URL to fetch content from.
        return_format (Literal["markdown", "text", "html"], optional): The format of the returned content. Defaults to "text".
        timeout (float, optional): Timeout for the HTTP request. Defaults to TIMEOUT_DEFAULT.
        proxy (str, optional): Proxy to use for the HTTP request. Defaults to None.

    Returns:
        str: Parsed content from Jina AI.
    """
    try:
        headers = {
            "X-Return-Format": return_format,
            "X-Remove-Selector": "header, .class, #id",
            "X-Target-Selector": "body, .class, #id",
        }
        jina_reader_url = "https://r.jina.ai/"
        response = httpx.get(
            jina_reader_url + url,
            headers=headers,
            timeout=timeout,
            proxy=proxy,
        )
        response.raise_for_status()
        return response.text
    except httpx.HTTPStatusError as e:
        logger.debug(f"HTTP Error [{e.response.status_code}]: {e}")
        return ""
    except Exception as e:
        logger.debug(f"Other error: {e}")
        return ""


def _get_content_with_bs4(
    url: str,
    timeout: float = TIMEOUT_DEFAULT,
    proxy: Optional[str] = None,
) -> str:
    """
    Utilizes BeautifulSoup to fetch and parse the content of a webpage.

    Args:
        url (str): The URL of the webpage.
        timeout (float, Optional): Timeout for the HTTP request. Defaults to TIMEOUT_DEFAULT.
        proxy (str, Optional): Proxy to use for the HTTP request. Defaults to None.

    Returns:
        str: Parsed text content of the webpage.
    """
    try:
        ua = ua_generator.generate(browser=["chrome", "edge"])  # type: ignore
        ua.headers.accept_ch("Sec-CH-UA-Platform-Version, Sec-CH-UA-Full-Version-List")
        response = httpx.get(
            url,
            headers=ua.headers.get(),
            timeout=timeout,
            follow_redirects=True,
            proxy=proxy,
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for element in soup(["script", "style", "nav", "footer", "iframe", "noscript"]):
            element.decompose()
        main_content = (
            soup.find("main")
            or soup.find("article")
            or soup.find("div", {"class": "content"})
        )
        content_source = main_content if main_content else soup.body
        if not content_source:
            return ""
        return content_source.get_text(separator=" ", strip=True)
    except httpx.HTTPStatusError as e:
        logger.debug(f"HTTP Error [{e.response.status_code}]: {e}")
        return ""
    except Exception as e:
        logger.debug(f"Error parsing webpage content: {e}")
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
