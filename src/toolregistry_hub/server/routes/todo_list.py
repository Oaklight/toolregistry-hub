"""TodoList API routes."""

from typing import Dict, List, Union

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ...todo_list import TodoList

# ============================================================
# Request models
# ============================================================


class TodoListWriteRequest(BaseModel):
    """Request model for todo list write operation."""

    todos: Union[List[str], List[Dict[str, str]]] = Field(
        description="List of todo entries in simple string format or dictionary format",
        examples=[
            [
                "[fix-bug] resolve critical issue (done)",
                "[implement-feature] add new functionality (pending)",
                "[create-test] write a simple test case for todo list tool (planned)",
            ]
        ],
    )


# ============================================================
# Response models
# ============================================================


class TodoListWriteResponse(BaseModel):
    """Response model for todo list write operation."""

    markdown_table: str = Field(
        ..., description="Markdown-styled table of todo entries"
    )


# ============================================================
# API routes
# ============================================================

# Create router with prefix and tags
router = APIRouter(prefix="/todolist", tags=["todolist"])


@router.post(
    "/write",
    summary="Create markdown table from todo entries",
    description=TodoList.write.__doc__,
    operation_id="todolist-write",
    response_model=TodoListWriteResponse,
)
def todolist_write(data: TodoListWriteRequest) -> TodoListWriteResponse:
    """Create markdown-styled table from list of todo entries.

    Args:
        data: Request containing list of todo entries in one of two formats:
            1. Simple string format: "[id] content (status)"
               Example: "[create-test] write a simple test case (planned)"
            2. Dictionary format: {"id": "...", "content": "...", "status": "..."}

    Returns:
        Response containing markdown-styled table of todo entries

    Raises:
        HTTPException: If input format is invalid or todo format is malformed
    """
    try:
        markdown_table = TodoList.write(data.todos)
        return TodoListWriteResponse(markdown_table=markdown_table)
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
