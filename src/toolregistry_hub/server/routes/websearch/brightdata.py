"""Bright Data search API route."""

from dataclasses import asdict
from typing import Optional

from fastapi import APIRouter
from loguru import logger
from pydantic import BaseModel, Field

from ....websearch import websearch_brightdata
from .models import WebSearchResponse, WebSearchResultItem

# Try to initialize search instance, skip if configuration is missing
router = APIRouter(prefix="/web", tags=["websearch"])
brightdata_search = None

try:
    brightdata_search = websearch_brightdata.BrightDataSearch()
    logger.info("Bright Data search initialized successfully")
except Exception as e:
    logger.warning(f"Bright Data search not available: {e}")
    # Don't create the router if initialization fails
    router = None


class BrightDataSearchRequest(BaseModel):
    """Request model for Bright Data web search."""

    query: str = Field(
        description="Search query string", examples=["weather in Beijing"]
    )
    max_results: int = Field(5, description="Number of results to return", ge=1, le=20)
    timeout: Optional[float] = Field(10.0, description="Timeout in seconds")
    cursor: Optional[str] = Field(
        None, description="Pagination cursor (page number, 0-based)"
    )


if brightdata_search and router:

    @router.post(
        "/search_brightdata",
        summary="Search Google using Bright Data SERP API",
        description=(
            (brightdata_search.search.__doc__ or "")
            + "\n\nPerform a web search using Bright Data Google Search API."
            + "\n\nUses Bright Data's SERP API to bypass anti-bot protection and return structured Google search results."
            + "\n\n**Note**: when used, properly cite results' URLs at the end of the generated content, unless instructed otherwise."
            + "\nIncrease the `max_results` in case of deep research."
        ),
        operation_id="search_brightdata",
        response_model=WebSearchResponse,
    )
    def search_brightdata(data: BrightDataSearchRequest) -> WebSearchResponse:
        """Search Google using Bright Data SERP API.

        Args:
            data: Request containing search query and parameters

        Returns:
            Response containing list of search results from Google via Bright Data

        Raises:
            HTTPException: If Bright Data Search is not configured
        """
        timeout = data.timeout if data.timeout is not None else 10.0
        assert (
            brightdata_search is not None
        )  # This should never be None due to the if check above
        results = brightdata_search.search(
            data.query,
            max_results=data.max_results,
            timeout=timeout,
            cursor=data.cursor,
        )
        search_items = [WebSearchResultItem(**asdict(result)) for result in results]
        return WebSearchResponse(results=search_items)
