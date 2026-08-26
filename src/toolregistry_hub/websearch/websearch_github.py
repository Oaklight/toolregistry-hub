"""
GitHub Search API Implementation

Searches GitHub repositories via the GitHub REST Search API.
Works unauthenticated (10 search requests/minute) or with personal access
tokens for higher throughput (30 search requests/minute per token).

Setup (optional — works without tokens at reduced rate limits):
    export GITHUB_TOKENS="ghp_token1,ghp_token2"

Usage:
    from toolregistry_hub.websearch import GitHubSearch

    search = GitHubSearch()
    results = search.search("machine learning language:python stars:>1000")

    for result in results:
        print(f"Repo: {result.title}")
        print(f"URL: {result.url}")
        print(f"Info: {result.content}")

API Documentation: https://docs.github.com/en/rest/search/search#search-repositories
Rate limits: https://docs.github.com/en/rest/search/search#rate-limit
"""

from typing import cast

from .._vendor.httpclient import Client, HTTPError, HttpTimeoutError, Response
from .._vendor.structlog import get_logger
from ..utils.api_key_parser import APIKeyParser
from .base import TIMEOUT_DEFAULT, BaseSearch, SearchBackendError
from .search_result import SearchResult

logger = get_logger()


class GitHubSearch(BaseSearch):
    """GitHub Search API client for repository search.

    Supports unauthenticated access and optional PAT-based authentication
    with key rotation for higher rate limits.
    """

    def __init__(self, api_keys: str | None = None, rate_limit_delay: float = 1.0):
        """Initialize GitHub search client.

        Args:
            api_keys: Comma-separated GitHub personal access tokens.
                If not provided, tries ``GITHUB_TOKENS`` env var.
                If neither is set, operates unauthenticated.
            rate_limit_delay: Delay between requests in seconds.
        """
        self.api_key_parser = APIKeyParser(
            api_keys=api_keys,
            env_var_name="GITHUB_TOKENS",
            rate_limit_delay=rate_limit_delay,
        )
        self.base_url = "https://api.github.com"

    def _is_configured(self) -> bool:
        """Always returns True — GitHub works without authentication."""
        return True

    def _build_headers(self, api_key: str | None = None) -> dict:
        """Generate request headers.

        Args:
            api_key: GitHub PAT for authenticated requests, or None for
                unauthenticated access.
        """
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "toolregistry-hub/GitHubSearch",
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        return headers

    def search(
        self,
        query: str,
        *,
        max_results: int = 5,
        timeout: float = TIMEOUT_DEFAULT,
        **kwargs,
    ) -> list[SearchResult]:
        """Search GitHub repositories.

        The query string supports GitHub search qualifiers, e.g.
        ``"machine learning language:python stars:>1000 topic:deep-learning"``.

        Args:
            query: Search query, optionally including GitHub qualifiers.
            max_results: Maximum number of results to return (capped at 100).
            timeout: Request timeout in seconds.
            **kwargs: Additional parameters forwarded to the GitHub API
                (``sort``, ``order``, ``page``).

        Returns:
            List of search results representing GitHub repositories.
        """
        if not query.strip():
            logger.warning("Empty query provided")
            return []

        max_results = min(max_results, 100)
        kwargs["per_page"] = max_results
        kwargs["timeout"] = timeout

        results = self._search_impl(query=query, **kwargs)
        return results[:max_results]

    def _build_params(self, query: str, **kwargs) -> dict:
        """Build query parameters for the GitHub Search API.

        Args:
            query: The search query string.
            **kwargs: Additional parameters from the caller.

        Returns:
            Dict of query parameters.
        """
        params: dict = {
            "q": query,
            "per_page": min(kwargs.get("per_page", 30), 100),
        }
        for key in ("sort", "order", "page"):
            if key in kwargs:
                params[key] = kwargs[key]
        return params

    def _search_impl(self, query: str, **kwargs) -> list[SearchResult]:
        """Perform the actual search against the GitHub API.

        When tokens are configured, retries with key rotation on auth/rate-limit
        errors. Without tokens, makes a single unauthenticated request.

        Args:
            query: The search query string.
            **kwargs: Additional parameters for the API.

        Returns:
            List of SearchResult.
        """
        if not query.strip():
            return []

        params = self._build_params(query, **kwargs)
        timeout = kwargs.get("timeout", TIMEOUT_DEFAULT)
        max_attempts = max(self.api_key_parser.key_count, 1)

        with Client(timeout=timeout) as client:
            for _attempt in range(max_attempts):
                api_key = None
                if self.api_key_parser.key_count > 0:
                    try:
                        api_key = self.api_key_parser.get_next_valid_key()
                    except ValueError:
                        logger.error("All GitHub tokens are currently unavailable")
                        break
                    self.api_key_parser.wait_for_rate_limit(api_key=api_key)

                try:
                    response = cast(
                        Response,
                        client.get(
                            f"{self.base_url}/search/repositories",
                            headers=self._build_headers(api_key),
                            params=params,
                        ),
                    )
                    response.raise_for_status()

                    data = response.json()
                    if data.get("incomplete_results"):
                        logger.warning(
                            "GitHub search returned incomplete results",
                            query=query,
                        )
                    results = self._parse_results(data)

                    logger.info(
                        "GitHub search returned results",
                        query=query,
                        count=len(results),
                    )
                    return results

                except HttpTimeoutError:
                    logger.error(
                        "GitHub API request timed out",
                        timeout=timeout,
                    )
                    return []
                except HTTPError as e:
                    if api_key and self._handle_http_error(e, api_key, "GitHub"):
                        continue
                    raise SearchBackendError(
                        f"GitHub API error {e.status_code}: {e.body}"
                    ) from e
                except SearchBackendError:
                    raise
                except Exception as e:
                    logger.error("GitHub API request failed", error=str(e))
                    return []

        raise SearchBackendError(
            "GitHub search failed: all tokens exhausted or unavailable"
        )

    def _parse_results(self, raw_results: dict) -> list[SearchResult]:
        """Parse GitHub API response into SearchResult objects.

        Args:
            raw_results: Raw JSON response from the GitHub Search API.

        Returns:
            List of parsed search results.
        """
        results = []
        for item in raw_results.get("items", []):
            description = item.get("description") or "No description"
            stars = item.get("stargazers_count", 0)
            language = item.get("language") or "Unknown"
            topics = item.get("topics", [])
            updated = item.get("updated_at", "")

            content_parts = [description, f"Stars: {stars} | Language: {language}"]
            if topics:
                content_parts.append(f"Topics: {', '.join(topics)}")
            if updated:
                content_parts.append(f"Updated: {updated}")

            results.append(
                SearchResult(
                    title=item.get("full_name", "unknown/unknown"),
                    url=item.get("html_url", ""),
                    content=" | ".join(content_parts),
                )
            )
        return results


def main():
    """Demo usage of GitHubSearch."""
    try:
        search = GitHubSearch()

        print("=== GitHub Repository Search ===")
        results = search.search(
            "machine learning language:python stars:>5000",
            max_results=5,
        )

        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result.title}")
            print(f"   URL: {result.url}")
            print(f"   {result.content}")

    except Exception as e:
        print(f"Demo failed: {e}")


if __name__ == "__main__":
    main()
