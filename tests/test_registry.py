"""Test central registry functionality."""

import os
import sys
import unittest
from unittest.mock import patch

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from toolregistry_hub.server.registry import build_registry, get_registry
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
                t for t in reg._tools if reg._tools[t].namespace == "brave_search"
            ]
            for tool_name in brave_tools:
                self.assertFalse(
                    reg.is_enabled(tool_name),
                    f"Tool {tool_name} should be disabled without BRAVE_API_KEY",
                )

            # Find searxng_search tools and check they are disabled
            searxng_tools = [
                t for t in reg._tools if reg._tools[t].namespace == "searxng_search"
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
                t for t in reg._tools if reg._tools[t].namespace == "brave_search"
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
                t for t in reg._tools if reg._tools[t].namespace == "brave_search"
            ]
            self.assertGreater(len(brave_tools), 0)
            for tool_name in brave_tools:
                self.assertTrue(
                    reg.is_enabled(tool_name),
                    f"Tool {tool_name} should be enabled with tool_kwargs API key",
                )

            # Tavily should still be disabled (no env var, no tool_kwargs)
            tavily_tools = [
                t for t in reg._tools if reg._tools[t].namespace == "tavily_search"
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
                tool_kwargs={
                    "searxng_search": {"base_url": "http://localhost:8080"}
                }
            )

            searxng_tools = [
                t for t in reg._tools if reg._tools[t].namespace == "searxng_search"
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
