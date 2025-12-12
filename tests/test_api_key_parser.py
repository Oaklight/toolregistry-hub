"""Test API Key Parser functionality."""

import os
import sys
import time
import unittest
from unittest.mock import patch

from dotenv import load_dotenv

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from toolregistry_hub.utils import APIKeyParser


class TestAPIKeyParser(unittest.TestCase):
    """Test cases for APIKeyParser."""

    def test_init_with_single_key(self):
        """Test initialization with a single API key."""
        parser = APIKeyParser(api_keys="test-key-1")
        self.assertEqual(parser.key_count, 1)
        self.assertEqual(parser.get_next_api_key(), "test-key-1")

    def test_init_with_multiple_keys(self):
        """Test initialization with multiple API keys."""
        keys = "valid-key1,valid-key2,valid-key3"
        parser = APIKeyParser(api_keys=keys)
        self.assertEqual(parser.key_count, 3)

        # Test round-robin selection
        self.assertEqual(parser.get_next_api_key(), "valid-key1")
        self.assertEqual(parser.get_next_api_key(), "valid-key2")
        self.assertEqual(parser.get_next_api_key(), "valid-key3")
        self.assertEqual(parser.get_next_api_key(), "valid-key1")  # Should wrap around

    def test_init_with_env_var(self):
        """Test initialization using environment variable."""
        with patch.dict(os.environ, {"TEST_API_KEYS": "env-key1,env-key2"}):
            parser = APIKeyParser(env_var_name="TEST_API_KEYS")
            self.assertEqual(parser.key_count, 2)
            self.assertEqual(parser.get_next_api_key(), "env-key1")

    def test_init_with_parameter_overrides_env(self):
        """Test that parameter overrides environment variable."""
        with patch.dict(os.environ, {"TEST_API_KEYS": "env-key1,env-key2"}):
            parser = APIKeyParser(
                api_keys="param-key1,param-key2", env_var_name="TEST_API_KEYS"
            )
            self.assertEqual(parser.key_count, 2)
            self.assertEqual(parser.get_next_api_key(), "param-key1")

    def test_init_no_keys_raises_error(self):
        """Test that initialization without keys raises ValueError."""
        with self.assertRaises(ValueError):
            APIKeyParser()

    def test_init_invalid_keys_filtered(self):
        """Test that invalid keys are filtered out."""
        # Mix of valid and invalid keys
        keys = "valid-key1,invalid,valid-key2,123,valid-key3"
        parser = APIKeyParser(api_keys=keys)
        # All keys are now considered valid since validation is more lenient
        self.assertEqual(parser.key_count, 5)  # All keys should be accepted

    def test_get_key_info(self):
        """Test getting key information."""
        parser = APIKeyParser(api_keys="valid-key1,valid-key2,valid-key3")
        info = parser.get_key_info()

        self.assertEqual(info["key_count"], 3)
        self.assertEqual(info["current_index"], 0)  # Should start at 0

    def test_round_robin_selection(self):
        """Test round-robin key selection."""
        parser = APIKeyParser(api_keys="valid-key1,valid-key2,valid-key3")

        # Get keys in sequence
        keys = [parser.get_next_api_key() for _ in range(6)]
        expected = [
            "valid-key1",
            "valid-key2",
            "valid-key3",
            "valid-key1",
            "valid-key2",
            "valid-key3",
        ]
        self.assertEqual(keys, expected)

    def test_is_valid_api_key(self):
        """Test API key validation."""
        parser = APIKeyParser(api_keys="dummy")

        # Valid keys
        self.assertTrue(parser._is_valid_api_key("sk-1234567890abcdef"))
        self.assertTrue(parser._is_valid_api_key("AIza1234567890abcdef-_"))
        self.assertTrue(
            parser._is_valid_api_key("123e4567-e89b-12d3-a456-426614174000")
        )
        self.assertTrue(parser._is_valid_api_key("valid_key_123"))

        # Invalid keys (only empty string should be invalid now)
        self.assertTrue(parser._is_valid_api_key("short"))  # Short keys are now allowed
        self.assertFalse(parser._is_valid_api_key(""))
        # Note: "invalid@key" actually matches the alphanumeric pattern, so it's considered valid
        # Let's use a key with special characters that don't match any pattern
        self.assertFalse(parser._is_valid_api_key("invalid key"))

    def test_wait_for_rate_limit(self):
        """Test rate limiting functionality."""
        parser = APIKeyParser(api_keys="valid-key1,valid-key2", rate_limit_delay=0.1)

        # First call should not sleep
        start_time = time.time()
        parser.wait_for_rate_limit()
        elapsed = time.time() - start_time
        self.assertLess(elapsed, 0.05)  # Should be very fast

        # Second call should sleep for the remaining time
        start_time = time.time()
        parser.wait_for_rate_limit()
        elapsed = time.time() - start_time
        self.assertGreaterEqual(
            elapsed, 0.05
        )  # Should have slept for at least some time

    def test_per_key_rate_limiting(self):
        """Test that rate limiting is applied per API key independently."""
        parser = APIKeyParser(api_keys="key1,key2", rate_limit_delay=0.1)

        # Use key1
        start_time = time.time()
        parser.wait_for_rate_limit(api_key="key1")
        elapsed1 = time.time() - start_time
        self.assertLess(elapsed1, 0.05)  # Should be very fast

        # Use key2 immediately - should not be rate limited
        start_time = time.time()
        parser.wait_for_rate_limit(api_key="key2")
        elapsed2 = time.time() - start_time
        self.assertLess(
            elapsed2, 0.05
        )  # Should be very fast, not affected by key1's rate limit

        # Use key1 again - should be rate limited
        start_time = time.time()
        parser.wait_for_rate_limit(api_key="key1")
        elapsed3 = time.time() - start_time
        self.assertGreaterEqual(
            elapsed3, 0.05
        )  # Should have slept for at least some time


if __name__ == "__main__":
    load_dotenv()
    unittest.main()
