"""Unit tests for Bright Data Search module."""

import json
from unittest.mock import MagicMock, patch

import httpx
import pytest

from toolregistry_hub.websearch.search_result import SearchResult
from toolregistry_hub.websearch.websearch_brightdata import BrightDataSearch


class TestBrightDataSearch:
    """Test cases for BrightDataSearch class."""

    def test_init_with_api_token(self):
        """Test initialization with API token."""
        search = BrightDataSearch(api_token="test_token_123")
        assert search.api_token == "test_token_123"
        assert search.zone == "mcp_unlocker"  # Default zone

    def test_init_with_custom_zone(self):
        """Test initialization with custom zone."""
        search = BrightDataSearch(api_token="test_token", zone="custom_zone")
        assert search.zone == "custom_zone"

    @patch.dict("os.environ", {"BRIGHTDATA_API_KEY": "env_token"})
    def test_init_from_env(self):
        """Test initialization from environment variable."""
        search = BrightDataSearch()
        assert search.api_token == "env_token"

    @patch.dict(
        "os.environ",
        {"BRIGHTDATA_API_KEY": "env_token", "BRIGHTDATA_ZONE": "env_zone"},
    )
    def test_init_zone_from_env(self):
        """Test zone initialization from environment variable."""
        search = BrightDataSearch()
        assert search.zone == "env_zone"

    def test_init_without_token_raises_error(self):
        """Test that initialization without token raises ValueError."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="API token is required"):
                BrightDataSearch()

    def test_headers_property(self):
        """Test headers property."""
        search = BrightDataSearch(api_token="test_token")
        headers = search._headers

        assert headers["Authorization"] == "Bearer test_token"
        assert headers["Content-Type"] == "application/json"
        assert headers["Accept"] == "application/json"

    @patch(
        "toolregistry_hub.websearch.websearch_brightdata.BrightDataSearch._ensure_zone_exists"
    )
    @patch("httpx.Client")
    def test_search_basic(self, mock_client, mock_ensure):
        """Test basic search functionality."""
        # Mock response
        mock_response = MagicMock()
        mock_response.text = json.dumps(
            {
                "organic": [
                    {
                        "title": "Test Result 1",
                        "url": "https://example1.com",
                        "description": "Description 1",
                    },
                    {
                        "title": "Test Result 2",
                        "url": "https://example2.com",
                        "description": "Description 2",
                    },
                ]
            }
        )
        mock_response.raise_for_status = MagicMock()

        # Setup mock client
        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value = mock_client_instance

        # Perform search
        search = BrightDataSearch(api_token="test_token")
        results = search.search("test query", max_results=5)

        # Assertions
        assert len(results) == 2
        assert isinstance(results[0], SearchResult)
        assert results[0].title == "Test Result 1"
        assert results[0].url == "https://example1.com"
        assert results[0].content == "Description 1"
        assert results[1].title == "Test Result 2"

    @patch("httpx.Client")
    def test_search_with_pagination(self, mock_client):
        """Test search with pagination cursor."""
        mock_response = MagicMock()
        mock_response.text = json.dumps({"organic": []})
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value = mock_client_instance

        search = BrightDataSearch(api_token="test_token")
        search.search("test query", cursor="2")

        # Verify the URL contains correct start parameter
        call_args = mock_client_instance.post.call_args
        payload = call_args[1]["json"]
        assert "start=20" in payload["url"]  # Page 2 = start at 20

    @patch("httpx.Client")
    def test_search_empty_query(self, mock_client):
        """Test search with empty query."""
        search = BrightDataSearch(api_token="test_token")
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

        search = BrightDataSearch(api_token="test_token")
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

        search = BrightDataSearch(api_token="invalid_token")
        results = search.search("test query")

        assert results == []

    @patch("httpx.Client")
    def test_search_http_422_error(self, mock_client):
        """Test search with 422 zone error."""
        mock_response = MagicMock()
        mock_response.status_code = 422
        mock_response.text = "Zone not found"

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.post.side_effect = httpx.HTTPStatusError(
            "Zone error", request=MagicMock(), response=mock_response
        )
        mock_client.return_value = mock_client_instance

        search = BrightDataSearch(api_token="test_token", zone="invalid_zone")
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

        search = BrightDataSearch(api_token="test_token")
        results = search.search("test query")

        assert results == []

    @patch("httpx.Client")
    def test_search_json_decode_error(self, mock_client):
        """Test search with invalid JSON response."""
        mock_response = MagicMock()
        mock_response.text = "Invalid JSON"
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value = mock_client_instance

        search = BrightDataSearch(api_token="test_token")
        results = search.search("test query")

        assert results == []

    def test_parse_results(self):
        """Test parsing of API results."""
        search = BrightDataSearch(api_token="test_token")

        raw_results = {
            "organic": [
                {
                    "title": "Result 1",
                    "url": "https://example1.com",
                    "description": "Description 1",
                },
                {
                    "title": "Result 2",
                    "url": "https://example2.com",
                    "description": "Description 2",
                },
            ],
            "images": ["img1.jpg", "img2.jpg"],
            "pagination": {"current_page": 1},
        }

        results = search._parse_results(raw_results)

        assert len(results) == 2
        assert results[0].title == "Result 1"
        assert results[0].url == "https://example1.com"
        assert results[0].content == "Description 1"
        assert results[0].score == 1.0

    def test_parse_results_empty(self):
        """Test parsing of empty results."""
        search = BrightDataSearch(api_token="test_token")
        results = search._parse_results({"organic": []})

        assert results == []

    def test_parse_results_missing_fields(self):
        """Test parsing results with missing fields."""
        search = BrightDataSearch(api_token="test_token")

        raw_results = {
            "organic": [
                {"url": "https://example.com"},  # Missing title and description
            ]
        }

        results = search._parse_results(raw_results)

        assert len(results) == 1
        assert results[0].title == "No title"
        assert results[0].url == "https://example.com"
        assert results[0].content == "No content available"

    @patch("time.sleep")
    @patch("time.time")
    def test_rate_limiting(self, mock_time, mock_sleep):
        """Test rate limiting functionality."""
        mock_time.side_effect = [0, 0.5, 1.5]  # Simulate time progression

        search = BrightDataSearch(api_token="test_token", rate_limit_delay=1.0)
        search.last_request_time = 0

        # First call should not sleep
        search._wait_for_rate_limit()
        mock_sleep.assert_not_called()

        # Second call within delay should sleep
        search._wait_for_rate_limit()
        mock_sleep.assert_called_once()

    @patch("httpx.Client")
    def test_search_max_results_pagination(self, mock_client):
        """Test search with max_results > 20 triggers pagination."""
        mock_response = MagicMock()
        mock_response.text = json.dumps({"organic": []})
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value = mock_client_instance

        search = BrightDataSearch(api_token="test_token")
        search.search("test query", max_results=45)

        # Should make 3 calls (45 / 20 = 2.25, rounded up to 3)
        assert mock_client_instance.post.call_count == 3

    @patch("httpx.Client")
    def test_search_max_results_cap(self, mock_client):
        """Test that max_results is capped at 180."""
        mock_response = MagicMock()
        mock_response.text = json.dumps({"organic": []})
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value = mock_client_instance

        search = BrightDataSearch(api_token="test_token")
        search.search("test query", max_results=200)

        # Should make 9 calls (180 / 20 = 9)
        assert mock_client_instance.post.call_count == 9
