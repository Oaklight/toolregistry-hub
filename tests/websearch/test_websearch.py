"""Unit tests for WebSearch base module (BaseSearch and SearchResult)."""

from typing import Any
from unittest.mock import patch

import pytest

from toolregistry_hub.websearch.base import BaseSearch
from toolregistry_hub.websearch.search_result import SearchResult


class TestSearchResult:
    """Test cases for SearchResult dataclass."""

    def test_create_result(self):
        """Test creating a search result."""
        result = SearchResult(
            title="Example Title",
            url="https://example.com",
            content="Example content",
        )

        assert result.title == "Example Title"
        assert result.url == "https://example.com"
        assert result.content == "Example content"
        assert result.score == 1.0  # Default score

    def test_create_result_with_score(self):
        """Test creating a search result with custom score."""
        result = SearchResult(
            title="Title",
            url="https://example.com",
            content="Content",
            score=0.75,
        )

        assert result.score == 0.75

    def test_get_method(self):
        """Test dict-like get method."""
        result = SearchResult(
            title="Title",
            url="https://example.com",
            content="Content",
        )

        assert result.get("title") == "Title"
        assert result.get("url") == "https://example.com"
        assert result.get("content") == "Content"
        assert result.get("score") == 1.0

    def test_get_method_default(self):
        """Test get method with default value for missing attribute."""
        result = SearchResult(
            title="Title",
            url="https://example.com",
            content="Content",
        )

        assert result.get("nonexistent") is None
        assert result.get("nonexistent", "default") == "default"


class ConcreteSearch(BaseSearch):
    """Concrete implementation for testing abstract base class."""

    @property
    def _headers(self) -> dict:
        return {"User-Agent": "test"}

    def search(
        self, query: str, *, max_results: int = 5, timeout: float = 10.0, **kwargs
    ) -> list[SearchResult]:
        return self._search_impl(query, **kwargs)[:max_results]

    def _parse_results(self, raw_results: Any) -> list[SearchResult]:
        return [
            SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                content=item.get("content", ""),
            )
            for item in raw_results
        ]

    def _search_impl(self, query: str, **kwargs) -> list[SearchResult]:
        return [
            SearchResult(
                title="Result 1",
                url="https://example1.com",
                content="Content 1",
            ),
            SearchResult(
                title="Result 2",
                url="https://example2.com",
                content="Content 2",
            ),
        ]


class TestBaseSearch:
    """Test cases for BaseSearch abstract base class."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that abstract base class cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseSearch()

    def test_concrete_implementation(self):
        """Test concrete implementation of abstract class."""
        searcher = ConcreteSearch()
        results = searcher.search("test query")

        assert len(results) == 2
        assert results[0].url == "https://example1.com"
        assert results[1].title == "Result 2"

    def test_concrete_max_results(self):
        """Test that max_results is respected."""
        searcher = ConcreteSearch()
        results = searcher.search("test query", max_results=1)

        assert len(results) == 1

    @patch("toolregistry_hub.websearch.base.Fetch.fetch_content")
    def test_fetch_webpage_content_success(self, mock_fetch):
        """Test successful webpage content fetching."""
        mock_fetch.return_value = "Fetched webpage content"

        entry = SearchResult(
            title="Example Title",
            url="https://example.com",
            content="Example excerpt",
        )

        result = BaseSearch._fetch_webpage_content(entry)

        assert result["title"] == "Example Title"
        assert result["url"] == "https://example.com"
        assert result["content"] == "Fetched webpage content"
        assert result["excerpt"] == "Example excerpt"

        mock_fetch.assert_called_once()

    @patch("toolregistry_hub.websearch.base.Fetch.fetch_content")
    def test_fetch_webpage_content_failure(self, mock_fetch):
        """Test webpage content fetching failure."""
        mock_fetch.side_effect = Exception("Network error")

        entry = SearchResult(
            title="Example Title",
            url="https://example.com",
            content="Example excerpt",
        )

        result = BaseSearch._fetch_webpage_content(entry)

        assert result["title"] == "Example Title"
        assert result["url"] == "https://example.com"
        assert result["content"] == "Unable to fetch content"
        assert result["excerpt"] == "Example excerpt"

    def test_fetch_webpage_content_missing_url(self):
        """Test webpage content fetching with missing URL."""
        entry = SearchResult(
            title="Title",
            url="",
            content="Content",
        )

        with pytest.raises(ValueError, match="Result missing URL"):
            BaseSearch._fetch_webpage_content(entry)

    @patch("toolregistry_hub.websearch.base.Fetch.fetch_content")
    def test_fetch_webpage_content_with_timeout(self, mock_fetch):
        """Test webpage content fetching with custom timeout."""
        mock_fetch.return_value = "Content"

        entry = SearchResult(
            title="Title",
            url="https://example.com",
            content="Excerpt",
        )

        BaseSearch._fetch_webpage_content(entry, timeout=30)

        mock_fetch.assert_called_once_with(
            "https://example.com", timeout=30, proxy=None
        )

    @patch("toolregistry_hub.websearch.base.Fetch.fetch_content")
    def test_fetch_webpage_content_with_proxy(self, mock_fetch):
        """Test webpage content fetching with proxy."""
        mock_fetch.return_value = "Content"

        entry = SearchResult(
            title="Title",
            url="https://example.com",
            content="Excerpt",
        )

        BaseSearch._fetch_webpage_content(
            entry, timeout=10, proxy="http://proxy.example.com:8080"
        )

        mock_fetch.assert_called_once_with(
            "https://example.com", timeout=10, proxy="http://proxy.example.com:8080"
        )


class TestWebSearchIntegration:
    """Integration tests for WebSearch functionality."""

    def test_search_method_signature(self):
        """Test that search method has correct signature."""
        searcher = ConcreteSearch()

        results = searcher.search(query="test", max_results=3, timeout=15)

        assert isinstance(results, list)
        assert len(results) == 2  # Based on our mock implementation

    def test_search_method_defaults(self):
        """Test search method with default parameters."""
        searcher = ConcreteSearch()

        results = searcher.search("test query")

        assert isinstance(results, list)
        assert len(results) == 2

    def test_headers_property(self):
        """Test that headers property works."""
        searcher = ConcreteSearch()
        headers = searcher._headers

        assert isinstance(headers, dict)
        assert "User-Agent" in headers
