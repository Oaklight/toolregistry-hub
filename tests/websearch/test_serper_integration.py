"""Integration test for Serper Search API using real API key from .env.

Usage:
    python -m pytest tests/websearch/test_serper_integration.py -v -s
    python tests/websearch/test_serper_integration.py
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest
from dotenv import load_dotenv
from toolregistry_hub._vendor.structlog import setup_logging
from toolregistry_hub.websearch.websearch_serper import SerperSearch

logger = setup_logging(level="DEBUG", renderer="console")


class TestSerperIntegration:
    """Integration tests for Serper Search API with real API calls."""

    @pytest.mark.skipif(
        not os.getenv("SERPER_API_KEY"), reason="SERPER_API_KEY not set"
    )
    def test_serper_basic_search(self):
        """Test basic English search with real API."""
        logger.info("Testing Serper - Basic English Search")
        search = SerperSearch()
        results = search.search("Python programming language", max_results=3)
        logger.info(f"Returned {len(results)} results")
        for i, r in enumerate(results, 1):
            logger.info(f"  {i}. {r.title}")
            logger.info(f"     URL: {r.url}")
            logger.info(f"     Content: {r.content[:100]}...")
            logger.info(f"     Score: {r.score}")
        assert len(results) > 0, "Should return at least one result"
        assert results[0].title, "First result should have a title"
        assert results[0].url, "First result should have a URL"
        assert results[0].content, "First result should have content"

    @pytest.mark.skipif(
        not os.getenv("SERPER_API_KEY"), reason="SERPER_API_KEY not set"
    )
    def test_serper_chinese_search(self):
        """Test Chinese search with gl and hl parameters."""
        logger.info("Testing Serper - Chinese Search")
        search = SerperSearch()
        results = search.search(
            "\u4eba\u5de5\u667a\u80fd\u6700\u65b0\u8fdb\u5c55",
            max_results=3,
            hl="zh",
            gl="cn",
        )
        logger.info(f"Returned {len(results)} results")
        for i, r in enumerate(results, 1):
            logger.info(f"  {i}. {r.title}")
            logger.info(f"     URL: {r.url}")
            logger.info(f"     Content: {r.content[:100]}...")
        assert len(results) > 0, "Should return at least one result for Chinese query"

    @pytest.mark.skipif(
        not os.getenv("SERPER_API_KEY"), reason="SERPER_API_KEY not set"
    )
    def test_serper_max_results_limit(self):
        """Test that max_results parameter is respected."""
        logger.info("Testing Serper - max_results=1")
        search = SerperSearch()
        results = search.search("OpenAI ChatGPT", max_results=1)
        logger.info(f"Returned {len(results)} results (expected: 1)")
        if results:
            logger.info(f"  Title: {results[0].title}")
            logger.info(f"  URL: {results[0].url}")
        assert len(results) == 1, "Should return exactly 1 result"

    @pytest.mark.skipif(
        not os.getenv("SERPER_API_KEY"), reason="SERPER_API_KEY not set"
    )
    def test_serper_empty_query(self):
        """Test that empty query returns empty results."""
        logger.info("Testing Serper - Empty Query")
        search = SerperSearch()
        results = search.search("")
        logger.info(f"Empty query returned {len(results)} results (expected: 0)")
        assert len(results) == 0, "Empty query should return no results"

    @pytest.mark.skipif(
        not os.getenv("SERPER_API_KEY"), reason="SERPER_API_KEY not set"
    )
    def test_serper_multi_key_rotation(self):
        """Test multi-API-key initialization and rotation."""
        logger.info("Testing Serper - Multi API Key Rotation")

        api_key_str = os.getenv("SERPER_API_KEY", "")
        env_key_count = len([k.strip() for k in api_key_str.split(",") if k.strip()])

        # Test with keys from env (may be single or multi-key)
        search_from_env = SerperSearch()
        logger.info(f"Env key count: {search_from_env.api_key_parser.key_count}")
        assert search_from_env.api_key_parser.key_count == env_key_count, (
            f"Should have {env_key_count} key(s) from env"
        )

        # Test with explicit two keys (use first key from env, duplicated)
        first_key = api_key_str.split(",")[0].strip()
        two_keys = first_key + "," + first_key
        search_two = SerperSearch(api_keys=two_keys)
        logger.info(f"Explicit two-key count: {search_two.api_key_parser.key_count}")
        assert search_two.api_key_parser.key_count == 2, "Should have exactly 2 keys"

        # Verify round-robin rotation with the two-key instance
        key1 = search_two.api_key_parser.get_next_api_key()
        key2 = search_two.api_key_parser.get_next_api_key()
        key3 = search_two.api_key_parser.get_next_api_key()
        logger.info(f"Key rotation: k1={key1[:8]}... k2={key2[:8]}... k3={key3[:8]}...")
        assert key1 == key3, "Round-robin should cycle back to first key after 2 keys"
        assert key1 == key2, "Both keys are the same (duplicated for testing)"

        # If env has multiple keys, verify rotation works with real different keys
        if env_key_count > 1:
            logger.info(
                f"Env has {env_key_count} keys, testing real multi-key rotation"
            )
            search_from_env.api_key_parser._current_key_index = 0
            keys_seen = []
            for idx in range(env_key_count):
                k = search_from_env.api_key_parser.get_next_api_key()
                keys_seen.append(k[:8])
                logger.info(f"  Key {idx + 1}: {k[:8]}...")
            k_wrap = search_from_env.api_key_parser.get_next_api_key()
            logger.info(f"  Key wrap-around: {k_wrap[:8]}...")
            assert k_wrap[:8] == keys_seen[0], "Should wrap around to first key"

        # Verify multi-key search actually works with env keys
        results = search_from_env.search("test query multi key", max_results=2)
        logger.info(f"Multi-key search returned {len(results)} results")
        assert len(results) > 0, "Multi-key search should return results"
        for i, r in enumerate(results, 1):
            logger.info(f"  {i}. {r.title}")
            logger.info(f"     URL: {r.url}")

    @pytest.mark.skipif(
        not os.getenv("SERPER_API_KEY"), reason="SERPER_API_KEY not set"
    )
    def test_serper_is_configured(self):
        """Test _is_configured method with real API key."""
        logger.info("Testing Serper - _is_configured check")
        search = SerperSearch()
        logger.info(f"_is_configured: {search._is_configured()}")
        assert search._is_configured(), "Should be configured with valid API key"


def main():
    """Run integration tests directly."""
    logger.info("Starting Serper Search integration tests")
    logger.info("=" * 80)

    if not os.getenv("SERPER_API_KEY"):
        logger.warning("Skipping Serper tests - SERPER_API_KEY not set")
        return

    api_key_str = os.getenv("SERPER_API_KEY", "")
    key_count = len([k.strip() for k in api_key_str.split(",") if k.strip()])
    logger.info(f"API Key count: {key_count}, first 8 chars: {api_key_str[:8]}...")

    test = TestSerperIntegration()

    logger.info("\nTEST 1: Basic Search")
    test.test_serper_basic_search()

    logger.info("\nTEST 2: Chinese Search")
    test.test_serper_chinese_search()

    logger.info("\nTEST 3: Max Results Limit")
    test.test_serper_max_results_limit()

    logger.info("\nTEST 4: Empty Query")
    test.test_serper_empty_query()

    logger.info("\nTEST 5: Multi Key Rotation")
    test.test_serper_multi_key_rotation()

    logger.info("\nTEST 6: is_configured Check")
    test.test_serper_is_configured()

    logger.info("\n" + "=" * 80)
    logger.info("All Serper integration tests completed successfully!")
    logger.info("=" * 80)


if __name__ == "__main__":
    load_dotenv()
    main()
