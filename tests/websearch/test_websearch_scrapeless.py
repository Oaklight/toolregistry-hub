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
        search = ScrapelessSearch(api_key="test_key_123")
        assert search.api_key == "test_key_123"
        assert search.base_url == "https://api.scrapeless.com"

    def test_init_with_custom_base_url(self):
        """Test initialization with custom base URL."""
        search = ScrapelessSearch(api_key="test_key", base_url="https://custom.api.com")
        assert search.base_url == "https://custom.api.com"

    @patch.dict("os.environ", {"SCRAPELESS_API_KEY": "env_key"})
    def test_init_from_env(self):
        """Test initialization from environment variable."""
        search = ScrapelessSearch()
        assert search.api_key == "env_key"

    def test_init_without_key_raises_error(self):
        """Test that initialization without API key raises ValueError."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="API key is required"):
                ScrapelessSearch()

    def test_headers_property(self):
        """Test headers property."""
        search = ScrapelessSearch(api_key="test_key")
        headers = search._headers

        assert headers["Content-Type"] == "application/json"
        assert headers["X-API-Key"] == "test_key"

    @patch("httpx.Client")
    def test_search_basic_google(self, mock_client):
        """Test basic Google search functionality."""
        # Mock HTML response
        mock_html = """
        <html>
            <div class="g">
                <h3>Test Result 1</h3>
                <a href="https://example1.com">Link 1</a>
                <div class="VwiC3b">Description 1</div>
            </div>
            <div class="g">
                <h3>Test Result 2</h3>
                <a href="https://example2.com">Link 2</a>
                <div class="VwiC3b">Description 2</div>
            </div>
        </html>
        """

        mock_response = MagicMock()
        mock_response.text = mock_html
        mock_response.raise_for_status = MagicMock()

        # Setup mock client
        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value = mock_client_instance

        # Perform search
        search = ScrapelessSearch(api_key="test_key")
        results = search.search("test query", max_results=5, engine="google")

        # Assertions
        assert len(results) == 2
        assert isinstance(results[0], SearchResult)
        assert results[0].title == "Test Result 1"
        assert results[0].url == "https://example1.com"
        assert results[0].content == "Description 1"

    @patch("httpx.Client")
    def test_search_empty_query(self, mock_client):
        """Test search with empty query."""
        search = ScrapelessSearch(api_key="test_key")
        results = search.search("")

        assert results == []
        mock_client.assert_not_called()

    @patch("httpx.Client")
    def test_search_unsupported_engine(self, mock_client):
        """Test search with unsupported engine falls back to Google."""
        mock_html = "<html><div class='g'><h3>Test</h3><a href='https://example.com'>Link</a></div></html>"
        mock_response = MagicMock()
        mock_response.text = mock_html
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value = mock_client_instance

        search = ScrapelessSearch(api_key="test_key")
        results = search.search("test query", engine="unsupported")

        # Should fall back to Google
        call_args = mock_client_instance.post.call_args
        payload = call_args[1]["json"]
        assert "google.com" in payload["input"]["url"]

    @patch("httpx.Client")
    def test_search_timeout_error(self, mock_client):
        """Test search with timeout error."""
        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.post.side_effect = httpx.TimeoutException("Timeout")
        mock_client.return_value = mock_client_instance

        search = ScrapelessSearch(api_key="test_key")
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

        search = ScrapelessSearch(api_key="invalid_key")
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

        search = ScrapelessSearch(api_key="test_key")
        results = search.search("test query")

        assert results == []

    def test_parse_google_results(self):
        """Test parsing of Google search results."""
        search = ScrapelessSearch(api_key="test_key")

        html = """
        <html>
            <div class="g">
                <h3>Result 1</h3>
                <a href="https://example1.com">Link 1</a>
                <div class="VwiC3b">Description 1</div>
            </div>
            <div class="g">
                <h3>Result 2</h3>
                <a href="https://example2.com">Link 2</a>
                <div class="VwiC3b">Description 2</div>
            </div>
        </html>
        """

        results = search._parse_google_results(html)

        assert len(results) == 2
        assert results[0].title == "Result 1"
        assert results[0].url == "https://example1.com"
        assert results[0].content == "Description 1"
        assert results[1].title == "Result 2"

    def test_parse_google_results_empty(self):
        """Test parsing of empty Google results."""
        search = ScrapelessSearch(api_key="test_key")
        results = search._parse_google_results("<html></html>")

        assert results == []

    def test_parse_bing_results(self):
        """Test parsing of Bing search results."""
        search = ScrapelessSearch(api_key="test_key")

        html = """
        <html>
            <li class="b_algo">
                <h2><a href="https://example1.com">Result 1</a></h2>
                <div class="b_caption"><p>Description 1</p></div>
            </li>
            <li class="b_algo">
                <h2><a href="https://example2.com">Result 2</a></h2>
                <div class="b_caption"><p>Description 2</p></div>
            </li>
        </html>
        """

        results = search._parse_bing_results(html)

        assert len(results) == 2
        assert results[0].title == "Result 1"
        assert results[0].url == "https://example1.com"
        assert results[0].content == "Description 1"

    def test_parse_duckduckgo_results(self):
        """Test parsing of DuckDuckGo search results."""
        search = ScrapelessSearch(api_key="test_key")

        html = """
        <html>
            <article data-testid="result">
                <h2><a href="https://example1.com">Result 1</a></h2>
                <div data-result="snippet">Description 1</div>
            </article>
            <article data-testid="result">
                <h2><a href="https://example2.com">Result 2</a></h2>
                <div data-result="snippet">Description 2</div>
            </article>
        </html>
        """

        results = search._parse_duckduckgo_results(html)

        assert len(results) == 2
        assert results[0].title == "Result 1"
        assert results[0].url == "https://example1.com"
        assert results[0].content == "Description 1"

    def test_parse_baidu_results(self):
        """Test parsing of Baidu search results."""
        search = ScrapelessSearch(api_key="test_key")

        html = """
        <html>
            <div class="result">
                <h3><a href="https://example1.com">Result 1</a></h3>
                <div class="c-abstract">Description 1</div>
            </div>
            <div class="c-container">
                <h3><a href="https://example2.com">Result 2</a></h3>
                <div class="c-span">Description 2</div>
            </div>
        </html>
        """

        results = search._parse_baidu_results(html)

        assert len(results) == 2
        assert results[0].title == "Result 1"
        assert results[0].url == "https://example1.com"

    def test_parse_generic_results(self):
        """Test generic parser for unknown search engines."""
        search = ScrapelessSearch(api_key="test_key")

        html = """
        <html>
            <a href="https://example1.com">Link 1</a>
            <a href="https://example2.com">Link 2</a>
            <a href="javascript:void(0)">Invalid Link</a>
        </html>
        """

        results = search._parse_generic_results(html)

        assert len(results) >= 2
        assert all(r.url.startswith("http") for r in results)

    @patch("httpx.Client")
    def test_search_max_results_cap(self, mock_client):
        """Test that max_results is properly capped."""
        mock_html = "<html><div class='g'><h3>Test</h3><a href='https://example.com'>Link</a></div></html>"
        mock_response = MagicMock()
        mock_response.text = mock_html
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value = mock_client_instance

        search = ScrapelessSearch(api_key="test_key")
        results = search.search("test query", max_results=5)

        # Should cap results to max_results
        assert len(results) <= 5

    @patch("httpx.Client")
    def test_search_request_payload(self, mock_client):
        """Test that request payload is correctly formatted."""
        mock_html = "<html></html>"
        mock_response = MagicMock()
        mock_response.text = mock_html
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value = mock_client_instance

        search = ScrapelessSearch(api_key="test_key")
        search.search("test query", engine="google")

        # Verify payload structure
        call_args = mock_client_instance.post.call_args
        payload = call_args[1]["json"]

        assert payload["actor"] == "unlocker.webunlocker"
        assert "url" in payload["input"]
        assert "jsRender" in payload["input"]
        assert payload["input"]["jsRender"]["enabled"] is True
        assert payload["input"]["jsRender"]["headless"] is True

    def test_search_engines_available(self):
        """Test that all search engines are available."""
        search = ScrapelessSearch(api_key="test_key")

        assert "google" in search.SEARCH_ENGINES
        assert "bing" in search.SEARCH_ENGINES
        assert "duckduckgo" in search.SEARCH_ENGINES
        assert "baidu" in search.SEARCH_ENGINES
