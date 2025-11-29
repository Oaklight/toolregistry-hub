from typing import List, Literal
import re
from pydantic import BaseModel


class Todo(BaseModel):
    id: str  # short description of the todo item
    content: str  # detailed description of the todo item
    status: Literal["done", "planned", "cancelled"]


class TodoListTool:
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
            id_cell = TodoListTool._escape_cell(str(r.get("id", "")))
            task_cell = TodoListTool._escape_cell(str(r.get("task", "")))
            status_cell = TodoListTool._escape_cell(str(r.get("status", "")))
            lines.append(f"| {id_cell} | {task_cell} | {status_cell} |")
        return "\n".join(lines)

    @staticmethod
    def todo_list_from_objects(todos: List[Todo]) -> str:
        """Convert a list of Todo objects into a Markdown table string.

        This is a minimal, deterministic renderer. It accepts only a list of
        validated Todo Pydantic models (with status in: done, planned,
        cancelled) and returns a Markdown table.
        """
        rows = []
        for t in todos:
            if not isinstance(t, Todo):
                try:
                    t = Todo(**t)
                except Exception as e:
                    raise TypeError(
                        f"Each item must be a Todo or a dict convertible to Todo: {e}"
                    ) from e
            rows.append({"id": t.id, "task": t.content, "status": t.status})

        return TodoListTool._render_table(rows)
