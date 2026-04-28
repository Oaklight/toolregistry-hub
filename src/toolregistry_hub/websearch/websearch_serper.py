"""
Serper Google Search API Implementation

This module provides a web search interface using the Serper API (serper.dev).
Serper offers fast Google search results (1-2 seconds) via a simple POST-based API
with structured JSON responses.

Setup:
1. Sign up at https://serper.dev/ to get an API key
2. Set your API key as an environment variable:
   export SERPER_API_KEY="your-serper-api-key-here"

Usage:
    from websearch_serper import SerperSearch

    search = SerperSearch()
    results = search.search("python web scraping", max_results=5)

    for result in results:
        print(f"Title: {result.title}")
        print(f"URL: {result.url}")
        print(f"Content: {result.content[:200]}...")
        print(f"Score: {result.score}")
        print("-" * 50)

API Documentation: https://serper.dev/playground
"""

import json
from typing import Any

from .._vendor.httpclient import Client, HTTPError, HttpTimeoutError

from .._vendor.structlog import get_logger
from ..utils.api_key_parser import APIKeyParser
from ..utils.requirements import requires_env
from .base import TIMEOUT_DEFAULT, BaseSearch
from .search_result import SearchResult

logger = get_logger()


@requires_env("SERPER_API_KEY")
class SerperSearch(BaseSearch):
    """Serper Google Search API client for web search functionality.

    Serper provides fast, affordable Google search results via a POST-based API.
    It supports multiple search types including web, news, images, videos,
    places, maps, shopping, scholar, patents, and autocomplete.
    """

    def __init__(
        self,
        api_keys: str | None = None,
        rate_limit_delay: float = 1.0,
    ):
        """Initialize Serper search client.

        Args:
            api_keys: Comma-separated Serper API keys. If not provided, will try to get from SERPER_API_KEY env var.
            rate_limit_delay: Delay between requests in seconds to avoid rate limits.
        """
        self.api_key_parser = APIKeyParser(
            api_keys=api_keys,
            env_var_name="SERPER_API_KEY",
            rate_limit_delay=rate_limit_delay,
        )

        self.base_url = "https://google.serper.dev"

    def _build_headers(self, api_key: str | None = None) -> dict:
        """Generate headers with the given API key.

        Args:
            api_key: Serper API key to use for authentication.
        """
        return {
            "X-API-KEY": api_key or "",
            "Content-Type": "application/json",
        }

    def search(
        self,
        query: str,
        *,
        max_results: int = 5,
        timeout: float = TIMEOUT_DEFAULT,
        **kwargs,
    ) -> list[SearchResult]:
        """Perform a Google search using Serper API.

        IMPORTANT: For time-sensitive queries (e.g., "recent news", "latest updates", "today's events"),
        you MUST first obtain the current date/time using an available time/datetime tool before
        constructing your search query. As an LLM, you have no inherent sense of current time - your
        training data may be outdated. Always verify the current date when temporal context matters.

        Args:
            query: The search query string
            max_results: Maximum number of results to return (1~100)
            timeout: Request timeout in seconds
            **kwargs: Additional query parameters supported by Serper API:
                - gl (str): Country code (e.g., 'us', 'uk', 'cn')
                - hl (str): Language code (e.g., 'en', 'zh', 'es')
                - location (str): Location for localized results (e.g., 'Austin, Texas')
                - autocorrect (bool): Enable/disable spell correction
                - page (int): Result page number (1-based)

        Returns:
            List of search results with title, url, content and score
        """
        if not query.strip():
            logger.warning("Empty query provided")
            return []

        results = []

        if max_results <= 100:
            results.extend(
                self._search_impl(
                    query=query, num=max_results, timeout=timeout, **kwargs
                )
            )
        else:
            # Paginate for large result sets
            collected = 0
            page = 1
            while collected < max_results:
                remaining = max_results - collected
                num = min(remaining, 100)
                page_results = self._search_impl(
                    query=query, num=num, timeout=timeout, page=page, **kwargs
                )
                results.extend(page_results)
                collected += len(page_results)
                page += 1

                if len(page_results) < num:
                    break

        return results[:max_results] if results else []

    def _search_impl(self, query: str, **kwargs) -> list[SearchResult]:
        """Perform the actual search using Serper API for a single request.

        Args:
            query: The search query string
            **kwargs: Additional parameters specific to the Serper API

        Returns:
            List of SearchResult
        """
        if not query.strip():
            logger.warning("Empty query provided")
            return []

        payload: dict[str, Any] = {"q": query}

        # Add num parameter
        num = kwargs.get("num")
        if num is not None:
            payload["num"] = num

        # Add optional parameters
        optional_params = ["gl", "hl", "location", "autocorrect", "page"]
        for param in optional_params:
            if param in kwargs and kwargs[param] is not None:
                payload[param] = kwargs[param]

        # Add any additional kwargs not already handled
        handled = {"num", "timeout"} | set(optional_params)
        for key, value in kwargs.items():
            if key not in handled:
                payload[key] = value

        timeout = kwargs.get("timeout", TIMEOUT_DEFAULT)

        max_attempts = max(self.api_key_parser.key_count, 1)

        for attempt in range(max_attempts):
            try:
                api_key = self.api_key_parser.get_next_valid_key()
            except ValueError:
                logger.error("All Serper API keys are currently unavailable")
                break

            self.api_key_parser.wait_for_rate_limit(api_key=api_key)

            try:
                with Client(timeout=timeout) as client:
                    response = client.post(
                        f"{self.base_url}/search",
                        headers=self._build_headers(api_key),
                        json=payload,
                    )
                    response.raise_for_status()

                    data = response.json()
                    results = self._parse_results(data)

                    logger.info(
                        f"Serper search for '{query}' returned {len(results)} results"
                    )
                    return results

            except HttpTimeoutError:
                logger.error(f"Serper API request timed out after {timeout}s")
                return []
            except HTTPError as e:
                status = e.status_code
                if status in (401, 403):
                    self.api_key_parser.mark_key_failed(
                        api_key, f"HTTP {status}", ttl=3600.0
                    )
                    logger.warning(
                        f"Serper API key auth failed (HTTP {status}), trying next key"
                    )
                    continue
                if status == 429:
                    self.api_key_parser.mark_key_failed(
                        api_key, "rate limited", ttl=300.0
                    )
                    logger.warning("Serper API rate limit exceeded, trying next key")
                    continue
                logger.error(f"Serper API HTTP error {status}: {e.body}")
                return []
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Serper API response: {e}")
                return []
            except Exception as e:
                logger.error(f"Serper API request failed: {e}")
                return []

        return []

    def _parse_results(self, raw_results: Any) -> list[SearchResult]:
        """Parse Serper API response into standardized format.

        Args:
            raw_results: Raw API response data

        Returns:
            List of parsed search results
        """
        results = []

        # Parse organic results
        organic_results = raw_results.get("organic", [])

        for item in organic_results:
            result = SearchResult(
                title=item.get("title", "No title"),
                url=item.get("link", ""),
                content=item.get("snippet", "No content available"),
            )
            results.append(result)

        return results


def main():
    """Demo usage of SerperSearch."""
    try:
        search = SerperSearch(rate_limit_delay=1.0)

        print("=== Serper Google Search Test ===")
        results = search.search("artificial intelligence", max_results=5)

        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result.title}")
            print(f"   URL: {result.url}")
            print(f"   Content: {result.content}...")
            print(f"   Score: {result.score:.3f}")

    except ValueError as e:
        print(f"Setup error: {e}")
        print("Please set your SERPER_API_KEY environment variable.")
    except Exception as e:
        print(f"Demo failed: {e}")


if __name__ == "__main__":
    main()
