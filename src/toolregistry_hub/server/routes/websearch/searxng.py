"""SearXNG search API route."""

from dataclasses import asdict

from fastapi import APIRouter
from loguru import logger

from ....websearch import websearch_searxng
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

    @router.post(
        "/search_searxng",
        summary="Search SearXNG for a query",
        description=(searxng_search.search.__doc__ or "")
        + "\n Note: when used, properly cited results' URLs at the end of the generated content, unless instructed otherwise."
        + "\nIncrease the `max_results` in case of deep research.",
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
        timeout = data.timeout if data.timeout is not None else 10.0
        assert (
            searxng_search is not None
        )  # This should never be None due to the if check above
        results = searxng_search.search(
            data.query,
            max_results=data.max_results,
            timeout=timeout,
        )
        search_items = [WebSearchResultItem(**asdict(result)) for result in results]
        return WebSearchResponse(results=search_items)
