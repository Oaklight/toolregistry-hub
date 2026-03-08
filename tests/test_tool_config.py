"""Tests for the startup tool configuration module (JSONC)."""

import json
import textwrap
from unittest.mock import MagicMock

import pytest

from toolregistry_hub.server.tool_config import (
    ToolConfig,
    _strip_json_comments,
    apply_tool_config,
    load_tool_config,
)


# ---------------------------------------------------------------------------
# _strip_json_comments
# ---------------------------------------------------------------------------


class TestStripJsonComments:
    """Tests for the JSONC comment stripper."""

    def test_no_comments(self):
        raw = '{"key": "value"}'
        assert _strip_json_comments(raw) == raw

    def test_single_line_comment(self):
        raw = textwrap.dedent("""\
            {
                // this is a comment
                "key": "value"
            }""")
        result = _strip_json_comments(raw)
        data = json.loads(result)
        assert data == {"key": "value"}

    def test_block_comment(self):
        raw = textwrap.dedent("""\
            {
                /* block comment */
                "key": "value"
            }""")
        result = _strip_json_comments(raw)
        data = json.loads(result)
        assert data == {"key": "value"}

    def test_multiline_block_comment(self):
        raw = textwrap.dedent("""\
            {
                /*
                 * multi-line
                 * block comment
                 */
                "key": "value"
            }""")
        result = _strip_json_comments(raw)
        data = json.loads(result)
        assert data == {"key": "value"}

    def test_inline_comment(self):
        raw = '{"key": "value"} // trailing comment'
        result = _strip_json_comments(raw)
        data = json.loads(result)
        assert data == {"key": "value"}

    def test_comment_like_in_string_preserved(self):
        raw = '{"url": "http://example.com"}'
        result = _strip_json_comments(raw)
        data = json.loads(result)
        assert data == {"url": "http://example.com"}

    def test_double_slash_in_string_preserved(self):
        raw = '{"msg": "use // for comments"}'
        result = _strip_json_comments(raw)
        data = json.loads(result)
        assert data == {"msg": "use // for comments"}

    def test_escaped_quotes_in_string(self):
        raw = r'{"msg": "say \"hello\""}'
        result = _strip_json_comments(raw)
        data = json.loads(result)
        assert data == {"msg": 'say "hello"'}

    def test_mixed_comments(self):
        raw = textwrap.dedent("""\
            {
                // line comment
                "a": 1, /* inline block */
                "b": "// not a comment",
                /* another
                   block */
                "c": true
            }""")
        result = _strip_json_comments(raw)
        data = json.loads(result)
        assert data == {"a": 1, "b": "// not a comment", "c": True}


# ---------------------------------------------------------------------------
# load_tool_config
# ---------------------------------------------------------------------------


class TestLoadToolConfig:
    """Tests for config file loading and parsing."""

    def test_no_config_returns_none(self, tmp_path, monkeypatch):
        """No config file anywhere → returns None."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("TOOLS_CONFIG", raising=False)
        assert load_tool_config() is None

    def test_explicit_path(self, tmp_path):
        """Explicit path loads the file."""
        cfg = tmp_path / "my_config.jsonc"
        cfg.write_text('{"mode": "denylist", "disabled": ["fetch"]}')
        result = load_tool_config(str(cfg))
        assert result is not None
        assert result.mode == "denylist"
        assert result.disabled == ["fetch"]
        assert result.source == str(cfg)

    def test_explicit_path_not_found(self):
        """Explicit path that doesn't exist raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_tool_config("/nonexistent/path/tools.jsonc")

    def test_env_var_discovery(self, tmp_path, monkeypatch):
        """TOOLS_CONFIG env var is used for discovery."""
        cfg = tmp_path / "env_config.jsonc"
        cfg.write_text('{"mode": "allowlist", "enabled": ["calculator"]}')
        monkeypatch.setenv("TOOLS_CONFIG", str(cfg))
        monkeypatch.chdir(tmp_path)
        result = load_tool_config()
        assert result is not None
        assert result.mode == "allowlist"
        assert result.enabled == ["calculator"]

    def test_env_var_nonexistent_warns(self, tmp_path, monkeypatch, caplog):
        """TOOLS_CONFIG pointing to nonexistent file logs warning."""
        monkeypatch.setenv("TOOLS_CONFIG", "/nonexistent/tools.jsonc")
        monkeypatch.chdir(tmp_path)
        result = load_tool_config()
        assert result is None

    def test_working_dir_discovery(self, tmp_path, monkeypatch):
        """./tools.jsonc in working directory is discovered."""
        cfg = tmp_path / "tools.jsonc"
        cfg.write_text('{"mode": "denylist", "disabled": ["filesystem"]}')
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("TOOLS_CONFIG", raising=False)
        result = load_tool_config()
        assert result is not None
        assert result.disabled == ["filesystem"]

    def test_default_mode_is_denylist(self, tmp_path):
        """Missing 'mode' key defaults to denylist."""
        cfg = tmp_path / "config.jsonc"
        cfg.write_text('{"disabled": ["fetch"]}')
        result = load_tool_config(str(cfg))
        assert result is not None
        assert result.mode == "denylist"

    def test_invalid_mode_raises(self, tmp_path):
        """Invalid mode value raises ValueError."""
        cfg = tmp_path / "config.jsonc"
        cfg.write_text('{"mode": "blocklist"}')
        with pytest.raises(ValueError, match="Invalid mode"):
            load_tool_config(str(cfg))

    def test_invalid_json_raises(self, tmp_path):
        """Malformed JSON raises ValueError."""
        cfg = tmp_path / "config.jsonc"
        cfg.write_text("{invalid json}")
        with pytest.raises(ValueError, match="Invalid JSON"):
            load_tool_config(str(cfg))

    def test_non_object_raises(self, tmp_path):
        """Top-level array raises ValueError."""
        cfg = tmp_path / "config.jsonc"
        cfg.write_text('["not", "an", "object"]')
        with pytest.raises(ValueError, match="must contain a JSON object"):
            load_tool_config(str(cfg))

    def test_disabled_not_list_raises(self, tmp_path):
        """'disabled' as a string raises ValueError."""
        cfg = tmp_path / "config.jsonc"
        cfg.write_text('{"disabled": "fetch"}')
        with pytest.raises(ValueError, match="must be a list"):
            load_tool_config(str(cfg))

    def test_enabled_not_list_raises(self, tmp_path):
        """'enabled' as a number raises ValueError."""
        cfg = tmp_path / "config.jsonc"
        cfg.write_text('{"mode": "allowlist", "enabled": 42}')
        with pytest.raises(ValueError, match="must be a list"):
            load_tool_config(str(cfg))

    def test_jsonc_with_comments(self, tmp_path):
        """Full JSONC file with comments parses correctly."""
        cfg = tmp_path / "config.jsonc"
        cfg.write_text(
            textwrap.dedent("""\
            {
                // Startup config
                "mode": "denylist",
                /* Security: disable filesystem access */
                "disabled": [
                    "filesystem",  // fs ops
                    "file_ops"     // file editing
                ]
            }""")
        )
        result = load_tool_config(str(cfg))
        assert result is not None
        assert result.mode == "denylist"
        assert result.disabled == ["filesystem", "file_ops"]

    def test_discovery_priority_cli_over_env(self, tmp_path, monkeypatch):
        """CLI path takes priority over TOOLS_CONFIG env var."""
        cli_cfg = tmp_path / "cli.jsonc"
        cli_cfg.write_text('{"disabled": ["fetch"]}')
        env_cfg = tmp_path / "env.jsonc"
        env_cfg.write_text('{"disabled": ["filesystem"]}')
        monkeypatch.setenv("TOOLS_CONFIG", str(env_cfg))
        result = load_tool_config(str(cli_cfg))
        assert result is not None
        assert result.disabled == ["fetch"]

    def test_empty_config(self, tmp_path):
        """Empty object is valid — no tools disabled."""
        cfg = tmp_path / "config.jsonc"
        cfg.write_text("{}")
        result = load_tool_config(str(cfg))
        assert result is not None
        assert result.mode == "denylist"
        assert result.disabled == []
        assert result.enabled == []

    def test_tools_field_parsed(self, tmp_path):
        """Config with 'tools' field parses ToolEntry list."""
        cfg = tmp_path / "config.jsonc"
        cfg.write_text(
            textwrap.dedent("""\
            {
                "tools": [
                    {"class": "toolregistry_hub.calculator.Calculator", "namespace": "calculator"},
                    {"class": "toolregistry_hub.fetch.Fetch", "namespace": "fetch"}
                ]
            }""")
        )
        result = load_tool_config(str(cfg))
        assert result is not None
        assert result.tools is not None
        assert len(result.tools) == 2
        assert result.tools[0].class_path == "toolregistry_hub.calculator.Calculator"
        assert result.tools[0].namespace == "calculator"
        assert result.tools[1].class_path == "toolregistry_hub.fetch.Fetch"
        assert result.tools[1].namespace == "fetch"

    def test_tools_field_absent_returns_none(self, tmp_path):
        """Config without 'tools' field has tools=None."""
        cfg = tmp_path / "config.jsonc"
        cfg.write_text('{"mode": "denylist", "disabled": []}')
        result = load_tool_config(str(cfg))
        assert result is not None
        assert result.tools is None

    def test_tools_field_not_list_warns(self, tmp_path):
        """Non-list 'tools' field logs warning and results in tools=None."""
        cfg = tmp_path / "config.jsonc"
        cfg.write_text('{"tools": "not_a_list"}')
        result = load_tool_config(str(cfg))
        assert result is not None
        assert result.tools is None

    def test_tools_field_invalid_entry_skipped(self, tmp_path):
        """Invalid entries in 'tools' list are skipped with warning."""
        cfg = tmp_path / "config.jsonc"
        cfg.write_text(
            textwrap.dedent("""\
            {
                "tools": [
                    {"class": "toolregistry_hub.calculator.Calculator", "namespace": "calculator"},
                    "not_a_dict",
                    {"class": "toolregistry_hub.fetch.Fetch"},
                    {"namespace": "missing_class"},
                    {"class": "", "namespace": "empty_class"},
                    {"class": "toolregistry_hub.fetch.Fetch", "namespace": "fetch"}
                ]
            }""")
        )
        result = load_tool_config(str(cfg))
        assert result is not None
        assert result.tools is not None
        # Only the first and last valid entries should be parsed
        assert len(result.tools) == 2
        assert result.tools[0].namespace == "calculator"
        assert result.tools[1].namespace == "fetch"

    def test_tools_field_empty_list(self, tmp_path):
        """Empty 'tools' list results in empty list (not None)."""
        cfg = tmp_path / "config.jsonc"
        cfg.write_text('{"tools": []}')
        result = load_tool_config(str(cfg))
        assert result is not None
        assert result.tools is not None
        assert result.tools == []


# ---------------------------------------------------------------------------
# apply_tool_config
# ---------------------------------------------------------------------------


def _make_mock_registry(namespaces):
    """Create a mock ToolRegistry with tools in the given namespaces.

    Each namespace gets one tool named ``{namespace}-method``.
    """
    registry = MagicMock()
    tools = {}
    for ns in namespaces:
        tool = MagicMock()
        tool.namespace = ns
        tool.name = f"{ns}-method"
        tools[f"{ns}-method"] = tool
    registry._tools = tools
    registry.is_enabled = MagicMock(return_value=True)
    registry.disable = MagicMock()
    return registry


class TestApplyToolConfig:
    """Tests for applying config to a registry."""

    def test_denylist_disables_listed(self):
        """Denylist mode disables tools in listed namespaces."""
        registry = _make_mock_registry(
            ["calculator", "datetime", "filesystem", "file_ops"]
        )
        config = ToolConfig(
            mode="denylist",
            disabled=["filesystem", "file_ops"],
            source="test",
        )
        apply_tool_config(registry, config)

        # Should have called disable for filesystem-method and file_ops-method
        disabled_names = [call.args[0] for call in registry.disable.call_args_list]
        assert "filesystem-method" in disabled_names
        assert "file_ops-method" in disabled_names
        assert "calculator-method" not in disabled_names
        assert "datetime-method" not in disabled_names

    def test_denylist_unknown_namespace_warns(self, caplog):
        """Denylist with unknown namespace logs a warning."""
        registry = _make_mock_registry(["calculator"])
        config = ToolConfig(
            mode="denylist",
            disabled=["nonexistent"],
            source="test",
        )
        apply_tool_config(registry, config)
        # No disable calls for unknown namespace
        assert registry.disable.call_count == 0

    def test_allowlist_disables_unlisted(self):
        """Allowlist mode disables tools NOT in the allow list."""
        registry = _make_mock_registry(
            ["calculator", "datetime", "filesystem", "fetch"]
        )
        config = ToolConfig(
            mode="allowlist",
            enabled=["calculator", "datetime"],
            source="test",
        )
        apply_tool_config(registry, config)

        disabled_names = [call.args[0] for call in registry.disable.call_args_list]
        assert "filesystem-method" in disabled_names
        assert "fetch-method" in disabled_names
        assert "calculator-method" not in disabled_names
        assert "datetime-method" not in disabled_names

    def test_allowlist_unknown_namespace_warns(self, caplog):
        """Allowlist with unknown namespace logs a warning."""
        registry = _make_mock_registry(["calculator"])
        config = ToolConfig(
            mode="allowlist",
            enabled=["calculator", "nonexistent"],
            source="test",
        )
        apply_tool_config(registry, config)
        # calculator should NOT be disabled
        disabled_names = [call.args[0] for call in registry.disable.call_args_list]
        assert "calculator-method" not in disabled_names

    def test_empty_denylist_disables_nothing(self):
        """Empty denylist leaves all tools enabled."""
        registry = _make_mock_registry(["calculator", "datetime"])
        config = ToolConfig(mode="denylist", disabled=[], source="test")
        apply_tool_config(registry, config)
        assert registry.disable.call_count == 0

    def test_empty_allowlist_disables_everything(self):
        """Empty allowlist disables all tools."""
        registry = _make_mock_registry(["calculator", "datetime"])
        config = ToolConfig(mode="allowlist", enabled=[], source="test")
        apply_tool_config(registry, config)
        assert registry.disable.call_count == 2

    def test_denylist_multiple_tools_per_namespace(self):
        """Denylist disables all tools in a namespace, not just one."""
        registry = MagicMock()
        tools = {}
        for method in ["add", "subtract", "multiply"]:
            tool = MagicMock()
            tool.namespace = "calculator"
            tool.name = f"calculator-{method}"
            tools[f"calculator-{method}"] = tool
        registry._tools = tools
        registry.disable = MagicMock()

        config = ToolConfig(
            mode="denylist",
            disabled=["calculator"],
            source="test",
        )
        apply_tool_config(registry, config)

        disabled_names = [call.args[0] for call in registry.disable.call_args_list]
        assert "calculator-add" in disabled_names
        assert "calculator-subtract" in disabled_names
        assert "calculator-multiply" in disabled_names


# ---------------------------------------------------------------------------
# Integration: build_registry with config
# ---------------------------------------------------------------------------


class TestBuildRegistryWithConfig:
    """Integration tests for build_registry with tools_config_path."""

    def test_build_registry_with_denylist(self, tmp_path):
        """build_registry applies denylist config."""
        cfg = tmp_path / "tools.jsonc"
        cfg.write_text(
            textwrap.dedent("""\
            {
                "mode": "denylist",
                "disabled": ["calculator", "datetime"]
            }""")
        )

        from toolregistry_hub.server.registry import build_registry

        registry = build_registry(tools_config_path=str(cfg))

        # calculator and datetime tools should be disabled
        for tool_name, tool in registry._tools.items():
            if tool.namespace in ("calculator", "datetime"):
                assert not registry.is_enabled(tool_name), (
                    f"{tool_name} should be disabled"
                )

    def test_build_registry_with_allowlist(self, tmp_path):
        """build_registry applies allowlist config."""
        cfg = tmp_path / "tools.jsonc"
        cfg.write_text(
            textwrap.dedent("""\
            {
                "mode": "allowlist",
                "enabled": ["calculator"]
            }""")
        )

        from toolregistry_hub.server.registry import build_registry

        registry = build_registry(tools_config_path=str(cfg))

        # Only calculator tools should be enabled
        for tool_name, tool in registry._tools.items():
            if tool.namespace == "calculator":
                assert registry.is_enabled(tool_name), f"{tool_name} should be enabled"
            elif tool.namespace is not None:
                assert not registry.is_enabled(tool_name), (
                    f"{tool_name} should be disabled (not in allowlist)"
                )

    def test_build_registry_no_config(self, tmp_path, monkeypatch):
        """build_registry without config leaves all configured tools enabled."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("TOOLS_CONFIG", raising=False)

        from toolregistry_hub.server.registry import build_registry

        registry = build_registry()

        # Static-method tools (calculator, datetime, etc.) should be enabled
        for tool_name, tool in registry._tools.items():
            if tool.namespace == "calculator":
                assert registry.is_enabled(tool_name), (
                    f"{tool_name} should be enabled without config"
                )
