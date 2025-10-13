"""
SearXNG Search API Demo Implementation

This module provides a simple interface to SearXNG instances for web search functionality.
SearXNG is a free, open-source metasearch engine that aggregates results from multiple search engines.

Setup:
1. Set up a SearXNG instance (local or remote)
2. Set the instance URL as an environment variable:
   export SEARXNG_URL="http://localhost:8080"

   Or use a public instance (not recommended for production):
   export SEARXNG_URL="https://search.example.com"

Usage:
    from websearch_searxng import SearXNGSearch

    search = SearXNGSearch()
    results = search.search("python web scraping", max_results=5)

    for result in results:
        print(f"Title: {result['title']}")
        print(f"URL: {result['url']}")
        print(f"Content: {result['content'][:200]}...")
        print(f"Score: {result['score']}")
        print("-" * 50)

API Documentation: https://docs.searxng.org/dev/search_api.html
SearXNG Setup: https://docs.searxng.org/admin/installation.html
"""

import os
from typing import Dict, List, Optional

import httpx
from loguru import logger

from .base import TIMEOUT_DEFAULT, BaseSearch
from .search_result import SearchResult


class SearXNGSearch(BaseSearch):
    """Simple SearXNG API client for web search functionality."""

    def __init__(self, base_url: Optional[str] = None):
        """Initialize SearXNG search client.

        Args:
            base_url: SearXNG instance URL. If not provided, will try to get from SEARXNG_URL env var.
        """
        self.base_url = base_url or os.getenv("SEARXNG_URL")
        if not self.base_url:
            raise ValueError(
                "SearXNG URL is required. Set SEARXNG_URL environment variable "
                "Such as https://searxng.url, `json` response format should be set in SearXNG configuration"
            )

        self.base_url = self.base_url.rstrip("/")

        # Ensure we have the search endpoint
        if not self.base_url.endswith("/search"):
            self.search_url = f"{self.base_url}/search"
        else:
            self.search_url = self.base_url

    @property
    def _headers(self) -> dict:
        """Generate headers necessary for making upstream query."""
        return {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def search(
        self,
        query: str,
        *,
        max_results: int = 5,
        timeout: float = TIMEOUT_DEFAULT,
        **kwargs,
    ) -> List[SearchResult]:
        """Perform a web search using SearXNG API.

        Args:
            query: The search query string
            max_results: Maximum number of results to return (1~20 recommended, 180 at max)
            timeout: Request timeout in seconds
            **kwargs: additional query parameters defined by SearXNG API

        Returns:
            List of search results with title, url, content, excerpt and score
        """
        if not query.strip():
            logger.warning("Empty query provided")
            return []

        results = []

        if max_results > 50:
            logger.warning("max_results exceeds the maximum limit of 50")
            max_results = 50

        pageno = 1
        while len(results) < max_results:
            kwargs["pageno"] = pageno
            page_results = self._search_impl(query=query, timeout=timeout, **kwargs)

            # If no results returned, break the loop
            if not page_results:
                break

            results.extend(page_results)
            pageno += 1

        # Sort by score if available, otherwise by position
        results = sorted(results, key=lambda x: x.score, reverse=True)

        return results[:max_results] if results else []

    def _search_impl(self, query: str, **kwargs) -> List[SearchResult]:
        """Perform the actual search using SearXNG API for a single query.

        Args:
            query: The search query string
            **kwargs: Additional parameters specific to the SearXNG API

        Returns:
            List of SearchResult
        """
        if not query.strip():
            logger.warning("Empty query provided")
            return []

        params = {
            "q": query,
            "format": "json",
            "pageno": kwargs.get("pageno", 1),
            "language": kwargs.get("language", "en"),
            "safesearch": kwargs.get("safesearch", 1),
        }

        # Add optional parameters
        optional_params = ["categories", "engines"]
        for param in optional_params:
            if param in kwargs and kwargs[param] is not None:
                params[param] = kwargs[param]

        timeout = kwargs.get("timeout", TIMEOUT_DEFAULT)
        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.get(
                    self.search_url, headers=self._headers, params=params
                )
                response.raise_for_status()

                data = response.json()
                results = self._parse_results(data)

                logger.info(
                    f"SearXNG search for '{query}' returned {len(results)} results"
                )
                return results

        except httpx.TimeoutException:
            logger.error(f"SearXNG API request timed out after {timeout}s")
            return []
        except httpx.HTTPStatusError as e:
            logger.error(
                f"SearXNG API HTTP error {e.response.status_code}: {e.response.text}"
            )
            return []
        except Exception as e:
            logger.error(f"SearXNG API request failed: {e}")
            return []

    def _parse_results(self, raw_results: Dict) -> List[SearchResult]:
        """Parse SearXNG API response into standardized format.

        Args:
            raw_results: Raw API response data

        Returns:
            List of parsed search results
        """
        results = []
        raw_results_data = raw_results.get("results", [])

        for item in raw_results_data:
            result = SearchResult(
                title=item.get("title", "No title"),
                url=item.get("url", ""),
                content=item.get("content", "No content available"),
                score=float(item.get("score", 0.0)),
            )
            results.append(result)

        return results


def main():
    """Demo usage of SearXNGSearch."""
    try:
        search = SearXNGSearch()

        print(f"✓ Connected to SearXNG at {search.base_url}")

        # Test basic search
        print("\n=== Basic Search Test ===")
        results = search.search("python programming tutorial", max_results=10)

        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result.title}")
            print(f"   URL: {result.url}")
            print(f"   Score: {result.score:.3f}")
            print(f"   Content: {result.content[:150]}...")

    except Exception as e:
        print(f"Demo failed: {e}")
        print(
            f"Make sure SearXNG is running at {os.getenv('SEARXNG_URL', 'http://localhost:8080')}"
        )


if __name__ == "__main__":
    main()
