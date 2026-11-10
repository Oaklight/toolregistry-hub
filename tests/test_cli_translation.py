"""Unit tests for the Hub launcher's argv translation.

The Hub no longer parses or dispatches its own command line: it rewrites the
Hub command into the equivalent ``toolregistry-server`` command, resolves the
tool preset, and removes the Hub-only flags.  These tests cover that rewrite
without starting a server.
"""

from __future__ import annotations

import os

import pytest

from toolregistry_hub.server import cli
from toolregistry_hub.server.registry import default_preset_path

PRESET = str(default_preset_path())


@pytest.fixture(autouse=True)
def _isolated_discovery(monkeypatch, tmp_path):
    """Run each test in an empty directory with no ``TOOLS_CONFIG``."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("TOOLS_CONFIG", raising=False)
    monkeypatch.delenv(cli.COMMAND_ENV, raising=False)


class TestTranslate:
    def test_openapi_uses_the_gateway(self):
        assert cli._translate("openapi", ["--port", "9000"]) == [
            "gateway",
            "--openapi",
            "--port",
            "9000",
        ]

    @pytest.mark.parametrize("transport", ["streamable-http", "http"])
    def test_http_mcp_transports_use_the_gateway(self, transport):
        assert cli._translate("mcp", ["--transport", transport, "--port", "9"]) == [
            "gateway",
            "--mcp",
            "--port",
            "9",
        ]

    def test_sse_uses_the_gateway(self):
        assert cli._translate("mcp", ["--transport=sse"]) == ["gateway", "--sse"]

    def test_stdio_is_the_direct_mcp_server(self):
        assert cli._translate("mcp", ["--transport", "stdio"]) == [
            "mcp",
            "--transport",
            "stdio",
        ]

    def test_no_transport_defaults_to_stdio(self):
        assert cli._translate("mcp", []) == ["mcp", "--transport", "stdio"]

    def test_stdio_strips_backend(self):
        assert cli._translate("mcp", ["--backend", "httpserver"]) == [
            "mcp",
            "--transport",
            "stdio",
        ]
        assert cli._translate("mcp", ["--backend=httpserver", "--port", "9"]) == [
            "mcp",
            "--transport",
            "stdio",
            "--port",
            "9",
        ]

    def test_backend_survives_on_the_gateway(self):
        assert cli._translate("openapi", ["--backend", "httpserver"]) == [
            "gateway",
            "--openapi",
            "--backend",
            "httpserver",
        ]

    @pytest.mark.parametrize("command", ["gateway", "local-hub", "hub-shim", "keys"])
    def test_other_commands_pass_through(self, command):
        assert cli._translate(command, ["--flag", "value"]) == [
            command,
            "--flag",
            "value",
        ]

    def test_unknown_transport_is_passed_through(self):
        assert cli._translate("mcp", ["--transport", "carrier-pigeon"]) == [
            "mcp",
            "--transport",
            "carrier-pigeon",
        ]


class TestConfigInjection:
    def test_packaged_preset_is_injected(self):
        assert cli._inject_config(["gateway", "--openapi"])[-2:] == [
            "--config",
            PRESET,
        ]

    def test_explicit_config_is_kept(self):
        argv = ["gateway", "--config", "mine.yaml"]
        assert cli._inject_config(argv) == argv

    def test_equals_form_is_kept(self):
        argv = ["gateway", "--config=mine.yaml"]
        assert cli._inject_config(argv) == argv

    def test_tools_config_env_wins(self, monkeypatch, tmp_path):
        path = tmp_path / "from-env.yaml"
        path.write_text("tools: []\n")
        monkeypatch.setenv("TOOLS_CONFIG", str(path))

        assert cli._inject_config(["gateway"])[-1] == str(path)

    def test_working_directory_config_is_discovered(self, tmp_path):
        path = tmp_path / "tools.yaml"
        path.write_text("tools: []\n")

        # Discovery returns the cwd-relative candidate, not an absolute path.
        assert cli._inject_config(["gateway"])[-1] == "tools.yaml"

    def test_keys_gets_no_config(self):
        assert cli._inject_config(["keys", "list"]) == ["keys", "list"]

    def test_local_hub_gets_config(self):
        assert cli._inject_config(["local-hub", "run"])[-2] == "--config"


class TestHubFlags:
    def test_all_flags_are_stripped_and_collected(self):
        options = cli.HubOptions()
        kept = cli._strip_hub_flags(
            [
                "--admin-port",
                "8081",
                "--no-tool-discovery",
                "--no-think-augment",
                "openapi",
                "--port",
                "9",
            ],
            options,
        )

        assert kept == ["openapi", "--port", "9"]
        assert options.admin_port == 8081
        assert options.enable_discovery is False
        assert options.enable_think is False

    def test_equals_form_and_defaults(self):
        options = cli.HubOptions()
        kept = cli._strip_hub_flags(
            ["mcp", "--admin-port=8082", "--tool-discovery", "--think-augment"],
            options,
        )

        assert kept == ["mcp"]
        assert options.admin_port == 8082
        assert options.enable_discovery is True
        assert options.enable_think is True

    def test_no_banner_is_recorded_and_stripped(self):
        options = cli.HubOptions()
        assert cli._strip_hub_flags(["--no-banner", "openapi"], options) == ["openapi"]
        assert options.no_banner is True

    def test_missing_admin_port_value_exits(self):
        with pytest.raises(SystemExit) as exc:
            cli._strip_hub_flags(["--admin-port"], cli.HubOptions())
        assert exc.value.code == 2

    def test_bad_admin_port_value_exits(self):
        with pytest.raises(SystemExit) as exc:
            cli._strip_hub_flags(["--admin-port", "eighty"], cli.HubOptions())
        assert exc.value.code == 2


class TestMain:
    @staticmethod
    def _fake_cli(monkeypatch):
        calls: dict = {}

        class FakeCLI:
            def __init__(self, app=None):
                calls["app"] = app

            def main(self, args=None):
                calls["args"] = list(args)
                return 0

        monkeypatch.setattr(cli, "CLI", FakeCLI)
        monkeypatch.setattr(
            cli, "_print_hub_banner", lambda: calls.__setitem__("banner", True)
        )
        return calls

    def test_openapi_is_forwarded_as_the_gateway(self, monkeypatch):
        calls = self._fake_cli(monkeypatch)

        cli.main(["openapi", "--port", "9000"])

        assert calls["args"][0] == "--no-banner"
        assert calls["args"][1:3] == ["gateway", "--openapi"]
        assert calls["args"][-2:] == ["--config", PRESET]
        assert calls["banner"] is True
        assert os.environ[cli.COMMAND_ENV] == cli.COMMAND_ENV_VALUE

    def test_hub_flags_reach_the_app(self, monkeypatch):
        calls = self._fake_cli(monkeypatch)

        cli.main(
            [
                "--admin-port",
                "8081",
                "--no-think-augment",
                "--no-tool-discovery",
                "mcp",
            ]
        )

        app = calls["app"]
        assert app.admin_port == 8081
        assert app.enable_think is False
        assert app.enable_discovery is False
        assert calls["args"][1:] == [
            "mcp",
            "--transport",
            "stdio",
            "--config",
            PRESET,
        ]

    def test_no_banner_suppresses_the_hub_banner(self, monkeypatch):
        calls = self._fake_cli(monkeypatch)

        cli.main(["--no-banner", "openapi"])

        assert "banner" not in calls
        assert calls["args"][0] == "--no-banner"

    def test_help_does_not_print_the_banner(self, monkeypatch):
        calls = self._fake_cli(monkeypatch)

        cli.main(["openapi", "--help"])

        assert "banner" not in calls
        assert calls["args"][1:4] == ["gateway", "--openapi", "--help"]

    def test_version_prints_and_does_not_start_the_server(self, monkeypatch, capsys):
        monkeypatch.setattr(
            cli, "_get_version_string", lambda: "toolregistry-hub 9.9.9"
        )
        started: list[bool] = []

        class FakeCLI:
            def __init__(self, app=None):
                started.append(True)

        monkeypatch.setattr(cli, "CLI", FakeCLI)

        assert cli.main(["--version"]) is None
        assert "toolregistry-hub 9.9.9" in capsys.readouterr().out
        assert started == []

    def test_top_level_help_lists_commands_and_hub_flags(self, capsys):
        cli.main(["--help"])

        out = capsys.readouterr().out
        for token in (
            "openapi",
            "mcp",
            "gateway",
            "local-hub",
            "hub-shim",
            "keys",
            "--admin-port",
            "--no-banner",
        ):
            assert token in out

    def test_no_arguments_prints_help(self, capsys):
        cli.main([])

        assert "usage: toolregistry-hub" in capsys.readouterr().out

    def test_help_before_the_command_prints_hub_help(self, monkeypatch, capsys):
        calls = self._fake_cli(monkeypatch)

        cli.main(["--help", "openapi"])

        assert "usage: toolregistry-hub" in capsys.readouterr().out
        assert "args" not in calls
