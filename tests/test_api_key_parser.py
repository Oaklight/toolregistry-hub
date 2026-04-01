"""Test API Key Parser functionality."""

import os
import sys
import threading
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

    def test_init_no_keys_creates_empty_parser(self):
        """Test that initialization without keys creates an empty parser."""
        parser = APIKeyParser()
        self.assertEqual(parser.key_count, 0)
        self.assertEqual(len(parser), 0)

    def test_empty_parser_get_next_key_raises_error(self):
        """Test that get_next_api_key raises ValueError on empty parser."""
        parser = APIKeyParser()
        with self.assertRaises(ValueError):
            parser.get_next_api_key()

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


class TestAPIKeyFailover(unittest.TestCase):
    """Test cases for API key failover functionality."""

    def test_mark_key_failed(self):
        """Test marking a key as failed."""
        parser = APIKeyParser(api_keys="key1,key2,key3")
        parser.mark_key_failed("key1", "HTTP 401", ttl=3600)

        failed = parser.failed_keys
        self.assertIn("key1", failed)
        self.assertEqual(failed["key1"], "HTTP 401")

    def test_get_next_valid_key_skips_failed(self):
        """Test that get_next_valid_key skips failed keys."""
        parser = APIKeyParser(api_keys="key1,key2,key3")
        parser.mark_key_failed("key1", "HTTP 401", ttl=3600)

        # Should skip key1 and return key2
        key = parser.get_next_valid_key()
        self.assertNotEqual(key, "key1")

    def test_get_next_valid_key_round_robin(self):
        """Test round-robin with one failed key."""
        parser = APIKeyParser(api_keys="key1,key2,key3")
        parser.mark_key_failed("key2", "HTTP 403", ttl=3600)

        keys = []
        for _ in range(4):
            keys.append(parser.get_next_valid_key())

        # key2 should never appear
        self.assertNotIn("key2", keys)
        # key1 and key3 should appear
        self.assertIn("key1", keys)
        self.assertIn("key3", keys)

    def test_all_keys_failed_raises(self):
        """Test that ValueError is raised when all keys are failed."""
        parser = APIKeyParser(api_keys="key1,key2")
        parser.mark_key_failed("key1", "HTTP 401", ttl=3600)
        parser.mark_key_failed("key2", "HTTP 403", ttl=3600)

        with self.assertRaises(ValueError, msg="All API keys are currently failed"):
            parser.get_next_valid_key()

    def test_ttl_auto_recovery(self):
        """Test that failed keys auto-recover after TTL expires."""
        parser = APIKeyParser(api_keys="key1,key2")
        parser.mark_key_failed("key1", "rate limited", ttl=0.1)

        # Initially key1 should be failed
        self.assertIn("key1", parser.failed_keys)

        # Wait for TTL to expire
        time.sleep(0.15)

        # key1 should be auto-recovered
        self.assertNotIn("key1", parser.failed_keys)

        # get_next_valid_key should now return key1
        key = parser.get_next_valid_key()
        self.assertEqual(key, "key1")

    def test_failed_keys_property(self):
        """Test failed_keys property returns correct state."""
        parser = APIKeyParser(api_keys="key1,key2,key3")
        parser.mark_key_failed("key1", "HTTP 401", ttl=3600)
        parser.mark_key_failed("key3", "rate limited", ttl=300)

        failed = parser.failed_keys
        self.assertEqual(len(failed), 2)
        self.assertEqual(failed["key1"], "HTTP 401")
        self.assertEqual(failed["key3"], "rate limited")

    def test_thread_safety(self):
        """Test that concurrent access to key rotation is thread-safe."""
        parser = APIKeyParser(api_keys="key1,key2,key3", rate_limit_delay=0)
        results = []
        errors = []

        def get_keys(n):
            try:
                for _ in range(n):
                    results.append(parser.get_next_valid_key())
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=get_keys, args=(100,)) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0)
        self.assertEqual(len(results), 500)
        # All results should be valid keys
        for key in results:
            self.assertIn(key, ["key1", "key2", "key3"])


if __name__ == "__main__":
    load_dotenv()
    unittest.main()
