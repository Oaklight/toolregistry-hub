"""
Scrapeless DeepSERP API Search Implementation

This module provides a web search interface using Scrapeless DeepSERP API.
Scrapeless offers powerful web scraping capabilities with built-in anti-bot bypass
and returns structured search results without requiring HTML parsing.

The implementation uses the DeepSERP API (scraper.google.search) which provides
pre-parsed, structured Google search results.

Setup:
1. Sign up at https://app.scrapeless.com/ to get an API key
2. Set your API key as an environment variable:
   export SCRAPELESS_API_KEY="your-scrapeless-api-key-here"

Usage:
    from websearch_scrapeless import ScrapelessSearch

    search = ScrapelessSearch()
    results = search.search("python web scraping", max_results=5)

    for result in results:
        print(f"Title: {result.title}")
        print(f"URL: {result.url}")
        print(f"Content: {result.content[:200]}...")
        print(f"Score: {result.score}")
        print("-" * 50)

API Documentation: https://docs.scrapeless.com/
"""

import json
from typing import Any

from .._vendor.httpclient import Client, HTTPError, HttpTimeoutError

from .._vendor.structlog import get_logger
from ..utils.api_key_parser import APIKeyParser
from ..utils.requirements import requires_env
from .base import TIMEOUT_DEFAULT, BaseSearch
from .google_parser import SCRAPELESS_CONFIG, GoogleResultParser
from .search_result import SearchResult

logger = get_logger()


@requires_env("SCRAPELESS_API_KEY")
class ScrapelessSearch(BaseSearch):
    """Scrapeless DeepSERP API client for Google search functionality."""

    def __init__(
        self,
        api_keys: str | None = None,
        base_url: str = "https://api.scrapeless.com",
    ):
        """Initialize Scrapeless search client.

        Args:
            api_keys: Comma-separated Scrapeless API keys. If not provided, will try to get from SCRAPELESS_API_KEY env var.
            base_url: Base URL for Scrapeless API. Defaults to https://api.scrapeless.com
        """

        # Initialize API key parser for multiple keys
        self.api_key_parser = APIKeyParser(
            api_keys=api_keys,
            env_var_name="SCRAPELESS_API_KEY",
        )

        self.base_url = base_url
        self.endpoint = f"{self.base_url}/api/v1/scraper/request"

        # Initialize parser with Scrapeless configuration
        self.parser = GoogleResultParser(SCRAPELESS_CONFIG)

        logger.info(
            f"Initialized ScrapelessSearch with {self.api_key_parser.key_count} API keys"
        )

    def _build_headers(self, api_key: str | None = None) -> dict:
        """Generate headers with the given API key.

        Args:
            api_key: Scrapeless API key to use for authentication.
        """
        return {
            "X-API-Key": api_key or "",
            "Content-Type": "application/json",
        }

    def search(
        self,
        query: str,
        *,
        max_results: int = 5,
        timeout: float = TIMEOUT_DEFAULT,
        language: str = "en",
        country: str = "us",
        start: int = 0,
        **kwargs,
    ) -> list[SearchResult]:
        """Perform a Google search using Scrapeless DeepSERP API.

        IMPORTANT: For time-sensitive queries (e.g., "recent news", "latest updates", "today's events"),
        you MUST first obtain the current date/time using an available time/datetime tool before
        constructing your search query. As an LLM, you have no inherent sense of current time - your
        training data may be outdated. Always verify the current date when temporal context matters.

        Args:
            query: The search query string
            max_results: Maximum number of results to return (1~20 recommended)
            timeout: Request timeout in seconds
            language: Language code (e.g., 'en', 'zh-CN', 'es'). Defaults to 'en'
            country: Country code (e.g., 'us', 'cn', 'uk'). Defaults to 'us'
            start: Starting offset for pagination (0-based). Defaults to 0.
            **kwargs: Additional parameters

        Returns:
            List of search results with title, url, content and score
        """
        if not query.strip():
            logger.warning("Empty query provided")
            return []

        results = []

        if max_results <= 10:
            # Single request for small result sets
            results.extend(
                self._search_impl(
                    query=query,
                    timeout=timeout,
                    language=language,
                    country=country,
                    start=start,
                    **kwargs,
                )
            )
        else:
            # Multiple requests for larger result sets
            # Google returns ~10 results per page
            num_pages = (max_results + 9) // 10

            for page in range(num_pages):
                page_start = start + (page * 10)
                page_results = self._search_impl(
                    query=query,
                    timeout=timeout,
                    language=language,
                    country=country,
                    start=page_start,
                    **kwargs,
                )
                results.extend(page_results)

                # Stop if we got fewer results than expected (no more results available)
                if len(page_results) < 10:
                    break

        return results[:max_results] if results else []

    def _search_impl(
        self,
        query: str,
        start: int = 0,
        timeout: float = TIMEOUT_DEFAULT,
        language: str = "en",
        country: str = "us",
        **kwargs,
    ) -> list[SearchResult]:
        """Perform the actual search using Scrapeless DeepSERP API for a single page.

        Args:
            query: The search query string
            start: Starting offset for pagination (0-based)
            timeout: Request timeout in seconds
            language: Language code
            country: Country code
            **kwargs: Additional parameters

        Returns:
            List of SearchResult
        """
        if not query.strip():
            logger.warning("Empty query provided")
            return []

        # Prepare request payload for Scrapeless DeepSERP API
        # Use 'start' parameter for pagination (Google search standard)
        payload = {
            "actor": "scraper.google.search",
            "input": {
                "q": query,
                "hl": language,
                "gl": country,
                "start": start,  # Pagination offset
            },
            "async": False,  # Wait for result synchronously
        }

        max_attempts = max(self.api_key_parser.key_count, 1)

        for attempt in range(max_attempts):
            try:
                api_key = self.api_key_parser.get_next_valid_key()
            except ValueError:
                logger.error("All Scrapeless API keys are currently unavailable")
                break

            self.api_key_parser.wait_for_rate_limit(api_key=api_key)

            try:
                with Client(timeout=timeout) as client:
                    response = client.post(
                        self.endpoint,
                        headers=self._build_headers(api_key),
                        json=payload,
                    )
                    response.raise_for_status()

                    response_data = response.json()
                    results = self.parser.parse(response_data)

                    page_num = start // 10
                    logger.info(
                        f"Scrapeless DeepSERP search for '{query}' (page {page_num}) returned {len(results)} results"
                    )
                    return results

            except HttpTimeoutError:
                logger.error(f"Scrapeless API request timed out after {timeout}s")
                return []
            except HTTPError as e:
                status = e.status_code
                if status in (401, 403):
                    self.api_key_parser.mark_key_failed(
                        api_key, f"HTTP {status}", ttl=3600.0
                    )
                    logger.warning(
                        f"Scrapeless API key auth failed (HTTP {status}), trying next key"
                    )
                    continue
                if status == 429:
                    self.api_key_parser.mark_key_failed(
                        api_key, "rate limited", ttl=300.0
                    )
                    logger.warning(
                        "Scrapeless API rate limit exceeded, trying next key"
                    )
                    continue
                logger.error(f"Scrapeless API HTTP error {status}: {e.body}")
                return []
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Scrapeless API response: {e}")
                return []
            except Exception as e:
                logger.error(f"Scrapeless API request failed: {e}")
                return []

        return []

    def _parse_results(self, raw_results: Any) -> list[SearchResult]:
        """Parse raw search results into standardized format.

        This method is required by BaseSearch abstract class.
        This method now delegates to the universal GoogleResultParser.

        Args:
            raw_results: Raw API response data (parsed JSON dict)

        Returns:
            List of parsed search results
        """
        return self.parser.parse(raw_results)


def main():
    """Demo usage of ScrapelessSearch."""
    try:
        search = ScrapelessSearch()

        # Test Google search
        print("=== Google Search Test (DeepSERP API) ===")
        results = search.search(
            "artificial intelligence", max_results=5, language="en", country="us"
        )

        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result.title}")
            print(f"   URL: {result.url}")
            print(f"   Content: {result.content[:150]}...")
            print(f"   Score: {result.score:.3f}")

        # Test Chinese search
        print("\n\n=== Chinese Search Test ===")
        results_cn = search.search(
            "人工智能", max_results=5, language="zh-CN", country="cn"
        )

        for i, result in enumerate(results_cn, 1):
            print(f"\n{i}. {result.title}")
            print(f"   URL: {result.url}")
            print(f"   Content: {result.content[:150]}...")

    except ValueError as e:
        print(f"Setup error: {e}")
        print("Please set your SCRAPELESS_API_KEY environment variable.")
    except Exception as e:
        print(f"Demo failed: {e}")


if __name__ == "__main__":
    main()
