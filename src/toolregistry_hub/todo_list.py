from typing import Dict, List, Literal

from pydantic import BaseModel, ValidationError


class Todo(BaseModel):
    id: str  # short description of the todo item
    content: str  # detailed description of the todo item
    status: Literal["planned", "pending", "done", "cancelled"]


class TodoList:
    """Utility for rendering todo lists as Markdown tables.

    Public API:
      - todo_list_from_objects(todos: List[Todo]) -> str

    The class intentionally exposes a single static helper that accepts a
    list of Todo Pydantic objects and returns a Markdown table (string).
    Internal helpers are static and minimal so external callers only need
    the one method requested.
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
    def todolist_write(todos: List[Dict[str, str]]) -> str:
        # google style docstring
        """
        Create markdown-styled table from list of todo entries.

        Args:
            todos: List[Dict[str, str]]
            A `todo` entry is defined as a Python Dict of following fields
            {
                id: str  # short description of the todo item, such as create-xxx-file
                content: str  # detailed description of the todo item
                status: Literal["planned", "pending", "done", "cancelled"]
            }

        Return:
            markdown-styled table of todo entries
        """
        rows = []
        for t in todos:
            if isinstance(t, dict):
                try:
                    # pydantic v2 推荐用 model_validate
                    todo = Todo.model_validate(t)
                except ValidationError as e:
                    raise TypeError(
                        "The elements in the input list must be dictionaries containing the keys: `id`, `content`, and `status`. The status must be one of: `planned`, `pending`, `done`, `cancelled`."
                    ) from e
            else:
                raise TypeError(
                    "The elements in the input list must be dictionaries containing the keys: `id`, `content`, and `status`. The status must be one of: `planned`, `pending`, `done`, `cancelled`."
                )
            rows.append(
                {
                    "id": todo.id,
                    "task": todo.content,
                    "status": todo.status,
                }
            )

        return TodoList._render_table(rows)
