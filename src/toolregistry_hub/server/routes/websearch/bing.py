"""Bing search API route."""

from dataclasses import asdict

from fastapi import APIRouter
from loguru import logger

from ....websearch import websearch_bing
from ...auth import get_security_dependencies
from .models import WebSearchRequest, WebSearchResponse, WebSearchResultItem

# Try to initialize search instance, skip if configuration is missing
router = APIRouter(prefix="/web", tags=["websearch"])
bing_search = None

try:
    bing_search = websearch_bing.BingSearch()
    logger.info("Bing search initialized successfully")
except Exception as e:
    logger.warning(f"Bing search not available: {e}")
    # Don't create the router if initialization fails
    router = None

if bing_search and router:
    # Get security dependencies
    security_deps = get_security_dependencies()

    @router.post(
        "/search_bing",
        summary="Search Bing for a query",
        description=bing_search.search.__doc__
        + "\n Note: when used, properly cited results' URLs at the end of the generated content, unless instructed otherwise."
        + "\nIncrease the `max_results` in case of deep research.",
        dependencies=security_deps,
        operation_id="search_bing",
        response_model=WebSearchResponse,
    )
    def search_bing(data: WebSearchRequest) -> WebSearchResponse:
        """Search Bing for a query.

        Args:
            data: Request containing search query and parameters

        Returns:
            Response containing list of search results from Bing
        """
        results = bing_search.search(
            data.query,
            max_results=data.max_results,
            timeout=data.timeout,
        )
        search_items = [WebSearchResultItem(**asdict(result)) for result in results]
        return WebSearchResponse(results=search_items)
