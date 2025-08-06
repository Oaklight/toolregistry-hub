"""Unit tests for WebSearch base module."""

from unittest.mock import patch

import pytest

from toolregistry_hub.websearch.websearch import (
    WebSearchGeneral,
    _WebSearchEntryGeneral,
)


class TestWebSearchEntryGeneral:
    """Test cases for _WebSearchEntryGeneral class."""

    def test_create_entry(self):
        """Test creating a search entry."""
        entry = _WebSearchEntryGeneral(
            url="https://example.com", title="Example Title", content="Example content"
        )

        assert entry["url"] == "https://example.com"
        assert entry["title"] == "Example Title"
        assert entry["content"] == "Example content"

    def test_entry_is_dict(self):
        """Test that entry behaves like a dictionary."""
        entry = _WebSearchEntryGeneral(url="https://test.com", title="Test")

        # Test dict-like access
        assert "url" in entry
        assert entry.get("title") == "Test"
        assert entry.get("nonexistent", "default") == "default"


class ConcreteWebSearch(WebSearchGeneral):
    """Concrete implementation for testing abstract base class."""

    def search(self, query, number_results=5, threshold=0.2, timeout=None):
        """Mock implementation of search method."""
        return [
            {
                "url": "https://example1.com",
                "title": "Result 1",
                "content": "Content 1",
            },
            {
                "url": "https://example2.com",
                "title": "Result 2",
                "content": "Content 2",
            },
        ]


class TestWebSearchGeneral:
    """Test cases for WebSearchGeneral abstract base class."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that abstract base class cannot be instantiated directly."""
        with pytest.raises(TypeError):
            WebSearchGeneral()

    def test_concrete_implementation(self):
        """Test concrete implementation of abstract class."""
        searcher = ConcreteWebSearch()
        results = searcher.search("test query")

        assert len(results) == 2
        assert results[0]["url"] == "https://example1.com"
        assert results[1]["title"] == "Result 2"

    @patch("toolregistry_hub.websearch.websearch.Fetch.fetch_content")
    def test_fetch_webpage_content_success(self, mock_fetch):
        """Test successful webpage content fetching."""
        mock_fetch.return_value = "Fetched webpage content"

        entry = _WebSearchEntryGeneral(
            url="https://example.com", title="Example Title", content="Example excerpt"
        )

        result = WebSearchGeneral._fetch_webpage_content(entry)

        assert result["title"] == "Example Title"
        assert result["url"] == "https://example.com"
        assert result["content"] == "Fetched webpage content"
        assert result["excerpt"] == "Example excerpt"

        mock_fetch.assert_called_once()

    @patch("toolregistry_hub.websearch.websearch.Fetch.fetch_content")
    def test_fetch_webpage_content_failure(self, mock_fetch):
        """Test webpage content fetching failure."""
        mock_fetch.side_effect = Exception("Network error")

        entry = _WebSearchEntryGeneral(
            url="https://example.com", title="Example Title", content="Example excerpt"
        )

        result = WebSearchGeneral._fetch_webpage_content(entry)

        assert result["title"] == "Example Title"
        assert result["url"] == "https://example.com"
        assert result["content"] == "Unable to fetch content"
        assert result["excerpt"] == "Example excerpt"

    def test_fetch_webpage_content_missing_url(self):
        """Test webpage content fetching with missing URL."""
        entry = _WebSearchEntryGeneral(title="Title", content="Content")

        # The implementation raises KeyError, not ValueError
        with pytest.raises(KeyError):
            WebSearchGeneral._fetch_webpage_content(entry)

    @patch("toolregistry_hub.websearch.websearch.Fetch.fetch_content")
    def test_fetch_webpage_content_with_timeout(self, mock_fetch):
        """Test webpage content fetching with custom timeout."""
        mock_fetch.return_value = "Content"

        entry = _WebSearchEntryGeneral(
            url="https://example.com", title="Title", content="Excerpt"
        )

        WebSearchGeneral._fetch_webpage_content(entry, timeout=30)

        # Verify fetch was called with the timeout
        mock_fetch.assert_called_once_with(
            "https://example.com", timeout=30, proxy=None
        )

    @patch("toolregistry_hub.websearch.websearch.Fetch.fetch_content")
    def test_fetch_webpage_content_with_proxy(self, mock_fetch):
        """Test webpage content fetching with proxy."""
        mock_fetch.return_value = "Content"

        entry = _WebSearchEntryGeneral(
            url="https://example.com", title="Title", content="Excerpt"
        )

        WebSearchGeneral._fetch_webpage_content(
            entry, timeout=10, proxy="http://proxy.example.com:8080"
        )

        # Verify fetch was called with the proxy
        mock_fetch.assert_called_once_with(
            "https://example.com", timeout=10, proxy="http://proxy.example.com:8080"
        )

    def test_fetch_webpage_content_missing_title(self):
        """Test webpage content fetching with missing title."""
        entry = _WebSearchEntryGeneral(url="https://example.com", content="Content")

        with patch(
            "toolregistry_hub.websearch.websearch.Fetch.fetch_content"
        ) as mock_fetch:
            mock_fetch.return_value = "Fetched content"
            result = WebSearchGeneral._fetch_webpage_content(entry)

            assert result["title"] == "Unable to fetch title"
            assert result["url"] == "https://example.com"
            assert result["content"] == "Fetched content"

    def test_fetch_webpage_content_missing_content(self):
        """Test webpage content fetching with missing content."""
        entry = _WebSearchEntryGeneral(url="https://example.com", title="Title")

        with patch(
            "toolregistry_hub.websearch.websearch.Fetch.fetch_content"
        ) as mock_fetch:
            mock_fetch.return_value = "Fetched content"
            result = WebSearchGeneral._fetch_webpage_content(entry)

            assert result["title"] == "Title"
            assert result["url"] == "https://example.com"
            assert result["content"] == "Fetched content"
            assert result["excerpt"] == "Unable to fetch content"


class TestWebSearchIntegration:
    """Integration tests for WebSearch functionality."""

    def test_search_method_signature(self):
        """Test that search method has correct signature."""
        searcher = ConcreteWebSearch()

        # Test with all parameters
        results = searcher.search(
            query="test", number_results=3, threshold=0.5, timeout=15
        )

        assert isinstance(results, list)
        assert len(results) == 2  # Based on our mock implementation

    def test_search_method_defaults(self):
        """Test search method with default parameters."""
        searcher = ConcreteWebSearch()

        # Test with minimal parameters
        results = searcher.search("test query")

        assert isinstance(results, list)
        assert len(results) == 2
