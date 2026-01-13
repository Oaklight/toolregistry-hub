"""Cognitive tools API routes.

Simplified design: recall (memory) + think (reasoning/exploration)
Inspired by "Eliciting Reasoning in Language Models with Cognitive Tools" (arxiv.org/html/2506.12115).
"""

from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ...think_tool import ThinkTool

# ============================================================
# Request models
# ============================================================


class RecallRequest(BaseModel):
    """Request for recall tool (memory/knowledge/facts)."""

    knowledge_content: str = Field(
        description="Dump your raw memory/knowledge about a subject. Can be internal knowledge or information from current context."
    )
    topic_tag: Optional[str] = Field(
        default=None, description="A short label for this memory block"
    )


class ThinkRequest(BaseModel):
    """Request for think tool (unified thinking - both structured reasoning and free exploration)."""

    thought_process: str = Field(
        description="Your detailed stream of thoughts. Can be long and messy. Don't summarize; show your actual thought process."
    )
    thinking_mode: Optional[str] = Field(
        default=None,
        description="The type of thinking you're doing. Common modes: 'analysis', 'hypothesis', 'planning', 'verification', 'correction', 'brainstorming', 'mental_simulation', 'perspective_taking', 'intuition', or any custom string.",
    )
    focus_area: Optional[str] = Field(
        default=None, description="What specific problem or topic you're thinking about"
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
    "/recall",
    summary="Dump raw memory and knowledge",
    description=ThinkTool.recall.__doc__,
    operation_id="recall",
    response_model=CognitiveToolResponse,
)
def recall(data: RecallRequest) -> CognitiveToolResponse:
    """Retrieve and record factual knowledge (what you know).

    Args:
        data: Request containing knowledge content and optional topic tag

    Returns:
        Response confirming the operation was processed
    """
    ThinkTool.recall(data.knowledge_content, data.topic_tag)
    return CognitiveToolResponse(message="Knowledge recalled")


@router.post(
    "/think",
    summary="Record thinking process - structured reasoning and free exploration",
    description=ThinkTool.think.__doc__,
    operation_id="think",
    response_model=CognitiveToolResponse,
)
def think(data: ThinkRequest) -> CognitiveToolResponse:
    """Record your thinking process - both structured reasoning and free exploration.

    Args:
        data: Request containing thought process, thinking mode, and focus area

    Returns:
        Response confirming the operation was processed
    """
    ThinkTool.think(data.thought_process, data.thinking_mode, data.focus_area)
    mode_msg = f" ({data.thinking_mode})" if data.thinking_mode else ""
    return CognitiveToolResponse(message=f"Thinking process{mode_msg} recorded")
