"""
Brave Search API Demo Implementation

This module provides a simple interface to the Brave Search API for web search functionality.
Brave Search offers independent search results without Google dependency and good privacy features.

Setup:
1. Sign up at https://api.search.brave.com/ to get an API key
2. Set your API key as an environment variable:
   export BRAVE_API_KEY="your-brave-api-key-here"

Usage:
    from websearch_brave import BraveSearch

    search = BraveSearch()
    results = search.search("python web scraping", max_results=5)

    for result in results:
        print(f"Title: {result['title']}")
        print(f"URL: {result['url']}")
        print(f"Content: {result['content'][:200]}...")
        print(f"Score: {result['score']}")
        print("-" * 50)

API Documentation: https://api-dashboard.search.brave.com/app/documentation/web-search/get-started
"""

from typing import Dict, List, Optional

import httpx
from loguru import logger

from ..utils.api_key_parser import APIKeyParser
from .base import TIMEOUT_DEFAULT, BaseSearch
from .search_result import SearchResult


class BraveSearch(BaseSearch):
    """Simple Brave Search API client for web search functionality."""

    def __init__(self, api_keys: Optional[str] = None, rate_limit_delay: float = 1.0):
        """Initialize Brave search client.

        Args:
            api_keys: Comma-separated Brave API keys. If not provided, will try to get from BRAVE_API_KEY env var.
            rate_limit_delay: Delay between requests in seconds to avoid rate limits.
        """
        # Initialize API key parser for multiple keys
        self.api_key_parser = APIKeyParser(
            api_keys=api_keys,
            env_var_name="BRAVE_API_KEY",
            rate_limit_delay=rate_limit_delay,
        )

        self.base_url = "https://api.search.brave.com/res/v1"

    @property
    def _headers(self) -> dict:
        """Generate headers with the current API key."""
        return {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key_parser.get_next_api_key(),
        }

    def search(
        self,
        query: str,
        *,
        max_results: int = 5,
        timeout: float = TIMEOUT_DEFAULT,
        **kwargs,
    ) -> List[SearchResult]:
        """Perform a web search using Brave Search API.

        Args:
            query: The search query string
            max_results: Maximum number of results to return (1~20 recommended, 180 at max)
            timeout: Request timeout in seconds
            **kwargs: additional query parameters defined by Brave Search API. Refer to https://api-dashboard.search.brave.com/app/documentation/web-search/query for details

        Returns:
            List of search results with title, url, content and score
        """
        if not query.strip():
            logger.warning("Empty query provided")
            return []

        results = []

        if max_results <= 20:
            results.extend(self._search_impl(query=query, timeout=timeout, **kwargs))
        else:
            if max_results > 180:
                logger.warning("max_results exceeds the maximum limit of 180")
                max_results = 180

            for i in range(round(max_results / 20 + 0.49)):
                kwargs["offset"] = i
                results.extend(
                    self._search_impl(query=query, timeout=timeout, **kwargs)
                )

        return results[:max_results] if results else []

    def _search_impl(self, query: str, **kwargs) -> List[SearchResult]:
        """Perform the actual search using Brave Search API for a single query.

        Args:
            query: The search query string
            **kwargs: Additional parameters specific to the Brave Search API

        Returns:
            List of SearchResult
        """
        if not query.strip():
            logger.warning("Empty query provided")
            return []

        params = {
            "q": query,
            "count": kwargs.get("count", 20),
            "offset": kwargs.get("offset", 0),
        }

        # Add optional parameters
        optional_params = [
            "country",
            "search_lang",
            "safesearch",
            "freshness",
            "result_filter",
        ]
        for param in optional_params:
            if param in kwargs and kwargs[param] is not None:
                params[param] = kwargs[param]

        # Set default safesearch if not provided
        if "safesearch" not in params:
            params["safesearch"] = "moderate"

        # Add any additional kwargs
        for key, value in kwargs.items():
            if key not in ["count", "offset", "timeout"] + optional_params:
                params[key] = value

        timeout = kwargs.get("timeout", TIMEOUT_DEFAULT)
        try:
            # Rate limiting: ensure minimum delay between requests
            self._wait_for_rate_limit()

            with httpx.Client(timeout=timeout) as client:
                response = client.get(
                    f"{self.base_url}/web/search", headers=self._headers, params=params
                )
                response.raise_for_status()

                data = response.json()
                results = self._parse_results(data)

                logger.info(
                    f"Brave search for '{query}' returned {len(results)} results"
                )
                return results

        except httpx.TimeoutException:
            logger.error(f"Brave API request timed out after {timeout}s")
            return []
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning(
                    "Rate limit exceeded, consider increasing rate_limit_delay"
                )
            logger.error(
                f"Brave API HTTP error {e.response.status_code}: {e.response.text}"
            )
            return []
        except Exception as e:
            logger.error(f"Brave API request failed: {e}")
            return []

    def _parse_results(self, raw_results: Dict) -> List[SearchResult]:
        """Parse Brave API response into standardized format.

        Args:
            raw_results: Raw API response data

        Returns:
            List of parsed search results
        """
        results = []

        # Parse web results
        web_results = raw_results.get("web", {}).get("results", [])

        for i, item in enumerate(web_results):
            result = SearchResult(
                title=item.get("title", "No title"),
                url=item.get("url", ""),
                content=item.get("description", "No content available"),
            )
            results.append(result)

        return results

    def _wait_for_rate_limit(self):
        """Ensure minimum delay between API requests to avoid rate limits."""
        # Get the current API key and pass it to the rate limiter
        current_key = self.api_key_parser.get_next_api_key()
        self.api_key_parser.wait_for_rate_limit(api_key=current_key)


def main():
    """Demo usage of BraveSearch."""
    try:
        # Use rate limiting to avoid 429 errors (1 request per second for free tier)
        search = BraveSearch(rate_limit_delay=1.2)

        # Test basic search
        print("=== Basic Search Test ===")
        results = search.search("artificial intelligence", max_results=45)

        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result.title}")
            print(f"   URL: {result.url}")
            print(f"   Content: {result.content}...")
            print(f"   Score: {result.score:.3f}")

    except ValueError as e:
        print(f"Setup error: {e}")
        print("Please set your BRAVE_API_KEY environment variable.")
    except Exception as e:
        print(f"Demo failed: {e}")


if __name__ == "__main__":
    main()
