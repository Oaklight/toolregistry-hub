"""Cognitive tools API routes.

Separates knowledge/memory/facts from reasoning/logic, inspired by cognitive psychology
and "Eliciting Reasoning in Language Models with Cognitive Tools" (arxiv.org/html/2506.12115).
"""

from typing import Literal, Optional

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


class ReasonRequest(BaseModel):
    """Request for reason tool (goal-directed logical reasoning)."""

    thought_process: str = Field(
        description="Your detailed stream of thoughts following a goal-directed path. Don't summarize; show the work."
    )
    reasoning_type: Optional[
        Literal["analysis", "hypothesis", "planning", "verification", "correction"]
    ] = Field(default=None, description="The stage of the problem-solving lifecycle")
    focus_area: Optional[str] = Field(
        default=None, description="What specific problem are you trying to solve here?"
    )


class ThinkRequest(BaseModel):
    """Request for think tool (free-form exploratory thinking)."""

    thought: str = Field(
        description="Your exploratory thinking without a predetermined path. For open-ended exploration, gut feelings, or trying out ideas."
    )
    thinking_type: str = Field(
        description="The specific mode of thinking. Recommended: 'brainstorming', 'mental_simulation', 'perspective_taking', 'intuition', or any custom string."
    )
    focus_area: Optional[str] = Field(
        default=None, description="The context or problem you are thinking about"
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
    "/reason",
    summary="Goal-directed logical reasoning",
    description=ThinkTool.reason.__doc__,
    operation_id="reason",
    response_model=CognitiveToolResponse,
)
def reason(data: ReasonRequest) -> CognitiveToolResponse:
    """Perform goal-directed logical reasoning (how you solve problems).

    Args:
        data: Request containing thought process, reasoning type, and focus area

    Returns:
        Response confirming the operation was processed
    """
    ThinkTool.reason(data.thought_process, data.reasoning_type, data.focus_area)
    return CognitiveToolResponse(message="Reasoning completed")


@router.post(
    "/think",
    summary="Open-ended exploratory thinking",
    description=ThinkTool.think.__doc__,
    operation_id="think",
    response_model=CognitiveToolResponse,
)
def think(data: ThinkRequest) -> CognitiveToolResponse:
    """Free-form exploratory thinking without a predetermined path.

    Args:
        data: Request containing thought, thinking type, and focus area

    Returns:
        Response confirming the operation was processed
    """
    ThinkTool.think(data.thought, data.thinking_type, data.focus_area)
    return CognitiveToolResponse(
        message=f"Exploratory thinking '{data.thinking_type}' recorded"
    )
