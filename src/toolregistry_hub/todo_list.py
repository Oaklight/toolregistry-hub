import re
from typing import List, Literal, Optional, Union

from pydantic import BaseModel, ValidationError


class Todo(BaseModel):
    """Todo item model with status constraints.

    Status values:
    - planned: Task is scheduled but not yet started
    - pending: Task is currently being worked on (in progress)
    - done: Task has been completed successfully
    - cancelled: Task has been cancelled or abandoned
    """

    id: str  # short description of the todo item
    content: str  # detailed description of the todo item
    status: Literal["planned", "pending", "done", "cancelled"]


class TodoList:
    """Utility for managing todo lists with optional formatting output.

    Only supports simple string format: "[id] content (status)"
    Can optionally output in different formats for display purposes.

    Status Constraints:
    - planned: Task is scheduled but not yet started
    - pending: Task is currently being worked on (in progress)
    - done: Task has been completed successfully
    - cancelled: Task has been cancelled or abandoned

    Example:
        "[setup-env] Configure development environment (planned)"
        "[fix-bug] Resolve login issue (pending)"
        "[write-docs] Update API documentation (done)"
        "[old-feature] Remove deprecated feature (cancelled)"
    """

    @staticmethod
    def _escape_cell(text: str) -> str:
        """Escape pipe characters in table cells."""
        if text is None:
            return ""
        return text.replace("|", "\\|")

    @staticmethod
    def _render_markdown_table(rows: List[dict]) -> str:
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
    def _render_ascii_table(rows: List[dict]) -> str:
        """Render rows into ASCII table format."""
        if not rows:
            return "No todos"

        # Calculate column widths
        id_width = max(len("ID"), max(len(str(r.get("id", ""))) for r in rows))
        task_width = max(len("TASK"), max(len(str(r.get("task", ""))) for r in rows))
        status_width = max(
            len("STATUS"), max(len(str(r.get("status", ""))) for r in rows)
        )

        # Create separator
        separator = f"+{'-' * (id_width + 2)}+{'-' * (task_width + 2)}+{'-' * (status_width + 2)}+"

        lines = []
        lines.append(separator)
        lines.append(
            f"| {'ID':<{id_width}} | {'TASK':<{task_width}} | {'STATUS':<{status_width}} |"
        )
        lines.append(separator)

        for r in rows:
            id_val = str(r.get("id", ""))
            task_val = str(r.get("task", ""))
            status_val = str(r.get("status", ""))
            lines.append(
                f"| {id_val:<{id_width}} | {task_val:<{task_width}} | {status_val:<{status_width}} |"
            )

        lines.append(separator)
        return "\n".join(lines)

    @staticmethod
    def _parse_simple_format(todo_str: str) -> dict:
        """Parse simple format string into todo dict.
        Example: "[create-test] write a simple test case for todo list tool (planned)"

        Args:
            todo_str: String in "[id] content (status)" format

        Returns:
            Dict with id, content, status keys

        Raises:
            ValueError: If string format is invalid or status is not valid

        Valid status values:
        - planned: Task is scheduled but not yet started
        - pending: Task is currently being worked on (in progress)
        - done: Task has been completed successfully
        - cancelled: Task has been cancelled or abandoned
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
    def update(
        todos: List[str],
        format: Optional[Literal["markdown", "simple", "ascii"]] = "simple",
    ) -> Optional[str]:
        """Update or create todo list with optional formatting output.

        Args:
            todos: List of todo entries as "[id] content (status)" strings.
                Example: ["[create-test] write a simple test case (planned)"]
                Order matters - todos will be maintained in the input order.
            format: Output format - 'simple' (no output), 'markdown', or 'ascii'.

        Returns:
            Formatted todo list if format is not 'simple', otherwise None. 'simple' should suffice most cases.

        Raises:
            TypeError: If input format is invalid.
            ValueError: If string format is malformed or status is invalid.
        """
        if not isinstance(todos, list):
            raise TypeError("Input must be a list")

        if not todos:
            if format == "simple":
                return None
            elif format == "markdown":
                return TodoList._render_markdown_table([])
            elif format == "ascii":
                return "No todos"

        rows = []
        for i, todo_item in enumerate(todos):
            try:
                if not isinstance(todo_item, str):
                    raise TypeError(
                        f"Todo item at index {i} must be a string in simple format, "
                        f"got {type(todo_item)}"
                    )

                # Parse simple format
                todo_dict = TodoList._parse_simple_format(todo_item)

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

        # Return formatted output based on format parameter
        if format == "simple":
            return None
        elif format == "markdown":
            return TodoList._render_markdown_table(rows)
        elif format == "ascii":
            return TodoList._render_ascii_table(rows)
        else:
            raise ValueError(
                f"Invalid format '{format}'. Must be one of: 'simple', 'markdown', 'ascii'"
            )
