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

    topic: str = Field(
        description="What to recall information about",
        examples=["Python async patterns", "Bug in auth.py line 45"],
    )
    context: Optional[str] = Field(
        default=None,
        description="Optional observed facts from current situation",
        examples=["Project uses FastAPI, has blocking DB calls"],
    )


class ReasonRequest(BaseModel):
    """Request for reason tool (logical reasoning/analysis)."""

    content: str = Field(
        description="Your reasoning process and conclusions",
        examples=[
            "Auth fails after v2.0. New code has shared cache without locks. Intermittent failures suggest race condition."
        ],
    )
    reasoning_type: Optional[
        Literal["deductive", "inductive", "abductive", "analogical", "causal"]
    ] = Field(
        default=None,
        description="Optional type of reasoning",
        examples=["causal"],
    )


class CognitiveOperationRequest(BaseModel):
    """Request for custom cognitive operation (extensibility)."""

    operation_type: str = Field(
        description="Name of operation",
        examples=[
            "hypothesis_generation",
            "mental_simulation",
            "constraint_satisfaction",
        ],
    )
    content: str = Field(
        description="The cognitive work being performed",
        examples=[
            "H1: DB query issue (high), H2: Memory leak (medium), H3: Network (low)"
        ],
    )
    metadata: Optional[str] = Field(
        default=None,
        description="Optional context about why/how this operation is used",
        examples=["Single-cause debugging failed, trying multiple hypotheses"],
    )


class ThinkRequest(BaseModel):
    """Request for legacy think tool (backward compatibility)."""

    reasoning: str = Field(
        description="Logical reasoning process",
        examples=["Error in auth.py after v2.0, likely from refactor"],
    )
    facts: Optional[str] = Field(
        default=None,
        description="Optional factual information",
        examples=["User uses Python 3.9. Error in auth.py line 45."],
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


class ThinkResponse(BaseModel):
    """Response for legacy think tool."""

    reasoning: str = Field(..., description="The processed reasoning")


# ============================================================
# API routes
# ============================================================

router = APIRouter(tags=["cognitive-tools"])


@router.post(
    "/recall",
    summary="Recall facts and knowledge (memory)",
    description=ThinkTool.recall.__doc__,
    operation_id="recall",
    response_model=CognitiveToolResponse,
)
def recall(data: RecallRequest) -> CognitiveToolResponse:
    """Recall facts, knowledge, and observations (memory, not reasoning).

    Args:
        data: Request containing topic and optional context

    Returns:
        Response confirming the operation was processed
    """
    ThinkTool.recall(data.topic, data.context)
    return CognitiveToolResponse(message="Knowledge recalled")


@router.post(
    "/reason",
    summary="Perform logical reasoning (logic/analysis)",
    description=ThinkTool.reason.__doc__,
    operation_id="reason",
    response_model=CognitiveToolResponse,
)
def reason(data: ReasonRequest) -> CognitiveToolResponse:
    """Perform logical reasoning and analysis.

    Args:
        data: Request containing reasoning content and optional type

    Returns:
        Response confirming the operation was processed
    """
    ThinkTool.reason(data.content, data.reasoning_type)
    return CognitiveToolResponse(message="Reasoning completed")


@router.post(
    "/cognitive-operation",
    summary="Custom cognitive operation (extensibility)",
    description=ThinkTool.cognitive_operation.__doc__,
    operation_id="cognitive_operation",
    response_model=CognitiveToolResponse,
)
def cognitive_operation(data: CognitiveOperationRequest) -> CognitiveToolResponse:
    """Perform custom cognitive operation for novel reasoning patterns.

    Args:
        data: Request containing operation type, content, and optional metadata

    Returns:
        Response confirming the operation was processed
    """
    ThinkTool.cognitive_operation(data.operation_type, data.content, data.metadata)
    return CognitiveToolResponse(message=f"Operation '{data.operation_type}' completed")


@router.post(
    "/think",
    summary="Think (legacy - use recall/reason instead)",
    description=ThinkTool.think.__doc__,
    operation_id="think",
    response_model=ThinkResponse,
    deprecated=True,
)
def think(data: ThinkRequest) -> ThinkResponse:
    """Legacy think method. Use recall() and reason() instead.

    Args:
        data: Request containing reasoning and optional facts

    Returns:
        Response containing the processed reasoning
    """
    ThinkTool.think(data.reasoning, data.facts)
    return ThinkResponse(reasoning=data.reasoning)
