"""Think tool API routes."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ...think_tool import ThinkTool
from ..auth import get_security_dependencies

# ============================================================
# Request models
# ============================================================


class ThinkRequest(BaseModel):
    """Request model for think tool."""

    thought: str = Field(
        description="Thought to process", examples=["How to solve this problem?"]
    )


# ============================================================
# Response models
# ============================================================


class ThinkResponse(BaseModel):
    """Response model for think tool."""

    thought: str = Field(..., description="The processed thought")


# ============================================================
# API routes
# ============================================================

# Create router with prefix and tags
router = APIRouter(tags=["think"])

# Get security dependencies
security_deps = get_security_dependencies()


@router.post(
    "/think",
    summary="Think about something",
    description=ThinkTool.think.__doc__,
    dependencies=security_deps,
    operation_id="think",
    response_model=ThinkResponse,
)
def think(data: ThinkRequest) -> ThinkResponse:
    """Think about something.

    Args:
        data: Request containing the thought to process

    Returns:
        Response containing the think tool result
    """
    result = ThinkTool.think(data.thought)
    return ThinkResponse(thought=result["thought"])
