"""Brave search API route."""

from dataclasses import asdict

from fastapi import APIRouter
from loguru import logger

from ....websearch import websearch_brave
from ...auth import get_security_dependencies
from .models import WebSearchRequest, WebSearchResponse, WebSearchResultItem

# Try to initialize search instance, skip if configuration is missing
router = APIRouter(prefix="/web", tags=["websearch"])
brave_search = None

try:
    brave_search = websearch_brave.BraveSearch()
    logger.info("Brave search initialized successfully")
except Exception as e:
    logger.warning(f"Brave search not available: {e}")
    # Don't create the router if initialization fails
    router = None

if brave_search and router:
    # Get security dependencies
    security_deps = get_security_dependencies()

    @router.post(
        "/search_brave",
        summary="Search Brave for a query",
        description=brave_search.search.__doc__
        + "\n Note: when used, properly cited results' URLs at the end of the generated content, unless instructed otherwise."
        + "\nIncrease the `max_results` in case of deep research.",
        dependencies=security_deps,
        operation_id="search_brave",
        response_model=WebSearchResponse,
    )
    def search_brave(data: WebSearchRequest) -> WebSearchResponse:
        """Search Brave for a query.

        Args:
            data: Request containing search query and parameters

        Returns:
            Response containing list of search results from Brave

        Raises:
            HTTPException: If Brave Search is not configured
        """
        results = brave_search.search(
            data.query,
            max_results=data.max_results,
            timeout=data.timeout,
        )
        search_items = [WebSearchResultItem(**asdict(result)) for result in results]
        return WebSearchResponse(results=search_items)
