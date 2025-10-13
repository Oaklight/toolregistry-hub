"""Shared models for websearch API routes."""

from typing import List, Optional

from pydantic import BaseModel, Field

from ....websearch.base import TIMEOUT_DEFAULT


class WebSearchRequest(BaseModel):
    """Request model for web search."""

    query: str = Field(
        description="Search query string", examples=["weather in Beijing"]
    )
    max_results: int = Field(5, description="Number of results to return", ge=1, le=20)
    timeout: Optional[float] = Field(TIMEOUT_DEFAULT, description="Timeout in seconds")


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
