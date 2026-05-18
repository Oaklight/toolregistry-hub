"""Test central registry functionality."""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from toolregistry.tool import ToolTag

from toolregistry_hub.server import registry as registry_module
from toolregistry_hub.server.registry import (
    _TOOL_METADATA,
    build_registry,
    get_registry,
)


class TestBuildRegistry(unittest.TestCase):
    """Test cases for build_registry function."""

    def test_build_registry_succeeds_without_env_vars(self):
        """Test that build_registry succeeds even without any environment variables."""
        env_vars_to_clear = [
            "BRAVE_API_KEY",
            "TAVILY_API_KEY",
            "SEARXNG_URL",
            "BRIGHTDATA_API_KEY",
            "SCRAPELESS_API_KEY",
        ]
        with patch.dict(os.environ, {}, clear=True):
            for var in env_vars_to_clear:
                os.environ.pop(var, None)

            reg = build_registry()
            self.assertIsNotNone(reg)
            self.assertGreater(len(reg._tools), 0)

    def test_build_registry_has_core_tools(self):
        """Test that build_registry registers core tools."""
        reg = build_registry()
        tool_names = list(reg._tools.keys())

        calc_tools = [t for t in tool_names if t.startswith("calc")]
        self.assertGreater(len(calc_tools), 0, "Calculator tools should be registered")

        dt_tools = [t for t in tool_names if t.startswith("datetime")]
        self.assertGreater(len(dt_tools), 0, "DateTime tools should be registered")

    def test_websearch_tools_disabled_without_env(self):
        """Test that websearch tools are auto-disabled when env vars are missing."""
        env_vars_to_clear = [
            "BRAVE_API_KEY",
            "TAVILY_API_KEY",
            "SEARXNG_URL",
            "BRIGHTDATA_API_KEY",
            "SCRAPELESS_API_KEY",
        ]
        with patch.dict(os.environ, {}, clear=True):
            for var in env_vars_to_clear:
                os.environ.pop(var, None)

            reg = build_registry()

            brave_tools = [
                t for t in reg._tools if reg._tools[t].namespace == "web/brave_search"
            ]
            for tool_name in brave_tools:
                self.assertFalse(
                    reg.is_enabled(tool_name),
                    f"Tool {tool_name} should be disabled without BRAVE_API_KEY",
                )

            searxng_tools = [
                t for t in reg._tools if reg._tools[t].namespace == "web/searxng_search"
            ]
            for tool_name in searxng_tools:
                self.assertFalse(
                    reg.is_enabled(tool_name),
                    f"Tool {tool_name} should be disabled without SEARXNG_URL",
                )

    def test_websearch_tools_enabled_with_env(self):
        """Test that websearch tools are enabled when env vars are set."""
        with patch.dict(os.environ, {"BRAVE_API_KEY": "test-key-for-brave"}):
            reg = build_registry()

            brave_tools = [
                t for t in reg._tools if reg._tools[t].namespace == "web/brave_search"
            ]
            self.assertGreater(len(brave_tools), 0)
            for tool_name in brave_tools:
                self.assertTrue(
                    reg.is_enabled(tool_name),
                    f"Tool {tool_name} should be enabled with BRAVE_API_KEY set",
                )

    def test_websearch_tools_enabled_with_tool_kwargs(self):
        """Test that websearch tools are enabled when API keys are passed via tool_kwargs."""
        with patch.dict(os.environ, {}, clear=True):
            for var in [
                "BRAVE_API_KEY",
                "TAVILY_API_KEY",
                "SEARXNG_URL",
                "BRIGHTDATA_API_KEY",
                "SCRAPELESS_API_KEY",
            ]:
                os.environ.pop(var, None)

            reg = build_registry(
                tool_kwargs={"brave_search": {"api_keys": "direct-test-key"}}
            )

            brave_tools = [
                t for t in reg._tools if reg._tools[t].namespace == "web/brave_search"
            ]
            self.assertGreater(len(brave_tools), 0)
            for tool_name in brave_tools:
                self.assertTrue(
                    reg.is_enabled(tool_name),
                    f"Tool {tool_name} should be enabled with tool_kwargs API key",
                )

            tavily_tools = [
                t for t in reg._tools if reg._tools[t].namespace == "web/tavily_search"
            ]
            for tool_name in tavily_tools:
                self.assertFalse(
                    reg.is_enabled(tool_name),
                    f"Tool {tool_name} should be disabled without config",
                )

    def test_tool_kwargs_searxng_url(self):
        """Test that SearXNG can be configured via tool_kwargs with base_url."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("SEARXNG_URL", None)

            reg = build_registry(
                tool_kwargs={"searxng_search": {"base_url": "http://localhost:8080"}}
            )

            searxng_tools = [
                t for t in reg._tools if reg._tools[t].namespace == "web/searxng_search"
            ]
            self.assertGreater(len(searxng_tools), 0)
            for tool_name in searxng_tools:
                self.assertTrue(
                    reg.is_enabled(tool_name),
                    f"Tool {tool_name} should be enabled with tool_kwargs base_url",
                )

    def test_core_tools_always_enabled(self):
        """Test that core tools (without env requirements) are always enabled."""
        reg = build_registry()

        calc_tools = [t for t in reg._tools if reg._tools[t].namespace == "calculator"]
        for tool_name in calc_tools:
            self.assertTrue(
                reg.is_enabled(tool_name),
                f"Core tool {tool_name} should always be enabled",
            )


class TestBuildRegistryWithToolsConfig(unittest.TestCase):
    """Test cases for build_registry with a JSONC/YAML config file."""

    def test_config_driven_tool_list(self):
        """Test that build_registry uses tools from config file (server format)."""
        config_content = """\
tools:
  - type: python
    class: toolregistry_hub.calculator.Calculator
    namespace: calculator
  - type: python
    class: toolregistry_hub.datetime_utils.DateTime
    namespace: datetime
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            reg = build_registry(tools_config_path=config_path)
            namespaces = {
                tool.namespace for tool in reg._tools.values() if tool.namespace
            }
            self.assertIn("calculator", namespaces)
            self.assertIn("datetime", namespaces)
            self.assertNotIn("web/fetch", namespaces)
            self.assertNotIn("web/brave_search", namespaces)
        finally:
            os.unlink(config_path)

    def test_config_without_tools_uses_defaults(self):
        """Test that build_registry uses defaults when tools field is absent."""
        config_content = "mode: denylist\ndisabled: []\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            reg = build_registry(tools_config_path=config_path)
            namespaces = {
                tool.namespace for tool in reg._tools.values() if tool.namespace
            }
            self.assertIn("calculator", namespaces)
            self.assertIn("datetime", namespaces)
            self.assertIn("web/fetch", namespaces)
        finally:
            os.unlink(config_path)

    def test_config_with_invalid_class_skips_tool(self):
        """Test that invalid class paths are skipped gracefully."""
        config_content = """\
tools:
  - type: python
    class: toolregistry_hub.calculator.Calculator
    namespace: calculator
  - type: python
    class: nonexistent.module.FakeClass
    namespace: fake
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            reg = build_registry(tools_config_path=config_path)
            namespaces = {
                tool.namespace for tool in reg._tools.values() if tool.namespace
            }
            self.assertIn("calculator", namespaces)
            self.assertNotIn("fake", namespaces)
        finally:
            os.unlink(config_path)


class TestToolMetadataAndDiscovery(unittest.TestCase):
    """Test cases for tool metadata, discovery, and think-augment features."""

    def test_tool_metadata_tags_applied(self):
        """Test that ToolTag metadata is applied to registered tools."""
        reg = build_registry(enable_discovery=False)

        calc_tools = [t for t in reg._tools.values() if t.namespace == "calculator"]
        for tool in calc_tools:
            self.assertIn(ToolTag.READ_ONLY, tool.metadata.tags)

        bash_tools = [t for t in reg._tools.values() if t.namespace == "bash"]
        for tool in bash_tools:
            self.assertIn(ToolTag.DESTRUCTIVE, tool.metadata.tags)
            self.assertIn(ToolTag.PRIVILEGED, tool.metadata.tags)

        fileops_tools = [t for t in reg._tools.values() if t.namespace == "file_ops"]
        for tool in fileops_tools:
            self.assertIn(ToolTag.FILE_SYSTEM, tool.metadata.tags)
            self.assertIn(ToolTag.DESTRUCTIVE, tool.metadata.tags)

    def test_deferred_tools_marked(self):
        """Test that tools in _TOOL_METADATA with defer=True are deferred."""
        reg = build_registry(enable_discovery=False)

        deferred_namespaces = {
            ns for ns, meta in _TOOL_METADATA.items() if meta.get("defer")
        }
        for tool in reg._tools.values():
            if tool.namespace in deferred_namespaces:
                self.assertTrue(
                    tool.metadata.defer,
                    f"Tool in namespace {tool.namespace} should be deferred",
                )

    def test_core_tools_not_deferred(self):
        """Test that core tools are not deferred."""
        reg = build_registry(enable_discovery=False)

        core_namespaces = {"calculator", "datetime", "think", "file_ops"}
        for tool in reg._tools.values():
            if tool.namespace in core_namespaces:
                self.assertFalse(
                    tool.metadata.defer,
                    f"Core tool in namespace {tool.namespace} should not be deferred",
                )

    def test_discovery_enabled(self):
        """Test that enable_discovery=True registers discover_tools."""
        reg = build_registry(enable_discovery=True)
        self.assertIn("discover_tools", reg._tools)

    def test_discovery_disabled(self):
        """Test that enable_discovery=False does not register discover_tools."""
        reg = build_registry(enable_discovery=False)
        self.assertNotIn("discover_tools", reg._tools)

    def test_think_augment_enabled(self):
        """Test that enable_think=True activates think-augmented calling."""
        reg = build_registry(enable_discovery=False, enable_think=True)
        self.assertTrue(reg._think_augment)

    def test_think_augment_disabled(self):
        """Test that enable_think=False deactivates think-augmented calling."""
        reg = build_registry(enable_discovery=False, enable_think=False)
        self.assertFalse(reg._think_augment)


class TestGetRegistry(unittest.TestCase):
    """Test cases for get_registry singleton function."""

    def setUp(self):
        """Reset the singleton before each test."""
        registry_module._registry = None

    def tearDown(self):
        """Reset the singleton after each test."""
        registry_module._registry = None

    def test_get_registry_returns_registry(self):
        """Test that get_registry returns a ToolRegistry instance."""
        reg = get_registry()
        self.assertIsNotNone(reg)

    def test_get_registry_returns_singleton(self):
        """Test that get_registry returns the same instance on multiple calls."""
        reg1 = get_registry()
        reg2 = get_registry()
        self.assertIs(reg1, reg2)


if __name__ == "__main__":
    unittest.main()
