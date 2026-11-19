"""Contract and handler tests for the kanban admin extension."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("toolregistry.admin.extensions")

from toolregistry import ToolRegistry  # noqa: E402
from toolregistry.admin.extensions import (  # noqa: E402
    ADMIN_EXTENSION_API,
    prepare_extensions,
)
from toolregistry.admin.server import AdminServer  # noqa: E402

from toolregistry_hub.board.admin import BoardAdminExtension  # noqa: E402


class _Request:
    """Minimal request stub: the handlers only read body and query params."""

    def __init__(self, payload=None, query=None):
        self.body = b"" if payload is None else json.dumps(payload).encode()
        self.query_params = query or {}

    def json(self):
        return json.loads(self.body)


class _Ctx:
    """Record route registrations without an HTTP server."""

    def __init__(self):
        self.routes = []

    def _add(self, method, path, handler):
        self.routes.append((method, path, handler.__name__))

    def get(self, path, handler=None):
        self._add("GET", path, handler)

    def post(self, path, handler=None):
        self._add("POST", path, handler)

    def put(self, path, handler=None):
        self._add("PUT", path, handler)

    def patch(self, path, handler=None):
        self._add("PATCH", path, handler)

    def delete(self, path, handler=None):
        self._add("DELETE", path, handler)


@pytest.fixture()
def extension(tmp_path: Path) -> BoardAdminExtension:
    return BoardAdminExtension(db=tmp_path / "board.sqlite3")


class TestContract:
    def test_manifest_fields(self, extension: BoardAdminExtension):
        assert extension.name == "board"
        assert extension.requires_api == ADMIN_EXTENSION_API
        assert extension.title == {"en": "Kanban", "zh": "看板"}
        assert extension.nav == {"group": "manage", "order": 30}
        assert extension.entry == "assets/ext/board/main.js"
        assert extension.styles == ("assets/ext/board/board.css",)

    def test_assets_exist_where_the_host_looks(self, extension: BoardAdminExtension):
        assets = Path(extension.assets)
        assert (assets / "main.js").is_file()
        assert (assets / "board.css").is_file()

    def test_host_accepts_the_declaration(self, extension: BoardAdminExtension):
        assert prepare_extensions([extension]) == (extension,)

    def test_route_table(self, extension: BoardAdminExtension):
        ctx = _Ctx()
        extension.register(ctx)
        assert {route[:2] for route in ctx.routes} == {
            ("GET", "/projects"),
            ("POST", "/projects"),
            ("PATCH", "/projects/<key>"),
            ("DELETE", "/projects/<key>"),
            ("GET", "/board"),
            ("GET", "/entries"),
            ("POST", "/entries"),
            ("GET", "/entries/<ref>"),
            ("PATCH", "/entries/<ref>"),
            ("DELETE", "/entries/<ref>"),
            ("GET", "/meta"),
        }


class TestHandlers:
    def test_project_lifecycle(self, extension: BoardAdminExtension):
        created = extension.create_project(_Request({"name": "Kanban", "key": "kan"}))
        assert created[1] == 201
        assert created[0]["project"]["key"] == "KAN"
        renamed = extension.update_project(_Request({"name": "Board"}), "KAN")
        assert renamed["project"]["name"] == "Board"
        removed = extension.remove_project(_Request(), "KAN")
        assert removed["archived"] is True

    def test_duplicate_key_is_a_conflict(self, extension: BoardAdminExtension):
        extension.create_project(_Request({"name": "Kanban", "key": "KAN"}))
        body, status = extension.create_project(_Request({"name": "x", "key": "KAN"}))
        assert status == 409

    def test_entry_lifecycle(self, extension: BoardAdminExtension):
        extension.create_project(_Request({"name": "Kanban", "key": "KAN"}))
        body, status = extension.create_entry(
            _Request(
                {
                    "project": "KAN",
                    "title": "wire",
                    "status": "planned",
                    "priority": "p1",
                    "due": "2026-12-01",
                    "labels": ["ui"],
                    "assignee": "pding",
                    "links": ["https://example.test/1"],
                }
            )
        )
        assert status == 201
        entry = body["entry"]
        assert entry["id"] == "KAN-1"
        assert entry["status"] == "todo"
        assert entry["priority"] == "high"

        updated = extension.update_entry(
            _Request({"content": "x", "status": "pending"}), "KAN-1"
        )
        assert updated["entry"]["status"] == "in_progress"
        assert updated["entry"]["content"] == "x"

        deleted = extension.delete_entry(_Request(), "KAN-1")
        assert deleted["entry"]["deleted"] is True

    def test_board_has_fixed_columns(self, extension: BoardAdminExtension):
        extension.create_project(_Request({"name": "Kanban", "key": "KAN"}))
        extension.create_entry(
            _Request({"project": "KAN", "title": "a", "status": "done"})
        )
        payload = extension.board(_Request(query={"project": ["kan"]}))
        assert [column["status"] for column in payload["columns"]] == [
            "backlog",
            "todo",
            "in_progress",
            "done",
            "cancelled",
        ]
        assert [len(column["entries"]) for column in payload["columns"]] == [
            0,
            0,
            0,
            1,
            0,
        ]

    def test_filters(self, extension: BoardAdminExtension):
        extension.create_project(_Request({"name": "Kanban", "key": "KAN"}))
        extension.create_entry(_Request({"project": "KAN", "title": "a"}))
        extension.create_entry(
            _Request({"project": "KAN", "title": "b", "status": "in_progress"})
        )
        extension.create_entry(
            _Request({"project": "KAN", "title": "c", "status": "done"})
        )
        # ``pending`` normalises to ``in_progress``, not to ``todo``.
        filtered = extension.list_entries(_Request(query={"status": ["pending"]}))[
            "entries"
        ]
        assert [entry["id"] for entry in filtered] == ["KAN-2"]
        todo = extension.list_entries(_Request(query={"status": ["todo"]}))["entries"]
        assert [entry["id"] for entry in todo] == ["KAN-1"]

    def test_unknown_entry_is_404(self, extension: BoardAdminExtension):
        body, status = extension.get_entry(_Request(), "KAN-9")
        assert status == 404
        assert body["error"] == "Not Found"

    def test_invalid_status_is_400(self, extension: BoardAdminExtension):
        extension.create_project(_Request({"name": "Kanban", "key": "KAN"}))
        body, status = extension.create_entry(
            _Request({"project": "KAN", "title": "a", "status": "shipped"})
        )
        assert status == 400

    def test_empty_title_is_400(self, extension: BoardAdminExtension):
        extension.create_project(_Request({"name": "Kanban", "key": "KAN"}))
        body, status = extension.create_entry(
            _Request({"project": "KAN", "title": " "})
        )
        assert status == 400

    def test_timestamps_cannot_be_written(self, extension: BoardAdminExtension):
        extension.create_project(_Request({"name": "Kanban", "key": "KAN"}))
        extension.create_entry(_Request({"project": "KAN", "title": "a"}))
        body, status = extension.update_entry(
            _Request({"created_at": "2000-01-01"}), "KAN-1"
        )
        assert status == 400
        assert "created_at" in body["message"]

    def test_empty_update_is_400(self, extension: BoardAdminExtension):
        extension.create_project(_Request({"name": "Kanban", "key": "KAN"}))
        extension.create_entry(_Request({"project": "KAN", "title": "a"}))
        body, status = extension.update_entry(_Request({}), "KAN-1")
        assert status == 400

    def test_meta_reports_the_database(self, extension: BoardAdminExtension):
        from toolregistry_hub.board.store import SCHEMA_VERSION

        payload = extension.meta(_Request())
        assert payload["schema_version"] == SCHEMA_VERSION
        assert payload["db_path"].endswith("board.sqlite3")

    def test_meta_can_hide_the_path(self, tmp_path: Path):
        hidden = BoardAdminExtension(db=tmp_path / "b.sqlite3", expose_path=False)
        assert "db_path" not in hidden.meta(_Request())


class TestMountedServer:
    @pytest.fixture()
    def server(self, tmp_path: Path):
        extension = BoardAdminExtension(db=tmp_path / "board.sqlite3")
        admin = AdminServer(
            ToolRegistry(), host="127.0.0.1", port=0, extensions=[extension]
        )
        info = admin.start()
        try:
            yield info
        finally:
            admin.stop()

    def test_manifest_lists_the_board(self, server):
        import urllib.request

        with urllib.request.urlopen(
            f"{server.url}/api/extensions", timeout=5
        ) as response:
            payload = json.load(response)
        names = [item["name"] for item in payload["extensions"]]
        assert names == ["board"]

    def test_assets_are_served(self, server):
        import urllib.request

        for path, content_type in (
            ("/assets/ext/board/main.js", "application/javascript"),
            ("/assets/ext/board/board.css", "text/css"),
        ):
            with urllib.request.urlopen(f"{server.url}{path}", timeout=5) as response:
                assert response.status == 200
                assert response.headers["Content-Type"].startswith(content_type)


class TestReviewRegressions:
    """Cases raised in the PR #274 review."""

    def test_patch_with_bad_status_writes_nothing(self, extension: BoardAdminExtension):
        extension.create_project(_Request({"name": "Kanban", "key": "KAN"}))
        extension.create_entry(_Request({"project": "KAN", "title": "one"}))

        body, status = extension.update_entry(
            _Request({"title": "MUTATED", "status": "bogus"}), "KAN-1"
        )

        assert status == 400
        entry = extension.get_entry(_Request(), "KAN-1")["entry"]
        assert entry["title"] == "one"
        assert entry["status"] == "todo"

    def test_post_rejects_unknown_fields(self, extension: BoardAdminExtension):
        extension.create_project(_Request({"name": "Kanban", "key": "KAN"}))
        body, status = extension.create_entry(
            _Request(
                {
                    "project": "KAN",
                    "title": "one",
                    "created_at": "2000-01-01T00:00:00+00:00",
                }
            )
        )
        assert status == 400
        assert "created_at" in body["message"]
        assert extension.list_entries(_Request())["entries"] == []

    def test_null_leaves_a_field_unchanged(self, extension: BoardAdminExtension):
        extension.create_project(_Request({"name": "Kanban", "key": "KAN"}))
        extension.create_entry(
            _Request({"project": "KAN", "title": "one", "content": "keep"})
        )
        extension.update_entry(_Request({"title": None, "content": None}), "KAN-1")
        entry = extension.get_entry(_Request(), "KAN-1")["entry"]
        assert entry["content"] == "keep"
        assert entry["title"] == "one"

    def test_empty_string_clears_a_field(self, extension: BoardAdminExtension):
        extension.create_project(_Request({"name": "Kanban", "key": "KAN"}))
        extension.create_entry(
            _Request({"project": "KAN", "title": "one", "content": "keep"})
        )
        extension.update_entry(_Request({"content": ""}), "KAN-1")
        assert extension.get_entry(_Request(), "KAN-1")["entry"]["content"] == ""

    def test_storage_failure_is_503(self, extension: BoardAdminExtension, monkeypatch):
        import sqlite3

        def boom(*args, **kwargs):
            raise sqlite3.OperationalError("database is locked")

        monkeypatch.setattr(extension.store, "list_projects", boom)
        body, status = extension.list_projects(_Request())
        assert status == 503
        assert body["error"] == "Service Unavailable"
