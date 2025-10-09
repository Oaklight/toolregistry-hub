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

import os
import time
from typing import Dict, List, Optional

import httpx
from loguru import logger

from .search_result import SearchResult


class BraveSearch:
    """Simple Brave Search API client for web search functionality."""

    def __init__(self, api_keys: Optional[str] = None, rate_limit_delay: float = 1.0):
        """Initialize Brave search client.

        Args:
            api_keys: Comma-separated Brave API keys. If not provided, will try to get from BRAVE_API_KEY env var.
            rate_limit_delay: Delay between requests in seconds to avoid rate limits.
        """
        api_keys_str = api_keys or os.getenv("BRAVE_API_KEY")
        if not api_keys_str:
            raise ValueError(
                "Brave API keys are required. Set BRAVE_API_KEY environment variable "
                "or pass api_keys parameter (comma-separated)."
            )

        # Parse and validate API keys
        self.api_keys = [key.strip() for key in api_keys_str.split(",") if key.strip()]
        if not self.api_keys:
            raise ValueError("No valid API keys provided")

        self.base_url = "https://api.search.brave.com/res/v1"
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0
        self._current_key_index = 0

    def _get_next_api_key(self) -> str:
        """Round-robin API key selection."""
        key = self.api_keys[self._current_key_index]
        self._current_key_index = (self._current_key_index + 1) % len(self.api_keys)
        return key

    @property
    def headers(self) -> dict:
        """Generate headers with the current API key."""
        return {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self._get_next_api_key(),
        }

    def _search(
        self,
        *,
        query: str,
        count: int = 20,
        offset: int = 0,
        country: Optional[str] = None,
        search_lang: Optional[str] = None,
        safesearch: str = "moderate",
        freshness: Optional[str] = None,
        result_filter: Optional[str] = None,
        timeout: float = 10.0,
        **kwargs,
    ):
        """Perform a web search using Brave Search API.
        For detailed Query Parameters: https://api-dashboard.search.brave.com/app/documentation/web-search/query

        Args:
            query: The search query string
            count: Number of results to return (1-20). Each page has 20 entries.
            offset: Offset for pagination (0-9)
            country: Country code for localized results, "US" by default (e.g., "US", "GB")
            search_lang: Language for search results, "en" by default (e.g., "en", "es")
            safesearch: Safe search setting, "moderate" by default ("off", "moderate", "strict")
            freshness: Freshness of results ("pd" for past day, "pw" for past week, etc.)
            result_filter: Filter for specific result types ("discussions", "faq", "infobox", "news", "query", "summarizer", "videos", "web", "locations")
            timeout: Request timeout in seconds
            **kwargs: Additional parameters to pass to the API

        Returns:
            List of search results with title, url, content, and score
        """
        if not query.strip():
            logger.warning("Empty query provided")
            return []

        params = {"q": query, "count": count, "offset": offset}

        # Add optional parameters
        if country:
            params["country"] = country
        if search_lang:
            params["search_lang"] = search_lang
        if safesearch != "moderate":
            params["safesearch"] = safesearch
        if freshness:
            params["freshness"] = freshness
        if result_filter:
            params["result_filter"] = result_filter

        # Add any additional kwargs
        if kwargs:
            params.update(kwargs)

        try:
            # Rate limiting: ensure minimum delay between requests
            self._wait_for_rate_limit()

            with httpx.Client(timeout=timeout) as client:
                response = client.get(
                    f"{self.base_url}/web/search", headers=self.headers, params=params
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

    def search(
        self, query: str, *, max_results: int = 5, timeout: float = 10.0, **kwargs
    ) -> List[SearchResult]:
        """Perform a web search using Brave Search API.

        Args:
            query: The search query string
            max_results: Maximum number of results to return (1~20 recommended, 180 at max)
            timeout: Request timeout in seconds
            **kwargs: additional query parameters defined by Brave Search API. Refer to https://api-dashboard.search.brave.com/app/documentation/web-search/query for details

        Returns:
            List of search results with title, url, content, excerpt and score
        """
        results = []

        if not query.strip():
            logger.warning("Empty query provided")
            return results

        kwargs["timeout"] = timeout

        if max_results <= 20:
            results.extend(self._search(query=query, **kwargs))
        else:
            if max_results > 180:
                logger.warning("max_results exceeds the maximum limit of 180")
                max_results = 180

            for i in range(round(max_results / 20 + 0.49)):
                results.extend(self._search(query=query, offset=i, **kwargs))

        return results[:max_results] if results else []

    def _parse_results(self, data: Dict) -> List[SearchResult]:
        """Parse Brave API response into standardized format.

        Args:
            data: Raw API response data

        Returns:
            List of parsed search results
        """
        results = []

        # Parse web results
        web_results = data.get("web", {}).get("results", [])

        for i, item in enumerate(web_results):
            result = SearchResult(
                title=item.get("title", "No title"),
                url=item.get("url", ""),
                content=item.get("description", "No content available"),
                excerpt=item.get("description", "...")[:150],
            )
            results.append(result)

        return results

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
            print(f"   Excerpt: {result.excerpt if result.excerpt else ''}...")
            print(f"   Score: {result.score:.3f}")

    except ValueError as e:
        print(f"Setup error: {e}")
        print("Please set your BRAVE_API_KEY environment variable.")
    except Exception as e:
        print(f"Demo failed: {e}")


if __name__ == "__main__":
    main()
