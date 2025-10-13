"""
Tavily Search API Demo Implementation

This module provides a simple interface to the Tavily Search API for web search functionality.
Tavily offers AI-powered search with LLM-generated answers and high-quality results.

Setup:
1. Sign up at https://tavily.com/ to get an API key
2. Set your API key as an environment variable:
   export TAVILY_API_KEY="tvly-your-api-key-here"

Usage:
    from websearch_tavily import TavilySearch

    search = TavilySearch()
    results = search.search("python web scraping", max_results=5)

    for result in results:
        print(f"Title: {result['title']}")
        print(f"URL: {result['url']}")
        print(f"Content: {result['content'][:200]}...")
        print(f"Score: {result['score']}")
        print("-" * 50)

API Documentation: https://docs.tavily.com/documentation/api-reference/endpoint/search
"""

import os
import time
from typing import Dict, List, Optional

import httpx
from loguru import logger

from .base import TIMEOUT_DEFAULT, BaseSearch
from .search_result import SearchResult


class TavilySearch(BaseSearch):
    """Simple Tavily Search API client for web search functionality."""

    def __init__(self, api_keys: Optional[str] = None, rate_limit_delay: float = 0.5):
        """Initialize Tavily search client.

        Args:
            api_keys: Comma-separated Tavily API keys. If not provided, will try to get from TAVILY_API_KEY env var.
            rate_limit_delay: Delay between requests in seconds to avoid rate limits.
        """
        api_keys_str = api_keys or os.getenv("TAVILY_API_KEY")
        if not api_keys_str:
            raise ValueError(
                "Tavily API keys are required. Set TAVILY_API_KEY environment variable "
                "or pass api_keys parameter (comma-separated)."
            )

        # Parse and validate API keys
        self.api_keys = [key.strip() for key in api_keys_str.split(",") if key.strip()]
        if not self.api_keys:
            raise ValueError("No valid API keys provided")

        self.base_url = "https://api.tavily.com"
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0
        self._current_key_index = 0

    def _get_next_api_key(self) -> str:
        """Round-robin API key selection."""
        key = self.api_keys[self._current_key_index]
        self._current_key_index = (self._current_key_index + 1) % len(self.api_keys)
        return key

    @property
    def _headers(self) -> dict:
        """Generate headers with the current API key."""
        return {
            "Authorization": f"Bearer {self._get_next_api_key()}",
            "Content-Type": "application/json",
        }

    def search(
        self,
        query: str,
        *,
        max_results: int = 5,
        timeout: float = TIMEOUT_DEFAULT,
        **kwargs,
    ) -> List[SearchResult]:
        """Perform a web search using Tavily API.

        Args:
            query: The search query string
            max_results: Maximum number of results to return (0-20)
            timeout: Request timeout in seconds
            **kwargs: Additional parameters to pass to the API. See https://docs.tavily.com/documentation/api-reference/endpoint/search for details.

        Returns:
            List of search results with title, url, content and score.
        """
        if not query.strip():
            logger.warning("Empty query provided")
            return []

        if max_results > 20:
            logger.warning("max_results exceeds the maximum allowed value of 20")
            max_results = 20

        kwargs["max_results"] = max_results
        kwargs["timeout"] = timeout

        results = self._search_impl(query=query, **kwargs)

        return results[:max_results] if results else []

    def _search_impl(self, query: str, **kwargs) -> List[SearchResult]:
        """Perform the actual search using Tavily API for a single query.

        Args:
            query: The search query string
            **kwargs: Additional parameters specific to the Tavily API

        Returns:
            List of SearchResult
        """
        if not query.strip():
            logger.warning("Empty query provided")
            return []

        max_results = kwargs.get("max_results", 5)
        if max_results < 0 or max_results > 20:
            logger.warning(f"max_results {max_results} out of range, clamping to 0-20")
            max_results = max(0, min(20, max_results))

        payload = {
            "query": query,
            "max_results": max_results,
            "topic": kwargs.get("topic", "general"),
            "search_depth": kwargs.get("search_depth", "basic"),
            "include_answer": kwargs.get("include_answer", False),
        }

        # Add any additional kwargs
        optional_params = ["include_domains", "exclude_domains", "include_raw_content"]
        for param in optional_params:
            if param in kwargs:
                payload[param] = kwargs[param]

        timeout = kwargs.get("timeout", TIMEOUT_DEFAULT)
        try:
            # Rate limiting: ensure minimum delay between requests
            self._wait_for_rate_limit()

            with httpx.Client(timeout=timeout) as client:
                response = client.post(
                    f"{self.base_url}/search", headers=self._headers, json=payload
                )
                response.raise_for_status()

                data = response.json()
                results = self._parse_results(data)

                logger.info(
                    f"Tavily search for '{query}' returned {len(results)} results"
                )
                return results

        except httpx.TimeoutException:
            logger.error(f"Tavily API request timed out after {timeout}s")
            return []
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning(
                    "Rate limit exceeded, consider increasing rate_limit_delay"
                )
            logger.error(
                f"Tavily API HTTP error {e.response.status_code}: {e.response.text}"
            )
            return []
        except Exception as e:
            logger.error(f"Tavily API request failed: {e}")
            return []

    def _parse_results(self, raw_results: Dict) -> List[SearchResult]:
        """Parse Tavily API response into standardized format.

        Args:
            raw_results: Raw API response data

        Returns:
            List of parsed search results
        """
        results = []

        # Add LLM answer as first result if available
        if raw_results.get("answer"):
            answer_result = SearchResult(
                title="AI Generated Answer",
                url="",
                content=raw_results["answer"],
                score=1.0,
            )
            results.append(answer_result)

        # Parse search results
        for item in raw_results.get("results", []):
            result = SearchResult(
                title=item.get("title", "No title"),
                url=item.get("url", ""),
                content=item.get("content", "No content available"),
                score=float(item.get("score", 0.0)),
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
    """Demo usage of TavilySearch."""
    try:
        search = TavilySearch()

        # Test basic search
        print("=== Basic Search Test ===")
        results = search.search("python web scraping libraries", max_results=5)

        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result.title}")
            print(f"   URL: {result.url}")
            print(f"   Content: {result.content}")
            print(f"   Score: {result.score:.3f}")

    except ValueError as e:
        print(f"Setup error: {e}")
        print("Please set your TAVILY_API_KEY environment variable.")
    except Exception as e:
        print(f"Demo failed: {e}")


if __name__ == "__main__":
    main()
