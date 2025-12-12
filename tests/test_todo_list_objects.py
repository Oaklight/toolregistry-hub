import pytest

from toolregistry_hub.todo_list import Todo, TodoList


def test_todolist_update_simple_format():
    """Test update with simple format (no output)."""
    todos = [
        "[task1] Task one (planned)",
        "[task2] Task two (done)",
    ]
    result = TodoList.update(todos, format="simple")

    # Should return None for simple format
    assert result is None


def test_todolist_update_markdown_format():
    """Test update with markdown format."""
    todos = [
        "[task1] Task one (planned)",
        "[task2] Task two (done)",
    ]
    result = TodoList.update(todos, format="markdown")

    # basic header and separator
    assert "| id | task | status |" in (result or '')
    assert "| --- | --- | --- |" in (result or '')

    # rows present
    assert "| task1 | Task one | planned |" in (result or '')
    assert "| task2 | Task two | done |" in (result or '')

    # there should be exactly header + separator + 2 rows -> 4 lines
    assert (result or '').count("\n") == 3


def test_todolist_update_ascii_format():
    """Test update with ASCII format."""
    todos = [
        "[task1] Task one (planned)",
        "[task2] Task two (done)",
    ]
    result = TodoList.update(todos, format="ascii")

    # Should contain ASCII table elements
    assert "+" in (result or '')  # table borders
    assert "ID" in (result or '')
    assert "TASK" in (result or '')
    assert "STATUS" in (result or '')
    assert "task1" in (result or '')
    assert "Task one" in (result or '')


def test_todolist_update_empty_list():
    """Test update with empty list."""
    # Simple format
    result = TodoList.update([], format="simple")
    assert result is None

    # Markdown format
    result = TodoList.update([], format="markdown")
    assert "| id | task | status |" in (result or '')
    assert "| --- | --- | --- |" in (result or '')

    # ASCII format
    result = TodoList.update([], format="ascii")
    assert result == "No todos"


def test_todolist_update_invalid_format():
    """Test update with invalid format."""
    todos = ["[task1] Task one (planned)"]
    with pytest.raises(ValueError, match="Invalid format"):
        TodoList.update(todos, format="invalid")  # type: ignore[reportArgumentType]


def test_todolist_update_invalid_todo_format():
    """Test update with invalid todo string format."""
    todos = ["invalid format"]
    with pytest.raises(ValueError, match="Invalid todo format"):
        TodoList.update(todos)


def test_todolist_update_invalid_status():
    """Test update with invalid status."""
    todos = ["[task1] Task one (invalid_status)"]
    with pytest.raises(ValueError, match="Invalid status"):
        TodoList.update(todos)


def test_todolist_update_non_string_input():
    """Test update with non-string todo items."""
    todos = [123, "[task1] Task one (planned)"]
    with pytest.raises(TypeError, match="must be a string"):
        TodoList.update(todos)


def test_escape_pipe_in_content():
    """Test that pipe characters are escaped in markdown output."""
    todos = ["[p1] A | B (planned)"]
    result = TodoList.update(todos, format="markdown")

    # pipe character should be escaped in the rendered table
    assert "\\|" in (result or '')
    assert "| p1 | A \\| B | planned |" in (result or '')


def test_todo_model_validation():
    """Test Todo model validation."""
    # Valid todo
    todo = Todo(id="test", content="Test task", status="planned")
    assert todo.id == "test"
    assert todo.content == "Test task"
    assert todo.status == "planned"

    # Invalid status
    with pytest.raises(ValueError):
        Todo(id="test", content="Test task", status="invalid")  # type: ignore[reportArgumentType]
