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
from typing import Any, List, Optional

import httpx
from loguru import logger

from ..utils.api_key_parser import APIKeyParser
from .base import TIMEOUT_DEFAULT, BaseSearch
from .google_parser import SCRAPELESS_CONFIG, GoogleResultParser
from .search_result import SearchResult


class ScrapelessSearch(BaseSearch):
    """Scrapeless DeepSERP API client for Google search functionality."""

    def __init__(
        self,
        api_keys: Optional[str] = None,
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

    @property
    def _headers(self) -> dict:
        """Generate headers with API key authentication."""
        return {
            "X-API-Key": self.api_key_parser.get_next_api_key(),
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
    ) -> List[SearchResult]:
        """Perform a Google search using Scrapeless DeepSERP API.

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
    ) -> List[SearchResult]:
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

        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.post(
                    self.endpoint, headers=self._headers, json=payload
                )
                response.raise_for_status()

                # Parse JSON response from Scrapeless DeepSERP API
                response_data = response.json()

                # # Debug: Log the complete raw response structure
                # logger.debug(f"Scrapeless raw response keys: {list(response_data.keys())}")
                # logger.debug(f"Scrapeless full response: {json.dumps(response_data, indent=2, ensure_ascii=False)}")

                # # Debug: Log organic results structure if available
                # if "organic_results" in response_data:
                #     logger.debug(f"Number of organic_results: {len(response_data['organic_results'])}")
                #     if response_data['organic_results']:
                #         logger.debug(f"First organic_result structure: {json.dumps(response_data['organic_results'][0], indent=2, ensure_ascii=False)}")

                # Use universal parser
                results = self.parser.parse(response_data)

                page_num = start // 10
                logger.info(
                    f"Scrapeless DeepSERP search for '{query}' (page {page_num}) returned {len(results)} results"
                )
                return results

        except httpx.TimeoutException:
            logger.error(f"Scrapeless API request timed out after {timeout}s")
            return []
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning("Rate limit exceeded")
            logger.error(
                f"Scrapeless API HTTP error {e.response.status_code}: {e.response.text}"
            )
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Scrapeless API response: {e}")
            return []
        except Exception as e:
            logger.error(f"Scrapeless API request failed: {e}")
            return []

    def _parse_results(self, raw_results: Any) -> List[SearchResult]:
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
