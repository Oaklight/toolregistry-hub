"""Unit tests for arXiv Search module."""

from unittest.mock import MagicMock, patch

from toolregistry_hub._vendor.httpclient import HTTPError, HttpTimeoutError
from toolregistry_hub.academics.arxiv_search import ArxivSearch
from toolregistry_hub.academics.paper_result import PaperResult

SAMPLE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/1706.03762v7</id>
    <published>2017-06-12T17:57:34Z</published>
    <title>Attention Is All
You Need</title>
    <summary>The dominant sequence transduction
models are based on complex recurrent networks.</summary>
    <author><name>Ashish Vaswani</name></author>
    <author><name>Noam Shazeer</name></author>
    <link href="http://arxiv.org/abs/1706.03762v7" rel="alternate" type="text/html"/>
    <link title="pdf" href="http://arxiv.org/pdf/1706.03762v7" rel="related" type="application/pdf"/>
    <arxiv:primary_category term="cs.CL"/>
    <arxiv:doi>10.5555/3295222.3295349</arxiv:doi>
  </entry>
</feed>"""

SAMPLE_XML_MINIMAL = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2401.00001v1</id>
    <published>2024-01-01T00:00:00Z</published>
    <title>A Simple Paper</title>
    <summary>Short abstract.</summary>
    <author><name>Jane Doe</name></author>
    <link href="http://arxiv.org/abs/2401.00001v1" rel="alternate" type="text/html"/>
  </entry>
</feed>"""


class TestArxivSearch:
    def test_init_defaults(self):
        search = ArxivSearch()
        assert search.base_url == "http://export.arxiv.org/api/query"
        assert search._rate_limit_delay == 1.0

    def test_always_configured(self):
        search = ArxivSearch()
        assert search._is_configured() is True

    @patch("toolregistry_hub.academics.arxiv_search.Client")
    def test_search_basic(self, mock_client):
        mock_response = MagicMock()
        mock_response.text = SAMPLE_XML
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value = mock_client_instance

        search = ArxivSearch(rate_limit_delay=0)
        results = search.search("attention mechanism", max_results=5)

        assert len(results) == 1
        r = results[0]
        assert isinstance(r, PaperResult)
        assert r.title == "Attention Is All You Need"
        assert r.authors == ["Ashish Vaswani", "Noam Shazeer"]
        assert r.year == 2017
        assert r.venue == "cs.CL"
        assert r.doi == "10.5555/3295222.3295349"
        assert r.pdf_url == "http://arxiv.org/pdf/1706.03762v7"
        assert r.source == "arxiv"
        assert r.url == "http://arxiv.org/abs/1706.03762v7"

    @patch("toolregistry_hub.academics.arxiv_search.Client")
    def test_search_normalizes_whitespace(self, mock_client):
        mock_response = MagicMock()
        mock_response.text = SAMPLE_XML
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value = mock_client_instance

        search = ArxivSearch(rate_limit_delay=0)
        results = search.search("test")

        assert "\n" not in results[0].title
        assert "\n" not in results[0].abstract

    @patch("toolregistry_hub.academics.arxiv_search.Client")
    def test_search_empty_query(self, mock_client):
        search = ArxivSearch(rate_limit_delay=0)
        results = search.search("")
        assert results == []
        mock_client.assert_not_called()

    @patch("toolregistry_hub.academics.arxiv_search.Client")
    def test_search_timeout(self, mock_client):
        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.get.side_effect = HttpTimeoutError("Timeout")
        mock_client.return_value = mock_client_instance

        search = ArxivSearch(rate_limit_delay=0)
        results = search.search("test query")
        assert results == []

    @patch("toolregistry_hub.academics.arxiv_search.Client")
    def test_search_http_error(self, mock_client):
        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.get.side_effect = HTTPError(
            503, "Service Unavailable", "http://export.arxiv.org/api/query"
        )
        mock_client.return_value = mock_client_instance

        search = ArxivSearch(rate_limit_delay=0)
        results = search.search("test query")
        assert results == []

    @patch("toolregistry_hub.academics.arxiv_search.Client")
    def test_search_wraps_plain_query(self, mock_client):
        mock_response = MagicMock()
        mock_response.text = SAMPLE_XML_MINIMAL
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value = mock_client_instance

        search = ArxivSearch(rate_limit_delay=0)
        search.search("plain query")

        call_kwargs = mock_client_instance.get.call_args
        params = call_kwargs.kwargs.get("params", {})
        assert params["search_query"] == "all:plain query"

    @patch("toolregistry_hub.academics.arxiv_search.Client")
    def test_search_preserves_arxiv_syntax(self, mock_client):
        mock_response = MagicMock()
        mock_response.text = SAMPLE_XML_MINIMAL
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value = mock_client_instance

        search = ArxivSearch(rate_limit_delay=0)
        search.search("ti:attention AND au:vaswani")

        call_kwargs = mock_client_instance.get.call_args
        params = call_kwargs.kwargs.get("params", {})
        assert params["search_query"] == "ti:attention AND au:vaswani"

    @patch("toolregistry_hub.academics.arxiv_search.Client")
    def test_parse_results_no_pdf(self, mock_client):
        mock_response = MagicMock()
        mock_response.text = SAMPLE_XML_MINIMAL
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value = mock_client_instance

        search = ArxivSearch(rate_limit_delay=0)
        results = search.search("test")

        assert len(results) == 1
        assert results[0].pdf_url is None
        assert results[0].doi is None
        assert results[0].venue is None

    def test_parse_results_invalid_xml(self):
        search = ArxivSearch(rate_limit_delay=0)
        results = search._parse_results("this is not xml")
        assert results == []

    @patch("toolregistry_hub.academics.arxiv_search.time")
    def test_rate_limiting_enforces_delay(self, mock_time):
        # First call: _last_request_time=0, now=10 → elapsed=10 > 1 → no sleep
        # Second call: _last_request_time=10, now=10.5 → elapsed=0.5 < 1 → sleep(0.5)
        mock_time.time.side_effect = [10.0, 10.0, 10.5, 10.5]
        mock_time.sleep = MagicMock()

        search = ArxivSearch(rate_limit_delay=1.0)
        search._wait_for_rate_limit()
        search._wait_for_rate_limit()

        mock_time.sleep.assert_called_once_with(0.5)
