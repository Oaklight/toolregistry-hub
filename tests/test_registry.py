"""Test central registry functionality."""

import os
import sys
import textwrap
import unittest
from unittest.mock import patch

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from toolregistry.tool import ToolTag

from toolregistry_hub.server.registry import (
    _TOOL_METADATA,
    _import_class,
    build_registry,
    get_registry,
)
from toolregistry_hub.server import registry as registry_module


class TestBuildRegistry(unittest.TestCase):
    """Test cases for build_registry function."""

    def test_build_registry_succeeds_without_env_vars(self):
        """Test that build_registry succeeds even without any environment variables."""
        # Clear all relevant env vars to ensure clean state
        env_vars_to_clear = [
            "BRAVE_API_KEY",
            "TAVILY_API_KEY",
            "SEARXNG_URL",
            "BRIGHTDATA_API_KEY",
            "SCRAPELESS_API_KEY",
        ]
        with patch.dict(os.environ, {}, clear=True):
            # Preserve PATH and other essential vars but clear API keys
            for var in env_vars_to_clear:
                os.environ.pop(var, None)

            reg = build_registry()
            self.assertIsNotNone(reg)
            # Should have tools registered
            self.assertGreater(len(reg._tools), 0)

    def test_build_registry_has_core_tools(self):
        """Test that build_registry registers core tools."""
        reg = build_registry()
        tool_names = list(reg._tools.keys())

        # Check that some core tools are registered (with namespace prefix)
        # Calculator tools should be present
        calc_tools = [t for t in tool_names if t.startswith("calc")]
        self.assertGreater(len(calc_tools), 0, "Calculator tools should be registered")

        # DateTime tools should be present
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

            # Find brave_search tools and check they are disabled
            brave_tools = [
                t for t in reg._tools if reg._tools[t].namespace == "web/brave_search"
            ]
            for tool_name in brave_tools:
                self.assertFalse(
                    reg.is_enabled(tool_name),
                    f"Tool {tool_name} should be disabled without BRAVE_API_KEY",
                )

            # Find searxng_search tools and check they are disabled
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
        with patch.dict(
            os.environ,
            {"BRAVE_API_KEY": "test-key-for-brave"},
        ):
            reg = build_registry()

            # Find brave_search tools and check they are enabled
            brave_tools = [
                t for t in reg._tools if reg._tools[t].namespace == "web/brave_search"
            ]
            self.assertGreater(
                len(brave_tools), 0, "Brave search tools should be registered"
            )
            for tool_name in brave_tools:
                self.assertTrue(
                    reg.is_enabled(tool_name),
                    f"Tool {tool_name} should be enabled with BRAVE_API_KEY set",
                )

    def test_websearch_tools_enabled_with_tool_kwargs(self):
        """Test that websearch tools are enabled when API keys are passed via tool_kwargs."""
        with patch.dict(os.environ, {}, clear=True):
            # Clear all API key env vars
            for var in [
                "BRAVE_API_KEY",
                "TAVILY_API_KEY",
                "SEARXNG_URL",
                "BRIGHTDATA_API_KEY",
                "SCRAPELESS_API_KEY",
            ]:
                os.environ.pop(var, None)

            # Pass API key directly via tool_kwargs
            reg = build_registry(
                tool_kwargs={"brave_search": {"api_keys": "direct-test-key"}}
            )

            # Brave search tools should be enabled (configured via tool_kwargs)
            brave_tools = [
                t for t in reg._tools if reg._tools[t].namespace == "web/brave_search"
            ]
            self.assertGreater(len(brave_tools), 0)
            for tool_name in brave_tools:
                self.assertTrue(
                    reg.is_enabled(tool_name),
                    f"Tool {tool_name} should be enabled with tool_kwargs API key",
                )

            # Tavily should still be disabled (no env var, no tool_kwargs)
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

        # Calculator tools should always be enabled
        calc_tools = [t for t in reg._tools if reg._tools[t].namespace == "calculator"]
        for tool_name in calc_tools:
            self.assertTrue(
                reg.is_enabled(tool_name),
                f"Core tool {tool_name} should always be enabled",
            )


class TestImportClass(unittest.TestCase):
    """Test cases for _import_class dynamic import function."""

    def test_import_known_class(self):
        """Test importing a known class succeeds."""
        cls = _import_class("toolregistry_hub.calculator.Calculator")
        from toolregistry_hub.calculator import Calculator

        self.assertIs(cls, Calculator)

    def test_import_nested_class(self):
        """Test importing a class from a nested module."""
        cls = _import_class("toolregistry_hub.websearch.websearch_brave.BraveSearch")
        from toolregistry_hub.websearch.websearch_brave import BraveSearch

        self.assertIs(cls, BraveSearch)

    def test_import_nonexistent_module(self):
        """Test importing from a nonexistent module raises ImportError."""
        with self.assertRaises(ImportError):
            _import_class("nonexistent.module.ClassName")

    def test_import_nonexistent_class(self):
        """Test importing a nonexistent class raises AttributeError."""
        with self.assertRaises(AttributeError):
            _import_class("toolregistry_hub.calculator.NonExistentClass")


class TestBuildRegistryWithToolsConfig(unittest.TestCase):
    """Test cases for build_registry with tools field in config."""

    def test_config_driven_tool_list(self):
        """Test that build_registry uses tools from config file."""
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonc", delete=False) as f:
            f.write(
                textwrap.dedent("""\
                {
                    "tools": [
                        {"class": "toolregistry_hub.calculator.Calculator", "namespace": "calculator"},
                        {"class": "toolregistry_hub.datetime_utils.DateTime", "namespace": "datetime"}
                    ]
                }""")
            )
            f.flush()
            config_path = f.name

        try:
            reg = build_registry(tools_config_path=config_path)
            # Should have calculator and datetime tools
            namespaces = {
                tool.namespace for tool in reg._tools.values() if tool.namespace
            }
            self.assertIn("calculator", namespaces)
            self.assertIn("datetime", namespaces)
            # Should NOT have other tools like web/fetch, filesystem, etc.
            self.assertNotIn("web/fetch", namespaces)
            self.assertNotIn("filesystem", namespaces)
            self.assertNotIn("web/brave_search", namespaces)
        finally:
            os.unlink(config_path)

    def test_config_without_tools_uses_defaults(self):
        """Test that build_registry uses defaults when tools field is absent."""
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonc", delete=False) as f:
            f.write('{"mode": "denylist", "disabled": []}')
            f.flush()
            config_path = f.name

        try:
            reg = build_registry(tools_config_path=config_path)
            # Should have all default tools
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
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonc", delete=False) as f:
            f.write(
                textwrap.dedent("""\
                {
                    "tools": [
                        {"class": "toolregistry_hub.calculator.Calculator", "namespace": "calculator"},
                        {"class": "nonexistent.module.FakeClass", "namespace": "fake"}
                    ]
                }""")
            )
            f.flush()
            config_path = f.name

        try:
            reg = build_registry(tools_config_path=config_path)
            namespaces = {
                tool.namespace for tool in reg._tools.values() if tool.namespace
            }
            # Calculator should be registered
            self.assertIn("calculator", namespaces)
            # Fake tool should be skipped
            self.assertNotIn("fake", namespaces)
        finally:
            os.unlink(config_path)


class TestToolMetadataAndDiscovery(unittest.TestCase):
    """Test cases for tool metadata, discovery, and think-augment features."""

    def test_tool_metadata_tags_applied(self):
        """Test that ToolTag metadata is applied to registered tools."""
        reg = build_registry(enable_discovery=False)

        # Calculator should have READ_ONLY tag
        calc_tools = [t for t in reg._tools.values() if t.namespace == "calculator"]
        for tool in calc_tools:
            self.assertIn(ToolTag.READ_ONLY, tool.metadata.tags)

        # BashTool should have DESTRUCTIVE and PRIVILEGED
        bash_tools = [t for t in reg._tools.values() if t.namespace == "bash"]
        for tool in bash_tools:
            self.assertIn(ToolTag.DESTRUCTIVE, tool.metadata.tags)
            self.assertIn(ToolTag.PRIVILEGED, tool.metadata.tags)

        # FileOps should have FILE_SYSTEM and DESTRUCTIVE
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
