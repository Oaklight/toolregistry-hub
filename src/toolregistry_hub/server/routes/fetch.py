"""Web fetch API routes."""

from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ...fetch import TIMEOUT_DEFAULT, Fetch

# ============================================================
# Request models
# ============================================================


class FetchWebpageRequest(BaseModel):
    """Request model for webpage fetching."""

    url: str = Field(
        description="URL of webpage to extract", examples=["https://example.com"]
    )
    timeout: Optional[float] = Field(TIMEOUT_DEFAULT, description="Timeout in seconds")


# ============================================================
# Response models
# ============================================================


class FetchWebpageResponse(BaseModel):
    """Response model for webpage fetching."""

    content: str = Field(..., description="Extracted content from the webpage")


# ============================================================
# API routes
# ============================================================

# Create router with prefix and tags
router = APIRouter(prefix="/web", tags=["web"])


@router.post(
    "/fetch_webpage",
    summary="Extract content from a webpage",
    description=Fetch.fetch_content.__doc__,
    operation_id="fetch_webpage",
    response_model=FetchWebpageResponse,
)
def fetch_webpage(data: FetchWebpageRequest) -> FetchWebpageResponse:
    """Extract content from a webpage.

    Args:
        data: Request containing URL and optional timeout

    Returns:
        Response containing extracted content from the webpage
    """
    timeout = data.timeout if data.timeout is not None else TIMEOUT_DEFAULT
    content = Fetch.fetch_content(data.url, timeout=timeout)
    return FetchWebpageResponse(content=content)
