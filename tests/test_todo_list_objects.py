import pytest
import sys
from toolregistry_hub.todo_list import TodoList, Todo


def test_todolist_write_with_dicts():
    todos = [
        {"id": "1", "content": "Task one", "status": "planned"},
        {"id": "2", "content": "Task two", "status": "done"},
    ]
    out = TodoList.write(todos)

    # basic header and separator
    assert "| id | task | status |" in out
    assert "| --- | --- | --- |" in out

    # rows present
    assert "| 1 | Task one | planned |" in out
    assert "| 2 | Task two | done |" in out

    # there should be exactly header + separator + 2 rows -> 4 lines
    assert out.count("\n") == 3


def test_todolist_write_with_todo_objects():
    # current implementation accepts dicts only; passing Todo instances should raise
    t1 = Todo(id="a", content="Do X", status="planned")
    t2 = Todo(id="b", content="Do Y", status="done")
    with pytest.raises(TypeError):
        TodoList.write([t1, t2])


def test_escape_pipe_in_content():
    todos = [{"id": "p1", "content": "A | B", "status": "planned"}]
    out = TodoList.write(todos)

    # pipe character should be escaped in the rendered table
    assert "\\|" in out
    assert "| p1 | A \\| B | planned |" in out


def test_invalid_element_type_raises_typeerror():
    with pytest.raises(TypeError):
        TodoList.write([1, 2, 3])


def test_invalid_status_raises_typeerror():
    # invalid status value is wrapped and re-raised as TypeError by todolist_write
    with pytest.raises(TypeError):
        TodoList.write(
            [{"id": "x", "content": "c", "status": "not-a-valid-status"}]
        )
