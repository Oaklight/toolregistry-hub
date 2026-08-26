"""
Reddit Search via Arctic Shift API

Searches Reddit posts via the Arctic Shift API, a free archive of all public
Reddit data from 2005 to present.  No API key or OAuth required.

The API requires a ``subreddit`` or ``author`` scope for keyword searches —
global full-text search is not supported.  The engine parses subreddit
references from the query string automatically (``r/python ...``,
``subreddit:python ...``).

Setup (optional — works with no configuration):
    export ARCTIC_SHIFT_URL="https://arctic-shift.photon-reddit.com"

Usage:
    from toolregistry_hub.websearch import RedditSearch

    search = RedditSearch()
    results = search.search("r/python web scraping", max_results=5)

    for result in results:
        print(f"{result.title}")
        print(f"  {result.url}")
        print(f"  {result.content}")

API Documentation: https://arctic-shift.photon-reddit.com/api/docs
"""

import os
import re
from typing import Any, cast

from .._vendor.httpclient import Client, HTTPError, HttpTimeoutError, Response
from .._vendor.structlog import get_logger
from .base import TIMEOUT_DEFAULT, BaseSearch, SearchBackendError
from .search_result import SearchResult

logger = get_logger()

_DEFAULT_BASE_URL = "https://arctic-shift.photon-reddit.com"

_SUBREDDIT_RE = re.compile(r"(?<!\w)/?r/(\w+)|subreddit:(\w+)", re.IGNORECASE)

_SELFTEXT_MAX_LEN = 500

_OPTIONAL_PARAMS = frozenset(
    {
        "after",
        "before",
        "over_18",
        "spoiler",
        "link_flair_text",
        "title",
        "selftext",
        "url",
    }
)


class RedditSearch(BaseSearch):
    """Arctic Shift API client for Reddit post search.

    Works without authentication.  Optionally accepts a custom base URL
    for self-hosted Arctic Shift instances.
    """

    def __init__(self, base_url: str | None = None):
        """Initialize Reddit search client.

        Args:
            base_url: Arctic Shift API base URL.  Falls back to the
                ``ARCTIC_SHIFT_URL`` environment variable, then to
                the public instance.
        """
        self.base_url = (
            base_url or os.getenv("ARCTIC_SHIFT_URL") or _DEFAULT_BASE_URL
        ).rstrip("/")

    def _is_configured(self) -> bool:
        return True

    def _build_headers(self, api_key: str | None = None) -> dict:
        return {
            "Accept": "application/json",
            "User-Agent": "toolregistry-hub/RedditSearch",
        }

    @staticmethod
    def _extract_subreddit(query: str) -> tuple[str, str | None]:
        """Parse a subreddit reference out of the query string.

        Recognises ``r/name``, ``/r/name``, and ``subreddit:name``.

        Returns:
            ``(cleaned_query, subreddit_name)`` — the cleaned query has the
            matched pattern removed.  ``subreddit_name`` is ``None`` when no
            pattern was found.
        """
        match = _SUBREDDIT_RE.search(query)
        if not match:
            return query, None
        subreddit = match.group(1) or match.group(2)
        cleaned = " ".join((query[: match.start()] + query[match.end() :]).split())
        return cleaned, subreddit

    def search(
        self,
        query: str,
        *,
        max_results: int = 5,
        timeout: float = TIMEOUT_DEFAULT,
        **kwargs,
    ) -> list[SearchResult]:
        """Search Reddit posts via Arctic Shift.

        The query string may include a subreddit reference (e.g.
        ``"r/python web scraping"``).  Alternatively, pass
        ``subreddit="python"`` as a keyword argument.

        Args:
            query: Search query, optionally prefixed with ``r/<name>``.
            max_results: Maximum results to return (capped at 100).
            timeout: Request timeout in seconds.
            **kwargs: Extra parameters forwarded to the Arctic Shift API
                (``subreddit``, ``author``, ``after``, ``before``, ``sort``,
                ``over_18``, etc.).

        Returns:
            List of search results representing Reddit posts.
        """
        if not query or not query.strip():
            return []

        max_results = min(max_results, 100)

        cleaned, parsed_sub = self._extract_subreddit(query)
        subreddit = kwargs.pop("subreddit", None) or parsed_sub
        author = kwargs.get("author")

        if not subreddit and not author:
            logger.warning(
                "Reddit search requires a subreddit or author scope — "
                "use 'r/<name> <query>' or pass subreddit=… / author=…"
            )
            return []

        kwargs["subreddit"] = subreddit
        kwargs["limit"] = max_results
        kwargs["timeout"] = timeout

        results = self._search_impl(query=cleaned, **kwargs)
        return results[:max_results]

    def _build_params(self, query: str, **kwargs) -> dict:
        """Build GET query parameters for the Arctic Shift API."""
        params: dict[str, Any] = {}
        if sub := kwargs.get("subreddit"):
            params["subreddit"] = sub
        if author := kwargs.get("author"):
            params["author"] = author
        if query.strip():
            params["query"] = query
        params["limit"] = kwargs.get("limit", 25)
        params["sort"] = kwargs.get("sort", "desc")
        for key in _OPTIONAL_PARAMS:
            if key in kwargs:
                params[key] = kwargs[key]
        return params

    def _search_impl(self, query: str, **kwargs) -> list[SearchResult]:
        """Perform the actual GET request against Arctic Shift."""
        params = self._build_params(query, **kwargs)
        timeout = kwargs.get("timeout", TIMEOUT_DEFAULT)

        try:
            with Client(timeout=timeout) as client:
                response = cast(
                    Response,
                    client.get(
                        f"{self.base_url}/api/posts/search",
                        headers=self._build_headers(),
                        params=params,
                    ),
                )
                response.raise_for_status()
                data = response.json()
                results = self._parse_results(data)
                logger.info(f"Reddit search returned {len(results)} results")
                return results
        except HttpTimeoutError:
            logger.error(f"Arctic Shift API timed out after {timeout}s")
            return []
        except HTTPError as e:
            raise SearchBackendError(
                f"Arctic Shift API HTTP {e.status_code}: {e.body}"
            ) from e
        except SearchBackendError:
            raise
        except Exception as e:
            raise SearchBackendError(f"Arctic Shift API request failed: {e}") from e

    @staticmethod
    def _post_body(post: dict) -> str:
        """Extract and truncate the post body text."""
        title = post.get("title") or "No title"
        selftext = (post.get("selftext") or "").strip()
        if selftext in ("[removed]", "[deleted]", ""):
            return title
        if len(selftext) <= _SELFTEXT_MAX_LEN:
            return selftext
        return selftext[:_SELFTEXT_MAX_LEN] + "…"

    @staticmethod
    def _post_meta(post: dict) -> list[str]:
        """Build metadata fragments for a post."""
        parts: list[str] = []
        if sub := post.get("subreddit"):
            parts.append(f"r/{sub}")
        if author := post.get("author"):
            parts.append(f"u/{author}")
        if (score := post.get("score")) is not None:
            parts.append(f"Score: {score}")
        if (num_comments := post.get("num_comments")) is not None:
            parts.append(f"{num_comments} comments")
        return parts

    def _parse_results(self, raw_results: Any) -> list[SearchResult]:
        """Parse Arctic Shift JSON into SearchResult objects."""
        items = raw_results.get("data") if isinstance(raw_results, dict) else None
        if not items:
            return []

        results: list[SearchResult] = []
        for post in items:
            title = post.get("title") or "No title"
            permalink = post.get("permalink", "")
            url = (
                f"https://www.reddit.com{permalink}"
                if permalink
                else post.get("url", "")
            )
            body = self._post_body(post)
            meta = self._post_meta(post)
            content = f"{body} | {' | '.join(meta)}" if meta else body
            results.append(SearchResult(title=title, url=url, content=content))
        return results


def main():
    """Demo usage of RedditSearch."""
    try:
        search = RedditSearch()
        print("=== Reddit Post Search (Arctic Shift) ===")
        results = search.search("r/python web scraping", max_results=5)
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result.title}")
            print(f"   URL: {result.url}")
            print(f"   {result.content}")
    except Exception as e:
        print(f"Demo failed: {e}")


if __name__ == "__main__":
    main()
