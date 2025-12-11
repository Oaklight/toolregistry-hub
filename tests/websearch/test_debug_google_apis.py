"""
Debug script to examine raw API responses from Bright Data and Scrapeless.

This script helps analyze the complete data structure returned by both APIs
to ensure we're not missing any valuable information in our parsing logic.

Usage:
    # Set log level to DEBUG to see detailed output
    export LOGURU_LEVEL=DEBUG

    # Run the test
    python -m pytest tests/websearch/test_debug_google_apis.py -v -s

    # Or run directly
    python tests/websearch/test_debug_google_apis.py
"""

import os
import sys
from pathlib import Path

# Add src to path for direct execution
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest
from dotenv import load_dotenv
from loguru import logger

from toolregistry_hub.websearch import websearch_brightdata, websearch_scrapeless

# Configure logger for debugging
logger.remove()  # Remove default handler
logger.add(
    sys.stderr,
    level="DEBUG",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
)


class TestBrightDataDebug:
    """Debug tests for Bright Data API responses."""

    @pytest.mark.skipif(
        not os.getenv("BRIGHTDATA_API_KEY"),
        reason="BRIGHTDATA_API_KEY not set",
    )
    def test_brightdata_raw_response(self):
        """Test Bright Data and examine raw API response structure."""
        logger.info("=" * 80)
        logger.info("Testing Bright Data Google Search API")
        logger.info("=" * 80)

        search = websearch_brightdata.BrightDataSearch()

        # Simple test query
        query = "python programming"
        logger.info(f"Searching for: '{query}'")

        results = search.search(query, max_results=3)

        logger.info(f"\n{'=' * 80}")
        logger.info(f"Returned {len(results)} results")
        logger.info(f"{'=' * 80}\n")

        for i, result in enumerate(results, 1):
            logger.info(f"Result {i}:")
            logger.info(f"  Title: {result.title}")
            logger.info(f"  URL: {result.url}")
            logger.info(f"  Content: {result.content[:100]}...")
            logger.info(f"  Score: {result.score}")
            logger.info("")

        assert len(results) > 0, "Should return at least one result"


class TestScrapelessDebug:
    """Debug tests for Scrapeless API responses."""

    @pytest.mark.skipif(
        not os.getenv("SCRAPELESS_API_KEY"),
        reason="SCRAPELESS_API_KEY not set",
    )
    def test_scrapeless_raw_response(self):
        """Test Scrapeless and examine raw API response structure."""
        logger.info("=" * 80)
        logger.info("Testing Scrapeless DeepSERP Google Search API")
        logger.info("=" * 80)

        search = websearch_scrapeless.ScrapelessSearch()

        # Simple test query
        query = "python programming"
        logger.info(f"Searching for: '{query}'")

        results = search.search(query, max_results=3)

        logger.info(f"\n{'=' * 80}")
        logger.info(f"Returned {len(results)} results")
        logger.info(f"{'=' * 80}\n")

        for i, result in enumerate(results, 1):
            logger.info(f"Result {i}:")
            logger.info(f"  Title: {result.title}")
            logger.info(f"  URL: {result.url}")
            logger.info(f"  Content: {result.content[:100]}...")
            logger.info(f"  Score: {result.score}")
            logger.info("")

        assert len(results) > 0, "Should return at least one result"


def main():
    """Run debug tests directly."""
    logger.info("Starting debug tests for Google Search APIs")
    logger.info("=" * 80)

    # Test Bright Data
    if os.getenv("BRIGHTDATA_API_KEY"):
        logger.info("\n\n" + "=" * 80)
        logger.info("BRIGHT DATA TEST")
        logger.info("=" * 80 + "\n")
        test = TestBrightDataDebug()
        test.test_brightdata_raw_response()
    else:
        logger.warning("Skipping Bright Data test - BRIGHTDATA_API_KEY not set")

    # Test Scrapeless
    if os.getenv("SCRAPELESS_API_KEY"):
        logger.info("\n\n" + "=" * 80)
        logger.info("SCRAPELESS TEST")
        logger.info("=" * 80 + "\n")
        test = TestScrapelessDebug()
        test.test_scrapeless_raw_response()
    else:
        logger.warning("Skipping Scrapeless test - SCRAPELESS_API_KEY not set")

    logger.info("\n" + "=" * 80)
    logger.info("Debug tests completed")
    logger.info("=" * 80)


if __name__ == "__main__":
    load_dotenv()
    main()
