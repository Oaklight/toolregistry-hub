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
import os
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger

from .base import TIMEOUT_DEFAULT, BaseSearch
from .search_result import SearchResult


class ScrapelessSearch(BaseSearch):
    """Scrapeless DeepSERP API client for Google search functionality."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.scrapeless.com",
    ):
        """Initialize Scrapeless search client.

        Args:
            api_key: Scrapeless API key. If not provided, will try to get from SCRAPELESS_API_KEY env var.
            base_url: Base URL for Scrapeless API. Defaults to https://api.scrapeless.com
        """
        self.api_key = api_key or os.getenv("SCRAPELESS_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Scrapeless API key is required. Set SCRAPELESS_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.base_url = base_url
        self.endpoint = f"{self.base_url}/api/v1/scraper/request"

    @property
    def _headers(self) -> dict:
        """Generate headers with API key authentication."""
        return {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
        }

    def search(
        self,
        query: str,
        *,
        max_results: int = 5,
        timeout: float = TIMEOUT_DEFAULT,
        language: str = "en",
        country: str = "us",
        **kwargs,
    ) -> List[SearchResult]:
        """Perform a Google search using Scrapeless DeepSERP API.

        Args:
            query: The search query string
            max_results: Maximum number of results to return (1~20 recommended)
            timeout: Request timeout in seconds
            language: Language code (e.g., 'en', 'zh-CN', 'es'). Defaults to 'en'
            country: Country code (e.g., 'us', 'cn', 'uk'). Defaults to 'us'
            **kwargs: Additional parameters

        Returns:
            List of search results with title, url, content and score
        """
        if not query.strip():
            logger.warning("Empty query provided")
            return []

        results = self._search_impl(
            query=query,
            max_results=max_results,
            timeout=timeout,
            language=language,
            country=country,
            **kwargs,
        )

        return results[:max_results] if results else []

    def _search_impl(
        self,
        query: str,
        max_results: int = 5,
        timeout: float = TIMEOUT_DEFAULT,
        language: str = "en",
        country: str = "us",
        **kwargs,
    ) -> List[SearchResult]:
        """Perform the actual search using Scrapeless DeepSERP API.

        Args:
            query: The search query string
            max_results: Maximum number of results to return
            timeout: Request timeout in seconds
            language: Language code
            country: Country code
            **kwargs: Additional parameters

        Returns:
            List of SearchResult
        """
        # Prepare request payload for Scrapeless DeepSERP API
        payload = {
            "actor": "scraper.google.search",
            "input": {
                "q": query,
                "hl": language,
                "gl": country,
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

                # DeepSERP returns structured data directly
                results = self._parse_deepserp_results(response_data)

                logger.info(
                    f"Scrapeless DeepSERP search for '{query}' returned {len(results)} results"
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
        For DeepSERP API, raw_results is the JSON response dict.

        Args:
            raw_results: Raw API response data (parsed JSON dict)

        Returns:
            List of parsed search results
        """
        return self._parse_deepserp_results(raw_results)


    def _parse_deepserp_results(
        self, response_data: Dict[str, Any]
    ) -> List[SearchResult]:
        """Parse DeepSERP API response into standardized format.

        The DeepSERP API returns structured data in the following format:
        {
            "organic_results": [
                {
                    "position": 1,
                    "title": "...",
                    "link": "...",
                    "snippet": "...",
                    "redirect_link": "...",
                    "snippet_highlighted_words": [...],
                    "source": "..."
                }
            ]
        }

        Args:
            response_data: Raw API response data (parsed JSON)

        Returns:
            List of parsed search results
        """
        results = []

        # Extract organic search results
        organic_results = response_data.get("organic_results", [])

        for item in organic_results:
            try:
                # Extract required fields
                title = item.get("title", "No title")
                url = item.get("link") or item.get("redirect_link", "")
                snippet = item.get("snippet", "No description available")
                position = item.get("position", 0)

                if not url:
                    logger.debug(f"Skipping result without URL: {title}")
                    continue

                # Calculate score based on position (higher position = lower score)
                score = 1.0 - (position * 0.05) if position > 0 else 1.0
                score = max(0.0, min(1.0, score))  # Clamp between 0 and 1

                result = SearchResult(
                    title=title,
                    url=url,
                    content=snippet,
                    score=score,
                )
                results.append(result)
                logger.debug(f"Parsed result {position}: {title[:50]}...")

            except Exception as e:
                logger.debug(f"Error parsing DeepSERP result: {e}")
                continue

        if not results:
            logger.warning("No results parsed from DeepSERP response")
            logger.debug(f"Response data: {json.dumps(response_data, indent=2)[:500]}")

        return results


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
