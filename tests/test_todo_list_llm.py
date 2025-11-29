"""Integration tests for TodoListTool using a fake LLM callable."""

from typing import List
import sys

sys.path.insert(0, r"D:\code\agent\toolregistry-hub\src")  # noqa
from toolregistry_hub.todo_list import TodoListTool


def _fake_llm_basic(prompt: str) -> str:
    """Return a valid markdown table regardless of prompt."""
    return (
        "| id | task | status |\n"
        "|---:|---|---|\n"
        "| 1 | Write unit tests | planned |\n"
        "| 2 | Implement parser | done |\n"
        "| 3 | Refactor code | planned |\n"
    )


def test_todo_list_happy_path():
    TodoListTool.llm = _fake_llm_basic
    TodoListTool.max_try_times = 3
    out = TodoListTool.todo_list("Create a todo list for the task")
    # normalized rendering: header + three rows
    assert out.startswith("| id | task | status |\n")
    assert "Write unit tests" in out
    assert "Implement parser" in out


def test_todo_list_retry_path():
    calls: List[str] = []

    def fake_llm(prompt: str) -> str:
        calls.append(prompt)
        if len(calls) == 1:
            return (
                "| id | task | status |\n"
                "|---:|---|---|\n"
                "| 1 | Step A | running |\n"
                "| 2 | Step B | planned |\n"
            )
        else:
            return (
                "| id | task | status |\n"
                "|---:|---|---|\n"
                "| 1 | Step A | planned |\n"
                "| 2 | Step B | done |\n"
            )

    TodoListTool.llm = fake_llm
    TodoListTool.max_try_times = 3
    out = TodoListTool.todo_list("Do steps A and B")
    # ensure fake llm was called at least twice (first failed, second corrected)
    assert len(calls) >= 2
    assert "PARSE ERROR" not in out
    assert "Step A" in out and "Step B" in out


def test_todo_list_persistent_failure():
    # LLM keeps returning invalid status -> final output should be a PARSE ERROR row

    def always_bad(prompt: str) -> str:
        return (
            "| id | task | status |\n"
            "|---:|---|---|\n"
            "| 1 | Do something | in-progress |\n"
        )

    TodoListTool.llm = always_bad
    TodoListTool.max_try_times = 2
    out = TodoListTool.todo_list("A task that fails parsing repeatedly")
    assert "PARSE ERROR" in out
    assert "cancelled" in out
