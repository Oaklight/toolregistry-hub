"""Launcher tests for the server-owned source manager and gateway.

Server 0.9.0 is the floor, so the runtime source manager and the gateway are
always present.  These tests run in the default matrix and against server
master; the Hub keeps no watcher and no source diff of its own.
"""

from __future__ import annotations

import importlib.util
import json
import time
from collections.abc import Callable
from typing import Any

import pytest
from toolregistry_server.source_manager import (  # noqa: E402
    ConfigWatcher as ServerConfigWatcher,
)
from toolregistry_server.source_manager import SourceManager  # noqa: E402

from toolregistry_hub.server.app import HubApp  # noqa: E402

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


def _wait_for(predicate: Callable[[], bool], timeout: float = 20.0) -> None:
    """Poll *predicate* until it is true, or fail the test."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.1)
    pytest.fail("condition was not met before the timeout")


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

        # Each method's ``@tool_metadata`` declaration reaches the tool the
        # manager registered; the core applies it in ``Tool.from_function``.
        assert registry.get_tool("calculator-evaluate").metadata.defer is True
        assert registry.get_tool("datetime-now").metadata.title
        schema = registry.get_tool("datetime-convert_timezone").metadata.extra.get(
            "output_schema"
        )
        assert schema and schema["type"] == "object"

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


class TestAdminPort:
    def test_admin_port_serves_a_panel(self, config_path) -> None:
        """--admin-port reaches ``enable_admin`` and serves a real panel."""
        import http.client

        app = HubApp()
        payload: dict[str, Any] = {}
        registry = app.prepare_registry(
            tools_config_path=str(config_path),
            enable_discovery=False,
            admin_port=0,  # ephemeral: no fixed port to collide on CI
            host="127.0.0.1",
        )
        try:
            info = registry.get_admin_info()
            assert info is not None
            # 0 selects an ephemeral port; the panel reports the bound one.
            assert info.port != 0
            assert info.host == "127.0.0.1"

            connection = http.client.HTTPConnection("127.0.0.1", info.port, timeout=10)
            try:
                connection.request("GET", "/api/tools")
                response = connection.getresponse()
                assert response.status == 200
                payload = json.loads(response.read().decode("utf-8"))
            finally:
                connection.close()
        finally:
            registry.disable_admin()

        names = {tool["name"] for tool in payload["tools"]}
        assert {"calculator-evaluate", "datetime-now"} <= names


class TestServerWatcher:
    def test_the_server_watcher_runs(self, config_path) -> None:
        app = HubApp()
        app.create_gateway(
            tools_config_path=str(config_path),
            enable_discovery=False,
            config_reload=True,
        )
        try:
            watcher = app.config_watcher
            assert isinstance(watcher, ServerConfigWatcher)
            assert watcher.manager is app.source_manager
        finally:
            app.stop_config_watcher()

    def test_a_config_edit_reaches_the_live_registry(self, config_path) -> None:
        """--config-reload is the server watcher: an edit must reach the
        registry the gateway serves, with no restart."""
        app = HubApp()
        app.create_gateway(
            tools_config_path=str(config_path),
            enable_discovery=False,
            config_reload=True,
        )
        try:
            registry = app.source_manager.registry
            assert registry.get_tool("calculator-evaluate") is not None
            assert registry.get_tool("think-think") is None

            config_path.write_text(
                json.dumps(
                    {
                        "tools": TOOLS
                        + [
                            {
                                "class": "toolregistry_hub.think_tool.ThinkTool",
                                "namespace": "think",
                            }
                        ]
                    }
                )
            )

            _wait_for(lambda: registry.get_tool("think-think") is not None)
            assert registry.is_enabled("think-think")
        finally:
            app.stop_config_watcher()

    def test_the_hub_ships_no_watcher_or_diff(self) -> None:
        """--config-reload delegates to the server; the Hub keeps no copy."""
        assert importlib.util.find_spec("toolregistry_hub.server.hot_reload") is None


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


class TestServerConfigKey:
    """The server dispatch names the config ``config_path``."""

    def test_prepare_registry_accepts_config_path(self, config_path) -> None:
        app = HubApp(enable_discovery=False)
        registry = app.prepare_registry(config_path=str(config_path))

        assert registry.get_tool("calculator-evaluate") is not None
        assert app.source_manager.config_path == str(config_path)

    def test_tools_config_path_wins_over_config_path(
        self, config_path, tmp_path
    ) -> None:
        other = tmp_path / "other.jsonc"
        other.write_text(json.dumps({"tools": []}))

        app = HubApp(enable_discovery=False)
        registry = app.prepare_registry(
            config_path=str(other), tools_config_path=str(config_path)
        )

        assert registry.get_tool("calculator-evaluate") is not None

    def test_constructor_flags_apply_when_kwargs_omit_them(self, config_path) -> None:
        app = HubApp(enable_discovery=False, enable_think=False)
        registry = app.prepare_registry(config_path=str(config_path))

        assert registry.get_tool("calculator-evaluate") is not None
        assert registry._think_augment is False
        assert "discover_tools" not in registry.list_tools(include_disabled=True)

    def test_constructor_admin_port_starts_the_panel(self, config_path) -> None:
        app = HubApp(enable_discovery=False, admin_port=0)
        registry = app.prepare_registry(config_path=str(config_path), host="127.0.0.1")
        try:
            info = registry.get_admin_info()
            assert info is not None
            assert info.port != 0
        finally:
            registry.disable_admin()

    def test_the_injected_preset_stays_memory_only(self) -> None:
        from toolregistry_hub.server.registry import default_preset_path

        app = HubApp(enable_discovery=False)
        registry = app.prepare_registry(config_path=str(default_preset_path()))

        assert registry.get_tool("calculator-evaluate") is not None
        # The launcher injects the packaged preset as --config; it must not
        # become a writable user config inside the installed package.
        assert app.source_manager.config_path is None
