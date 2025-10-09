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

    def __init__(self, api_key: Optional[str] = None, rate_limit_delay: float = 1.0):
        """Initialize Brave search client.

        Args:
            api_key: Brave API key. If not provided, will try to get from BRAVE_API_KEY env var.
            rate_limit_delay: Delay between requests in seconds to avoid rate limits.
        """
        self.api_key = api_key or os.getenv("BRAVE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Brave API key is required. Set BRAVE_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.base_url = "https://api.search.brave.com/res/v1"
        self.headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key,
        }
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0

    def search(
        self,
        query: str,
        max_results: int = 5,
        country: Optional[str] = None,
        search_lang: Optional[str] = None,
        ui_lang: Optional[str] = None,
        safesearch: str = "moderate",
        freshness: Optional[str] = None,
        timeout: float = 10.0,
    ) -> List[SearchResult]:
        """Perform a web search using Brave Search API.

        Args:
            query: The search query string
            max_results: Maximum number of results to return (1-20)
            country: Country code for localized results (e.g., "US", "GB")
            search_lang: Language for search results (e.g., "en", "es")
            ui_lang: Language for UI elements (e.g., "en-US")
            safesearch: Safe search setting ("off", "moderate", "strict")
            freshness: Freshness of results ("pd" for past day, "pw" for past week, etc.)
            timeout: Request timeout in seconds

        Returns:
            List of search results with title, url, content, and score
        """
        if not query.strip():
            logger.warning("Empty query provided")
            return []

        if max_results < 1 or max_results > 20:
            logger.warning(f"max_results {max_results} out of range, clamping to 1-20")
            max_results = max(1, min(20, max_results))

        params = {"q": query, "count": max_results}

        # Add optional parameters
        if country:
            params["country"] = country
        if search_lang:
            params["search_lang"] = search_lang
        if ui_lang:
            params["ui_lang"] = ui_lang
        if safesearch != "moderate":
            params["safesearch"] = safesearch
        if freshness:
            params["freshness"] = freshness

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
            # Calculate a simple score based on position (higher position = lower score)
            score = max(0.1, 1.0 - (i * 0.1))

            result = SearchResult(
                title=item.get("title", "No title"),
                url=item.get("url", ""),
                content=item.get("description", "No description available"),
                score=score,
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

    def search_with_metadata(self, query: str, max_results: int = 5) -> Dict:
        """Perform search and return results with additional metadata.

        Args:
            query: The search query string
            max_results: Maximum number of results to return

        Returns:
            Dictionary with 'results', 'query_info', and 'search_metadata' keys
        """
        if not query.strip():
            return {"results": [], "query_info": {}, "search_metadata": {}}

        params = {"q": query, "count": max_results}

        try:
            self._wait_for_rate_limit()

            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    f"{self.base_url}/web/search", headers=self.headers, params=params
                )
                response.raise_for_status()

                data = response.json()

                return {
                    "results": self._parse_results(data),
                    "query_info": data.get("query", {}),
                    "search_metadata": {
                        "type": data.get("type", ""),
                        "discussions": len(
                            data.get("discussions", {}).get("results", [])
                        ),
                        "videos": len(data.get("videos", {}).get("results", [])),
                        "news": len(data.get("news", {}).get("results", [])),
                        "locations": len(data.get("locations", {}).get("results", [])),
                    },
                }

        except Exception as e:
            logger.error(f"Brave search with metadata failed: {e}")
            return {"results": [], "query_info": {}, "search_metadata": {}}

    def search_news(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Search for news articles using Brave Search.

        Args:
            query: The search query string
            max_results: Maximum number of results to return

        Returns:
            List of news results with title, url, content, and score
        """
        if not query.strip():
            return []

        params = {
            "q": query,
            "count": max_results,
            "freshness": "pd",  # Past day for news
        }

        try:
            self._wait_for_rate_limit()

            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    f"{self.base_url}/web/search", headers=self.headers, params=params
                )
                response.raise_for_status()

                data = response.json()
                results = []

                # Parse news results if available
                news_results = data.get("news", {}).get("results", [])
                for i, item in enumerate(news_results):
                    score = max(0.1, 1.0 - (i * 0.1))
                    result = {
                        "title": item.get("title", "No title"),
                        "url": item.get("url", ""),
                        "content": item.get("description", "No description available"),
                        "score": score,
                    }
                    results.append(result)

                # If no news results, fall back to web results
                if not results:
                    results = self._parse_results(data)

                logger.info(
                    f"Brave news search for '{query}' returned {len(results)} results"
                )
                return results

        except Exception as e:
            logger.error(f"Brave news search failed: {e}")
            return []


def main():
    """Demo usage of BraveSearch."""
    try:
        # Use rate limiting to avoid 429 errors (1 request per second for free tier)
        search = BraveSearch(rate_limit_delay=1.2)

        # Test basic search
        print("=== Basic Search Test ===")
        results = search.search("python machine learning frameworks", max_results=3)

        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result.title}")
            print(f"   URL: {result.url}")
            print(f"   Score: {result.score:.3f}")
            print(f"   Content: {result.content[:150]}...")

        # Test search with metadata (with delay)
        print("\n\n=== Search with Metadata Test ===")
        print("(Waiting for rate limit...)")
        response = search.search_with_metadata("artificial intelligence", max_results=2)

        print(f"Query processed: {response['query_info'].get('original', 'N/A')}")
        print(f"Search metadata: {response['search_metadata']}")

        print(f"\nFound {len(response['results'])} results:")
        for result in response["results"]:
            print(f"- {result['title']}: {result['url']}")

        # Test news search (with delay)
        print("\n\n=== News Search Test ===")
        print("(Waiting for rate limit...)")
        news_results = search.search_news("technology news", max_results=2)

        print(f"Found {len(news_results)} news results:")
        for result in news_results:
            print(f"- {result['title']}")
            print(f"  {result['url']}")

    except ValueError as e:
        print(f"Setup error: {e}")
        print("Please set your BRAVE_API_KEY environment variable.")
    except Exception as e:
        print(f"Demo failed: {e}")


if __name__ == "__main__":
    main()
