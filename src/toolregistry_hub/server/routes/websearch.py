"""Web search API routes."""

from dataclasses import asdict
from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ...websearch import (
    websearch_bing,
    websearch_brave,
    websearch_searxng,
    websearch_tavily,
)
from ...websearch.base import TIMEOUT_DEFAULT
from ..auth import get_security_dependencies

# ============================================================
# Request models
# ============================================================


class WebSearchRequest(BaseModel):
    """Request model for web search."""

    query: str = Field(
        ..., description="Search query string", example="weather in Beijing"
    )
    max_results: int = Field(5, description="Number of results to return", ge=1, le=20)
    timeout: Optional[float] = Field(TIMEOUT_DEFAULT, description="Timeout in seconds")


# ============================================================
# Response models
# ============================================================


class WebSearchResultItem(BaseModel):
    """Individual search result item."""

    title: str = Field(..., description="The title of the search result")
    url: str = Field(..., description="The URL of the search result")
    content: str = Field(
        ..., description="The description/content from the search engine"
    )
    score: float = Field(..., description="Relevance score of the search result")


class WebSearchResponse(BaseModel):
    """Response model for web search."""

    results: List[WebSearchResultItem] = Field(
        ..., description="List of search results"
    )


# ============================================================
# API routes
# ============================================================

# Initialize web search instances
bing_search = websearch_bing.BingSearch()
brave_search = websearch_brave.BraveSearch()
tavily_search = websearch_tavily.TavilySearch()
searxng_search = websearch_searxng.SearXNGSearch()


# Create router with prefix and tags
router = APIRouter(prefix="/web", tags=["websearch"])

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


@router.post(
    "/search_tavily",
    summary="Search Tavily for a query",
    description=tavily_search.search.__doc__
    + "\n Note: when used, properly cited results' URLs at the end of the generated content, unless instructed otherwise."
    + "\nIncrease the `max_results` in case of deep research.",
    dependencies=security_deps,
    operation_id="search_tavily",
    response_model=WebSearchResponse,
)
def search_tavily(data: WebSearchRequest) -> WebSearchResponse:
    """Search Tavily for a query.

    Args:
        data: Request containing search query and parameters

    Returns:
        Response containing list of search results from Tavily

    Raises:
        HTTPException: If Tavily Search is not configured
    """
    results = tavily_search.search(
        data.query,
        max_results=data.max_results,
        timeout=data.timeout,
    )
    search_items = [WebSearchResultItem(**asdict(result)) for result in results]
    return WebSearchResponse(results=search_items)
