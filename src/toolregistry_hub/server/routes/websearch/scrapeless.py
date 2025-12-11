"""Scrapeless search API route."""

from dataclasses import asdict

from fastapi import APIRouter
from loguru import logger

from ....websearch import websearch_scrapeless
from .models import WebSearchRequest, WebSearchResponse, WebSearchResultItem

# Try to initialize search instance, skip if configuration is missing
router = APIRouter(prefix="/web", tags=["websearch"])
scrapeless_search = None

try:
    scrapeless_search = websearch_scrapeless.ScrapelessSearch()
    logger.info("Scrapeless search initialized successfully")
except Exception as e:
    logger.warning(f"Scrapeless search not available: {e}")
    # Don't create the router if initialization fails
    router = None

if scrapeless_search and router:

    @router.post(
        "/search_scrapeless",
        summary="Search Google using Scrapeless DeepSERP API",
        description=(scrapeless_search.search.__doc__ or "")
        + "\n Note: when used, properly cited results' URLs at the end of the generated content, unless instructed otherwise."
        + "\nIncrease the `max_results` in case of deep research."
        + "\nUses Google search via Scrapeless DeepSERP API with structured results.",
        operation_id="search_scrapeless",
        response_model=WebSearchResponse,
    )
    def search_scrapeless(data: WebSearchRequest) -> WebSearchResponse:
        """Search Google using Scrapeless DeepSERP API.

        Args:
            data: Request containing search query and parameters

        Returns:
            Response containing list of search results from Scrapeless

        Raises:
            HTTPException: If Scrapeless Search is not configured
        """
        timeout = data.timeout if data.timeout is not None else 10.0
        assert (
            scrapeless_search is not None
        )  # This should never be None due to the if check above

        # Extract language and country parameters if provided
        language = (
            data.model_extra.get("language", "en")
            if hasattr(data, "model_extra") and data.model_extra
            else "en"
        )
        country = (
            data.model_extra.get("country", "us")
            if hasattr(data, "model_extra") and data.model_extra
            else "us"
        )

        results = scrapeless_search.search(
            data.query,
            max_results=data.max_results,
            timeout=timeout,
            language=language,
            country=country,
        )
        search_items = [WebSearchResultItem(**asdict(result)) for result in results]
        return WebSearchResponse(results=search_items)
