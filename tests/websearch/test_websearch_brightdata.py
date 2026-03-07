"""Unit tests for Bright Data Search module."""

import json
from unittest.mock import MagicMock, patch

import httpx
import pytest

from toolregistry_hub.websearch.search_result import SearchResult
from toolregistry_hub.websearch.websearch_brightdata import BrightDataSearch


class TestBrightDataSearch:
    """Test cases for BrightDataSearch class."""

    @patch(
        "toolregistry_hub.websearch.websearch_brightdata.BrightDataSearch._ensure_zone_exists_for_all_keys"
    )
    def test_init_with_api_token(self, mock_ensure):
        """Test initialization with API token."""
        search = BrightDataSearch(api_keys="test_token_123")
        assert search.api_key_parser.key_count == 1
        assert search.zone == "mcp_unlocker"  # Default zone

    @patch(
        "toolregistry_hub.websearch.websearch_brightdata.BrightDataSearch._ensure_zone_exists_for_all_keys"
    )
    def test_init_with_custom_zone(self, mock_ensure):
        """Test initialization with custom zone."""
        search = BrightDataSearch(api_keys="test_token", zone="custom_zone")
        assert search.zone == "custom_zone"

    @patch(
        "toolregistry_hub.websearch.websearch_brightdata.BrightDataSearch._ensure_zone_exists_for_all_keys"
    )
    @patch.dict("os.environ", {"BRIGHTDATA_API_KEY": "env_token"})
    def test_init_from_env(self, mock_ensure):
        """Test initialization from environment variable."""
        search = BrightDataSearch()
        assert search.api_key_parser.api_keys[0] == "env_token"

    @patch(
        "toolregistry_hub.websearch.websearch_brightdata.BrightDataSearch._ensure_zone_exists_for_all_keys"
    )
    @patch.dict(
        "os.environ",
        {"BRIGHTDATA_API_KEY": "env_token", "BRIGHTDATA_ZONE": "env_zone"},
    )
    def test_init_zone_from_env(self, mock_ensure):
        """Test zone initialization from environment variable."""
        search = BrightDataSearch()
        assert search.zone == "env_zone"

    def test_init_without_token_creates_unconfigured_instance(self):
        """Test that initialization without token creates an unconfigured instance."""
        with patch.dict("os.environ", {}, clear=True):
            search = BrightDataSearch()
            assert search.api_key_parser.key_count == 0
            assert not search.is_configured()

    @patch(
        "toolregistry_hub.websearch.websearch_brightdata.BrightDataSearch._ensure_zone_exists_for_all_keys"
    )
    def test_headers_property(self, mock_ensure):
        """Test headers property."""
        search = BrightDataSearch(api_keys="test_token")
        headers = search._headers

        assert headers["Authorization"] == "Bearer test_token"
        assert headers["Content-Type"] == "application/json"
        assert headers["Accept"] == "application/json"

    @patch(
        "toolregistry_hub.websearch.websearch_brightdata.BrightDataSearch._ensure_zone_exists_for_all_keys"
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
        search = BrightDataSearch(api_keys="test_token")
        results = search.search("test query", max_results=5)

        # Assertions
        assert len(results) == 2
        assert isinstance(results[0], SearchResult)
        assert results[0].title == "Test Result 1"
        assert results[0].url == "https://example1.com"
        assert results[0].content == "Description 1"
        assert results[1].title == "Test Result 2"

    @patch(
        "toolregistry_hub.websearch.websearch_brightdata.BrightDataSearch._ensure_zone_exists_for_all_keys"
    )
    @patch("httpx.Client")
    def test_search_with_pagination(self, mock_client, mock_ensure):
        """Test search with pagination cursor."""
        mock_response = MagicMock()
        mock_response.text = json.dumps({"organic": []})
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value = mock_client_instance

        search = BrightDataSearch(api_keys="test_token")
        search.search("test query", cursor="2")

        # Verify the URL contains correct start parameter
        call_args = mock_client_instance.post.call_args
        payload = call_args[1]["json"]
        assert "start=20" in payload["url"]  # Page 2 = start at 20

    @patch(
        "toolregistry_hub.websearch.websearch_brightdata.BrightDataSearch._ensure_zone_exists_for_all_keys"
    )
    @patch("httpx.Client")
    def test_search_empty_query(self, mock_client, mock_ensure):
        """Test search with empty query."""
        search = BrightDataSearch(api_keys="test_token")
        results = search.search("")

        assert results == []
        mock_client.assert_not_called()

    @patch(
        "toolregistry_hub.websearch.websearch_brightdata.BrightDataSearch._ensure_zone_exists_for_all_keys"
    )
    @patch("httpx.Client")
    def test_search_timeout_error(self, mock_client, mock_ensure):
        """Test search with timeout error."""
        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.post.side_effect = httpx.TimeoutException("Timeout")
        mock_client.return_value = mock_client_instance

        search = BrightDataSearch(api_keys="test_token")
        results = search.search("test query")

        assert results == []

    @patch(
        "toolregistry_hub.websearch.websearch_brightdata.BrightDataSearch._ensure_zone_exists_for_all_keys"
    )
    @patch("httpx.Client")
    def test_search_http_401_error(self, mock_client, mock_ensure):
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

        search = BrightDataSearch(api_keys="invalid_token")
        results = search.search("test query")

        assert results == []

    @patch(
        "toolregistry_hub.websearch.websearch_brightdata.BrightDataSearch._ensure_zone_exists_for_all_keys"
    )
    @patch("httpx.Client")
    def test_search_http_422_error(self, mock_client, mock_ensure):
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

        search = BrightDataSearch(api_keys="test_token", zone="invalid_zone")
        results = search.search("test query")

        assert results == []

    @patch(
        "toolregistry_hub.websearch.websearch_brightdata.BrightDataSearch._ensure_zone_exists_for_all_keys"
    )
    @patch("httpx.Client")
    def test_search_http_429_error(self, mock_client, mock_ensure):
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

        search = BrightDataSearch(api_keys="test_token")
        results = search.search("test query")

        assert results == []

    @patch(
        "toolregistry_hub.websearch.websearch_brightdata.BrightDataSearch._ensure_zone_exists_for_all_keys"
    )
    @patch("httpx.Client")
    def test_search_json_decode_error(self, mock_client, mock_ensure):
        """Test search with invalid JSON response."""
        mock_response = MagicMock()
        mock_response.text = "Invalid JSON"
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value = mock_client_instance

        search = BrightDataSearch(api_keys="test_token")
        results = search.search("test query")

        assert results == []

    @patch(
        "toolregistry_hub.websearch.websearch_brightdata.BrightDataSearch._ensure_zone_exists_for_all_keys"
    )
    def test_parse_results(self, mock_ensure):
        """Test parsing of API results."""
        search = BrightDataSearch(api_keys="test_token")

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
        assert results[0].score == 0.95  # Position-based scoring: 1.0 - (1 * 0.05)

    @patch(
        "toolregistry_hub.websearch.websearch_brightdata.BrightDataSearch._ensure_zone_exists_for_all_keys"
    )
    def test_parse_results_empty(self, mock_ensure):
        """Test parsing of empty results."""
        search = BrightDataSearch(api_keys="test_token")
        results = search._parse_results({"organic": []})

        assert results == []

    @patch(
        "toolregistry_hub.websearch.websearch_brightdata.BrightDataSearch._ensure_zone_exists_for_all_keys"
    )
    def test_parse_results_missing_fields(self, mock_ensure):
        """Test parsing results with missing fields."""
        search = BrightDataSearch(api_keys="test_token")

        raw_results = {
            "organic": [
                {"url": "https://example.com"},  # Missing title and description
            ]
        }

        results = search._parse_results(raw_results)

        assert len(results) == 1
        assert results[0].title == "No title"
        assert results[0].url == "https://example.com"
        assert results[0].content == "No description available"

    @patch(
        "toolregistry_hub.websearch.websearch_brightdata.BrightDataSearch._ensure_zone_exists_for_all_keys"
    )
    @patch("httpx.Client")
    def test_search_max_results_pagination(self, mock_client, mock_ensure):
        """Test search with max_results > 20 triggers pagination."""
        mock_response = MagicMock()
        mock_response.text = json.dumps({"organic": []})
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value = mock_client_instance

        search = BrightDataSearch(api_keys="test_token")
        search.search("test query", max_results=45)

        # Should make 3 calls (45 / 20 = 2.25, rounded up to 3)
        assert mock_client_instance.post.call_count == 3

    @patch(
        "toolregistry_hub.websearch.websearch_brightdata.BrightDataSearch._ensure_zone_exists_for_all_keys"
    )
    @patch("httpx.Client")
    def test_search_max_results_cap(self, mock_client, mock_ensure):
        """Test that max_results is capped at 180."""
        mock_response = MagicMock()
        mock_response.text = json.dumps({"organic": []})
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value = mock_client_instance

        search = BrightDataSearch(api_keys="test_token")
        search.search("test query", max_results=200)

        # Should make 9 calls (180 / 20 = 9)
        assert mock_client_instance.post.call_count == 9
