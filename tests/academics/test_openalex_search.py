"""Unit tests for OpenAlex Search module."""

from unittest.mock import MagicMock, patch

from toolregistry_hub._vendor.httpclient import HTTPError, HttpTimeoutError
from toolregistry_hub.academics.openalex_search import OpenAlexSearch
from toolregistry_hub.academics.paper_result import PaperResult

SAMPLE_RESPONSE = {
    "results": [
        {
            "id": "https://openalex.org/W12345",
            "display_name": "Attention Is All You Need",
            "doi": "https://doi.org/10.5555/3295222.3295349",
            "publication_year": 2017,
            "authorships": [
                {"author": {"display_name": "Ashish Vaswani"}},
                {"author": {"display_name": "Noam Shazeer"}},
            ],
            "cited_by_count": 120000,
            "primary_location": {
                "source": {"display_name": "NeurIPS"},
            },
            "open_access": {"oa_url": "https://arxiv.org/pdf/1706.03762"},
            "abstract_inverted_index": {
                "The": [0],
                "dominant": [1],
                "sequence": [2],
                "models": [3, 14],
                "are": [4],
                "based": [5, 9],
                "on": [6],
                "complex": [7],
                "recurrent": [8],
            },
        }
    ]
}


class TestOpenAlexSearch:
    def test_init_with_api_key(self):
        search = OpenAlexSearch(api_keys="test_key_123")
        assert search.api_key_parser.key_count == 1
        assert search.base_url == "https://api.openalex.org"

    @patch.dict("os.environ", {"OPENALEX_API_KEY": "env_key"})
    def test_init_from_env(self):
        search = OpenAlexSearch()
        assert search.api_key_parser.api_keys[0] == "env_key"

    def test_init_without_key_unconfigured(self):
        with patch.dict("os.environ", {}, clear=True):
            search = OpenAlexSearch()
            assert search.api_key_parser.key_count == 0
            assert not search._is_configured()

    @patch("toolregistry_hub.academics.openalex_search.Client")
    def test_search_basic(self, mock_client):
        mock_response = MagicMock()
        mock_response.json.return_value = SAMPLE_RESPONSE
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value = mock_client_instance

        search = OpenAlexSearch(api_keys="test_key")
        results = search.search("attention mechanism", max_results=5)

        assert len(results) == 1
        assert isinstance(results[0], PaperResult)
        assert results[0].title == "Attention Is All You Need"
        assert results[0].authors == ["Ashish Vaswani", "Noam Shazeer"]
        assert results[0].year == 2017
        assert results[0].venue == "NeurIPS"
        assert results[0].doi == "https://doi.org/10.5555/3295222.3295349"
        assert results[0].pdf_url == "https://arxiv.org/pdf/1706.03762"
        assert results[0].cited_by_count == 120000
        assert results[0].source == "openalex"
        assert results[0].url == "https://openalex.org/W12345"

    @patch("toolregistry_hub.academics.openalex_search.Client")
    def test_search_empty_query(self, mock_client):
        search = OpenAlexSearch(api_keys="test_key")
        results = search.search("")
        assert results == []
        mock_client.assert_not_called()

    @patch("toolregistry_hub.academics.openalex_search.Client")
    def test_search_timeout(self, mock_client):
        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.get.side_effect = HttpTimeoutError("Timeout")
        mock_client.return_value = mock_client_instance

        search = OpenAlexSearch(api_keys="test_key")
        results = search.search("test query")
        assert results == []

    @patch("toolregistry_hub.academics.openalex_search.Client")
    def test_search_http_401_marks_key_failed(self, mock_client):
        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.get.side_effect = HTTPError(
            401, "Unauthorized", "https://api.openalex.org/works"
        )
        mock_client.return_value = mock_client_instance

        search = OpenAlexSearch(api_keys="bad_key")
        results = search.search("test query")
        assert results == []
        assert "bad_key" in search.api_key_parser.failed_keys

    @patch("toolregistry_hub.academics.openalex_search.Client")
    def test_search_http_429_marks_key_rate_limited(self, mock_client):
        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.get.side_effect = HTTPError(
            429, "Too Many Requests", "https://api.openalex.org/works"
        )
        mock_client.return_value = mock_client_instance

        search = OpenAlexSearch(api_keys="key1")
        results = search.search("test query")
        assert results == []
        failed = search.api_key_parser.failed_keys
        assert "key1" in failed
        assert "rate limited" in failed["key1"]

    @patch("toolregistry_hub.academics.openalex_search.Client")
    def test_search_uses_api_key_in_params(self, mock_client):
        mock_response = MagicMock()
        mock_response.json.return_value = {"results": []}
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value = mock_client_instance

        search = OpenAlexSearch(api_keys="my_api_key")
        search.search("test")

        call_kwargs = mock_client_instance.get.call_args
        params = call_kwargs.kwargs.get("params", {})
        assert params.get("api_key") == "my_api_key"

    @patch("toolregistry_hub.academics.openalex_search.Client")
    def test_parse_results_missing_fields(self, mock_client):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {
                    "id": "https://openalex.org/W99999",
                    "display_name": "Minimal Paper",
                    "authorships": [],
                    "publication_year": None,
                    "primary_location": None,
                    "open_access": None,
                    "abstract_inverted_index": None,
                    "doi": None,
                    "cited_by_count": None,
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value = mock_client_instance

        search = OpenAlexSearch(api_keys="test_key")
        results = search.search("test")

        assert len(results) == 1
        assert results[0].title == "Minimal Paper"
        assert results[0].authors == []
        assert results[0].abstract == ""
        assert results[0].venue is None
        assert results[0].pdf_url is None
        assert results[0].doi is None


class TestReconstructAbstract:
    def test_normal(self):
        index = {"The": [0], "cat": [1], "sat": [2]}
        assert OpenAlexSearch._reconstruct_abstract(index) == "The cat sat"

    def test_none(self):
        assert OpenAlexSearch._reconstruct_abstract(None) == ""

    def test_empty_dict(self):
        assert OpenAlexSearch._reconstruct_abstract({}) == ""

    def test_multiple_positions(self):
        index = {"the": [0, 4], "cat": [1], "and": [3], "dog": [5], "sat": [2]}
        result = OpenAlexSearch._reconstruct_abstract(index)
        assert result == "the cat sat and the dog"
