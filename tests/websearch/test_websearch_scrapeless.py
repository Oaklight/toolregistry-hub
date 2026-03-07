"""Unit tests for Scrapeless Search module."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from toolregistry_hub.websearch.search_result import SearchResult
from toolregistry_hub.websearch.websearch_scrapeless import ScrapelessSearch


class TestScrapelessSearch:
    """Test cases for ScrapelessSearch class."""

    def test_init_with_api_key(self):
        """Test initialization with API key."""
        search = ScrapelessSearch(api_keys="test_key_123")
        assert search.api_key_parser.key_count == 1
        assert search.base_url == "https://api.scrapeless.com"

    def test_init_with_custom_base_url(self):
        """Test initialization with custom base URL."""
        search = ScrapelessSearch(
            api_keys="test_key", base_url="https://custom.api.com"
        )
        assert search.base_url == "https://custom.api.com"
        assert search.endpoint == "https://custom.api.com/api/v1/scraper/request"

    @patch.dict("os.environ", {"SCRAPELESS_API_KEY": "env_key"})
    def test_init_from_env(self):
        """Test initialization from environment variable."""
        search = ScrapelessSearch()
        assert search.api_key_parser.api_keys[0] == "env_key"

    def test_init_without_key_raises_error(self):
        """Test that initialization without API key raises ValueError."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="API keys are required"):
                ScrapelessSearch()

    def test_headers_property(self):
        """Test headers property."""
        search = ScrapelessSearch(api_keys="test_key")
        headers = search._headers

        assert headers["Content-Type"] == "application/json"
        assert headers["X-API-Key"] == "test_key"

    @patch("httpx.Client")
    def test_search_basic(self, mock_client):
        """Test basic search functionality."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "organic_results": [
                {
                    "title": "Test Result 1",
                    "link": "https://example1.com",
                    "snippet": "Description 1",
                },
                {
                    "title": "Test Result 2",
                    "link": "https://example2.com",
                    "snippet": "Description 2",
                },
            ]
        }
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value = mock_client_instance

        search = ScrapelessSearch(api_keys="test_key")
        results = search.search("test query", max_results=5)

        assert len(results) == 2
        assert isinstance(results[0], SearchResult)
        assert results[0].title == "Test Result 1"
        assert results[0].url == "https://example1.com"

    @patch("httpx.Client")
    def test_search_empty_query(self, mock_client):
        """Test search with empty query."""
        search = ScrapelessSearch(api_keys="test_key")
        results = search.search("")

        assert results == []
        mock_client.assert_not_called()

    @patch("httpx.Client")
    def test_search_timeout_error(self, mock_client):
        """Test search with timeout error."""
        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.post.side_effect = httpx.TimeoutException("Timeout")
        mock_client.return_value = mock_client_instance

        search = ScrapelessSearch(api_keys="test_key")
        results = search.search("test query")

        assert results == []

    @patch("httpx.Client")
    def test_search_http_401_error(self, mock_client):
        """Test search with 401 authentication error."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.post.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=MagicMock(), response=mock_response
        )
        mock_client.return_value = mock_client_instance

        search = ScrapelessSearch(api_keys="invalid_key")
        results = search.search("test query")

        assert results == []

    @patch("httpx.Client")
    def test_search_http_429_error(self, mock_client):
        """Test search with 429 rate limit error."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.post.side_effect = httpx.HTTPStatusError(
            "Rate limit", request=MagicMock(), response=mock_response
        )
        mock_client.return_value = mock_client_instance

        search = ScrapelessSearch(api_keys="test_key")
        results = search.search("test query")

        assert results == []

    def test_parse_results(self):
        """Test parsing of API results."""
        search = ScrapelessSearch(api_keys="test_key")

        raw_results = {
            "organic_results": [
                {
                    "title": "Result 1",
                    "link": "https://example1.com",
                    "snippet": "Description 1",
                },
                {
                    "title": "Result 2",
                    "link": "https://example2.com",
                    "snippet": "Description 2",
                },
            ]
        }

        results = search._parse_results(raw_results)

        assert len(results) == 2
        assert results[0].title == "Result 1"
        assert results[0].url == "https://example1.com"

    def test_parse_results_empty(self):
        """Test parsing of empty results."""
        search = ScrapelessSearch(api_keys="test_key")
        results = search._parse_results({"organic_results": []})

        assert results == []

    @patch("httpx.Client")
    def test_search_request_payload(self, mock_client):
        """Test that request payload is correctly formatted."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"organic_results": []}
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value = mock_client_instance

        search = ScrapelessSearch(api_keys="test_key")
        search.search("test query")

        # Verify payload structure
        call_args = mock_client_instance.post.call_args
        payload = call_args[1]["json"]

        assert payload["actor"] == "scraper.google.search"
        assert payload["input"]["q"] == "test query"
        assert payload["async"] is False

    @patch("httpx.Client")
    def test_search_with_language_and_country(self, mock_client):
        """Test search with custom language and country."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"organic_results": []}
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value = mock_client_instance

        search = ScrapelessSearch(api_keys="test_key")
        search.search("test query", language="zh-CN", country="cn")

        call_args = mock_client_instance.post.call_args
        payload = call_args[1]["json"]

        assert payload["input"]["hl"] == "zh-CN"
        assert payload["input"]["gl"] == "cn"

    @patch("httpx.Client")
    def test_search_max_results_cap(self, mock_client):
        """Test that max_results is properly handled."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"organic_results": []}
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value = mock_client_instance

        search = ScrapelessSearch(api_keys="test_key")
        results = search.search("test query", max_results=5)

        # Should cap results to max_results
        assert len(results) <= 5
