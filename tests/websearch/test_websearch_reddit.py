"""Unit tests for Reddit Search (Arctic Shift) module."""

from unittest.mock import MagicMock, patch

import pytest

from toolregistry_hub._vendor.httpclient import HTTPError, HttpTimeoutError
from toolregistry_hub.websearch.base import SearchBackendError
from toolregistry_hub.websearch.search_result import SearchResult
from toolregistry_hub.websearch.websearch_reddit import RedditSearch

SAMPLE_REDDIT_RESPONSE = {
    "data": [
        {
            "title": "Best web scraping libraries in 2026?",
            "permalink": "/r/Python/comments/abc123/best_web_scraping_libraries/",
            "selftext": "Looking for recommendations on web scraping libraries.",
            "subreddit": "Python",
            "author": "dev_user",
            "score": 42,
            "num_comments": 15,
            "url": "https://www.reddit.com/r/Python/comments/abc123/best_web_scraping_libraries/",
            "created_utc": 1700000000,
        },
        {
            "title": "Scrapy vs Beautiful Soup",
            "permalink": "/r/Python/comments/def456/scrapy_vs_beautiful_soup/",
            "selftext": "What are the pros and cons of each?",
            "subreddit": "Python",
            "author": "another_dev",
            "score": 87,
            "num_comments": 32,
            "url": "https://www.reddit.com/r/Python/comments/def456/scrapy_vs_beautiful_soup/",
            "created_utc": 1700100000,
        },
    ]
}


class TestRedditSearch:
    """Test cases for RedditSearch initialization and configuration."""

    def test_init_defaults(self):
        with patch.dict("os.environ", {}, clear=True):
            search = RedditSearch()
            assert search.base_url == "https://arctic-shift.photon-reddit.com"
            assert search._is_configured() is True

    def test_init_with_custom_base_url(self):
        search = RedditSearch(base_url="https://custom.example.com")
        assert search.base_url == "https://custom.example.com"

    def test_init_strips_trailing_slash(self):
        search = RedditSearch(base_url="https://custom.example.com/")
        assert search.base_url == "https://custom.example.com"

    @patch.dict("os.environ", {"ARCTIC_SHIFT_URL": "https://env.example.com"})
    def test_init_from_env(self):
        search = RedditSearch()
        assert search.base_url == "https://env.example.com"

    def test_init_explicit_overrides_env(self):
        with patch.dict("os.environ", {"ARCTIC_SHIFT_URL": "https://env.example.com"}):
            search = RedditSearch(base_url="https://explicit.example.com")
            assert search.base_url == "https://explicit.example.com"

    def test_is_configured_always_true(self):
        with patch.dict("os.environ", {}, clear=True):
            search = RedditSearch()
            assert search._is_configured() is True

    def test_build_headers(self):
        search = RedditSearch()
        headers = search._build_headers()
        assert headers["Accept"] == "application/json"
        assert "User-Agent" in headers

    def test_build_headers_ignores_api_key(self):
        search = RedditSearch()
        headers = search._build_headers(api_key="ignored")
        assert "Authorization" not in headers


class TestExtractSubreddit:
    """Test subreddit parsing from query strings."""

    def test_r_slash_prefix(self):
        cleaned, sub = RedditSearch._extract_subreddit("r/python web scraping")
        assert cleaned == "web scraping"
        assert sub == "python"

    def test_slash_r_slash_prefix(self):
        cleaned, sub = RedditSearch._extract_subreddit("/r/python web scraping")
        assert cleaned == "web scraping"
        assert sub == "python"

    def test_subreddit_colon_prefix(self):
        cleaned, sub = RedditSearch._extract_subreddit("subreddit:python web scraping")
        assert cleaned == "web scraping"
        assert sub == "python"

    def test_mid_query(self):
        cleaned, sub = RedditSearch._extract_subreddit(
            "web scraping r/python tutorials"
        )
        assert cleaned == "web scraping tutorials"
        assert sub == "python"

    def test_no_subreddit(self):
        cleaned, sub = RedditSearch._extract_subreddit("web scraping")
        assert cleaned == "web scraping"
        assert sub is None

    def test_case_insensitive(self):
        cleaned, sub = RedditSearch._extract_subreddit("R/Python query")
        assert sub == "Python"
        assert cleaned == "query"

    def test_subreddit_only(self):
        cleaned, sub = RedditSearch._extract_subreddit("r/python")
        assert sub == "python"
        assert cleaned == ""

    def test_no_partial_match(self):
        """Should not match 'r/' inside a word like 'error/python'."""
        cleaned, sub = RedditSearch._extract_subreddit("error/python web")
        assert sub is None
        assert cleaned == "error/python web"


def _mock_client(response_data, *, side_effect=None):
    """Helper to set up a mocked HTTP Client context manager."""
    mock_response = MagicMock()
    mock_response.json.return_value = response_data
    mock_response.raise_for_status = MagicMock()

    mock_instance = MagicMock()
    mock_instance.__enter__.return_value = mock_instance
    mock_instance.__exit__.return_value = None
    if side_effect:
        mock_instance.get.side_effect = side_effect
    else:
        mock_instance.get.return_value = mock_response

    mock_cls = MagicMock(return_value=mock_instance)
    return mock_cls, mock_instance


class TestRedditSearchSearch:
    """Test the search() method."""

    @patch("toolregistry_hub.websearch.websearch_reddit.Client")
    def test_search_success(self, mock_client_cls):
        mock_cls, mock_instance = _mock_client(SAMPLE_REDDIT_RESPONSE)
        mock_client_cls.return_value = mock_cls.return_value

        search = RedditSearch()
        results = search.search("r/python web scraping", max_results=5)

        assert len(results) == 2
        assert isinstance(results[0], SearchResult)
        assert results[0].title == "Best web scraping libraries in 2026?"
        assert "reddit.com" in results[0].url
        assert "r/Python" in results[0].content

    def test_search_empty_query(self):
        search = RedditSearch()
        assert search.search("") == []
        assert search.search("   ") == []

    def test_search_no_subreddit_returns_empty(self):
        search = RedditSearch()
        results = search.search("web scraping")
        assert results == []

    @patch("toolregistry_hub.websearch.websearch_reddit.Client")
    def test_search_kwargs_subreddit(self, mock_client_cls):
        mock_cls, mock_instance = _mock_client(SAMPLE_REDDIT_RESPONSE)
        mock_client_cls.return_value = mock_cls.return_value

        search = RedditSearch()
        results = search.search("web scraping", subreddit="python")

        assert len(results) == 2
        call_args = mock_instance.get.call_args
        params = call_args[1]["params"]
        assert params["subreddit"] == "python"

    @patch("toolregistry_hub.websearch.websearch_reddit.Client")
    def test_search_parses_subreddit_from_query(self, mock_client_cls):
        mock_cls, mock_instance = _mock_client(SAMPLE_REDDIT_RESPONSE)
        mock_client_cls.return_value = mock_cls.return_value

        search = RedditSearch()
        search.search("r/python web scraping")

        call_args = mock_instance.get.call_args
        params = call_args[1]["params"]
        assert params["subreddit"] == "python"
        assert params["query"] == "web scraping"

    @patch("toolregistry_hub.websearch.websearch_reddit.Client")
    def test_search_kwargs_subreddit_overrides_parsed(self, mock_client_cls):
        mock_cls, mock_instance = _mock_client(SAMPLE_REDDIT_RESPONSE)
        mock_client_cls.return_value = mock_cls.return_value

        search = RedditSearch()
        search.search("r/javascript web scraping", subreddit="python")

        call_args = mock_instance.get.call_args
        params = call_args[1]["params"]
        assert params["subreddit"] == "python"

    @patch("toolregistry_hub.websearch.websearch_reddit.Client")
    def test_search_with_author(self, mock_client_cls):
        """Author alone satisfies the scope requirement."""
        mock_cls, mock_instance = _mock_client(SAMPLE_REDDIT_RESPONSE)
        mock_client_cls.return_value = mock_cls.return_value

        search = RedditSearch()
        results = search.search("web scraping", author="dev_user")

        assert len(results) == 2
        call_args = mock_instance.get.call_args
        params = call_args[1]["params"]
        assert params["author"] == "dev_user"

    @patch("toolregistry_hub.websearch.websearch_reddit.Client")
    def test_search_timeout_error(self, mock_client_cls):
        mock_cls, mock_instance = _mock_client(
            None, side_effect=HttpTimeoutError("Timeout")
        )
        mock_client_cls.return_value = mock_cls.return_value

        search = RedditSearch()
        results = search.search("r/python web scraping")

        assert results == []

    @patch("toolregistry_hub.websearch.websearch_reddit.Client")
    def test_search_http_429_error(self, mock_client_cls):
        mock_cls, mock_instance = _mock_client(
            None,
            side_effect=HTTPError(
                429, "Rate limit", "https://arctic-shift.photon-reddit.com"
            ),
        )
        mock_client_cls.return_value = mock_cls.return_value

        search = RedditSearch()
        with pytest.raises(SearchBackendError, match="429"):
            search.search("r/python web scraping")

    @patch("toolregistry_hub.websearch.websearch_reddit.Client")
    def test_search_http_500_error(self, mock_client_cls):
        mock_cls, mock_instance = _mock_client(
            None,
            side_effect=HTTPError(
                500, "Server error", "https://arctic-shift.photon-reddit.com"
            ),
        )
        mock_client_cls.return_value = mock_cls.return_value

        search = RedditSearch()
        with pytest.raises(SearchBackendError, match="500"):
            search.search("r/python web scraping")

    @patch("toolregistry_hub.websearch.websearch_reddit.Client")
    def test_search_max_results_cap(self, mock_client_cls):
        mock_cls, mock_instance = _mock_client(SAMPLE_REDDIT_RESPONSE)
        mock_client_cls.return_value = mock_cls.return_value

        search = RedditSearch()
        search.search("r/python test", max_results=200)

        call_args = mock_instance.get.call_args
        params = call_args[1]["params"]
        assert params["limit"] == 100

    @patch("toolregistry_hub.websearch.websearch_reddit.Client")
    def test_search_forwards_optional_params(self, mock_client_cls):
        mock_cls, mock_instance = _mock_client(SAMPLE_REDDIT_RESPONSE)
        mock_client_cls.return_value = mock_cls.return_value

        search = RedditSearch()
        search.search("r/python test", after="7d", before="1d", sort="asc")

        call_args = mock_instance.get.call_args
        params = call_args[1]["params"]
        assert params["after"] == "7d"
        assert params["before"] == "1d"
        assert params["sort"] == "asc"

    @patch("toolregistry_hub.websearch.websearch_reddit.Client")
    def test_search_uses_get(self, mock_client_cls):
        mock_cls, mock_instance = _mock_client(SAMPLE_REDDIT_RESPONSE)
        mock_client_cls.return_value = mock_cls.return_value

        search = RedditSearch()
        search.search("r/python test")

        mock_instance.get.assert_called_once()
        call_args = mock_instance.get.call_args
        assert "/api/posts/search" in call_args[0][0]


class TestRedditParseResults:
    """Test _parse_results method."""

    def test_basic(self):
        search = RedditSearch()
        results = search._parse_results(SAMPLE_REDDIT_RESPONSE)

        assert len(results) == 2
        assert results[0].title == "Best web scraping libraries in 2026?"
        assert (
            results[0].url
            == "https://www.reddit.com/r/Python/comments/abc123/best_web_scraping_libraries/"
        )
        assert "Looking for recommendations" in results[0].content
        assert "r/Python" in results[0].content
        assert "u/dev_user" in results[0].content
        assert "Score: 42" in results[0].content
        assert "15 comments" in results[0].content

    def test_empty_data(self):
        search = RedditSearch()
        assert search._parse_results({"data": []}) == []

    def test_null_data(self):
        search = RedditSearch()
        assert search._parse_results({"data": None}) == []

    def test_missing_data_key(self):
        search = RedditSearch()
        assert search._parse_results({}) == []

    def test_removed_selftext(self):
        search = RedditSearch()
        raw = {
            "data": [
                {
                    "title": "Removed post",
                    "permalink": "/r/test/comments/xyz/removed/",
                    "selftext": "[removed]",
                    "subreddit": "test",
                    "author": "user",
                    "score": 10,
                    "num_comments": 5,
                }
            ]
        }
        results = search._parse_results(raw)
        assert len(results) == 1
        assert "Removed post" in results[0].content
        assert "[removed]" not in results[0].content

    def test_deleted_selftext(self):
        search = RedditSearch()
        raw = {
            "data": [
                {
                    "title": "Deleted post",
                    "permalink": "/r/test/comments/xyz/deleted/",
                    "selftext": "[deleted]",
                    "subreddit": "test",
                    "author": "user",
                }
            ]
        }
        results = search._parse_results(raw)
        assert "[deleted]" not in results[0].content

    def test_missing_fields(self):
        search = RedditSearch()
        raw = {"data": [{"title": "Minimal post"}]}
        results = search._parse_results(raw)

        assert len(results) == 1
        assert results[0].title == "Minimal post"
        assert results[0].url == ""

    def test_url_from_permalink(self):
        search = RedditSearch()
        raw = {
            "data": [
                {
                    "title": "Test",
                    "permalink": "/r/test/comments/abc/test/",
                }
            ]
        }
        results = search._parse_results(raw)
        assert results[0].url == "https://www.reddit.com/r/test/comments/abc/test/"

    def test_long_selftext_truncated(self):
        search = RedditSearch()
        long_text = "x" * 1000
        raw = {
            "data": [
                {
                    "title": "Long post",
                    "permalink": "/r/test/comments/abc/long/",
                    "selftext": long_text,
                    "subreddit": "test",
                }
            ]
        }
        results = search._parse_results(raw)
        assert len(results[0].content) < 1000
        assert "…" in results[0].content

    def test_score_is_default(self):
        search = RedditSearch()
        results = search._parse_results(SAMPLE_REDDIT_RESPONSE)
        assert results[0].score == 1.0
