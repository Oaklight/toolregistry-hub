"""Unit tests for Serper Search module."""

from unittest.mock import MagicMock, patch

import httpx

from toolregistry_hub.websearch.search_result import SearchResult
from toolregistry_hub.websearch.websearch_serper import SerperSearch


class TestSerperSearch:
    """Test cases for SerperSearch class."""

    def test_init_with_api_key(self):
        """Test initialization with API key."""
        search = SerperSearch(api_keys="test_key_123")
        assert search.api_key_parser.key_count == 1
        assert search.base_url == "https://google.serper.dev"

    @patch.dict("os.environ", {"SERPER_API_KEY": "env_key"})
    def test_init_from_env(self):
        """Test initialization from environment variable."""
        search = SerperSearch()
        assert search.api_key_parser.api_keys[0] == "env_key"

    def test_init_without_key_creates_unconfigured_instance(self):
        """Test that initialization without API key creates an unconfigured instance."""
        with patch.dict("os.environ", {}, clear=True):
            search = SerperSearch()
            assert search.api_key_parser.key_count == 0
            assert not search._is_configured()

    def test_headers_property(self):
        """Test headers property."""
        search = SerperSearch(api_keys="test_key")
        headers = search._headers

        assert headers["Content-Type"] == "application/json"
        assert headers["X-API-KEY"] == "test_key"

    @patch("httpx.Client")
    def test_search_basic(self, mock_client):
        """Test basic search functionality."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "organic": [
                {
                    "title": "Test Result 1",
                    "link": "https://example1.com",
                    "snippet": "Description 1",
                    "position": 1,
                },
                {
                    "title": "Test Result 2",
                    "link": "https://example2.com",
                    "snippet": "Description 2",
                    "position": 2,
                },
            ]
        }
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value = mock_client_instance

        search = SerperSearch(api_keys="test_key")
        results = search.search("test query", max_results=5)

        assert len(results) == 2
        assert isinstance(results[0], SearchResult)
        assert results[0].title == "Test Result 1"
        assert results[0].url == "https://example1.com"
        assert results[0].content == "Description 1"

    @patch("httpx.Client")
    def test_search_empty_query(self, mock_client):
        """Test search with empty query."""
        search = SerperSearch(api_keys="test_key")
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

        search = SerperSearch(api_keys="test_key")
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

        search = SerperSearch(api_keys="invalid_key")
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

        search = SerperSearch(api_keys="test_key")
        results = search.search("test query")

        assert results == []

    def test_parse_results(self):
        """Test parsing of API results."""
        search = SerperSearch(api_keys="test_key")

        raw_results = {
            "organic": [
                {
                    "title": "Result 1",
                    "link": "https://example1.com",
                    "snippet": "Description 1",
                    "position": 1,
                },
                {
                    "title": "Result 2",
                    "link": "https://example2.com",
                    "snippet": "Description 2",
                    "position": 2,
                },
            ]
        }

        results = search._parse_results(raw_results)

        assert len(results) == 2
        assert results[0].title == "Result 1"
        assert results[0].url == "https://example1.com"
        assert results[0].content == "Description 1"

    def test_parse_results_empty(self):
        """Test parsing of empty results."""
        search = SerperSearch(api_keys="test_key")
        results = search._parse_results({"organic": []})

        assert results == []

    def test_parse_results_missing_fields(self):
        """Test parsing results with missing fields."""
        search = SerperSearch(api_keys="test_key")
        raw_results = {
            "organic": [
                {
                    "title": "Result 1",
                    "link": "https://example.com",
                },
            ]
        }

        results = search._parse_results(raw_results)

        assert len(results) == 1
        assert results[0].title == "Result 1"
        assert results[0].url == "https://example.com"
        assert results[0].content == "No content available"

    @patch("httpx.Client")
    def test_search_request_payload(self, mock_client):
        """Test that request payload is correctly formatted."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"organic": []}
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value = mock_client_instance

        search = SerperSearch(api_keys="test_key")
        search.search("test query")

        call_args = mock_client_instance.post.call_args
        payload = call_args[1]["json"]

        assert payload["q"] == "test query"

    @patch("httpx.Client")
    def test_search_with_gl_and_hl(self, mock_client):
        """Test search with country and language parameters."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"organic": []}
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value = mock_client_instance

        search = SerperSearch(api_keys="test_key")
        search.search("test query", gl="cn", hl="zh")

        call_args = mock_client_instance.post.call_args
        payload = call_args[1]["json"]

        assert payload["gl"] == "cn"
        assert payload["hl"] == "zh"

    @patch("httpx.Client")
    def test_search_with_location(self, mock_client):
        """Test search with location parameter."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"organic": []}
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value = mock_client_instance

        search = SerperSearch(api_keys="test_key")
        search.search("test query", location="Austin, Texas")

        call_args = mock_client_instance.post.call_args
        payload = call_args[1]["json"]

        assert payload["location"] == "Austin, Texas"

    @patch("httpx.Client")
    def test_search_max_results_cap(self, mock_client):
        """Test that max_results is properly handled."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "organic": [
                {
                    "title": f"Result {i}",
                    "link": f"https://example{i}.com",
                    "snippet": f"Desc {i}",
                }
                for i in range(10)
            ]
        }
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value = mock_client_instance

        search = SerperSearch(api_keys="test_key")
        results = search.search("test query", max_results=3)

        assert len(results) <= 3

    @patch("httpx.Client")
    def test_search_posts_to_correct_endpoint(self, mock_client):
        """Test that the search uses POST method to the correct endpoint."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"organic": []}
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value = mock_client_instance

        search = SerperSearch(api_keys="test_key")
        search.search("test query")

        mock_client_instance.post.assert_called_once()
        call_args = mock_client_instance.post.call_args
        assert call_args[0][0] == "https://google.serper.dev/search"
