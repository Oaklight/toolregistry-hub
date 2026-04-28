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

from .._vendor.httpclient import Client, HTTPError, HttpTimeoutError

from .._vendor.structlog import get_logger
from ..utils.api_key_parser import APIKeyParser
from ..utils.requirements import requires_env
from .base import TIMEOUT_DEFAULT, BaseSearch
from .search_result import SearchResult

logger = get_logger()


@requires_env("TAVILY_API_KEY")
class TavilySearch(BaseSearch):
    """Simple Tavily Search API client for web search functionality."""

    def __init__(self, api_keys: str | None = None, rate_limit_delay: float = 0.5):
        """Initialize Tavily search client.

        Args:
            api_keys: Comma-separated Tavily API keys. If not provided, will try to get from TAVILY_API_KEY env var.
            rate_limit_delay: Delay between requests in seconds to avoid rate limits.
        """
        # Initialize API key parser for multiple keys
        self.api_key_parser = APIKeyParser(
            api_keys=api_keys,
            env_var_name="TAVILY_API_KEY",
            rate_limit_delay=rate_limit_delay,
        )

        self.base_url = "https://api.tavily.com"

    def _build_headers(self, api_key: str | None = None) -> dict:
        """Generate headers with the given API key.

        Args:
            api_key: Tavily API key to use for authentication.
        """
        return {
            "Authorization": f"Bearer {api_key or ''}",
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
        """Perform a web search using Tavily API.

        IMPORTANT: For time-sensitive queries (e.g., "recent news", "latest updates", "today's events"),
        you MUST first obtain the current date/time using an available time/datetime tool before
        constructing your search query. As an LLM, you have no inherent sense of current time - your
        training data may be outdated. Always verify the current date when temporal context matters.

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

    def _search_impl(self, query: str, **kwargs) -> list[SearchResult]:
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
        max_attempts = max(self.api_key_parser.key_count, 1)

        for attempt in range(max_attempts):
            try:
                api_key = self.api_key_parser.get_next_valid_key()
            except ValueError:
                logger.error("All Tavily API keys are currently unavailable")
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
                        f"Tavily search for '{query}' returned {len(results)} results"
                    )
                    return results

            except HttpTimeoutError:
                logger.error(f"Tavily API request timed out after {timeout}s")
                return []
            except HTTPError as e:
                status = e.status_code
                if status in (401, 403):
                    self.api_key_parser.mark_key_failed(
                        api_key, f"HTTP {status}", ttl=3600.0
                    )
                    logger.warning(
                        f"Tavily API key auth failed (HTTP {status}), trying next key"
                    )
                    continue
                if status == 429:
                    self.api_key_parser.mark_key_failed(
                        api_key, "rate limited", ttl=300.0
                    )
                    logger.warning("Tavily API rate limit exceeded, trying next key")
                    continue
                logger.error(f"Tavily API HTTP error {status}: {e.body}")
                return []
            except Exception as e:
                logger.error(f"Tavily API request failed: {e}")
                return []

        return []

    def _parse_results(self, raw_results: dict) -> list[SearchResult]:
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
