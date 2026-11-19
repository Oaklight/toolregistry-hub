"""Store-level tests for the persistent board."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pytest

from toolregistry_hub.board import (
    ENV_VAR,
    BoardConflict,
    BoardNotFound,
    BoardStore,
    BoardValidation,
    derive_key,
    normalize_priority,
    normalize_status,
    resolve_db_path,
)
from toolregistry_hub.board.store import utc_now


@pytest.fixture()
def store(tmp_path: Path) -> BoardStore:
    return BoardStore(tmp_path / "board.sqlite3")


class TestKeys:
    def test_derive_key_uses_initials(self):
        assert derive_key("Tool Registry Hub") == "TRH"
        assert derive_key("kanban") == "K"

    def test_derive_key_falls_back_for_symbols(self):
        assert derive_key("***") == "PRJ"

    def test_auto_key_collision_gets_a_suffix(self, store: BoardStore):
        first = store.create_project("Kanban")
        second = store.create_project("Kanban")
        assert first["key"] == "K"
        assert second["key"] == "K2"

    def test_explicit_key_is_uppercased(self, store: BoardStore):
        assert store.create_project("Kanban", key="kan")["key"] == "KAN"

    def test_invalid_key_is_rejected(self, store: BoardStore):
        with pytest.raises(BoardValidation):
            store.create_project("Kanban", key="1kan")

    def test_duplicate_key_conflicts(self, store: BoardStore):
        store.create_project("Kanban", key="KAN")
        with pytest.raises(BoardConflict):
            store.create_project("Other", key="KAN")


class TestStatusAndPriority:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("planned", "todo"),
            ("pending", "in_progress"),
            ("in-progress", "in_progress"),
            ("doing", "in_progress"),
            ("active", "in_progress"),
            ("completed", "done"),
            ("closed", "done"),
            ("canceled", "cancelled"),
            ("done", "done"),
        ],
    )
    def test_status_aliases(self, value: str, expected: str):
        assert normalize_status(value) == expected

    def test_unknown_status_is_rejected(self):
        with pytest.raises(BoardValidation):
            normalize_status("shipped")

    @pytest.mark.parametrize(
        ("value", "expected"),
        [("p0", "urgent"), ("p1", "high"), ("p2", "medium"), ("p3", "low")],
    )
    def test_priority_aliases(self, value: str, expected: str):
        assert normalize_priority(value) == expected

    def test_storage_rejects_an_injected_status(self, tmp_path: Path):
        store = BoardStore(tmp_path / "b.sqlite3")
        store.create_project("Kanban", key="KAN")
        store.create_entry("KAN", "task")
        with sqlite3.connect(store.path) as conn, pytest.raises(sqlite3.IntegrityError):
            conn.execute("UPDATE entries SET status = 'shipped'")


class TestEntries:
    def test_sequence_is_never_reused(self, store: BoardStore):
        store.create_project("Kanban", key="KAN")
        first = store.create_entry("KAN", "one")["id"]
        second = store.create_entry("KAN", "two")["id"]
        store.delete_entry(first)
        third = store.create_entry("KAN", "three")["id"]
        assert (first, second, third) == ("KAN-1", "KAN-2", "KAN-3")

    def test_fields_round_trip(self, store: BoardStore):
        store.create_project("Kanban", key="KAN")
        entry = store.create_entry(
            "KAN",
            "wire UI",
            content="first pass",
            status="planned",
            priority="p1",
            due="2026-12-01",
            labels=["ui", "frontend"],
            assignee="pding",
            links=["https://example.test/1"],
        )
        assert entry["status"] == "todo"
        assert entry["priority"] == "high"
        assert entry["due"] == "2026-12-01"
        assert entry["labels"] == ["ui", "frontend"]
        assert entry["links"] == ["https://example.test/1"]
        assert entry["assignee"] == "pding"

    def test_timestamps_are_server_generated(self, store: BoardStore):
        store.create_project("Kanban", key="KAN")
        entry = store.create_entry("KAN", "one")
        assert entry["created_at"].endswith("+00:00")
        assert entry["created_at"] == entry["updated_at"]

    def test_no_public_method_accepts_a_timestamp(self, store: BoardStore):
        import inspect

        for name in ("create_entry", "update_entry", "update_status", "delete_entry"):
            signature = inspect.signature(getattr(store, name))
            forbidden = {"created_at", "updated_at", "closed_at", "deleted_at"}
            assert not forbidden & set(signature.parameters)

    def test_closing_sets_closed_at_and_reopening_clears_it(self, store: BoardStore):
        store.create_project("Kanban", key="KAN")
        store.create_entry("KAN", "one")
        closed = store.update_status("KAN-1", "done")
        assert closed["closed_at"] is not None
        reopened = store.update_status("KAN-1", "todo")
        assert reopened["closed_at"] is None

    def test_update_entry_changes_only_given_fields(self, store: BoardStore):
        store.create_project("Kanban", key="KAN")
        store.create_entry("KAN", "one", content="a", priority="low")
        updated = store.update_entry("KAN-1", content="b", labels=[])
        assert updated["content"] == "b"
        assert updated["priority"] == "low"
        assert updated["labels"] == []
        assert updated["title"] == "one"

    def test_invalid_due_is_rejected(self, store: BoardStore):
        store.create_project("Kanban", key="KAN")
        with pytest.raises(BoardValidation):
            store.create_entry("KAN", "one", due="tomorrow")

    def test_non_http_links_are_rejected(self, store: BoardStore):
        store.create_project("Kanban", key="KAN")
        with pytest.raises(BoardValidation):
            store.create_entry("KAN", "one", links=["file:///etc/passwd"])

    def test_soft_delete_hides_from_listing(self, store: BoardStore):
        store.create_project("Kanban", key="KAN")
        store.create_entry("KAN", "one")
        store.delete_entry("KAN-1")
        assert store.list_entries() == []
        assert [e["id"] for e in store.list_entries(include_deleted=True)] == ["KAN-1"]
        with pytest.raises(BoardNotFound):
            store.delete_entry("KAN-1")

    def test_ref_parsing(self, store: BoardStore):
        store.create_project("Kanban", key="KAN")
        store.create_entry("KAN", "one")
        assert store.get_entry("kan-1")["id"] == "KAN-1"
        for bad in ("KAN", "KAN-", "1", ""):
            with pytest.raises(BoardValidation):
                store.get_entry(bad)


class TestProjects:
    def test_counts_are_per_column(self, store: BoardStore):
        store.create_project("Kanban", key="KAN")
        store.create_entry("KAN", "a", status="todo")
        store.create_entry("KAN", "b", status="in_progress")
        project = store.list_projects()[0]
        assert project["counts"]["todo"] == 1
        assert project["counts"]["in_progress"] == 1
        assert project["counts"]["done"] == 0

    def test_archive_keeps_entries(self, store: BoardStore):
        store.create_project("Kanban", key="KAN")
        store.create_entry("KAN", "a")
        result = store.archive_project("KAN")
        assert result == {"key": "KAN", "archived": True, "deleted_entries": 0}
        assert store.list_projects() == []
        assert len(store.list_projects(include_archived=True)) == 1
        assert len(store.list_entries(project="KAN")) == 1

    def test_force_delete_cascades(self, store: BoardStore):
        store.create_project("Kanban", key="KAN")
        store.create_entry("KAN", "a")
        store.create_entry("KAN", "b")
        result = store.archive_project("KAN", force=True)
        assert result["deleted_entries"] == 2
        assert store.list_projects(include_archived=True) == []

    def test_unknown_project(self, store: BoardStore):
        with pytest.raises(BoardNotFound):
            store.get_project("NOPE")

    def test_lookup_by_name(self, store: BoardStore):
        store.create_project("Kanban Board", key="KAN")
        assert store.get_project("Kanban Board")["key"] == "KAN"


class TestConcurrencyAndPermissions:
    def test_two_stores_see_one_file(self, tmp_path: Path):
        path = tmp_path / "board.sqlite3"
        first = BoardStore(path)
        second = BoardStore(path)
        first.create_project("Kanban", key="KAN")
        first.create_entry("KAN", "one")
        assert [e["id"] for e in second.list_entries()] == ["KAN-1"]

    def test_file_and_directory_permissions(self, tmp_path: Path):
        path = tmp_path / "state" / "board.sqlite3"
        store = BoardStore(path)
        store.create_project("Kanban")
        assert oct(Path(path).stat().st_mode & 0o777) == "0o600"
        assert oct(Path(path).parent.stat().st_mode & 0o777) == "0o700"

    def test_construction_has_no_side_effect(self, tmp_path: Path):
        path = tmp_path / "lazy" / "board.sqlite3"
        BoardStore(path)
        assert not Path(path).exists()
        assert not Path(path).parent.exists()


class TestPathResolution:
    def test_explicit_beats_everything(self, tmp_path: Path, monkeypatch):
        monkeypatch.setenv(ENV_VAR, str(tmp_path / "env.sqlite3"))
        assert resolve_db_path(tmp_path / "x.sqlite3") == tmp_path / "x.sqlite3"

    def test_env_beats_xdg(self, tmp_path: Path, monkeypatch):
        monkeypatch.setenv(ENV_VAR, str(tmp_path / "env.sqlite3"))
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
        assert resolve_db_path() == tmp_path / "env.sqlite3"

    def test_xdg_state_home_is_used(self, tmp_path: Path, monkeypatch):
        monkeypatch.delenv(ENV_VAR, raising=False)
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
        assert resolve_db_path() == tmp_path / "toolregistry-hub" / "board.sqlite3"

    def test_home_fallback(self, tmp_path: Path, monkeypatch):
        monkeypatch.delenv(ENV_VAR, raising=False)
        monkeypatch.delenv("XDG_STATE_HOME", raising=False)
        monkeypatch.setenv("HOME", str(tmp_path))
        expected = tmp_path / ".local" / "state" / "toolregistry-hub" / "board.sqlite3"
        assert resolve_db_path() == expected


def test_utc_now_is_timezone_aware():
    stamp = utc_now()
    assert stamp.endswith("+00:00")
    assert os.path.sep not in stamp


class TestReviewRegressions:
    """Cases raised in the PR #274 review."""

    def test_update_on_deleted_entry_is_refused(self, store: BoardStore):
        store.create_project("Kanban", key="KAN")
        store.create_entry("KAN", "one")
        store.delete_entry("KAN-1")
        with pytest.raises(BoardNotFound):
            store.update_entry("KAN-1", title="changed")
        with pytest.raises(BoardNotFound):
            store.update_status("KAN-1", "done")

    def test_closed_at_moves_only_on_a_transition(self, store: BoardStore):
        store.create_project("Kanban", key="KAN")
        store.create_entry("KAN", "one")
        done = store.update_status("KAN-1", "done")
        stamp = done["closed_at"]
        assert stamp is not None

        # A title edit keeps the original close time.
        edited = store.update_entry("KAN-1", title="renamed")
        assert edited["closed_at"] == stamp

        # Re-saving the same status keeps it too, including through the
        # combined update path the admin panel uses.
        again = store.update_entry("KAN-1", title="again", status="done")
        assert again["closed_at"] == stamp

        # Reopening clears it; closing again stamps a fresh value.
        reopened = store.update_status("KAN-1", "todo")
        assert reopened["closed_at"] is None
        reclosed = store.update_status("KAN-1", "done")
        assert reclosed["closed_at"] is not None

    def test_force_deleted_key_keeps_its_sequence(self, store: BoardStore):
        store.create_project("Sequence", key="SEQ")
        store.create_entry("SEQ", "one")
        store.create_entry("SEQ", "two")
        store.create_entry("SEQ", "three")
        store.archive_project("SEQ", force=True)

        recreated = store.create_project("Sequence again", key="SEQ")
        assert recreated["key"] == "SEQ"
        assert store.create_entry("SEQ", "four")["id"] == "SEQ-4"

    def test_derived_key_collisions_terminate(self, store: BoardStore):
        keys = [store.create_project("Kanban")["key"] for _ in range(5)]
        assert keys == ["K", "K2", "K3", "K4", "K5"]

    def test_archived_project_refuses_writes(self, store: BoardStore):
        store.create_project("Kanban", key="KAN")
        store.create_entry("KAN", "one")
        store.archive_project("KAN")
        with pytest.raises(BoardValidation):
            store.create_entry("KAN", "two")
        with pytest.raises(BoardValidation):
            store.update_status("KAN-1", "done")
        with pytest.raises(BoardValidation):
            store.update_entry("KAN-1", title="changed")
        # Reads and deletion of existing work still work.
        assert [e["id"] for e in store.list_entries(project="KAN")] == ["KAN-1"]
        assert store.delete_entry("KAN-1")["deleted"] is True

    def test_created_and_updated_differ_within_a_second(self, store: BoardStore):
        store.create_project("Kanban", key="KAN")
        created = store.create_entry("KAN", "one")
        updated = store.update_entry("KAN-1", content="x")
        assert updated["updated_at"] != created["created_at"]

    def test_concurrent_creates_allocate_unique_sequences(self, store: BoardStore):
        import threading

        store.create_project("Kanban", key="KAN")
        ids: list[str] = []
        lock = threading.Lock()

        def worker() -> None:
            for _ in range(10):
                entry = store.create_entry("KAN", "task")
                with lock:
                    ids.append(entry["id"])

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert len(ids) == 80
        assert len(set(ids)) == 80
        assert sorted(int(item.split("-")[1]) for item in ids) == list(range(1, 81))

    def test_cold_start_from_several_processes_succeeds(self, tmp_path: Path):
        import threading

        path = tmp_path / "cold" / "board.sqlite3"
        errors: list[BaseException] = []

        def worker() -> None:
            try:
                BoardStore(path).list_projects()
            except BaseException as exc:  # noqa: BLE001 - surfaced by the assert
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert errors == []
