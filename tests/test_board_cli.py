"""Tests for the standalone ``toolregistry-hub admin`` command."""

from __future__ import annotations

import threading
from pathlib import Path

import pytest

from toolregistry_hub.server import admin_cli, cli

pytest.importorskip("toolregistry.admin.extensions")


class _Info:
    url = "http://127.0.0.1:8081/"


class _Registry:
    def __init__(self):
        self.kwargs = None
        self.admin_calls = []
        self.logging = False

    def enable_logging(self):
        self.logging = True

    def enable_admin(self, **kwargs):
        self.admin_calls.append(kwargs)
        return _Info()

    def disable_admin(self):
        self.admin_calls.append("disabled")


@pytest.fixture()
def fake_registry(monkeypatch):
    registry = _Registry()
    monkeypatch.setattr(admin_cli, "build_registry", lambda **kwargs: registry)
    return registry


class TestCommandRegistration:
    def test_admin_is_a_local_command(self):
        assert "admin" in cli.COMMANDS
        assert "admin" in cli.LOCAL_COMMANDS

    def test_translation_passes_admin_through(self):
        # ``admin`` never reaches the server CLI; if the launcher ever routed
        # it through ``_translate`` it must at least stay untranslated.
        assert cli._translate("admin", ["--port", "9000"]) == [
            "admin",
            "--port",
            "9000",
        ]

    def test_main_dispatches_to_run_admin(self, monkeypatch):
        calls = {}

        def fake_run(argv=None, **kwargs):
            calls["argv"] = argv
            return 0

        monkeypatch.setattr(admin_cli, "run_admin", fake_run)
        monkeypatch.setattr(
            cli, "_print_hub_banner", lambda: calls.__setitem__("banner", True)
        )
        assert cli.main(["admin", "--port", "9000", "--no-banner"]) == 0
        assert calls["argv"] == ["--port", "9000"]
        assert "banner" not in calls


class TestTokenRules:
    def test_inline_token_wins(self, fake_registry):
        stop = threading.Event()
        stop.set()
        assert admin_cli.run_admin(["--token", "abc"], stop_event=stop) == 0
        assert fake_registry.admin_calls[0]["auth_token"] == "abc"

    def test_both_flags_are_refused(self, tmp_path: Path):
        token_file = tmp_path / "token"
        token_file.write_text("abc\n", encoding="utf-8")
        with pytest.raises(SystemExit) as excinfo:
            admin_cli.run_admin(["--token", "abc", "--token-file", str(token_file)])
        assert excinfo.value.code == 2

    def test_token_file_uses_first_non_empty_line(self, fake_registry, tmp_path: Path):
        token_file = tmp_path / "token"
        token_file.write_text("\n  secret  \nsecond\n", encoding="utf-8")
        stop = threading.Event()
        stop.set()
        admin_cli.run_admin(["--token-file", str(token_file)], stop_event=stop)
        assert fake_registry.admin_calls[0]["auth_token"] == "secret"

    def test_empty_token_file_is_refused(self, tmp_path: Path):
        token_file = tmp_path / "token"
        token_file.write_text("\n\n", encoding="utf-8")
        with pytest.raises(SystemExit) as excinfo:
            admin_cli.run_admin(["--token-file", str(token_file)])
        assert excinfo.value.code == 2

    def test_non_loopback_requires_a_token(self):
        with pytest.raises(SystemExit) as excinfo:
            admin_cli.run_admin(["--host", "0.0.0.0"])
        assert excinfo.value.code == 2


class TestWiring:
    def test_registry_and_extension_are_configured(self, fake_registry, tmp_path: Path):
        stop = threading.Event()
        stop.set()
        db = tmp_path / "board.sqlite3"
        admin_cli.run_admin(["--db", str(db), "--config", "x.yaml"], stop_event=stop)

        extension = fake_registry.admin_calls[0]["extensions"][0]
        assert extension.name == "board"
        assert extension.store.path == db
        assert fake_registry.logging is True

    def test_admin_is_stopped_on_exit(self, fake_registry):
        stop = threading.Event()
        stop.set()
        admin_cli.run_admin([], stop_event=stop)
        assert fake_registry.admin_calls[-1] == "disabled"
