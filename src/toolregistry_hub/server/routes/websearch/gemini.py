"""Gemini Google Search API route."""

from dataclasses import asdict

from fastapi import APIRouter
from loguru import logger

from ....websearch import websearch_gemini
from .models import WebSearchRequest, WebSearchResponse, WebSearchResultItem

# Try to initialize search instance, skip if configuration is missing
router = APIRouter(prefix="/web", tags=["websearch"])
gemini_search = None

try:
    gemini_search = websearch_gemini.GeminiSearch()
    logger.info("Gemini search initialized successfully")
except Exception as e:
    logger.warning(f"Gemini search not available: {e}")
    # Don't create the router if initialization fails
    router = None

if gemini_search and router:

    @router.post(
        "/search_gemini",
        summary="Search using Gemini's Google Search grounding",
        description=(gemini_search.search.__doc__ or "")
        + "\n\nNote: Gemini returns a synthesized answer with citations rather than raw search results. "
        + "When used, properly cite results' URLs at the end of the generated content, unless instructed otherwise. "
        + "This uses Google's free Gemini API with built-in Google Search grounding capability.",
        operation_id="search_gemini",
        response_model=WebSearchResponse,
    )
    def search_gemini(data: WebSearchRequest) -> WebSearchResponse:
        """Search using Gemini's Google Search grounding.

        Args:
            data: Request containing search query and parameters

        Returns:
            Response containing synthesized answer with source citations from Gemini

        Raises:
            HTTPException: If Gemini Search is not configured
        """
        timeout = data.timeout if data.timeout is not None else 10.0
        assert (
            gemini_search is not None
        )  # This should never be None due to the if check above
        results = gemini_search.search(
            data.query,
            max_results=data.max_results,
            timeout=timeout,
        )
        search_items = [WebSearchResultItem(**asdict(result)) for result in results]
        return WebSearchResponse(results=search_items)
