"""Launcher tests for the server-owned source manager and gateway.

The runtime source manager and the gateway are on server master ahead of
0.9.0, so these tests skip on the released server floor.  The
``test-server-master`` CI job runs them; the default matrix runs the
released-floor path in ``test_config_hot_reload.py``.
"""

from __future__ import annotations

import argparse
import json
from typing import Any

import pytest

pytest.importorskip("toolregistry_server.source_manager")
pytest.importorskip("toolregistry_server.gateway")

from toolregistry_server.source_manager import (  # noqa: E402
    ConfigWatcher as ServerConfigWatcher,
)
from toolregistry_server.source_manager import SourceManager  # noqa: E402

from toolregistry_hub.server.app import HubApp  # noqa: E402
from toolregistry_hub.server.cli import HubCLI  # noqa: E402
from toolregistry_hub.server.hot_reload import (
    ConfigWatcher as HubConfigWatcher,  # noqa: E402
)

TOOLS = [
    {
        "class": "toolregistry_hub.calculator.Calculator",
        "namespace": "calculator",
    },
    {
        "class": "toolregistry_hub.datetime_utils.DateTime",
        "namespace": "datetime",
    },
]


@pytest.fixture()
def config_path(tmp_path):
    path = tmp_path / "tools.jsonc"
    path.write_text(json.dumps({"tools": TOOLS}))
    return path


class TestSourceManagerOwnsRegistration:
    def test_prepare_registry_uses_the_server_manager(self, config_path) -> None:
        app = HubApp()
        registry = app.prepare_registry(
            tools_config_path=str(config_path),
            enable_discovery=False,
        )

        assert isinstance(app.source_manager, SourceManager)
        assert app.source_manager.config_path == str(config_path)
        records = app.source_manager.to_dicts()
        assert len(records) == 2
        names = {name for record in records for name in record["names"]}
        assert "calculator-evaluate" in names
        assert "datetime-now" in names

        # The Hub's declarations and output schemas still reach the tools the
        # manager registered.
        assert registry.get_tool("calculator-evaluate").metadata.defer is True
        assert registry.get_tool("datetime-now").metadata.title

    def test_mutations_go_through_the_manager(self, config_path) -> None:
        from toolregistry.config import PythonSource

        app = HubApp()
        app.prepare_registry(tools_config_path=str(config_path), enable_discovery=False)
        manager = app.source_manager

        result = manager.add(
            PythonSource(
                class_path="toolregistry_hub.think_tool.ThinkTool",
                namespace="think",
            )
        )
        assert result.persisted is True
        assert manager.registry.get_tool("think-think") is not None

        source_id = result.entry.to_dict()["id"]
        manager.remove(source_id)
        assert manager.registry.get_tool("think-think") is None


class TestServerWatcher:
    def test_the_server_watcher_runs_and_hub_watcher_does_not(
        self, config_path
    ) -> None:
        app = HubApp()
        app.create_gateway(
            tools_config_path=str(config_path),
            enable_discovery=False,
            config_reload=True,
        )
        try:
            watcher = app.config_watcher
            assert isinstance(watcher, ServerConfigWatcher)
            assert not isinstance(watcher, HubConfigWatcher)
            assert watcher.manager is app.source_manager
        finally:
            app.stop_config_watcher()


class TestProfile:
    def test_profile_filters_startup_tools(self, tmp_path) -> None:
        """The manager does not filter startup sources; the launcher must."""
        from toolregistry_server import PROFILE_DISABLE_REASON

        path = tmp_path / "tools.jsonc"
        path.write_text(
            json.dumps(
                {
                    "tools": [
                        {
                            "class": "toolregistry_hub.file_ops.FileOps",
                            "namespace": "file_ops",
                        },
                        {
                            "class": "toolregistry_hub.calculator.Calculator",
                            "namespace": "calculator",
                        },
                    ]
                }
            )
        )
        app = HubApp()
        registry = app.prepare_registry(
            tools_config_path=str(path),
            enable_discovery=False,
            profile="remote",
        )

        assert registry.get_disable_reason("file_ops-read") == PROFILE_DISABLE_REASON
        assert registry.is_enabled("calculator-evaluate")
        # Later diffs are filtered by the manager itself.
        assert app.source_manager.profile == "remote"


class TestDispatch:
    def _cli(self, monkeypatch: pytest.MonkeyPatch) -> tuple[HubCLI, dict]:
        cli = HubCLI()
        calls: dict[str, Any] = {}

        def record(name):
            def capture(**kwargs: Any) -> None:
                calls.setdefault("name", name)
                calls.update(kwargs)

            return capture

        monkeypatch.setattr(cli.app, "serve_gateway", record("gateway"))
        monkeypatch.setattr(cli.app, "serve_openapi", record("openapi"))
        monkeypatch.setattr(cli.app, "serve_mcp", record("mcp"))
        return cli, calls

    @staticmethod
    def _parsed(command: str, **overrides: Any) -> argparse.Namespace:
        values: dict[str, Any] = {
            "command": command,
            "host": "127.0.0.1",
            "port": 8000,
            "tokens": None,
            "reload": False,
            "backend": "httpserver",
            "config": None,
            "tool_discovery": False,
            "think_augment": False,
            "profile": None,
            "admin_port": None,
            "config_reload": False,
            "config_write": False,
        }
        values.update(overrides)
        return argparse.Namespace(**values)

    def test_parser_builds_with_the_server_flags(self) -> None:
        # The server adds --config-reload/--no-config-write itself; defining
        # them again would make argparse reject the duplicate option.
        HubCLI().create_parser()

    def test_openapi_uses_the_gateway(self, monkeypatch) -> None:
        cli, calls = self._cli(monkeypatch)
        cli.dispatch(self._parsed("openapi"))

        assert calls["name"] == "gateway"
        assert calls["openapi_enabled"] is True
        assert calls["mcp_enabled"] is False
        assert calls["sse_enabled"] is False
        assert calls["backend"] == "httpserver"

    def test_gateway_command_serves_every_frontend(self, monkeypatch) -> None:
        cli, calls = self._cli(monkeypatch)
        cli.dispatch(self._parsed("gateway"))

        assert calls["name"] == "gateway"
        assert calls["openapi_enabled"] is None
        assert calls["mcp_enabled"] is None
        assert calls["sse_enabled"] is None

    @pytest.mark.parametrize(
        ("transport", "mcp_enabled", "sse_enabled"),
        [
            ("streamable-http", True, False),
            ("http", True, False),
            ("sse", False, True),
        ],
    )
    def test_http_mcp_transports_use_the_gateway(
        self, monkeypatch, transport, mcp_enabled, sse_enabled
    ) -> None:
        cli, calls = self._cli(monkeypatch)
        cli.dispatch(self._parsed("mcp", transport=transport))

        assert calls["name"] == "gateway"
        assert calls["openapi_enabled"] is False
        assert calls["mcp_enabled"] is mcp_enabled
        assert calls["sse_enabled"] is sse_enabled

    def test_stdio_stays_on_the_mcp_server(self, monkeypatch) -> None:
        cli, calls = self._cli(monkeypatch)
        cli.dispatch(self._parsed("mcp", transport="stdio"))

        assert calls["name"] == "mcp"
        assert calls["transport"] == "stdio"
