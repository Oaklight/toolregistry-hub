"""Unit tests for Gemini Search module."""

from unittest.mock import MagicMock, Mock, patch

import httpx
import pytest

from toolregistry_hub.websearch.search_result import SearchResult
from toolregistry_hub.websearch.websearch_gemini import GeminiSearch


class TestGeminiSearch:
    """Test cases for GeminiSearch class."""

    def test_init_with_api_key(self):
        """Test initialization with API key."""
        search = GeminiSearch(api_keys="test_key_123")
        assert search.api_key_parser.key_count == 1
        assert search.model == "gemini-2.0-flash-exp"  # Default model

    def test_init_with_custom_model(self):
        """Test initialization with custom model."""
        search = GeminiSearch(api_keys="test_key", model="gemini-1.5-pro")
        assert search.model == "gemini-1.5-pro"

    @patch.dict("os.environ", {"GEMINI_API_KEY": "env_key"})
    def test_init_from_env(self):
        """Test initialization from environment variable."""
        search = GeminiSearch()
        assert search.api_keys == "env_key"

    @patch.dict(
        "os.environ",
        {"GEMINI_API_KEY": "env_key", "GEMINI_MODEL": "gemini-1.5-flash"},
    )
    def test_init_model_from_env(self):
        """Test model initialization from environment variable."""
        search = GeminiSearch()
        assert search.model == "gemini-1.5-flash"

    def test_init_without_key_raises_error(self):
        """Test that initialization without API key raises ValueError."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="API key is required"):
                GeminiSearch()

    def test_headers_property(self):
        """Test headers property."""
        search = GeminiSearch(api_keys="test_key")
        headers = search._headers

        assert headers["Content-Type"] == "application/json"
        assert headers["x-goog-api-key"] == "test_key"

    @patch("httpx.Client")
    def test_search_basic(self, mock_client_class):
        """Test basic search functionality."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "This is a test answer about Python programming."}
                        ]
                    },
                    "groundingMetadata": {
                        "groundingChunks": [
                            {
                                "web": {
                                    "title": "Python Tutorial",
                                    "uri": "https://example1.com"
                                }
                            },
                            {
                                "web": {
                                    "title": "Python Guide",
                                    "uri": "https://example2.com"
                                }
                            }
                        ]
                    }
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()

        # Setup mock client
        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.post.return_value = mock_response
        mock_client_class.return_value = mock_client_instance

        # Perform search
        search = GeminiSearch(api_keys="test_key")
        results = search.search("test query", max_results=5)

        # Assertions
        assert len(results) == 2
        assert isinstance(results[0], SearchResult)
        assert results[0].title == "Python Tutorial"
        assert results[0].url == "https://example1.com"
        assert "test answer" in results[0].content
        assert results[1].title == "Python Guide"

    @patch("httpx.Client")
    def test_search_empty_query(self, mock_client_class):
        """Test search with empty query."""
        search = GeminiSearch(api_keys="test_key")
        results = search.search("")

        assert results == []
        mock_client_class.assert_not_called()

    @patch("httpx.Client")
    def test_search_no_grounding_metadata(self, mock_client_class):
        """Test search when response has no grounding metadata."""
        # Mock response without grounding metadata
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "This is a synthesized answer."}
                        ]
                    }
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.post.return_value = mock_response
        mock_client_class.return_value = mock_client_instance

        search = GeminiSearch(api_keys="test_key")
        results = search.search("test query")

        # Should return a single result with synthesized answer
        assert len(results) == 1
        assert results[0].title == "Gemini Synthesized Answer"
        assert results[0].content == "This is a synthesized answer."

    @patch("httpx.Client")
    def test_search_timeout_error(self, mock_client_class):
        """Test search with timeout error."""
        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.post.side_effect = httpx.TimeoutException("Timeout")
        mock_client_class.return_value = mock_client_instance

        search = GeminiSearch(api_keys="test_key")
        results = search.search("test query")

        assert results == []

    @patch("httpx.Client")
    def test_search_http_error(self, mock_client_class):
        """Test search with HTTP error."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.post.side_effect = httpx.HTTPStatusError(
            "Bad Request", request=MagicMock(), response=mock_response
        )
        mock_client_class.return_value = mock_client_instance

        search = GeminiSearch(api_keys="test_key")
        results = search.search("test query")

        assert results == []

    @patch("httpx.Client")
    def test_search_empty_response(self, mock_client_class):
        """Test search with empty response text."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": ""}
                        ]
                    }
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.post.return_value = mock_response
        mock_client_class.return_value = mock_client_instance

        search = GeminiSearch(api_keys="test_key")
        results = search.search("test query")

        assert results == []

    @patch("httpx.Client")
    def test_search_max_results_limiting(self, mock_client_class):
        """Test that results are limited to max_results."""
        # Create mock response with multiple sources
        chunks = [
            {"web": {"title": f"Title {i}", "uri": f"https://example{i}.com"}}
            for i in range(10)
        ]

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": "Test answer"}]
                    },
                    "groundingMetadata": {
                        "groundingChunks": chunks
                    }
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.post.return_value = mock_response
        mock_client_class.return_value = mock_client_instance

        search = GeminiSearch(api_keys="test_key")
        results = search.search("test query", max_results=3)

        # Should be limited to 3 results
        assert len(results) == 3

    @patch("httpx.Client")
    def test_parse_results_with_multiple_text_parts(self, mock_client_class):
        """Test parsing response with multiple text parts."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "First part. "},
                            {"text": "Second part."}
                        ]
                    }
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.post.return_value = mock_response
        mock_client_class.return_value = mock_client_instance

        search = GeminiSearch(api_keys="test_key")
        results = search.search("test query")

        assert len(results) == 1
        assert results[0].content == "First part. Second part."

    @patch("time.sleep")
    @patch("time.time")
    @patch("httpx.Client")
    def test_rate_limiting(self, mock_client_class, mock_time, mock_sleep):
        """Test rate limiting functionality."""
        mock_time.side_effect = [0, 0.5, 1.5]  # Simulate time progression

        # Mock successful response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": "Test"}]
                    }
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.post.return_value = mock_response
        mock_client_class.return_value = mock_client_instance

        search = GeminiSearch(api_keys="test_key", rate_limit_delay=1.0)

        # First call should not sleep
        search.search("query1")
        assert mock_sleep.call_count == 0

        # Second call within delay should sleep
        search.search("query2")
        assert mock_sleep.call_count == 1

    @patch("httpx.Client")
    def test_get_response_text_no_candidates(self, mock_client_class):
        """Test _get_response_text with no candidates."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"candidates": []}
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.post.return_value = mock_response
        mock_client_class.return_value = mock_client_instance

        search = GeminiSearch(api_keys="test_key")
        results = search.search("test query")

        assert results == []

    @patch("httpx.Client")
    def test_score_decreasing(self, mock_client_class):
        """Test that scores decrease for later results."""
        # Create mock response with multiple sources
        chunks = [
            {"web": {"title": f"Title {i}", "uri": f"https://example{i}.com"}}
            for i in range(3)
        ]

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": "Test answer"}]
                    },
                    "groundingMetadata": {
                        "groundingChunks": chunks
                    }
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.post.return_value = mock_response
        mock_client_class.return_value = mock_client_instance

        search = GeminiSearch(api_keys="test_key")
        results = search.search("test query")

        # Scores should decrease
        assert results[0].score == 1.0
        assert results[1].score == 0.95
        assert results[2].score == 0.90


class TestGeminiSearchIntegration:
    """Integration tests for GeminiSearch."""

    def test_search_method_signature(self):
        """Test search method accepts all expected parameters."""
        search = GeminiSearch(api_keys="test_key")

        # Mock the _search_impl to avoid actual API calls
        with patch.object(search, "_search_impl", return_value=[]):
            # This should not raise any errors
            search.search(query="test", max_results=5, timeout=10)

    def test_base_url_format(self):
        """Test that base URL is correctly formatted."""
        search = GeminiSearch(api_keys="test_key")
        assert search.base_url == "https://generativelanguage.googleapis.com/v1beta"