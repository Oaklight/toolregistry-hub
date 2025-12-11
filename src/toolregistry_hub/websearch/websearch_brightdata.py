"""
Bright Data Google Search API Implementation

This module provides an interface to Bright Data's SERP API for Google search functionality.
Bright Data offers enterprise-grade web scraping with automatic anti-bot bypass.

Setup:
1. Sign up at https://brightdata.com to get an API token
2. Set your API token as an environment variable:
   export BRIGHTDATA_API_KEY="your-api-token-here"
3. (Optional) Set custom zone:
   export BRIGHTDATA_ZONE="your-zone-name"

Usage:
    from websearch_brightdata import BrightDataSearch

    search = BrightDataSearch()
    results = search.search("python web scraping", max_results=10)

    for result in results:
        print(f"Title: {result.title}")
        print(f"URL: {result.url}")
        print(f"Content: {result.content[:200]}...")
        print("-" * 50)

API Documentation: https://docs.brightdata.com/
"""

import json
import os
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import httpx
from loguru import logger

from .base import TIMEOUT_DEFAULT, BaseSearch
from .google_parser import BRIGHTDATA_CONFIG, GoogleResultParser
from .search_result import SearchResult


class BrightDataSearch(BaseSearch):
    """Bright Data Google Search API client for web search functionality."""

    def __init__(
        self,
        api_token: Optional[str] = None,
        zone: Optional[str] = None,
        rate_limit_delay: float = 1.0,
    ):
        """Initialize Bright Data search client.

        Args:
            api_token: Bright Data API token. If not provided, will try to get from BRIGHTDATA_API_KEY env var.
            zone: Zone name for the request. If not provided, will try BRIGHTDATA_ZONE env var, defaults to 'mcp_unlocker'.
            rate_limit_delay: Delay between requests in seconds to avoid rate limits.

        Raises:
            ValueError: If API token is not provided and not found in environment variables.
        """
        self.api_token = api_token or os.getenv("BRIGHTDATA_API_KEY")
        if not self.api_token:
            raise ValueError(
                "Bright Data API token is required. Set BRIGHTDATA_API_KEY environment variable "
                "or pass api_token parameter."
            )

        self.zone = zone or os.getenv("BRIGHTDATA_ZONE", "mcp_unlocker")
        self.base_url = "https://api.brightdata.com/request"
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0

        # Initialize parser with Bright Data configuration
        self.parser = GoogleResultParser(BRIGHTDATA_CONFIG)

        # Ensure zone exists
        self._ensure_zone_exists()

        logger.info(f"Initialized BrightDataSearch with zone: {self.zone}")

    def _ensure_zone_exists(self):
        """Ensure the required zone exists, create it if it doesn't."""
        try:
            # Check if zone exists
            with httpx.Client(timeout=30.0) as client:
                response = client.get(
                    "https://api.brightdata.com/zone/get_active_zones",
                    headers=self._headers,
                )
                response.raise_for_status()
                zones = response.json() or []

                has_zone = any(zone.get("name") == self.zone for zone in zones)

                if not has_zone:
                    logger.info(f"Zone '{self.zone}' not found, creating it...")
                    # Create the zone
                    create_response = client.post(
                        "https://api.brightdata.com/zone",
                        headers=self._headers,
                        json={
                            "zone": {"name": self.zone, "type": "unblocker"},
                            "plan": {"type": "unblocker"},
                        },
                    )
                    create_response.raise_for_status()
                    logger.info(f"Zone '{self.zone}' created successfully")
                else:
                    logger.debug(f"Zone '{self.zone}' already exists")

        except Exception as e:
            logger.warning(
                f"Could not verify/create zone '{self.zone}': {e}. "
                f"Proceeding anyway - zone might exist or will be created on first use."
            )

    @property
    def _headers(self) -> dict:
        """Generate headers for API requests."""
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def search(
        self,
        query: str,
        *,
        max_results: int = 5,
        timeout: float = TIMEOUT_DEFAULT,
        cursor: Optional[str] = None,
        **kwargs,
    ) -> List[SearchResult]:
        """Perform a web search using Bright Data Google Search API.

        Args:
            query: The search query string
            max_results: Maximum number of results to return (1~20 recommended, 180 at max)
            timeout: Request timeout in seconds
            cursor: Pagination cursor (page number, 0-based). Defaults to 0.
            **kwargs: Additional parameters (currently unused)

        Returns:
            List of search results with title, url, content and score
        """
        if not query.strip():
            logger.warning("Empty query provided")
            return []

        results = []

        if max_results <= 20:
            results.extend(
                self._search_impl(query=query, timeout=timeout, cursor=cursor, **kwargs)
            )
        else:
            if max_results > 180:
                logger.warning("max_results exceeds the maximum limit of 180")
                max_results = 180

            # Calculate number of pages needed (20 results per page)
            num_pages = (max_results + 19) // 20

            for page in range(num_pages):
                page_cursor = str(page) if cursor is None else str(int(cursor) + page)
                results.extend(
                    self._search_impl(
                        query=query, timeout=timeout, cursor=page_cursor, **kwargs
                    )
                )

        return results[:max_results] if results else []

    def _search_impl(
        self, query: str, cursor: Optional[str] = None, **kwargs
    ) -> List[SearchResult]:
        """Perform the actual search using Bright Data API for a single query.

        Args:
            query: The search query string
            cursor: Pagination cursor (page number, 0-based)
            **kwargs: Additional parameters (timeout, etc.)

        Returns:
            List of SearchResult
        """
        if not query.strip():
            logger.warning("Empty query provided")
            return []

        # Build Google search URL
        page_num = int(cursor or 0)
        search_params = {
            "q": query,
            "start": page_num * 10,  # Google uses 'start' parameter for pagination
            "brd_json": "1",  # Bright Data specific flag for JSON response
        }
        google_url = f"https://www.google.com/search?{urlencode(search_params)}"

        # Prepare request payload for Bright Data API
        payload = {
            "url": google_url,
            "zone": self.zone,
            "format": "raw",
            "data_format": "parsed",  # Request parsed/structured data
        }

        timeout = kwargs.get("timeout", TIMEOUT_DEFAULT)

        try:
            # Rate limiting: ensure minimum delay between requests
            self._wait_for_rate_limit()

            with httpx.Client(timeout=timeout) as client:
                response = client.post(
                    self.base_url,
                    headers=self._headers,
                    json=payload,
                )
                response.raise_for_status()

                # Parse the response
                # Bright Data returns the Google SERP data as text
                raw_data = response.text
                data = json.loads(raw_data)

                # # Debug: Log the complete raw response structure
                # logger.debug(f"Bright Data raw response keys: {list(data.keys())}")
                # logger.debug(
                #     f"Bright Data full response: {json.dumps(data, indent=2, ensure_ascii=False)}"
                # )

                # # Debug: Log organic results structure if available
                # if "organic" in data:
                #     logger.debug(f"Number of organic results: {len(data['organic'])}")
                #     if data["organic"]:
                #         logger.debug(
                #             f"First organic result structure: {json.dumps(data['organic'][0], indent=2, ensure_ascii=False)}"
                #         )

                # Use universal parser
                results = self.parser.parse(data)

                logger.info(
                    f"Bright Data search for '{query}' (page {page_num}) returned {len(results)} results"
                )
                return results

        except httpx.TimeoutException:
            logger.error(f"Bright Data API request timed out after {timeout}s")
            return []
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.error("Authentication failed. Check your BRIGHTDATA_API_KEY")
            elif e.response.status_code == 422:
                logger.error(
                    f"Zone '{self.zone}' does not exist. Check your BRIGHTDATA_ZONE configuration"
                )
            elif e.response.status_code == 429:
                logger.warning(
                    "Rate limit exceeded, consider increasing rate_limit_delay"
                )
            else:
                logger.error(
                    f"Bright Data API HTTP error {e.response.status_code}: {e.response.text}"
                )
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Bright Data API response: {e}")
            return []
        except Exception as e:
            logger.error(f"Bright Data API request failed: {e}")
            return []

    def _parse_results(self, raw_results: Dict[str, Any]) -> List[SearchResult]:
        """Parse Bright Data API response into standardized format.

        This method now delegates to the universal GoogleResultParser.

        Args:
            raw_results: Raw API response data (parsed JSON)

        Returns:
            List of parsed search results
        """
        return self.parser.parse(raw_results)

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
    """Demo usage of BrightDataSearch."""
    try:
        search = BrightDataSearch(rate_limit_delay=1.2)

        # Test basic search
        print("=== Basic Search Test ===")
        results = search.search("artificial intelligence", max_results=10)

        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result.title}")
            print(f"   URL: {result.url}")
            print(f"   Content: {result.content[:150]}...")
            print(f"   Score: {result.score:.3f}")

        # Test pagination
        print("\n\n=== Pagination Test (Page 2) ===")
        results_page2 = search.search(
            "artificial intelligence", max_results=5, cursor="1"
        )

        for i, result in enumerate(results_page2, 1):
            print(f"\n{i}. {result.title}")
            print(f"   URL: {result.url}")

    except ValueError as e:
        print(f"Setup error: {e}")
        print("Please set your BRIGHTDATA_API_KEY environment variable.")
    except Exception as e:
        print(f"Demo failed: {e}")


if __name__ == "__main__":
    main()
