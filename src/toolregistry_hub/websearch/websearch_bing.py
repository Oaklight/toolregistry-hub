"""
Bing Web Search Implementation

.. deprecated:: 0.5.2
    This module is deprecated due to frequent bot detection issues.
    Please use alternative search providers:
    - BraveSearch for general web search
    - TavilySearch for AI-optimized search
    - SearXNGSearch for privacy-focused search
    - BrightDataGoogleSearch or ScrapelessGoogleSearch for Google results

This module provides a simple interface to Bing Web Search functionality.
Bing offers comprehensive web search results with good localization and relevance.

Usage:
    from websearch_bing import BingSearch

    search = BingSearch()
    results = search.search("python web scraping", max_results=5)

    for result in results:
        print(f"Title: {result['title']}")
        print(f"URL: {result['url']}")
        print(f"Content: {result['content'][:200]}...")
        print(f"Score: {result['score']}")
        print("-" * 50)
"""

import base64
import os
import time
import warnings
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from time import sleep
from typing import Dict, List, Optional, Set
from urllib.parse import parse_qs, unquote, urlparse

import httpx
import ua_generator
from bs4 import BeautifulSoup, Tag
from loguru import logger

from .base import TIMEOUT_DEFAULT, BaseSearch
from .search_result import SearchResult


class BingSearch(BaseSearch):
    """BingSearch provides a unified interface for performing web searches on Bing.
    It handles search queries and result processing.

    .. deprecated:: 0.5.2
        BingSearch is deprecated due to frequent bot detection issues.
        Use BraveSearch, TavilySearch, SearXNGSearch, or Google-based alternatives instead.

    Features:
    - Performs web searches using Bing
    - Returns formatted results with title, URL and description
    - Supports proxy settings
    - Extracts real URLs from Bing redirects

    Examples:
        >>> from toolregistry.hub.websearch_bing import BingSearch
        >>> searcher = BingSearch()
        >>> results = searcher.search("python web scraping", max_results=3)
        >>> for result in results:
        ...     print(result.title)
    """

    def __init__(
        self,
        bing_base_url: str = "https://www.bing.com",
        proxy: Optional[str] = None,
        rate_limit_delay: float = 1.0,
    ):
        """Initialize BingSearch with configuration parameters.

        .. deprecated:: 0.5.2
            BingSearch is deprecated. Use alternative search providers instead.

        Args:
            bing_base_url: Base URL for the Bing search. Defaults to "https://www.bing.com".
            proxy: Optional proxy server URL (e.g. "http://proxy.example.com:8080")
            rate_limit_delay: Delay between requests in seconds to avoid rate limits.
        """
        warnings.warn(
            "BingSearch is deprecated due to frequent bot detection issues. "
            "Please use BraveSearch, TavilySearch, SearXNGSearch, or Google-based alternatives instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        
        self.bing_base_url = bing_base_url.rstrip("/")
        if not self.bing_base_url.endswith("/search"):
            self.bing_base_url += "/search"  # Ensure the URL ends with /search

        self.proxy = proxy or os.environ.get("BING_PROXY_URL", None)
        if self.proxy:
            logger.info(f"Bing search using proxy: {self.proxy}")
        else:
            logger.debug("Bing search without proxy")
        
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0

    @property
    def _headers(self) -> dict:
        """Generate headers for Bing search requests."""
        ua = ua_generator.generate(browser=["chrome", "edge"])
        headers = ua.headers.get()
        headers["Accept-Ch"] = "Sec-CH-UA-Platform-Version, Sec-CH-UA-Full-Version-List"
        return headers

    def search(
        self,
        query: str,
        *,
        max_results: int = 5,
        timeout: float = TIMEOUT_DEFAULT,
        **kwargs,
    ) -> List[SearchResult]:
        """Perform search and return results.

        Args:
            query: The search query.
            max_results: The maximum number of results to return. Default is 5.
            timeout: Request timeout in seconds.
            **kwargs: Additional parameters (not used for Bing)

        Returns:
            List of search results with title, url, content and score.
        """
        if not query.strip():
            logger.warning("Empty query provided")
            return []

        try:
            # Rate limiting
            self._wait_for_rate_limit()

            # Perform the Bing search
            results = self._search_impl(
                query=query,
                max_results=max_results * 2,  # Get more results for filtering
                timeout=timeout,
            )

            # Filter and limit results
            if len(results) > max_results:
                results = results[:max_results]

            # Enrich with full content if needed
            if kwargs.get("fetch_content", False):
                with ProcessPoolExecutor() as executor:
                    enriched_results = list(
                        executor.map(
                            partial(
                                self._fetch_webpage_content,
                                timeout=timeout,
                                proxy=self.proxy,
                            ),
                            results,
                        )
                    )
                    # Convert back to SearchResult objects
                    results = [
                        SearchResult(
                            title=r["title"],
                            url=r["url"],
                            content=r["content"],
                        )
                        for r in enriched_results
                    ]

            return results

        except httpx.RequestError as e:
            logger.error(f"Bing search request error: {e}")
            return []
        except httpx.HTTPStatusError as e:
            logger.error(f"Bing search HTTP error: {e.response.status_code}")
            return []
        except Exception as e:
            logger.error(f"Bing search failed: {e}")
            return []

    def _search_impl(self, query: str, **kwargs) -> List[SearchResult]:
        """Perform the actual search using Bing for a single query.

        Args:
            query: The search query string
            **kwargs: Additional parameters including max_results and timeout

        Returns:
            List of SearchResult
        """
        print(kwargs["max_results"])
        max_results = kwargs.get("max_results", 10)
        print(max_results)
        timeout = kwargs.get("timeout", TIMEOUT_DEFAULT)

        results = []
        fetched_links: Set[str] = set()
        fetched_results = 0
        offset = 0

        with httpx.Client(
            proxy=self.proxy,
            headers=self._headers,
            timeout=timeout,
            follow_redirects=True,
        ) as client:
            while fetched_results < max_results:
                response = client.get(
                    url=self.bing_base_url,
                    params={
                        "q": query,
                        "count": min(10, max_results - fetched_results),
                        "first": offset + 1,
                        "FORM": "PERE",
                    },
                    cookies={
                        "CONSENT": "PENDING+987",
                    },
                )
                response.raise_for_status()

                batch_entries = self._parse_results(
                    {
                        "html": response.text,
                        "fetched_links": fetched_links,
                        "max_results": max_results - fetched_results,
                    }
                )
                if not batch_entries:
                    break

                fetched_results += len(batch_entries)
                results.extend(batch_entries)
                offset += len(batch_entries)

                # Small delay between requests
                sleep(0.1)

        return results

    def _parse_results(self, raw_results: Dict) -> List[SearchResult]:
        """Parse raw Bing search results into standardized format.

        Args:
            raw_results: Dictionary containing:
                - html: Raw HTML response from Bing
                - fetched_links: Set of already fetched URLs to avoid duplicates
                - max_results: Maximum number of results to parse

        Returns:
            List of standardized SearchResult objects
        """
        html = raw_results["html"]
        fetched_links = raw_results["fetched_links"]
        max_results = raw_results["max_results"]

        soup = BeautifulSoup(html, "html.parser")
        result_block = soup.find_all("li", class_="b_algo")
        new_results = 0

        results = []
        for result in result_block:
            if new_results >= max_results:
                break

            # Skip non-Tag elements
            if not isinstance(result, Tag):
                continue

            link_tag = result.find("a", href=True)
            if not link_tag or not isinstance(link_tag, Tag):
                continue

            h2_tag = result.find("h2")
            if not isinstance(h2_tag, Tag):
                continue

            link_tag = h2_tag.find("a")
            if not isinstance(link_tag, Tag):
                continue

            caption = result.find("div", class_="b_caption")
            if not isinstance(caption, Tag):
                continue

            description_tag = caption.find("p")
            if not isinstance(description_tag, Tag):
                continue

            try:
                raw_link = link_tag.get("href")
                if not raw_link or not isinstance(raw_link, str):
                    continue

                # Extract the real URL from Bing's redirect URL
                link = self._extract_real_url(raw_link)

                if link in fetched_links:
                    continue

                fetched_links.add(link)
                title = h2_tag.get_text() if h2_tag else ""
                description = description_tag.get_text() if description_tag else ""
                new_results += 1

                results.append(
                    SearchResult(
                        title=title,
                        url=link,
                        content=description,
                        score=1.0
                        - (new_results * 0.01),  # Simple scoring based on position
                    )
                )

            except (AttributeError, KeyError, TypeError) as e:
                logger.debug(f"Error parsing Bing search result: {e}")
                continue

        return results

    @staticmethod
    def _extract_real_url(bing_url: str) -> str:
        """Extract the real URL from Bing's redirect URL.

        Args:
            bing_url: The Bing redirect URL

        Returns:
            The actual destination URL, or the original URL if extraction fails
        """
        try:
            # Parse the URL
            parsed = urlparse(bing_url)

            # Check if it's a Bing redirect URL
            if "bing.com" not in parsed.netloc or "/ck/a" not in parsed.path:
                return bing_url

            # Extract query parameters
            query_params = parse_qs(parsed.query)

            # Look for the 'u' parameter which contains the base64 encoded URL
            if "u" in query_params:
                encoded_url = query_params["u"][0]
                try:
                    # The URL is base64 encoded with some prefix, try to decode
                    if encoded_url.startswith("a1"):
                        # Remove the 'a1' prefix and decode
                        encoded_part = encoded_url[2:]
                        # Add padding if needed for base64 decoding
                        padding = 4 - (len(encoded_part) % 4)
                        if padding != 4:
                            encoded_part += "=" * padding
                        decoded_bytes = base64.b64decode(encoded_part)
                        decoded_url = decoded_bytes.decode("utf-8")
                        return decoded_url
                except Exception as e:
                    logger.debug(f"Failed to decode base64 URL: {e}")
                    pass

            # If base64 decoding fails, try URL unquoting
            if "u" in query_params:
                try:
                    return unquote(query_params["u"][0])
                except Exception as e:
                    logger.debug(f"Failed to unquote URL: {e}")
                    pass

            # If all else fails, return the original URL
            return bing_url

        except Exception as e:
            logger.debug(f"Error extracting real URL from {bing_url}: {e}")
            return bing_url

    def _wait_for_rate_limit(self):
        """Ensure minimum delay between API requests to avoid rate limits."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_request
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)

        self.last_request_time = time.time()


def main():
    """Demo usage of BingSearch."""
    try:
        search = BingSearch()

        # Test basic search
        print("=== Basic Search Test ===")
        results = search.search("python web scraping", max_results=15)

        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result.title}")
            print(f"   URL: {result.url}")
            print(f"   Content: {result.content}...")
            print(f"   Score: {result.score:.3f}")

    except Exception as e:
        print(f"Demo failed: {e}")


if __name__ == "__main__":
    main()
