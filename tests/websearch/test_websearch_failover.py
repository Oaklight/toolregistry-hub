"""Integration tests for API key failover across websearch implementations."""

from unittest.mock import MagicMock, patch

import httpx

from toolregistry_hub.websearch.websearch_brave import BraveSearch


class TestWebSearchFailover:
    """Test API key failover behavior using BraveSearch as representative."""

    def _make_search(self, num_keys=3):
        keys = ",".join(f"key{i}" for i in range(1, num_keys + 1))
        return BraveSearch(api_keys=keys, rate_limit_delay=0)

    @patch("httpx.Client")
    def test_retry_on_401(self, mock_client_cls):
        """First key returns 401, second key succeeds."""
        search = self._make_search(2)

        response_401 = MagicMock()
        response_401.status_code = 401
        response_401.text = "Unauthorized"
        response_401.raise_for_status.side_effect = httpx.HTTPStatusError(
            "401", request=MagicMock(), response=response_401
        )

        response_ok = MagicMock()
        response_ok.status_code = 200
        response_ok.raise_for_status.return_value = None
        response_ok.json.return_value = {
            "web": {
                "results": [
                    {
                        "title": "Result",
                        "url": "https://example.com",
                        "description": "desc",
                    }
                ]
            }
        }

        client_instance = MagicMock()
        client_instance.__enter__ = MagicMock(return_value=client_instance)
        client_instance.__exit__ = MagicMock(return_value=False)
        client_instance.get.side_effect = [response_401, response_ok]
        mock_client_cls.return_value = client_instance

        results = search.search("test query", max_results=5)

        assert len(results) == 1
        assert results[0].title == "Result"
        # First key should be marked as failed
        assert "key1" in search.api_key_parser.failed_keys

    @patch("httpx.Client")
    def test_retry_on_429(self, mock_client_cls):
        """Rate-limited key is marked failed with shorter TTL."""
        search = self._make_search(2)

        response_429 = MagicMock()
        response_429.status_code = 429
        response_429.text = "Too Many Requests"
        response_429.raise_for_status.side_effect = httpx.HTTPStatusError(
            "429", request=MagicMock(), response=response_429
        )

        response_ok = MagicMock()
        response_ok.status_code = 200
        response_ok.raise_for_status.return_value = None
        response_ok.json.return_value = {
            "web": {
                "results": [
                    {"title": "OK", "url": "https://ok.com", "description": "ok"}
                ]
            }
        }

        client_instance = MagicMock()
        client_instance.__enter__ = MagicMock(return_value=client_instance)
        client_instance.__exit__ = MagicMock(return_value=False)
        client_instance.get.side_effect = [response_429, response_ok]
        mock_client_cls.return_value = client_instance

        results = search.search("test query", max_results=5)

        assert len(results) == 1
        failed = search.api_key_parser.failed_keys
        assert "key1" in failed
        assert failed["key1"] == "rate limited"

    @patch("httpx.Client")
    def test_all_keys_fail(self, mock_client_cls):
        """All keys return 401 -> empty results."""
        search = self._make_search(2)

        response_401 = MagicMock()
        response_401.status_code = 401
        response_401.text = "Unauthorized"
        response_401.raise_for_status.side_effect = httpx.HTTPStatusError(
            "401", request=MagicMock(), response=response_401
        )

        client_instance = MagicMock()
        client_instance.__enter__ = MagicMock(return_value=client_instance)
        client_instance.__exit__ = MagicMock(return_value=False)
        client_instance.get.side_effect = [response_401, response_401]
        mock_client_cls.return_value = client_instance

        results = search.search("test query", max_results=5)

        assert results == []
        assert len(search.api_key_parser.failed_keys) == 2

    @patch("httpx.Client")
    def test_failed_key_skipped_on_subsequent_call(self, mock_client_cls):
        """A key marked failed is skipped in subsequent search calls."""
        search = self._make_search(2)

        # First call: key1 fails with 401, key2 succeeds
        response_401 = MagicMock()
        response_401.status_code = 401
        response_401.text = "Unauthorized"
        response_401.raise_for_status.side_effect = httpx.HTTPStatusError(
            "401", request=MagicMock(), response=response_401
        )

        def make_ok_response():
            resp = MagicMock()
            resp.status_code = 200
            resp.raise_for_status.return_value = None
            resp.json.return_value = {
                "web": {
                    "results": [
                        {"title": "R", "url": "https://r.com", "description": "d"}
                    ]
                }
            }
            return resp

        client_instance = MagicMock()
        client_instance.__enter__ = MagicMock(return_value=client_instance)
        client_instance.__exit__ = MagicMock(return_value=False)
        client_instance.get.side_effect = [
            response_401,
            make_ok_response(),
            make_ok_response(),
        ]
        mock_client_cls.return_value = client_instance

        # First search: triggers failover
        search.search("test1", max_results=5)
        assert "key1" in search.api_key_parser.failed_keys

        # Second search: should only try key2 (key1 is still failed)
        results = search.search("test2", max_results=5)
        assert len(results) == 1
        # Total get calls: 2 from first search (401 + ok) + 1 from second (ok)
        assert client_instance.get.call_count == 3
