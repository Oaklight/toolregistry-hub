import re
from typing import Dict, List, Literal, Union

from pydantic import BaseModel, ValidationError


class Todo(BaseModel):
    id: str  # short description of the todo item
    content: str  # detailed description of the todo item
    status: Literal["planned", "pending", "done", "cancelled"]


class TodoList:
    """Utility for rendering todo lists as Markdown tables.

    Supports two input formats:
    1. Simple string format: "[id] content (status)"
    2. Dictionary format: {"id": "...", "content": "...", "status": "..."}

    Always outputs markdown table format.
    """

    @staticmethod
    def _escape_cell(text: str) -> str:
        """Escape pipe characters in table cells."""
        if text is None:
            return ""
        return text.replace("|", "\\|")

    @staticmethod
    def _render_table(rows: List[dict]) -> str:
        """Render rows into a normalized Markdown table string.

        Expected row keys: 'id', 'task', 'status'.
        """
        headers = ["id", "task", "status"]
        lines = []
        # header
        lines.append("| " + " | ".join(headers) + " |")
        # separator
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        for r in rows:
            id_cell = TodoList._escape_cell(str(r.get("id", "")))
            task_cell = TodoList._escape_cell(str(r.get("task", "")))
            status_cell = TodoList._escape_cell(str(r.get("status", "")))
            lines.append(f"| {id_cell} | {task_cell} | {status_cell} |")
        return "\n".join(lines)

    @staticmethod
    def _parse_simple_format(todo_str: str) -> Dict[str, str]:
        """Parse simple format string into todo dict.

        Expected format: "[id] content (status)"
        Example: "[create-test] write a simple test case for todo list tool (planned)"

        Args:
            todo_str: String in simple format

        Returns:
            Dict with id, content, status keys

        Raises:
            ValueError: If string format is invalid
        """
        # Pattern to match [id] content (status)
        pattern = r"^\[([^\]]+)\]\s+(.+?)\s+\(([^)]+)\)$"
        match = re.match(pattern, todo_str.strip())

        if not match:
            raise ValueError(
                f"Invalid todo format: '{todo_str}'. "
                "Expected format: '[id] content (status)'"
            )

        id_part, content_part, status_part = match.groups()

        # Validate status
        valid_statuses = ["planned", "pending", "done", "cancelled"]
        if status_part not in valid_statuses:
            raise ValueError(
                f"Invalid status '{status_part}'. "
                f"Must be one of: {', '.join(valid_statuses)}"
            )

        return {"id": id_part, "content": content_part, "status": status_part}

    @staticmethod
    def write(todos: Union[List[str], List[Dict[str, str]]]) -> str:
        """
        Create markdown-styled table from list of todo entries.

        Args:
            todos: List of todo entries in one of two formats:
                1. Simple string format: "[id] content (status)"
                   Example: "[create-test] write a simple test case (planned)"
                2. Dictionary format: {"id": "...", "content": "...", "status": "..."}

        Returns:
            Markdown-styled table of todo entries

        Raises:
            TypeError: If input format is invalid
            ValueError: If simple string format is malformed
        """
        if not isinstance(todos, list):
            raise TypeError("Input must be a list")

        if not todos:
            return TodoList._render_table([])

        rows = []
        for i, todo_item in enumerate(todos):
            try:
                if isinstance(todo_item, str):
                    # Parse simple format
                    todo_dict = TodoList._parse_simple_format(todo_item)
                elif isinstance(todo_item, dict):
                    # Use dictionary format directly
                    todo_dict = todo_item
                else:
                    raise TypeError(
                        f"Todo item at index {i} must be either a string or dictionary, "
                        f"got {type(todo_item)}"
                    )

                # Validate using Pydantic model
                todo = Todo.model_validate(todo_dict)

                rows.append(
                    {
                        "id": todo.id,
                        "task": todo.content,
                        "status": todo.status,
                    }
                )

            except ValidationError as e:
                raise TypeError(f"Invalid todo item at index {i}: {e}") from e
            except ValueError as e:
                raise ValueError(f"Invalid todo format at index {i}: {e}") from e

        return TodoList._render_table(rows)
