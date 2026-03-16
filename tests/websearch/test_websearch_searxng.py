"""Unit tests for SearXNGSearch module."""

from unittest.mock import MagicMock, patch

import httpx

from toolregistry_hub.websearch.search_result import SearchResult
from toolregistry_hub.websearch.websearch_searxng import SearXNGSearch


class TestSearXNGSearch:
    """Test cases for SearXNGSearch class."""

    def test_init_with_base_url(self):
        """Test SearXNGSearch initialization with base URL."""
        searcher = SearXNGSearch("http://localhost:8080")

        assert searcher.base_url == "http://localhost:8080"
        assert searcher.search_url == "http://localhost:8080/search"

    def test_init_with_trailing_slash(self):
        """Test initialization with trailing slash in base URL."""
        searcher = SearXNGSearch("http://localhost:8080/")

        assert searcher.base_url == "http://localhost:8080"
        assert searcher.search_url == "http://localhost:8080/search"

    def test_init_with_search_path(self):
        """Test initialization when base URL already has /search path."""
        searcher = SearXNGSearch("http://localhost:8080/search")

        assert searcher.search_url == "http://localhost:8080/search"

    @patch.dict("os.environ", {"SEARXNG_URL": "http://env-searxng:8080"})
    def test_init_from_env(self):
        """Test initialization from environment variable."""
        searcher = SearXNGSearch()

        assert searcher.base_url == "http://env-searxng:8080"

    def test_init_without_url_creates_unconfigured_instance(self):
        """Test that initialization without URL creates an unconfigured instance."""
        with patch.dict("os.environ", {}, clear=True):
            searcher = SearXNGSearch()
            assert searcher.search_url is None
            assert not searcher._is_configured()

    def test_headers_property(self):
        """Test headers property."""
        searcher = SearXNGSearch("http://localhost:8080")
        headers = searcher._headers

        assert "User-Agent" in headers
        assert headers["Accept"] == "application/json"

    @patch("httpx.Client")
    def test_search_success(self, mock_client):
        """Test successful search operation."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {
                    "url": "https://example1.com",
                    "title": "Title 1",
                    "content": "Content 1",
                    "score": 0.8,
                },
                {
                    "url": "https://example2.com",
                    "title": "Title 2",
                    "content": "Content 2",
                    "score": 0.6,
                },
            ]
        }
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value = mock_client_instance

        searcher = SearXNGSearch("http://localhost:8080")
        results = searcher.search("test query", max_results=2)

        assert len(results) == 2
        assert isinstance(results[0], SearchResult)
        # Results should be sorted by score descending
        assert results[0].score == 0.8
        assert results[1].score == 0.6

    @patch("httpx.Client")
    def test_search_empty_query(self, mock_client):
        """Test search with empty query."""
        searcher = SearXNGSearch("http://localhost:8080")
        results = searcher.search("")

        assert results == []

    @patch("httpx.Client")
    def test_search_timeout_error(self, mock_client):
        """Test search with timeout error."""
        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.get.side_effect = httpx.TimeoutException("Timeout")
        mock_client.return_value = mock_client_instance

        searcher = SearXNGSearch("http://localhost:8080")
        results = searcher.search("test query")

        assert results == []

    @patch("httpx.Client")
    def test_search_http_error(self, mock_client):
        """Test search with HTTP error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.get.side_effect = httpx.HTTPStatusError(
            "Internal Server Error",
            request=MagicMock(),
            response=mock_response,
        )
        mock_client.return_value = mock_client_instance

        searcher = SearXNGSearch("http://localhost:8080")
        results = searcher.search("test query")

        assert results == []

    @patch("httpx.Client")
    def test_search_max_results_cap(self, mock_client):
        """Test that max_results exceeding 50 is capped."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"results": []}
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value = mock_client_instance

        searcher = SearXNGSearch("http://localhost:8080")
        # Should not raise, max_results is capped internally
        results = searcher.search("test query", max_results=100)

        assert results == []

    def test_parse_results(self):
        """Test parsing of SearXNG API results."""
        searcher = SearXNGSearch("http://localhost:8080")

        raw_results = {
            "results": [
                {
                    "title": "Result 1",
                    "url": "https://example1.com",
                    "content": "Description 1",
                    "score": 0.9,
                },
                {
                    "title": "Result 2",
                    "url": "https://example2.com",
                    "content": "Description 2",
                    "score": 0.5,
                },
            ]
        }

        results = searcher._parse_results(raw_results)

        assert len(results) == 2
        assert results[0].title == "Result 1"
        assert results[0].url == "https://example1.com"
        assert results[0].content == "Description 1"
        assert results[0].score == 0.9

    def test_parse_results_empty(self):
        """Test parsing of empty results."""
        searcher = SearXNGSearch("http://localhost:8080")
        results = searcher._parse_results({"results": []})

        assert results == []

    def test_parse_results_missing_fields(self):
        """Test parsing results with missing fields."""
        searcher = SearXNGSearch("http://localhost:8080")

        raw_results = {
            "results": [
                {"url": "https://example.com"},  # Missing title and content
            ]
        }

        results = searcher._parse_results(raw_results)

        assert len(results) == 1
        assert results[0].title == "No title"
        assert results[0].url == "https://example.com"
        assert results[0].content == "No content available"

    def test_parse_results_no_results_key(self):
        """Test parsing when response has no 'results' key."""
        searcher = SearXNGSearch("http://localhost:8080")
        results = searcher._parse_results({"error": "No results found"})

        assert results == []


class TestSearXNGSearchIntegration:
    """Integration tests for SearXNGSearch."""

    def test_search_method_signature(self):
        """Test search method accepts all expected parameters."""
        searcher = SearXNGSearch("http://localhost:8080")

        with patch("httpx.Client") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {"results": []}
            mock_response.raise_for_status = MagicMock()

            mock_client_instance = MagicMock()
            mock_client_instance.__enter__.return_value = mock_client_instance
            mock_client_instance.__exit__.return_value = None
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value = mock_client_instance

            searcher.search(query="test", max_results=5, timeout=10)

            assert mock_client_instance.get.called

    def test_url_normalization(self):
        """Test that base URL is properly normalized."""
        searcher1 = SearXNGSearch("http://localhost:8080/")
        searcher2 = SearXNGSearch("http://localhost:8080")

        assert searcher1.search_url == searcher2.search_url
        assert searcher1.search_url == "http://localhost:8080/search"

    @patch("httpx.Client")
    def test_score_sorting(self, mock_client):
        """Test that results are properly sorted by score."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {
                    "url": "https://low.com",
                    "title": "Low",
                    "content": "c",
                    "score": 0.3,
                },
                {
                    "url": "https://high.com",
                    "title": "High",
                    "content": "c",
                    "score": 0.9,
                },
                {
                    "url": "https://medium.com",
                    "title": "Medium",
                    "content": "c",
                    "score": 0.6,
                },
            ]
        }
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value = mock_client_instance

        searcher = SearXNGSearch("http://localhost:8080")
        results = searcher.search("test query", max_results=3)

        # Should be sorted by score in descending order
        assert results[0].score == 0.9
        assert results[1].score == 0.6
        assert results[2].score == 0.3
