"""Bing search API route.

.. deprecated:: 0.3.0
    Bing search is deprecated due to frequent bot detection issues.
    Use alternative search providers instead.
"""

from dataclasses import asdict

from loguru import logger

from ....websearch import websearch_bing
from ..websearch.models import WebSearchRequest, WebSearchResponse, WebSearchResultItem

# DEPRECATED: Bing search is deprecated due to bot detection issues
# Router is set to None to prevent automatic registration
# router = APIRouter(prefix="/web", tags=["websearch"])
router = None
bing_search = None

try:
    bing_search = websearch_bing.BingSearch()
    logger.info("Bing search initialized successfully")
except Exception as e:
    logger.warning(f"Bing search not available: {e}")
    # Don't create the router if initialization fails
    router = None

if bing_search and router:

    @router.post(
        "/search_bing",
        summary="[DEPRECATED] Search Bing for a query",
        description="⚠️ **DEPRECATED**: This endpoint is deprecated due to frequent bot detection issues. "
        + "Please use alternative search providers:\n"
        + "- `/web/search_brave` for general web search\n"
        + "- `/web/search_tavily` for AI-optimized search\n"
        + "- `/web/search_searxng` for privacy-focused search\n"
        + "- `/web/search_brightdata` or `/web/search_scrapeless` for Google results\n\n"
        + (bing_search.search.__doc__ or "")
        + "\n Note: when used, properly cited results' URLs at the end of the generated content, unless instructed otherwise."
        + "\nIncrease the `max_results` in case of deep research.",
        operation_id="search_bing",
        response_model=WebSearchResponse,
        deprecated=True,
    )
    def search_bing(data: WebSearchRequest) -> WebSearchResponse:
        """Search Bing for a query.

        Args:
            data: Request containing search query and parameters

        Returns:
            Response containing list of search results from Bing
        """
        timeout = data.timeout if data.timeout is not None else 10.0
        assert (
            bing_search is not None
        )  # This should never be None due to the if check above
        results = bing_search.search(
            data.query,
            max_results=data.max_results,
            timeout=timeout,
        )
        search_items = [WebSearchResultItem(**asdict(result)) for result in results]
        return WebSearchResponse(results=search_items)
