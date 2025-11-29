import pytest
from toolregistry_hub.todo_list import Todo, TodoListTool


def test_todo_from_instance():
    t = Todo(id="1", content="Do X", status="planned")
    expected = (
        "| id | task | status |\n" "| --- | --- | --- |\n" "| 1 | Do X | planned |"
    )
    assert TodoListTool.todo_list_from_objects([t]) == expected


def test_todo_from_dict():
    d = {"id": "2", "content": "Write tests", "status": "done"}
    expected = "| id | task | status |\n| --- | --- | --- |\n| 2 | Write tests | done |"
    assert TodoListTool.todo_list_from_objects([d]) == expected


def test_todo_invalid_raises():
    with pytest.raises(TypeError):
        TodoListTool.todo_list_from_objects(
            [{"id": 3, "content": "Bad", "status": "unknown"}]
        )
