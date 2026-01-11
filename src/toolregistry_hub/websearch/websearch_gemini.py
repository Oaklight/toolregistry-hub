"""
Gemini Google Search Implementation

This module provides a web search interface using Google Gemini's built-in
Grounding with Google Search feature via REST API.

Setup:
1. Get a Gemini API key from https://aistudio.google.com/
2. Set your API key as an environment variable:
   export GEMINI_API_KEY="your-gemini-api-key-here"

Optional Configuration:
   export GEMINI_MODEL="gemini-2.0-flash-exp"  # Default model

Usage:
    from websearch_gemini import GeminiSearch

    search = GeminiSearch()
    results = search.search("python web scraping", max_results=5)

    for result in results:
        print(f"Title: {result['title']}")
        print(f"URL: {result['url']}")
        print(f"Content: {result['content'][:200]}...")
        print("-" * 50)

API Documentation: https://ai.google.dev/gemini-api/docs/google-search
"""

import os
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger

from ..utils.api_key_parser import APIKeyParser
from .base import TIMEOUT_DEFAULT, BaseSearch
from .search_result import SearchResult


class GeminiSearch(BaseSearch):
    """Gemini-powered web search using Google's Grounding with Google Search via REST API."""

    def __init__(
        self,
        api_keys: Optional[str] = None,
        model: Optional[str] = None,
        rate_limit_delay: float = 1.0,
    ):
        """Initialize Gemini search client.

        Args:
            api_keys: Comma-separated Gemini API keys. If not provided, will try to get from GEMINI_API_KEY env var.
            model: Gemini model to use. Defaults to GEMINI_MODEL env var or "gemini-2.0-flash-exp".
            rate_limit_delay: Delay between requests in seconds to avoid rate limits.
        """
        # Initialize API key parser for multiple keys
        self.api_key_parser = APIKeyParser(
            api_keys=api_keys,
            env_var_name="GEMINI_API_KEY",
            rate_limit_delay=rate_limit_delay,
        )

        self.model = model or os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

        logger.info(f"Initialized Gemini search with model: {self.model}")

    @property
    def _headers(self) -> dict:
        """Generate headers for Gemini API requests."""
        return {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key_parser.get_next_api_key(),
        }

    def search(
        self,
        query: str,
        *,
        max_results: int = 5,
        timeout: float = TIMEOUT_DEFAULT,
        **kwargs,
    ) -> List[SearchResult]:
        """Perform a web search using Gemini's Google Search grounding.

        Args:
            query: The search query string
            max_results: Maximum number of results to return (note: actual count depends on Gemini's response)
            timeout: Request timeout in seconds
            **kwargs: Additional parameters (currently unused)

        Returns:
            List of search results with title, url, content and score

        Note:
            Unlike traditional search APIs, Gemini returns a synthesized answer with citations
            rather than a list of raw search results. The results are extracted from the
            grounding metadata.
        """
        if not query.strip():
            logger.warning("Empty query provided")
            return []

        try:
            results = self._search_impl(query=query, timeout=timeout, **kwargs)
            # Cap results to max_results
            return results[:max_results] if results else []
        except Exception as e:
            logger.error(f"Gemini search failed: {e}")
            return []

    def _search_impl(self, query: str, **kwargs) -> List[SearchResult]:
        """Perform the actual search using Gemini REST API.

        Args:
            query: The search query string
            **kwargs: Additional parameters (timeout, etc.)

        Returns:
            List of SearchResult
        """
        if not query.strip():
            logger.warning("Empty query provided")
            return []

        timeout = kwargs.get("timeout", TIMEOUT_DEFAULT)

        try:
            # Rate limiting: ensure minimum delay between requests
            self._wait_for_rate_limit()

            # Prepare the request payload
            payload = {
                "contents": [{"parts": [{"text": query}]}],
                "tools": [{"google_search": {}}],
            }

            # Make the API call
            url = f"{self.base_url}/models/{self.model}:generateContent"

            with httpx.Client(timeout=timeout) as client:
                response = client.post(url, headers=self._headers, json=payload)
                response.raise_for_status()
                data = response.json()

            # Parse the response
            results = self._parse_results(data)

            logger.info(f"Gemini search for '{query}' returned {len(results)} results")
            return results

        except httpx.TimeoutException:
            logger.error(f"Gemini API request timed out after {timeout}s")
            return []
        except httpx.HTTPStatusError as e:
            logger.error(
                f"Gemini API HTTP error {e.response.status_code}: {e.response.text}"
            )
            return []
        except Exception as e:
            logger.error(f"Gemini API request failed: {e}")
            return []

    def _parse_results(self, response_data: Dict[str, Any]) -> List[SearchResult]:
        """Parse Gemini API response into standardized format.

        Args:
            response_data: Raw API response data

        Returns:
            List of parsed search results with individual content per source
        """
        results = []

        try:
            # Extract candidates
            candidates = response_data.get("candidates", [])
            if not candidates:
                logger.warning("No candidates found in Gemini response")
                return []

            candidate = candidates[0]

            # Extract the response text
            response_text = self._get_response_text(candidate)

            if not response_text or not response_text.strip():
                logger.warning("No response text from Gemini model")
                return []

            # Extract grounding metadata
            grounding_metadata = candidate.get("groundingMetadata")

            if not grounding_metadata:
                logger.warning("No grounding metadata found in response")
                return []

            # Extract sources from grounding chunks
            grounding_chunks = grounding_metadata.get("groundingChunks", [])
            grounding_supports = grounding_metadata.get("groundingSupports", [])

            if not grounding_chunks:
                logger.warning("No grounding chunks found")
                return []

            logger.debug(
                f"Found {len(grounding_chunks)} grounding chunks and {len(grounding_supports)} supports"
            )

            # Build a map of chunk index to supported text segments
            chunk_to_segments = {}
            for support in grounding_supports:
                segment = support.get("segment", {})
                chunk_indices = support.get("groundingChunkIndices", [])
                segment_text = segment.get("text", "")

                for chunk_idx in chunk_indices:
                    if chunk_idx not in chunk_to_segments:
                        chunk_to_segments[chunk_idx] = []
                    if (
                        segment_text
                        and segment_text not in chunk_to_segments[chunk_idx]
                    ):
                        chunk_to_segments[chunk_idx].append(segment_text)

            # Create results from grounding chunks
            for i, chunk in enumerate(grounding_chunks):
                web_info = chunk.get("web")
                if web_info:
                    title = web_info.get("title", "No title")
                    url = web_info.get("uri", "")

                    # Get the text segments supported by this chunk
                    segments = chunk_to_segments.get(i, [])

                    # Use the segments as content
                    if segments:
                        # Join unique segments
                        content = " ".join(segments)
                    else:
                        # If no specific segments, use the full response as fallback
                        content = response_text

                    logger.debug(
                        f"Chunk {i}: title={title}, segments={len(segments)}, content_len={len(content)}"
                    )

                    result = SearchResult(
                        title=title,
                        url=url,
                        content=content,
                        score=1.0 - (i * 0.05),  # Decreasing score based on position
                    )
                    results.append(result)

        except Exception as e:
            logger.error(f"Error parsing Gemini response: {e}")
            import traceback

            logger.error(traceback.format_exc())

        return results

    def _get_response_text(self, candidate: Dict[str, Any]) -> str:
        """Extract text from Gemini response candidate.

        Args:
            candidate: Gemini API response candidate

        Returns:
            Extracted text content
        """
        try:
            content = candidate.get("content", {})
            parts = content.get("parts", [])

            if not parts:
                return ""

            # Collect all text parts
            text_segments = []
            for part in parts:
                if "text" in part:
                    text_segments.append(part["text"])

            return "".join(text_segments)

        except Exception as e:
            logger.error(f"Error extracting response text: {e}")
            return ""

    def _wait_for_rate_limit(self):
        """Ensure minimum delay between API requests to avoid rate limits."""
        # Get the current API key and pass it to the rate limiter
        current_key = self.api_key_parser.get_next_api_key()
        self.api_key_parser.wait_for_rate_limit(api_key=current_key)


def main():
    """Demo usage of GeminiSearch."""
    try:
        # Use rate limiting to avoid rate limit errors
        search = GeminiSearch(rate_limit_delay=1.0)

        # Test basic search
        print("=== Gemini Google Search Test ===")
        results = search.search(
            "latest developments in artificial intelligence", max_results=5
        )

        print(f"\nFound {len(results)} results:\n")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result.title}")
            print(f"   URL: {result.url}")
            print(f"   Content: {result.content[:300]}...")
            print(f"   Score: {result.score:.3f}")

    except ValueError as e:
        print(f"Setup error: {e}")
        print("Please set your GEMINI_API_KEY environment variable.")
    except Exception as e:
        print(f"Demo failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
