"""Unit tests for GitHub Search module."""

from unittest.mock import MagicMock, patch

import pytest

from toolregistry_hub._vendor.httpclient import HTTPError, HttpTimeoutError
from toolregistry_hub.websearch.base import SearchBackendError
from toolregistry_hub.websearch.search_result import SearchResult
from toolregistry_hub.websearch.websearch_github import GitHubSearch

SAMPLE_GITHUB_RESPONSE = {
    "total_count": 2,
    "incomplete_results": False,
    "items": [
        {
            "full_name": "tensorflow/tensorflow",
            "html_url": "https://github.com/tensorflow/tensorflow",
            "description": "An Open Source Machine Learning Framework",
            "stargazers_count": 180000,
            "language": "C++",
            "topics": ["machine-learning", "deep-learning", "tensorflow"],
            "updated_at": "2026-08-25T12:00:00Z",
        },
        {
            "full_name": "pytorch/pytorch",
            "html_url": "https://github.com/pytorch/pytorch",
            "description": "Tensors and Dynamic neural networks in Python",
            "stargazers_count": 75000,
            "language": "Python",
            "topics": ["pytorch", "deep-learning"],
            "updated_at": "2026-08-24T08:00:00Z",
        },
    ],
}


class TestGitHubSearch:
    """Test cases for GitHubSearch class."""

    def test_init_with_tokens(self):
        """Test initialization with explicit tokens."""
        search = GitHubSearch(api_keys="ghp_test123")
        assert search.api_key_parser.key_count == 1
        assert search.base_url == "https://api.github.com"

    @patch.dict("os.environ", {"GITHUB_TOKENS": "ghp_env_token"})
    def test_init_from_env(self):
        """Test initialization from environment variable."""
        search = GitHubSearch()
        assert search.api_key_parser.api_keys[0] == "ghp_env_token"

    def test_init_without_tokens(self):
        """Test that initialization without tokens still creates a configured instance."""
        with patch.dict("os.environ", {}, clear=True):
            search = GitHubSearch()
            assert search.api_key_parser.key_count == 0
            assert search._is_configured()

    def test_is_configured_always_true(self):
        """Test _is_configured returns True even without tokens."""
        with patch.dict("os.environ", {}, clear=True):
            search = GitHubSearch()
            assert search._is_configured() is True

    def test_is_configured_with_keys(self):
        """Test _is_configured returns True with tokens."""
        search = GitHubSearch(api_keys="ghp_test")
        assert search._is_configured() is True

    def test_build_headers_with_key(self):
        """Test _build_headers includes Authorization when key is provided."""
        search = GitHubSearch(api_keys="ghp_test")
        headers = search._build_headers("ghp_test")

        assert headers["Authorization"] == "Bearer ghp_test"
        assert headers["Accept"] == "application/vnd.github+json"
        assert headers["X-GitHub-Api-Version"] == "2022-11-28"
        assert headers["User-Agent"] == "toolregistry-hub/GitHubSearch"

    def test_build_headers_without_key(self):
        """Test _build_headers omits Authorization when no key."""
        with patch.dict("os.environ", {}, clear=True):
            search = GitHubSearch()
            headers = search._build_headers(None)

            assert "Authorization" not in headers
            assert headers["Accept"] == "application/vnd.github+json"
            assert headers["X-GitHub-Api-Version"] == "2022-11-28"
            assert "User-Agent" in headers

    @patch("toolregistry_hub.websearch.websearch_github.Client")
    def test_search_basic(self, mock_client):
        """Test basic search functionality."""
        mock_response = MagicMock()
        mock_response.json.return_value = SAMPLE_GITHUB_RESPONSE
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value = mock_client_instance

        search = GitHubSearch(api_keys="ghp_test")
        results = search.search("machine learning", max_results=5)

        assert len(results) == 2
        assert isinstance(results[0], SearchResult)
        assert results[0].title == "tensorflow/tensorflow"
        assert results[0].url == "https://github.com/tensorflow/tensorflow"
        assert "An Open Source Machine Learning Framework" in results[0].content
        assert "Stars: 180000" in results[0].content
        assert "Language: C++" in results[0].content

    @patch("toolregistry_hub.websearch.websearch_github.Client")
    def test_search_empty_query(self, mock_client):
        """Test search with empty query."""
        search = GitHubSearch(api_keys="ghp_test")
        results = search.search("")

        assert results == []
        mock_client.assert_not_called()

    @patch("toolregistry_hub.websearch.websearch_github.Client")
    def test_search_unauthenticated(self, mock_client):
        """Test search without tokens makes unauthenticated request."""
        mock_response = MagicMock()
        mock_response.json.return_value = SAMPLE_GITHUB_RESPONSE
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value = mock_client_instance

        with patch.dict("os.environ", {}, clear=True):
            search = GitHubSearch()
            results = search.search("test query")

        assert len(results) == 2
        call_args = mock_client_instance.get.call_args
        headers = call_args[1]["headers"]
        assert "Authorization" not in headers

    @patch("toolregistry_hub.websearch.websearch_github.Client")
    def test_search_authenticated(self, mock_client):
        """Test search with tokens includes Authorization header."""
        mock_response = MagicMock()
        mock_response.json.return_value = SAMPLE_GITHUB_RESPONSE
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value = mock_client_instance

        search = GitHubSearch(api_keys="ghp_test")
        search.search("test query")

        call_args = mock_client_instance.get.call_args
        headers = call_args[1]["headers"]
        assert headers["Authorization"] == "Bearer ghp_test"

    @patch("toolregistry_hub.websearch.websearch_github.Client")
    def test_search_timeout_error(self, mock_client):
        """Test search with timeout error."""
        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.get.side_effect = HttpTimeoutError("Timeout")
        mock_client.return_value = mock_client_instance

        search = GitHubSearch(api_keys="ghp_test")
        results = search.search("test query")

        assert results == []

    @patch("toolregistry_hub.websearch.websearch_github.Client")
    def test_search_http_401_raises(self, mock_client):
        """Test search with 401 raises SearchBackendError after exhausting keys."""
        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.get.side_effect = HTTPError(
            401, "Bad credentials", "https://api.github.com/search/repositories"
        )
        mock_client.return_value = mock_client_instance

        search = GitHubSearch(api_keys="ghp_invalid")
        with pytest.raises(SearchBackendError, match="all tokens exhausted"):
            search.search("test query")

    @patch("toolregistry_hub.websearch.websearch_github.Client")
    def test_search_http_403_raises(self, mock_client):
        """Test search with 403 raises SearchBackendError after exhausting keys."""
        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.get.side_effect = HTTPError(
            403, "API rate limit exceeded", "https://api.github.com/search/repositories"
        )
        mock_client.return_value = mock_client_instance

        search = GitHubSearch(api_keys="ghp_test")
        with pytest.raises(SearchBackendError, match="all tokens exhausted"):
            search.search("test query")

    @patch("toolregistry_hub.websearch.websearch_github.Client")
    def test_search_http_429_raises(self, mock_client):
        """Test search with 429 raises SearchBackendError after exhausting keys."""
        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.get.side_effect = HTTPError(
            429, "Rate limit exceeded", "https://api.github.com/search/repositories"
        )
        mock_client.return_value = mock_client_instance

        search = GitHubSearch(api_keys="ghp_test")
        with pytest.raises(SearchBackendError, match="all tokens exhausted"):
            search.search("test query")

    @patch("toolregistry_hub.websearch.websearch_github.Client")
    def test_search_http_422_raises(self, mock_client):
        """Test search with 422 raises SearchBackendError (malformed query)."""
        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.get.side_effect = HTTPError(
            422, "Validation Failed", "https://api.github.com/search/repositories"
        )
        mock_client.return_value = mock_client_instance

        search = GitHubSearch(api_keys="ghp_test")
        with pytest.raises(SearchBackendError, match="422"):
            search.search("test query")

    @patch("toolregistry_hub.websearch.websearch_github.Client")
    def test_search_unauthenticated_rate_limit_raises(self, mock_client):
        """Test that unauthenticated 403 raises SearchBackendError."""
        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.get.side_effect = HTTPError(
            403, "Rate limit exceeded", "https://api.github.com/search/repositories"
        )
        mock_client.return_value = mock_client_instance

        with patch.dict("os.environ", {}, clear=True):
            search = GitHubSearch()
            with pytest.raises(SearchBackendError, match="403"):
                search.search("test query")

    @patch("toolregistry_hub.websearch.websearch_github.Client")
    def test_search_http_401_retries_with_multiple_keys(self, mock_client):
        """Test that 401 triggers key rotation before raising."""
        mock_response = MagicMock()
        mock_response.json.return_value = SAMPLE_GITHUB_RESPONSE
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.get.side_effect = [
            HTTPError(
                401, "Bad credentials", "https://api.github.com/search/repositories"
            ),
            mock_response,
        ]
        mock_client.return_value = mock_client_instance

        search = GitHubSearch(api_keys="ghp_bad,ghp_good")
        results = search.search("test query")

        assert len(results) == 2
        assert mock_client_instance.get.call_count == 2

    @patch("toolregistry_hub.websearch.websearch_github.Client")
    def test_search_incomplete_results_logs_warning(self, mock_client):
        """Test that incomplete_results triggers a warning log."""
        incomplete_response = {**SAMPLE_GITHUB_RESPONSE, "incomplete_results": True}
        mock_response = MagicMock()
        mock_response.json.return_value = incomplete_response
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value = mock_client_instance

        search = GitHubSearch(api_keys="ghp_test")
        with patch("toolregistry_hub.websearch.websearch_github.logger") as mock_logger:
            results = search.search("broad query")

        assert len(results) == 2
        mock_logger.warning.assert_called_once()

    def test_parse_results(self):
        """Test parsing of API results."""
        search = GitHubSearch(api_keys="ghp_test")
        results = search._parse_results(SAMPLE_GITHUB_RESPONSE)

        assert len(results) == 2
        assert results[0].title == "tensorflow/tensorflow"
        assert results[0].url == "https://github.com/tensorflow/tensorflow"
        assert "An Open Source Machine Learning Framework" in results[0].content
        assert "Stars: 180000" in results[0].content
        assert "Language: C++" in results[0].content
        assert "machine-learning" in results[0].content
        assert "2026-08-25T12:00:00Z" in results[0].content

    def test_parse_results_empty(self):
        """Test parsing of empty results."""
        search = GitHubSearch(api_keys="ghp_test")
        results = search._parse_results({"total_count": 0, "items": []})

        assert results == []

    def test_parse_results_missing_fields(self):
        """Test parsing results with missing optional fields."""
        search = GitHubSearch(api_keys="ghp_test")
        raw = {
            "items": [
                {
                    "full_name": "user/repo",
                    "html_url": "https://github.com/user/repo",
                }
            ]
        }
        results = search._parse_results(raw)

        assert len(results) == 1
        assert results[0].title == "user/repo"
        assert "No description" in results[0].content
        assert "Language: Unknown" in results[0].content

    @patch("toolregistry_hub.websearch.websearch_github.Client")
    def test_search_request_params(self, mock_client):
        """Test that request parameters are correctly formatted."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "total_count": 0,
            "incomplete_results": False,
            "items": [],
        }
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value = mock_client_instance

        search = GitHubSearch(api_keys="ghp_test")
        search.search("python stars:>1000", max_results=10)

        call_args = mock_client_instance.get.call_args
        params = call_args[1]["params"]

        assert params["q"] == "python stars:>1000"
        assert params["per_page"] == 10

    @patch("toolregistry_hub.websearch.websearch_github.Client")
    def test_search_with_sort(self, mock_client):
        """Test search with sort parameter."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "total_count": 0,
            "incomplete_results": False,
            "items": [],
        }
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value = mock_client_instance

        search = GitHubSearch(api_keys="ghp_test")
        search.search("test", sort="stars", order="desc")

        call_args = mock_client_instance.get.call_args
        params = call_args[1]["params"]

        assert params["sort"] == "stars"
        assert params["order"] == "desc"

    @patch("toolregistry_hub.websearch.websearch_github.Client")
    def test_search_max_results_cap(self, mock_client):
        """Test that max_results caps results correctly."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "total_count": 10,
            "incomplete_results": False,
            "items": [
                {
                    "full_name": f"user/repo{i}",
                    "html_url": f"https://github.com/user/repo{i}",
                    "description": f"Repo {i}",
                    "stargazers_count": i * 100,
                    "language": "Python",
                    "topics": [],
                    "updated_at": "2026-01-01T00:00:00Z",
                }
                for i in range(10)
            ],
        }
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value = mock_client_instance

        search = GitHubSearch(api_keys="ghp_test")
        results = search.search("test", max_results=3)

        assert len(results) <= 3

    @patch("toolregistry_hub.websearch.websearch_github.Client")
    def test_search_gets_correct_endpoint(self, mock_client):
        """Test that the search uses GET to the correct endpoint."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "total_count": 0,
            "incomplete_results": False,
            "items": [],
        }
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value = mock_client_instance

        search = GitHubSearch(api_keys="ghp_test")
        search.search("test query")

        mock_client_instance.get.assert_called_once()
        call_args = mock_client_instance.get.call_args
        assert call_args[0][0] == "https://api.github.com/search/repositories"

    @patch("toolregistry_hub.websearch.websearch_github.Client")
    def test_search_reuses_client_across_retries(self, mock_client):
        """Test that the Client is created once and reused across retries."""
        mock_response = MagicMock()
        mock_response.json.return_value = SAMPLE_GITHUB_RESPONSE
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.get.side_effect = [
            HTTPError(
                429, "Rate limited", "https://api.github.com/search/repositories"
            ),
            mock_response,
        ]
        mock_client.return_value = mock_client_instance

        search = GitHubSearch(api_keys="ghp_key1,ghp_key2")
        results = search.search("test query")

        assert len(results) == 2
        mock_client.assert_called_once()
