"""Tests for the fetch module."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from toolregistry_hub.fetch import (
    _JINA_TIMEOUT_BUFFER,
    _JINA_WAIT_SELECTORS,
    _MIN_CONTENT_LENGTH,
    _SPA_SHELL_INDICATORS,
    _extract,
    _extract_with_readability,
    _extract_with_soup,
    _fetch_html,
    _format_text,
    _get_content_with_jina_reader,
    _get_content_with_markdown_negotiation,
    _is_content_sufficient,
    _jina_reader_request,
)


# ============================================================
# _is_content_sufficient tests
# ============================================================


class TestIsContentSufficient:
    """Tests for the _is_content_sufficient function."""

    def test_empty_string(self):
        assert _is_content_sufficient("") is False

    def test_short_content(self):
        assert _is_content_sufficient("Hello world") is False

    def test_exactly_min_length(self):
        text = "a" * _MIN_CONTENT_LENGTH
        assert _is_content_sufficient(text) is True

    def test_below_min_length(self):
        text = "a" * (_MIN_CONTENT_LENGTH - 1)
        assert _is_content_sufficient(text) is False

    def test_sufficient_content(self):
        text = "This is a meaningful article about technology. " * 10
        assert _is_content_sufficient(text) is True

    @pytest.mark.parametrize("indicator", _SPA_SHELL_INDICATORS)
    def test_spa_shell_indicators(self, indicator):
        # Content long enough but contains SPA indicator
        text = f"Some prefix text. {indicator} Some suffix text." + "x" * 200
        assert _is_content_sufficient(text) is False

    def test_spa_indicator_case_insensitive(self):
        text = "Some text. PLEASE ENABLE JAVASCRIPT to continue." + "x" * 200
        assert _is_content_sufficient(text) is False

    def test_normal_content_with_no_indicators(self):
        text = (
            "Angular is a web framework that empowers developers to build "
            "fast, reliable applications that users love. Maintained by a "
            "dedicated team at Google, Angular provides a broad suite of "
            "tools, APIs, and libraries to simplify your development workflow."
        )
        assert _is_content_sufficient(text) is True


# ============================================================
# _format_text tests
# ============================================================


class TestFormatText:
    """Tests for the _format_text function."""

    def test_normalize_whitespace(self):
        assert _format_text("hello   world") == "hello world"

    def test_normalize_newlines(self):
        assert _format_text("hello\n\n\nworld") == "hello\nworld"

    def test_strip_whitespace(self):
        assert _format_text("  hello world  ") == "hello world"

    def test_unicode_normalization(self):
        # NFKC normalization: ﬁ -> fi
        assert _format_text("ﬁnd") == "find"

    def test_preserve_single_newlines(self):
        assert _format_text("line1\nline2") == "line1\nline2"


# ============================================================
# _get_content_with_markdown_negotiation tests
# ============================================================


class TestMarkdownNegotiation:
    """Tests for the _get_content_with_markdown_negotiation function."""

    @patch("toolregistry_hub.fetch.httpx.get")
    def test_success_with_markdown_content_type(self, mock_get):
        mock_response = MagicMock()
        mock_response.headers = {
            "content-type": "text/markdown; charset=utf-8",
            "x-markdown-tokens": "500",
        }
        mock_response.text = "# Hello\nThis is markdown."
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = _get_content_with_markdown_negotiation("https://example.com")
        assert result == "# Hello\nThis is markdown."

    @patch("toolregistry_hub.fetch.httpx.get")
    def test_not_supported_returns_empty(self, mock_get):
        mock_response = MagicMock()
        mock_response.headers = {"content-type": "text/html; charset=utf-8"}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = _get_content_with_markdown_negotiation("https://example.com")
        assert result == ""

    @patch("toolregistry_hub.fetch.httpx.get")
    def test_http_error_returns_empty(self, mock_get):
        mock_get.side_effect = httpx.ConnectError("Connection refused")

        result = _get_content_with_markdown_negotiation("https://example.com")
        assert result == ""

    @patch("toolregistry_hub.fetch.httpx.get")
    def test_accept_header_is_text_markdown(self, mock_get):
        mock_response = MagicMock()
        mock_response.headers = {"content-type": "text/html"}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        _get_content_with_markdown_negotiation("https://example.com")

        call_kwargs = mock_get.call_args
        headers = call_kwargs.kwargs.get("headers") or call_kwargs[1].get("headers")
        assert headers["Accept"] == "text/markdown"


# ============================================================
# _get_content_with_jina_reader tests
# ============================================================


class TestJinaReaderRequest:
    """Tests for the _jina_reader_request low-level function."""

    @patch("toolregistry_hub.fetch.httpx.post")
    def test_success_returns_content(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "code": 200,
            "data": {
                "content": "# Article Title\nSome article content here.",
                "title": "Article Title",
            },
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = _jina_reader_request("https://example.com")
        assert result == "# Article Title\nSome article content here."

    @patch("toolregistry_hub.fetch.httpx.post")
    def test_empty_content_returns_empty(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"code": 200, "data": {"content": ""}}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = _jina_reader_request("https://example.com")
        assert result == ""

    @patch("toolregistry_hub.fetch.httpx.post")
    def test_http_error_returns_empty(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Bad Request",
            request=MagicMock(),
            response=mock_response,
        )
        mock_post.return_value = mock_response

        result = _jina_reader_request("https://example.com")
        assert result == ""

    @patch("toolregistry_hub.fetch.httpx.post")
    def test_uses_post_method(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"code": 200, "data": {"content": "test"}}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        _jina_reader_request("https://example.com")
        mock_post.assert_called_once()

    @patch("toolregistry_hub.fetch.httpx.post")
    def test_headers_include_expected_fields(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"code": 200, "data": {"content": "test"}}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        _jina_reader_request("https://example.com", engine="browser")

        call_kwargs = mock_post.call_args
        headers = call_kwargs.kwargs.get("headers") or call_kwargs[1].get("headers")
        assert headers["X-Engine"] == "browser"
        assert headers["Accept"] == "application/json"
        assert "X-Timeout" in headers
        assert headers["X-Remove-Selector"] == "header, footer, nav, aside"
        assert headers["X-Wait-For-Selector"] == _JINA_WAIT_SELECTORS

    @patch("toolregistry_hub.fetch.httpx.post")
    def test_sends_url_in_json_body(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"code": 200, "data": {"content": "test"}}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        _jina_reader_request("https://example.com/page")

        call_kwargs = mock_post.call_args
        json_body = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert json_body == {"url": "https://example.com/page"}

    @patch("toolregistry_hub.fetch.httpx.post")
    def test_timeout_error_returns_empty(self, mock_post):
        mock_post.side_effect = httpx.ReadTimeout("Read timed out")

        result = _jina_reader_request("https://example.com")
        assert result == ""

    @patch("toolregistry_hub.fetch.httpx.post")
    def test_httpx_timeout_exceeds_jina_timeout(self, mock_post):
        """httpx transport timeout must be larger than Jina X-Timeout."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"code": 200, "data": {"content": "ok"}}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        custom_timeout = 20.0
        _jina_reader_request("https://example.com", timeout=custom_timeout)

        call_kwargs = mock_post.call_args
        httpx_timeout = call_kwargs.kwargs.get("timeout")
        headers = call_kwargs.kwargs.get("headers") or call_kwargs[1].get("headers")
        jina_timeout = int(headers["X-Timeout"])

        assert httpx_timeout == custom_timeout + _JINA_TIMEOUT_BUFFER
        assert jina_timeout == int(custom_timeout)
        assert httpx_timeout > jina_timeout

    @patch("toolregistry_hub.fetch.httpx.post")
    def test_custom_engine(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"code": 200, "data": {"content": "test"}}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        _jina_reader_request("https://example.com", engine="cf-browser-rendering")

        call_kwargs = mock_post.call_args
        headers = call_kwargs.kwargs.get("headers") or call_kwargs[1].get("headers")
        assert headers["X-Engine"] == "cf-browser-rendering"


class TestJinaReader:
    """Tests for the _get_content_with_jina_reader orchestrator function."""

    @patch("toolregistry_hub.fetch._jina_reader_request")
    def test_success_on_first_engine(self, mock_request):
        """Returns content from the first engine when sufficient."""
        sufficient = "# Article Title\nSome article content here. " * 10
        mock_request.return_value = sufficient

        result = _get_content_with_jina_reader("https://example.com")
        assert result == sufficient
        # Only called once (browser engine)
        assert mock_request.call_count == 1

    @patch("toolregistry_hub.fetch._jina_reader_request")
    def test_retries_with_cf_engine_on_insufficient(self, mock_request):
        """Falls back to cf-browser-rendering when browser returns short content."""
        sufficient = "# Full Content\nComplete article text here. " * 10
        mock_request.side_effect = ["Short", sufficient]

        result = _get_content_with_jina_reader("https://example.com")
        assert result == sufficient
        assert mock_request.call_count == 2
        # Verify engine order
        engines = [
            call.kwargs.get("engine") or call.args[1]
            for call in mock_request.call_args_list
        ]
        assert engines[0] == "browser"
        assert engines[1] == "cf-browser-rendering"

    @patch("toolregistry_hub.fetch._jina_reader_request")
    def test_returns_last_result_when_all_engines_fail(self, mock_request):
        """Returns the last engine's result (even empty) when all fail."""
        mock_request.return_value = ""

        result = _get_content_with_jina_reader("https://example.com")
        assert result == ""
        assert mock_request.call_count == 2

    @patch("toolregistry_hub.fetch._jina_reader_request")
    def test_passes_timeout_and_proxy(self, mock_request):
        sufficient = "Enough content for testing purposes. " * 10
        mock_request.return_value = sufficient

        _get_content_with_jina_reader(
            "https://example.com", timeout=45.0, proxy="http://proxy:8080"
        )

        call_kwargs = mock_request.call_args
        assert call_kwargs.kwargs["timeout"] == 45.0
        assert call_kwargs.kwargs["proxy"] == "http://proxy:8080"


# ============================================================
# _fetch_html tests
# ============================================================


class TestFetchHtml:
    """Tests for the _fetch_html function."""

    @patch("toolregistry_hub.fetch.httpx.get")
    def test_success_returns_html(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = "<html><body>Hello</body></html>"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = _fetch_html("https://example.com")
        assert result == "<html><body>Hello</body></html>"

    @patch("toolregistry_hub.fetch.httpx.get")
    def test_http_error_returns_empty(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Forbidden",
            request=MagicMock(),
            response=mock_response,
        )
        mock_get.return_value = mock_response

        result = _fetch_html("https://example.com")
        assert result == ""

    @patch("toolregistry_hub.fetch.httpx.get")
    def test_connection_error_returns_empty(self, mock_get):
        mock_get.side_effect = httpx.ConnectError("Connection refused")

        result = _fetch_html("https://example.com")
        assert result == ""

    @patch("toolregistry_hub.fetch.httpx.get")
    def test_passes_proxy(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = "<html></html>"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        _fetch_html("https://example.com", proxy="http://proxy:8080")

        call_kwargs = mock_get.call_args
        assert call_kwargs.kwargs.get("proxy") == "http://proxy:8080"


# ============================================================
# _extract_with_readability tests
# ============================================================


class TestReadabilityExtraction:
    """Tests for the _extract_with_readability function."""

    def test_extracts_article_content(self):
        paragraphs = "<p>This is a test paragraph with enough content. </p>" * 20
        html = f"""
        <html><head><title>Test Article</title></head>
        <body>
            <nav>Navigation links</nav>
            <article>{paragraphs}</article>
            <footer>Footer content</footer>
        </body></html>
        """
        result = _extract_with_readability(html, "https://example.com")
        assert len(result) >= _MIN_CONTENT_LENGTH
        assert "test paragraph" in result.lower()

    def test_short_content_returns_empty(self):
        html = "<html><body><p>Short.</p></body></html>"
        result = _extract_with_readability(html, "https://example.com")
        assert result == ""

    def test_returns_plain_text(self):
        paragraphs = "<p>Some meaningful content for testing purposes. </p>" * 20
        html = f"<html><body><article>{paragraphs}</article></body></html>"
        result = _extract_with_readability(html, "https://example.com")
        # Result should be plain text, not HTML
        assert "<p>" not in result
        assert "<article>" not in result

    def test_exception_returns_empty(self):
        # Invalid input that might cause parsing issues
        result = _extract_with_readability("", "https://example.com")
        assert result == ""


# ============================================================
# _extract_with_soup tests
# ============================================================


class TestSoupExtraction:
    """Tests for the _extract_with_soup function."""

    def test_extracts_main_content(self):
        html = """
        <html><body>
            <nav>Navigation</nav>
            <main><p>Main content here with enough text to be meaningful.</p></main>
            <footer>Footer</footer>
        </body></html>
        """
        result = _extract_with_soup(html)
        assert "Main content" in result
        assert "Navigation" not in result

    def test_extracts_article_content(self):
        html = """
        <html><body>
            <article><p>Article content here.</p></article>
        </body></html>
        """
        result = _extract_with_soup(html)
        assert "Article content" in result

    def test_no_body_returns_empty(self):
        html = "<html></html>"
        result = _extract_with_soup(html)
        assert result == ""

    def test_malformed_html_no_crash(self):
        html = "<div><p>Unclosed paragraph<div>Nested improperly"
        result = _extract_with_soup(html)
        # Should not raise, may return content or empty
        assert isinstance(result, str)


# ============================================================
# _extract integration tests
# ============================================================


class TestExtract:
    """Integration tests for the _extract function."""

    @patch("toolregistry_hub.fetch._get_content_with_jina_reader")
    @patch("toolregistry_hub.fetch._extract_with_soup")
    @patch("toolregistry_hub.fetch._extract_with_readability")
    @patch("toolregistry_hub.fetch._fetch_html")
    @patch("toolregistry_hub.fetch._get_content_with_markdown_negotiation")
    def test_markdown_negotiation_success(
        self, mock_md, mock_fetch, mock_readability, mock_soup, mock_jina
    ):
        mock_md.return_value = "# Markdown Content\nSome text here."
        result = _extract("https://example.com")
        assert "Markdown Content" in result
        mock_fetch.assert_not_called()
        mock_jina.assert_not_called()

    @patch("toolregistry_hub.fetch._get_content_with_jina_reader")
    @patch("toolregistry_hub.fetch._extract_with_soup")
    @patch("toolregistry_hub.fetch._extract_with_readability")
    @patch("toolregistry_hub.fetch._fetch_html")
    @patch("toolregistry_hub.fetch._get_content_with_markdown_negotiation")
    def test_readability_sufficient_content(
        self, mock_md, mock_fetch, mock_readability, mock_soup, mock_jina
    ):
        mock_md.return_value = ""
        mock_fetch.return_value = "<html>...</html>"
        mock_readability.return_value = "This is a long enough article. " * 10
        mock_soup.return_value = "Short soup."
        result = _extract("https://example.com")
        assert "long enough article" in result
        mock_jina.assert_not_called()

    @patch("toolregistry_hub.fetch._get_content_with_jina_reader")
    @patch("toolregistry_hub.fetch._extract_with_soup")
    @patch("toolregistry_hub.fetch._extract_with_readability")
    @patch("toolregistry_hub.fetch._fetch_html")
    @patch("toolregistry_hub.fetch._get_content_with_markdown_negotiation")
    def test_readability_fails_soup_sufficient(
        self, mock_md, mock_fetch, mock_readability, mock_soup, mock_jina
    ):
        mock_md.return_value = ""
        mock_fetch.return_value = "<html>...</html>"
        mock_readability.return_value = ""
        mock_soup.return_value = "Soup extracted content is good enough. " * 10
        result = _extract("https://example.com")
        assert "Soup extracted" in result
        mock_jina.assert_not_called()

    @patch("toolregistry_hub.fetch._get_content_with_jina_reader")
    @patch("toolregistry_hub.fetch._extract_with_soup")
    @patch("toolregistry_hub.fetch._extract_with_readability")
    @patch("toolregistry_hub.fetch._fetch_html")
    @patch("toolregistry_hub.fetch._get_content_with_markdown_negotiation")
    def test_local_spa_shell_triggers_jina(
        self, mock_md, mock_fetch, mock_readability, mock_soup, mock_jina
    ):
        mock_md.return_value = ""
        mock_fetch.return_value = "<html>...</html>"
        mock_readability.return_value = (
            "Loading... Please enable JavaScript to continue." + "x" * 200
        )
        mock_soup.return_value = (
            "Loading... Please enable JavaScript to continue." + "x" * 200
        )
        mock_jina.return_value = "# Real Content\nActual article text here. " * 10

        result = _extract("https://example.com")
        assert "Real Content" in result
        mock_jina.assert_called_once()

    @patch("toolregistry_hub.fetch._get_content_with_jina_reader")
    @patch("toolregistry_hub.fetch._extract_with_soup")
    @patch("toolregistry_hub.fetch._extract_with_readability")
    @patch("toolregistry_hub.fetch._fetch_html")
    @patch("toolregistry_hub.fetch._get_content_with_markdown_negotiation")
    def test_no_html_triggers_jina(
        self, mock_md, mock_fetch, mock_readability, mock_soup, mock_jina
    ):
        mock_md.return_value = ""
        mock_fetch.return_value = ""
        mock_jina.return_value = "# Jina Content\nFetched via Jina. " * 10

        result = _extract("https://example.com")
        assert "Jina Content" in result
        mock_readability.assert_not_called()
        mock_soup.assert_not_called()

    @patch("toolregistry_hub.fetch._get_content_with_jina_reader")
    @patch("toolregistry_hub.fetch._extract_with_soup")
    @patch("toolregistry_hub.fetch._extract_with_readability")
    @patch("toolregistry_hub.fetch._fetch_html")
    @patch("toolregistry_hub.fetch._get_content_with_markdown_negotiation")
    def test_jina_failure_falls_back_to_local(
        self, mock_md, mock_fetch, mock_readability, mock_soup, mock_jina
    ):
        mock_md.return_value = ""
        mock_fetch.return_value = "<html>...</html>"
        mock_readability.return_value = "Short low quality"
        mock_soup.return_value = ""
        mock_jina.return_value = ""

        result = _extract("https://example.com")
        assert "Short low quality" in result

    @patch("toolregistry_hub.fetch._get_content_with_jina_reader")
    @patch("toolregistry_hub.fetch._extract_with_soup")
    @patch("toolregistry_hub.fetch._extract_with_readability")
    @patch("toolregistry_hub.fetch._fetch_html")
    @patch("toolregistry_hub.fetch._get_content_with_markdown_negotiation")
    def test_all_strategies_fail(
        self, mock_md, mock_fetch, mock_readability, mock_soup, mock_jina
    ):
        mock_md.return_value = ""
        mock_fetch.return_value = ""
        mock_jina.return_value = ""

        result = _extract("https://example.com")
        assert result == "Unable to fetch content"
