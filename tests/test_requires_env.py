"""Test requires_env decorator and Configurable protocol functionality."""

import os
import sys
import unittest

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from toolregistry_hub.utils.configurable import Configurable
from toolregistry_hub.utils.requirements import requires_env


class TestRequiresEnv(unittest.TestCase):
    """Test cases for requires_env decorator."""

    def test_decorator_sets_required_envs(self):
        """Test that requires_env sets _required_envs attribute on the class."""

        @requires_env("MY_API_KEY")
        class MyTool:
            pass

        self.assertTrue(hasattr(MyTool, "_required_envs"))
        self.assertEqual(MyTool._required_envs, ["MY_API_KEY"])

    def test_decorator_multiple_envs(self):
        """Test that requires_env supports multiple environment variables."""

        @requires_env("KEY_A", "KEY_B", "KEY_C")
        class MultiEnvTool:
            pass

        self.assertEqual(MultiEnvTool._required_envs, ["KEY_A", "KEY_B", "KEY_C"])

    def test_undecorated_class_has_no_required_envs(self):
        """Test that undecorated classes do not have _required_envs attribute."""

        class PlainTool:
            pass

        self.assertFalse(hasattr(PlainTool, "_required_envs"))

    def test_decorator_preserves_class(self):
        """Test that the decorator returns the same class."""

        @requires_env("SOME_KEY")
        class OriginalTool:
            """A tool with a docstring."""

            def do_something(self):
                return 42

        self.assertEqual(OriginalTool.__name__, "OriginalTool")
        self.assertEqual(OriginalTool.__doc__, "A tool with a docstring.")
        self.assertEqual(OriginalTool().do_something(), 42)

    def test_decorator_does_not_block_instantiation(self):
        """Test that requires_env does NOT block instantiation — it is pure metadata."""

        @requires_env("NONEXISTENT_ENV_VAR_12345")
        class MetadataOnlyTool:
            def __init__(self):
                self.value = "created"

        # Should instantiate without error even though env var is missing
        tool = MetadataOnlyTool()
        self.assertEqual(tool.value, "created")

    def test_websearch_classes_have_required_envs(self):
        """Test that websearch classes are properly decorated with requires_env."""
        from toolregistry_hub.websearch import (
            BraveSearch,
            BrightDataSearch,
            ScrapelessSearch,
            SearXNGSearch,
            TavilySearch,
        )

        self.assertEqual(BraveSearch._required_envs, ["BRAVE_API_KEY"])
        self.assertEqual(TavilySearch._required_envs, ["TAVILY_API_KEY"])
        self.assertEqual(SearXNGSearch._required_envs, ["SEARXNG_URL"])
        self.assertEqual(BrightDataSearch._required_envs, ["BRIGHTDATA_API_KEY"])
        self.assertEqual(ScrapelessSearch._required_envs, ["SCRAPELESS_API_KEY"])


class TestConfigurableProtocol(unittest.TestCase):
    """Test cases for Configurable protocol."""

    def test_class_with_is_configured_satisfies_protocol(self):
        """Test that any class with is_configured() satisfies the Configurable protocol."""

        class MyConfigurable:
            def is_configured(self) -> bool:
                return True

        instance = MyConfigurable()
        self.assertIsInstance(instance, Configurable)

    def test_class_without_is_configured_does_not_satisfy(self):
        """Test that a class without is_configured() does not satisfy the protocol."""

        class NotConfigurable:
            pass

        instance = NotConfigurable()
        self.assertNotIsInstance(instance, Configurable)

    def test_websearch_classes_satisfy_configurable(self):
        """Test that all websearch classes satisfy the Configurable protocol."""
        from toolregistry_hub.websearch import (
            BraveSearch,
            BrightDataSearch,
            ScrapelessSearch,
            SearXNGSearch,
            TavilySearch,
        )

        # Instantiate without env vars (deferred validation)
        brave = BraveSearch()
        tavily = TavilySearch()
        searxng = SearXNGSearch()
        brightdata = BrightDataSearch()
        scrapeless = ScrapelessSearch()

        for instance in [brave, tavily, searxng, brightdata, scrapeless]:
            self.assertIsInstance(
                instance,
                Configurable,
                f"{type(instance).__name__} should satisfy Configurable protocol",
            )

    def test_unconfigured_websearch_returns_false(self):
        """Test that websearch instances without keys/URL report not configured."""
        from toolregistry_hub.websearch import BraveSearch, SearXNGSearch

        from unittest.mock import patch

        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("BRAVE_API_KEY", None)
            os.environ.pop("SEARXNG_URL", None)

            brave = BraveSearch()
            self.assertFalse(brave.is_configured())

            searxng = SearXNGSearch()
            self.assertFalse(searxng.is_configured())

    def test_configured_websearch_returns_true(self):
        """Test that websearch instances with keys/URL report configured."""
        from toolregistry_hub.websearch import BraveSearch, SearXNGSearch

        brave = BraveSearch(api_keys="test-key")
        self.assertTrue(brave.is_configured())

        searxng = SearXNGSearch(base_url="http://localhost:8080")
        self.assertTrue(searxng.is_configured())


if __name__ == "__main__":
    unittest.main()
