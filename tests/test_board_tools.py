"""Tool-surface tests for the board namespace."""

from __future__ import annotations

from pathlib import Path

import pytest
from toolregistry import ToolTag

from toolregistry_hub.board import BoardTools
from toolregistry_hub.server.registry import build_registry


@pytest.fixture()
def board(tmp_path: Path) -> BoardTools:
    return BoardTools(str(tmp_path / "board.sqlite3"))


class TestReturnShapes:
    def test_create_project_returns_declared_keys(self, board: BoardTools):
        result = board.create_project("Kanban", key="KAN")
        assert set(result) == {"key", "name", "created_at"}

    def test_create_entry_returns_an_entry(self, board: BoardTools):
        board.create_project("Kanban", key="KAN")
        result = board.create_entry("KAN", "one")
        assert result["id"] == "KAN-1"
        assert result["status"] == "todo"

    def test_delete_returns_an_acknowledgement(self, board: BoardTools):
        board.create_project("Kanban", key="KAN")
        board.create_entry("KAN", "one")
        result = board.delete_entry("KAN-1")
        assert result["deleted"] is True
        assert result["deleted_at"]

    def test_listings_are_strings(self, board: BoardTools):
        assert "No projects" in board.list_projects()
        board.create_project("Kanban", key="KAN")
        assert "KAN" in board.list_projects()
        assert "KAN" in board.list_entries()
        assert "KAN-1" not in board.list_entries()

    def test_view_uses_the_only_project(self, board: BoardTools):
        board.create_project("Kanban", key="KAN")
        board.create_entry("KAN", "one", status="in_progress")
        text = board.view()
        assert "## In progress (1)" in text
        assert "**KAN-1** one" in text

    def test_view_requires_a_project_when_several_exist(self, board: BoardTools):
        board.create_project("One", key="ONE")
        board.create_project("Two", key="TWO")
        with pytest.raises(ValueError):
            board.view()

    def test_results_are_never_none(self, board: BoardTools):
        board.create_project("Kanban", key="KAN")
        board.create_entry("KAN", "one")
        calls = [
            board.create_project("Other", key="OTH"),
            board.create_entry("KAN", "two"),
            board.get_entry("KAN-1"),
            board.update_entry("KAN-1", content="x"),
            board.update_status("KAN-1", "done"),
            board.list_projects(),
            board.list_entries(),
            board.view("KAN"),
            board.delete_entry("KAN-2"),
            board.archive_project("KAN"),
        ]
        assert all(value is not None for value in calls)


class TestMetadata:
    def test_every_method_declares_hints(self):
        registry = build_registry(enable_discovery=False, enable_think=False)
        tools = [t for t in registry._tools.values() if t.namespace == "board"]
        assert len(tools) == 10
        for tool in tools:
            meta = tool.metadata
            assert meta.read_only_hint is not None, tool.name
            assert meta.open_world_hint is False, tool.name
            assert meta.defer is True, tool.name

    def test_destructive_methods_are_marked(self):
        registry = build_registry(enable_discovery=False, enable_think=False)
        by_name = {
            t.name: t for t in registry._tools.values() if t.namespace == "board"
        }
        assert by_name["board-delete_entry"].metadata.destructive_hint is True
        assert by_name["board-archive_project"].metadata.destructive_hint is True
        assert by_name["board-list_entries"].metadata.read_only_hint is True

    def test_declarations_are_file_system_scoped(self):
        registry = build_registry(enable_discovery=False, enable_think=False)
        for tool in registry._tools.values():
            if tool.namespace == "board":
                assert ToolTag.FILE_SYSTEM in tool.metadata.tags


class TestLazyConstruction:
    def test_instantiating_the_tool_creates_nothing(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
        monkeypatch.delenv("TOOLREGISTRY_HUB_BOARD_DB", raising=False)
        BoardTools()
        assert not (tmp_path / "state").exists()

    def test_building_the_registry_creates_nothing(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
        monkeypatch.delenv("TOOLREGISTRY_HUB_BOARD_DB", raising=False)
        build_registry(enable_discovery=False, enable_think=False)
        assert not (tmp_path / "state").exists()
