"""Cognitive tools API routes.

Unified design: single think tool handles all cognitive operations
Inspired by "Eliciting Reasoning in Language Models with Cognitive Tools" (arxiv.org/html/2506.12115).
"""

from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ...think_tool import ThinkTool

# ============================================================
# Request models
# ============================================================


class ThinkRequest(BaseModel):
    """Request for think tool (unified cognitive operations).

    Parameter order matters: thinking_mode -> focus_area -> thought_process
    This guides the model to decide HOW to think before WHAT to think about.
    """

    thinking_mode: Optional[str] = Field(
        default=None,
        description="The type of cognitive operation. Choose this FIRST. "
        "Core modes: 'reasoning' (analysis/deduction), 'planning' (task breakdown), 'reflection' (review/verify). "
        "Memory mode: 'recalling' (dump knowledge/facts). "
        "Creative modes: 'brainstorming' (generate ideas), 'exploring' (what-if scenarios). "
        "Or use any custom string.",
        examples=["reasoning", "planning", "reflection", "recalling"],
    )
    focus_area: Optional[str] = Field(
        default=None,
        description="What specific problem or topic you're thinking about. Set this SECOND.",
    )
    thought_process: str = Field(
        description="Your detailed stream of thoughts. Write this LAST. "
        "Can be long and messy. Don't summarize; show your actual thought process.",
    )


# ============================================================
# Response models
# ============================================================


class CognitiveToolResponse(BaseModel):
    """Generic response for cognitive tools."""

    status: str = Field(default="processed", description="Processing status")
    message: str = Field(
        default="Cognitive operation completed", description="Response message"
    )


# ============================================================
# API routes
# ============================================================

router = APIRouter(tags=["cognitive-tools"])


@router.post(
    "/think",
    summary="Record cognitive process - thinking, reasoning, planning, or recalling",
    description=ThinkTool.think.__doc__,
    operation_id="think",
    response_model=CognitiveToolResponse,
)
def think(data: ThinkRequest) -> CognitiveToolResponse:
    """Record your cognitive process - unified tool for all thinking operations.

    Args:
        data: Request containing thinking_mode, focus_area, and thought_process

    Returns:
        Response confirming the operation was processed
    """
    ThinkTool.think(data.thinking_mode, data.focus_area, data.thought_process)
    mode_msg = f" ({data.thinking_mode})" if data.thinking_mode else ""
    return CognitiveToolResponse(message=f"Thinking process{mode_msg} recorded")
