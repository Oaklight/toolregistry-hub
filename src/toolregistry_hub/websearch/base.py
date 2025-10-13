from abc import ABC, abstractmethod
from typing import Any, List, Optional

from loguru import logger

from ..fetch import Fetch
from .search_result import SearchResult

_UNABLE_TO_FETCH_CONTENT = "Unable to fetch content"
_UNABLE_TO_FETCH_TITLE = "Unable to fetch title"

TIMEOUT_DEFAULT = 10.0


class BaseSearch(ABC):
    @property
    @abstractmethod
    def _headers(self) -> dict:
        """Generate headers necessary for making upstream query"""
        # this method is for generating necessary headers used for upstream api call
        # the content could be
        # - BEARER authentication token
        # - fake user agent from ua-generator
        # - API key rotation
        # - ...

    @abstractmethod
    def search(
        self, query: str, *, max_results: int = 5, timeout: float = 10.0, **kwargs
    ) -> List[SearchResult]:
        """Perform a web search and return results.

        Args:
            query: The search query string
            max_results: Maximum number of results to return (1~20 recommended, 180 at max)
            timeout: Request timeout in seconds
            **kwargs: additional query parameters defined by Brave Search API. Refer to https://api-dashboard.search.brave.com/app/documentation/web-search/query for details

        Returns:
            List of search results with title, url, content and score
        """
        # this method is public facing for LLM tool call. It should be implemented by child class. The core logic of upstream api call is recommended to be implemented in _search method, which is protected and called by this method.
        # When empty query is provided, return empty list
        # Always cap max_results before return, in case _search returns more than max_results
        # The implementation here is for general use purpose and to showcase the design pattern
        # Developer should rewrite this function if they see fit

    @abstractmethod
    def _parse_results(self, raw_results: Any) -> List[SearchResult]:
        """Parse raw search results into standardized format.
        Used inside _search method to parse raw results from upstream API call.

        Args:
            raw_results: Raw results from upstream API call

        Returns:
            List of standardized search results
        """

    @abstractmethod
    def _search_impl(self, query: str, **kwargs) -> List[SearchResult]:
        """Perform the actual search using upstream API for a single query.
        It should be reused in case of pagination or similar situation.

        Args:
            query: The search query string
            **kwargs: Additional parameters specific to the upstream API

        Returns:
            List of SearchResult
        """

    @staticmethod
    def _fetch_webpage_content(
        entry: SearchResult,
        *,
        timeout: float = TIMEOUT_DEFAULT,
        proxy: Optional[str] = None,
    ) -> dict:
        """Retrieve complete webpage content from search result entry.

        Args:
            entry (SearchResult): The search result entry.
            timeout (float, optional): Request timeout in seconds. Defaults to None.
            proxy (str, optional): Proxy to use for the request. Defaults to None.

        Returns:
            Dict[str, str]: A dictionary containing the title, URL, content, and excerpt of the webpage.
        """
        url = entry.get("url")
        if not url:
            raise ValueError("Result missing URL")

        try:
            content = Fetch.fetch_content(
                url,
                timeout=timeout,
                proxy=proxy,
            )
        except Exception as e:
            content = _UNABLE_TO_FETCH_CONTENT
            logger.debug(f"Error retrieving webpage content: {e}")

        return {
            "title": entry.get("title", _UNABLE_TO_FETCH_TITLE),
            "url": url,
            "content": content,
            "excerpt": entry.get("content", _UNABLE_TO_FETCH_CONTENT),
        }
