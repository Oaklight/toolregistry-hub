"""SearXNG search API route."""

from dataclasses import asdict

from fastapi import APIRouter
from loguru import logger

from ....websearch import websearch_searxng
from ...auth import get_security_dependencies
from .models import WebSearchRequest, WebSearchResponse, WebSearchResultItem

# Try to initialize search instance, skip if configuration is missing
router = APIRouter(prefix="/web", tags=["websearch"])
searxng_search = None

try:
    searxng_search = websearch_searxng.SearXNGSearch()
    logger.info("SearXNG search initialized successfully")
except Exception as e:
    logger.warning(f"SearXNG search not available: {e}")
    # Don't create the router if initialization fails
    router = None

if searxng_search and router:
    # Get security dependencies
    security_deps = get_security_dependencies()

    @router.post(
        "/search_searxng",
        summary="Search SearXNG for a query",
        description=searxng_search.search.__doc__
        + "\n Note: when used, properly cited results' URLs at the end of the generated content, unless instructed otherwise."
        + "\nIncrease the `max_results` in case of deep research.",
        dependencies=security_deps,
        operation_id="search_searxng",
        response_model=WebSearchResponse,
    )
    def search_searxng(data: WebSearchRequest) -> WebSearchResponse:
        """Search SearXNG for a query.

        Args:
            data: Request containing search query and parameters

        Returns:
            Response containing list of search results from SearXNG

        Raises:
            HTTPException: If SearXNG is not configured
        """
        results = searxng_search.search(
            data.query,
            max_results=data.max_results,
            timeout=data.timeout,
        )
        search_items = [WebSearchResultItem(**asdict(result)) for result in results]
        return WebSearchResponse(results=search_items)
