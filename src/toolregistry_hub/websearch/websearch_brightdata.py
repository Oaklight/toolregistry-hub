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
from typing import Any, cast
from urllib.parse import urlencode

from .._vendor.httpclient import Client, HTTPError, HttpTimeoutError, Response
from .._vendor.structlog import get_logger
from ..utils.api_key_parser import APIKeyParser
from ..utils.requirements import requires_env
from .base import BaseSearch, SearchBackendError
from .google_parser import BRIGHTDATA_CONFIG, GoogleResultParser
from .search_result import SearchResult

logger = get_logger()

# Bright Data SERP API routes through a proxy/scraping layer, so it is
# significantly slower than direct API services like Serper or Brave.
# 60 seconds gives enough headroom for slow responses while still
# catching stuck requests.
_BRIGHTDATA_TIMEOUT_DEFAULT: float = 60.0

# Aligned with official @brightdata/mcp package
_MCP_PACKAGE_NAME = "@brightdata/mcp"
_MCP_FALLBACK_VERSION = "2.9.5"
_NPM_REGISTRY_URL = "https://registry.npmjs.org/@brightdata/mcp/latest"

# Official MCP remote endpoint for account activation
_MCP_REMOTE_URL = "https://mcp.brightdata.com/mcp"

# Known BrightData error codes returned via x-brd-err-code header
_BRD_ERR_SUSPENDED = "client_10020"
_BRD_ERR_USAGE_LIMIT = "client_10100"

# Cached at module level — fetched once per process lifetime.
_mcp_version_cache: str | None = None


def _get_mcp_version() -> str:
    """Fetch the latest ``@brightdata/mcp`` version from the npm registry.

    The result is cached in ``_mcp_version_cache`` so subsequent calls
    are free.  Falls back to ``_MCP_FALLBACK_VERSION`` on any error.
    """
    global _mcp_version_cache  # noqa: PLW0603
    if _mcp_version_cache is not None:
        return _mcp_version_cache

    try:
        with Client(timeout=5.0) as client:
            resp = cast(Response, client.get(_NPM_REGISTRY_URL))
            resp.raise_for_status()
            version = resp.json().get("version", _MCP_FALLBACK_VERSION)
            _mcp_version_cache = version
            logger.debug(f"Fetched @brightdata/mcp version from npm: {version}")
            return version
    except Exception:
        logger.debug(
            f"Could not fetch @brightdata/mcp version from npm, "
            f"using fallback {_MCP_FALLBACK_VERSION}"
        )
        _mcp_version_cache = _MCP_FALLBACK_VERSION
        return _MCP_FALLBACK_VERSION


def _get_mcp_user_agent() -> str:
    """Return the user-agent string matching the official MCP package."""
    return f"{_MCP_PACKAGE_NAME}/{_get_mcp_version()}"


@requires_env("BRIGHTDATA_API_KEY")
class BrightDataSearch(BaseSearch):
    """Bright Data Google Search API client for web search functionality."""

    def __init__(
        self,
        api_keys: str | None = None,
        zone: str | None = None,
    ):
        """Initialize Bright Data search client.

        Args:
            api_keys: Comma-separated Bright Data API tokens. If not provided,
                will try to get from BRIGHTDATA_API_KEY env var.
            zone: Zone name for the request. If not provided, will try
                BRIGHTDATA_ZONE env var, defaults to 'mcp_unlocker'.

        Raises:
            ValueError: If API tokens are not provided and not found in
                environment variables.
        """
        # Initialize API key parser for multiple tokens
        self.api_key_parser = APIKeyParser(
            api_keys=api_keys,
            env_var_name="BRIGHTDATA_API_KEY",
        )

        self.zone = zone or os.getenv("BRIGHTDATA_ZONE", "mcp_unlocker")
        self.browser_zone = os.getenv("BRIGHTDATA_BROWSER_ZONE", "mcp_browser")
        self.base_url = "https://api.brightdata.com/request"

        # Initialize parser with Bright Data configuration
        self.parser = GoogleResultParser(BRIGHTDATA_CONFIG)

        # Ensure zones exist for each API key
        self._ensure_zone_exists_for_all_keys()

        logger.info(
            f"Initialized BrightDataSearch with zone: {self.zone}, "
            f"{self.api_key_parser.key_count} API tokens"
        )

    def _zone_api_headers(self, api_key: str) -> dict:
        """Generate headers for zone management API calls.

        Aligned with official @brightdata/mcp headers.

        Args:
            api_key: Bright Data API token.
        """
        return {
            "user-agent": _get_mcp_user_agent(),
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def _ensure_zone_exists_for_all_keys(self):
        """Ensure the required zones exist for all API keys.

        Creates both ``mcp_unlocker`` (unblocker) and ``mcp_browser``
        (browser_api) zones, aligned with the official @brightdata/mcp
        initialization behaviour.
        """
        for i, api_key in enumerate(self.api_key_parser.api_keys):
            try:
                headers = self._zone_api_headers(api_key)

                with Client(timeout=30.0) as client:
                    response = cast(
                        Response,
                        client.get(
                            "https://api.brightdata.com/zone/get_active_zones",
                            headers=headers,
                        ),
                    )
                    response.raise_for_status()
                    zones = response.json() or []

                    has_unlocker = any(zone.get("name") == self.zone for zone in zones)
                    has_browser = any(
                        zone.get("name") == self.browser_zone for zone in zones
                    )

                    key_label = f"key {i + 1}/{self.api_key_parser.key_count}"

                    if not has_unlocker:
                        logger.info(
                            f"Zone '{self.zone}' not found for {key_label}, "
                            f"creating it..."
                        )
                        create_response = client.post(
                            "https://api.brightdata.com/zone",
                            headers=headers,
                            json={
                                "zone": {
                                    "name": self.zone,
                                    "type": "unblocker",
                                },
                                "plan": {
                                    "type": "unblocker",
                                    "ub_premium": True,
                                },
                            },
                        )
                        create_response.raise_for_status()
                        logger.info(f"Zone '{self.zone}' created for {key_label}")
                    else:
                        logger.debug(
                            f"Zone '{self.zone}' already exists for {key_label}"
                        )

                    if not has_browser:
                        logger.info(
                            f"Zone '{self.browser_zone}' not found for "
                            f"{key_label}, creating it..."
                        )
                        create_response = client.post(
                            "https://api.brightdata.com/zone",
                            headers=headers,
                            json={
                                "zone": {
                                    "name": self.browser_zone,
                                    "type": "browser_api",
                                },
                                "plan": {"type": "browser_api"},
                            },
                        )
                        create_response.raise_for_status()
                        logger.info(
                            f"Zone '{self.browser_zone}' created for {key_label}"
                        )
                    else:
                        logger.debug(
                            f"Zone '{self.browser_zone}' already exists for {key_label}"
                        )

            except Exception as e:
                logger.warning(
                    f"Could not verify/create zones for key "
                    f"{i + 1}/{self.api_key_parser.key_count}: {e}. "
                    f"Proceeding anyway - zones might exist or will be "
                    f"created on first use."
                )

    def _build_headers(self, api_key: str | None = None) -> dict:
        """Generate headers for search API requests.

        Aligned with official @brightdata/mcp ``api_headers()`` including
        ``user-agent`` and ``x-mcp-tool`` headers.

        Args:
            api_key: Bright Data API token to use for authentication.
        """
        return {
            "user-agent": _get_mcp_user_agent(),
            "Authorization": f"Bearer {api_key or ''}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "x-mcp-tool": "search_engine",
        }

    @staticmethod
    def _check_brd_error(response: Response) -> None:
        """Check BrightData-specific error headers on the response.

        BrightData may return HTTP 200 with an empty body when the account
        has issues.  The actual error information is conveyed via
        ``x-brd-err-code`` / ``x-brd-err-msg`` response headers.

        Args:
            response: The HTTP response to inspect.

        Raises:
            SearchBackendError: If a BrightData error code is detected.
        """
        err_code = response.headers.get("x-brd-err-code")
        if not err_code:
            return

        err_msg = response.headers.get(
            "x-brd-err-msg",
            response.headers.get("x-brd-error", "Unknown error"),
        )

        if err_code == _BRD_ERR_SUSPENDED:
            raise SearchBackendError(
                f"BrightData account is suspended ({err_code}): {err_msg}. "
                f"Visit https://brightdata.com/cp/setting/billing to "
                f"reactivate."
            )

        if err_code == _BRD_ERR_USAGE_LIMIT:
            raise SearchBackendError(
                f"BrightData free tier limit reached ({err_code}): {err_msg}. "
                f"Create a new Web Unlocker zone at brightdata.com/cp or "
                f"upgrade your plan."
            )

        raise SearchBackendError(f"BrightData API error ({err_code}): {err_msg}")

    @staticmethod
    def activate_account(api_key: str, timeout: float = 30.0) -> bool:
        """Activate a new BrightData account via the official remote MCP.

        New BrightData accounts must be initialized through the official
        MCP endpoint at ``mcp.brightdata.com`` to provision the free
        monthly allowance ($7.50).  This method performs that one-time
        initialization.

        Args:
            api_key: The BrightData API token to activate.
            timeout: Request timeout in seconds.

        Returns:
            True if activation succeeded, False otherwise.
        """
        try:
            with Client(timeout=timeout) as client:
                response = cast(
                    Response,
                    client.post(
                        f"{_MCP_REMOTE_URL}?token={api_key}",
                        headers={
                            "Content-Type": "application/json",
                            "Accept": "text/event-stream, application/json",
                        },
                        data=json.dumps(
                            {
                                "jsonrpc": "2.0",
                                "id": 1,
                                "method": "initialize",
                                "params": {
                                    "protocolVersion": "2024-11-05",
                                    "capabilities": {},
                                    "clientInfo": {
                                        "name": _MCP_PACKAGE_NAME,
                                        "version": _get_mcp_version(),
                                    },
                                },
                            }
                        ),
                    ),
                )
                if response.status_code == 200 and response.text:
                    logger.info(
                        f"BrightData account activated via official MCP "
                        f"for key {api_key[:8]}..."
                    )
                    return True
                logger.warning(
                    f"BrightData account activation returned "
                    f"HTTP {response.status_code} for key {api_key[:8]}..."
                )
                return False
        except Exception as e:
            logger.warning(
                f"Failed to activate BrightData account for key {api_key[:8]}...: {e}"
            )
            return False

    def search(
        self,
        query: str,
        *,
        max_results: int = 5,
        timeout: float = _BRIGHTDATA_TIMEOUT_DEFAULT,
        cursor: str | None = None,
        **kwargs,
    ) -> list[SearchResult]:
        """Perform a web search using Bright Data Google Search API.

        IMPORTANT: For time-sensitive queries (e.g., "recent news", "latest
        updates", "today's events"), you MUST first obtain the current
        date/time using an available time/datetime tool before constructing
        your search query. As an LLM, you have no inherent sense of current
        time - your training data may be outdated. Always verify the current
        date when temporal context matters.

        Args:
            query: The search query string
            max_results: Maximum number of results to return
                (1~20 recommended, 180 at max)
            timeout: Request timeout in seconds (default: 60s, higher
                than other providers due to proxy/scraping latency)
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
                        query=query,
                        timeout=timeout,
                        cursor=page_cursor,
                        **kwargs,
                    )
                )

        return results[:max_results] if results else []

    def _search_impl(
        self, query: str, cursor: str | None = None, **kwargs
    ) -> list[SearchResult]:
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
            "start": page_num * 10,  # Google uses 'start' for pagination
            "brd_json": "1",  # Bright Data flag for JSON response
        }
        google_url = f"https://www.google.com/search?{urlencode(search_params)}"

        # Prepare request payload for Bright Data API
        payload = {
            "url": google_url,
            "zone": self.zone,
            "format": "raw",
            "data_format": "parsed",  # Request parsed/structured data
        }

        timeout = kwargs.get("timeout", _BRIGHTDATA_TIMEOUT_DEFAULT)

        max_attempts = max(self.api_key_parser.key_count, 1)

        for _attempt in range(max_attempts):
            try:
                api_key = self.api_key_parser.get_next_valid_key()
            except ValueError:
                logger.error("All Bright Data API keys are currently unavailable")
                break

            self.api_key_parser.wait_for_rate_limit(api_key=api_key)

            try:
                with Client(timeout=timeout) as client:
                    response = cast(
                        Response,
                        client.post(
                            self.base_url,
                            headers=self._build_headers(api_key),
                            json=payload,
                        ),
                    )
                    response.raise_for_status()

                    # Check BrightData-specific error headers (may be
                    # present even on HTTP 200)
                    self._check_brd_error(response)

                    raw_data = response.text
                    if not raw_data or not raw_data.strip():
                        raise SearchBackendError(
                            "BrightData API returned HTTP 200 with empty "
                            "body. The account may be suspended or the "
                            "zone may be misconfigured."
                        )

                    data = json.loads(raw_data)
                    results = self.parser.parse(data)

                    logger.info(
                        f"Bright Data search for '{query}' (page "
                        f"{page_num}) returned {len(results)} results"
                    )
                    return results

            except SearchBackendError:
                raise
            except HttpTimeoutError:
                logger.error(f"Bright Data API request timed out after {timeout}s")
                return []
            except HTTPError as e:
                if e.status_code == 422:
                    raise SearchBackendError(
                        f"BrightData zone '{self.zone}' does not exist or "
                        f"account is in invalid state (HTTP 422). Check "
                        f"your BRIGHTDATA_ZONE configuration."
                    ) from e
                if self._handle_http_error(e, api_key, "Bright Data"):
                    continue
                raise SearchBackendError(
                    f"BrightData API returned HTTP {e.status_code}: {str(e.body)[:200]}"
                ) from e
            except json.JSONDecodeError as e:
                raise SearchBackendError(
                    f"Failed to parse BrightData API response as JSON: {e}"
                ) from e
            except Exception as e:
                raise SearchBackendError(f"BrightData API request failed: {e}") from e

        raise SearchBackendError(
            "All BrightData API keys exhausted without a successful response"
        )

    def _parse_results(self, raw_results: dict[str, Any]) -> list[SearchResult]:
        """Parse Bright Data API response into standardized format.

        This method now delegates to the universal GoogleResultParser.

        Args:
            raw_results: Raw API response data (parsed JSON)

        Returns:
            List of parsed search results
        """
        return self.parser.parse(raw_results)


def main():
    """Demo usage of BrightDataSearch."""
    try:
        search = BrightDataSearch()

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
