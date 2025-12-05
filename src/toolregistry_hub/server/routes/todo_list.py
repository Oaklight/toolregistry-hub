"""TodoList API routes."""

from typing import List, Literal, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ...todo_list import TodoList

# ============================================================
# Request models
# ============================================================


class TodoListUpdateRequest(BaseModel):
    """Request model for todo list update operation.

    Status Constraints:
    - planned: Task is scheduled but not yet started
    - pending: Task is currently being worked on (in progress)
    - done: Task has been completed successfully
    - cancelled: Task has been cancelled or abandoned
    """

    todos: List[str] = Field(
        description="List of todo entries in simple string format: '[id] content (status)'",
        examples=[
            [
                "[write-docs] Update API documentation (done)",
                "[old-feature] Remove deprecated feature (cancelled)",
                "[setup-env] Configure development environment (planned)",
                "[fix-bug] Resolve critical login issue (pending)",
            ]
        ],
    )
    format: Optional[Literal["markdown", "simple", "ascii"]] = Field(
        default="simple",
        description="Output format - 'simple' (no output), 'markdown', or 'ascii'",
    )


# ============================================================
# Response models
# ============================================================


class TodoListUpdateResponse(BaseModel):
    """Response model for todo list update operation.

    Returns formatted todo list based on the requested format:
    - simple: Returns None (no output)
    - markdown: Returns markdown table format
    - ascii: Returns ASCII table format
    """

    formatted_output: Optional[str] = Field(
        None, description="Formatted todo list output (None for 'simple' format)"
    )


# ============================================================
# API routes
# ============================================================

# Create router with prefix and tags
router = APIRouter(prefix="/todolist", tags=["todolist"])


@router.post(
    "/update",
    summary="Update todo list with optional formatting",
    description=TodoList.update.__doc__,
    operation_id="todolist-update",
    response_model=TodoListUpdateResponse,
)
def todolist_update(data: TodoListUpdateRequest) -> TodoListUpdateResponse:
    """Update or create todo list for tracking purposes with optional formatting output.

    Args:
        data: Request containing list of todo entries in simple string format
              and optional format specification

    Returns:
        Response containing formatted todo list output (None for 'simple' format)

    Raises:
        HTTPException: If input format is invalid, todo format is malformed, or status is invalid

    Valid status values:
    - planned: Task is scheduled but not yet started
    - pending: Task is currently being worked on (in progress)
    - done: Task has been completed successfully
    - cancelled: Task has been cancelled or abandoned
    """
    try:
        formatted_output = TodoList.update(data.todos, data.format)
        return TodoListUpdateResponse(formatted_output=formatted_output)
    except TypeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid input format: {str(e)}",
        ) from e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid todo format: {str(e)}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        ) from e
