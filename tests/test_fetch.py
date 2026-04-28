"""Tests for the fetch module."""

from unittest.mock import MagicMock, patch

import pytest

from toolregistry_hub._vendor.httpclient import (
    HTTPError,
    HttpConnectionError,
    HttpTimeoutError,
)

from toolregistry_hub.fetch import (
    _JINA_TIMEOUT_BUFFER,
    _JINA_WAIT_SELECTORS,
    _MIN_CONTENT_LENGTH,
    _NON_HTML_CONTENT_TYPES,
    _SOUP_CONTENT_SELECTORS,
    _SPA_SHELL_INDICATORS,
    Fetch,
    _extract,
    _extract_with_readability,
    _extract_with_soup,
    _fetch_raw,
    _format_text,
    _get_content_with_jina_reader,
    _get_content_with_markdown_negotiation,
    _is_content_sufficient,
    _jina_reader_request,
)
from toolregistry_hub.utils.api_key_parser import APIKeyParser


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

    def test_navigation_only_text_rejected(self):
        """Navigation-only content with many short lines should be rejected."""
        nav_text = "\n".join(
            [
                "产品",
                "文档",
                "快速入门",
                "产品简介",
                "计费说明",
                "使用指南",
                "API参考",
                "常见问题",
                "联系我们",
                "技术支持",
                "帮助中心",
                "开发者工具",
                "SDK下载",
                "版本更新",
            ]
        )
        assert not _is_content_sufficient(nav_text)

    def test_real_article_content_accepted(self):
        """Content with real paragraphs should be accepted."""
        article = (
            "This is a comprehensive guide to using the API.\n\n"
            "The API provides several endpoints for managing resources. "
            "Each endpoint accepts standard HTTP methods and returns JSON "
            "responses with appropriate status codes.\n\n"
            "For authentication, include your API key in the Authorization header."
        )
        assert _is_content_sufficient(article)

    def test_short_valid_content_accepted(self):
        """Short content with fewer than threshold lines should pass."""
        short = "Error: Connection refused\nPlease check your network settings.\nRetry later."
        # Pad to meet minimum length
        short = short + " " * (101 - len(short)) if len(short) < 101 else short
        assert _is_content_sufficient(short)

    def test_mixed_changelog_content_accepted(self):
        """Mixed content with both short and long lines should pass."""
        changelog = (
            "## v2.0.0\n"
            "- Added new authentication system with OAuth 2.0 support and "
            "token refresh capabilities\n"
            "- Fixed critical bug in data processing pipeline that caused "
            "memory leaks under heavy load\n"
            "## v1.9.0\n"
            "- Minor updates"
        )
        assert _is_content_sufficient(changelog)


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

    @patch("toolregistry_hub.fetch._http_get")
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

    @patch("toolregistry_hub.fetch._http_get")
    def test_not_supported_returns_empty(self, mock_get):
        mock_response = MagicMock()
        mock_response.headers = {"content-type": "text/html; charset=utf-8"}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = _get_content_with_markdown_negotiation("https://example.com")
        assert result == ""

    @patch("toolregistry_hub.fetch._http_get")
    def test_http_error_returns_empty(self, mock_get):
        mock_get.side_effect = HttpConnectionError("Connection refused")

        result = _get_content_with_markdown_negotiation("https://example.com")
        assert result == ""

    @patch("toolregistry_hub.fetch._http_get")
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

    @patch("toolregistry_hub.fetch._http_post")
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

    @patch("toolregistry_hub.fetch._http_post")
    def test_empty_content_returns_empty(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"code": 200, "data": {"content": ""}}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = _jina_reader_request("https://example.com")
        assert result == ""

    @patch("toolregistry_hub.fetch._http_post")
    def test_http_error_returns_empty(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = HTTPError(
            400, "Bad Request", "https://r.jina.ai/"
        )
        mock_post.return_value = mock_response

        result = _jina_reader_request("https://example.com")
        assert result == ""

    @patch("toolregistry_hub.fetch._http_post")
    def test_uses_post_method(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"code": 200, "data": {"content": "test"}}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        _jina_reader_request("https://example.com")
        mock_post.assert_called_once()

    @patch("toolregistry_hub.fetch._http_post")
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

    @patch("toolregistry_hub.fetch._http_post")
    def test_sends_url_in_json_body(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"code": 200, "data": {"content": "test"}}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        _jina_reader_request("https://example.com/page")

        call_kwargs = mock_post.call_args
        json_body = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert json_body == {"url": "https://example.com/page"}

    @patch("toolregistry_hub.fetch._http_post")
    def test_timeout_error_returns_empty(self, mock_post):
        mock_post.side_effect = HttpTimeoutError("Read timed out")

        result = _jina_reader_request("https://example.com")
        assert result == ""

    @patch("toolregistry_hub.fetch._http_post")
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

    @patch("toolregistry_hub.fetch._http_post")
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
# _fetch_raw tests
# ============================================================


class TestFetchRaw:
    """Tests for the _fetch_raw function."""

    @patch("toolregistry_hub.fetch._http_get")
    def test_success_returns_body_and_content_type(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = "<html><body>Hello</body></html>"
        mock_response.headers = {"content-type": "text/html; charset=utf-8"}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        body, ct = _fetch_raw("https://example.com")
        assert body == "<html><body>Hello</body></html>"
        assert ct == "text/html"

    @patch("toolregistry_hub.fetch._http_get")
    def test_content_type_stripped_and_lowercased(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = '{"key": "value"}'
        mock_response.headers = {"content-type": "Application/JSON ; charset=utf-8"}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        _, ct = _fetch_raw("https://example.com/api")
        assert ct == "application/json"

    @patch("toolregistry_hub.fetch._http_get")
    def test_missing_content_type_header(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = "some content"
        mock_response.headers = {}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        body, ct = _fetch_raw("https://example.com")
        assert body == "some content"
        assert ct == ""

    @patch("toolregistry_hub.fetch._http_get")
    def test_http_4xx_error_returns_empty_no_retry(self, mock_get):
        """4xx errors are definitive and must not be retried."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.raise_for_status.side_effect = HTTPError(
            403, "Forbidden", "https://example.com"
        )
        mock_get.return_value = mock_response

        body, ct = _fetch_raw("https://example.com")
        assert body == ""
        assert ct == ""
        assert mock_get.call_count == 1

    @patch("toolregistry_hub.fetch._http_get")
    def test_http_404_no_retry(self, mock_get):
        """404 Not Found is a client error and must not be retried."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = HTTPError(
            404, "Not Found", "https://example.com"
        )
        mock_get.return_value = mock_response

        body, ct = _fetch_raw("https://example.com")
        assert body == ""
        assert ct == ""
        assert mock_get.call_count == 1

    @patch("toolregistry_hub.fetch.time.sleep")
    @patch("toolregistry_hub.fetch._http_get")
    def test_http_500_retries(self, mock_get, mock_sleep):
        """5xx errors should be retried with exponential backoff."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = HTTPError(
            500, "Internal Server Error", "https://example.com"
        )
        mock_get.return_value = mock_response

        body, ct = _fetch_raw("https://example.com")
        assert body == ""
        assert ct == ""
        assert mock_get.call_count == 3
        assert mock_sleep.call_count == 2

    @patch("toolregistry_hub.fetch.time.sleep")
    @patch("toolregistry_hub.fetch._http_get")
    def test_http_503_retries_then_succeeds(self, mock_get, mock_sleep):
        """Retry succeeds on second attempt after a 5xx error."""
        mock_error_response = MagicMock()
        mock_error_response.status_code = 503
        mock_error_response.raise_for_status.side_effect = HTTPError(
            503, "Service Unavailable", "https://example.com"
        )

        mock_ok_response = MagicMock()
        mock_ok_response.text = "<html><body>Success</body></html>"
        mock_ok_response.headers = {"content-type": "text/html"}
        mock_ok_response.raise_for_status = MagicMock()

        mock_get.side_effect = [mock_error_response, mock_ok_response]

        body, ct = _fetch_raw("https://example.com")
        assert body == "<html><body>Success</body></html>"
        assert ct == "text/html"
        assert mock_get.call_count == 2

    @patch("toolregistry_hub.fetch.time.sleep")
    @patch("toolregistry_hub.fetch._http_get")
    def test_timeout_retries(self, mock_get, mock_sleep):
        """Timeout errors should be retried."""
        mock_get.side_effect = HttpTimeoutError("Read timed out")

        body, ct = _fetch_raw("https://example.com")
        assert body == ""
        assert ct == ""
        assert mock_get.call_count == 3

    @patch("toolregistry_hub.fetch.time.sleep")
    @patch("toolregistry_hub.fetch._http_get")
    def test_connect_error_retries(self, mock_get, mock_sleep):
        """Connection errors should be retried."""
        mock_get.side_effect = HttpConnectionError("Connection refused")

        body, ct = _fetch_raw("https://example.com")
        assert body == ""
        assert ct == ""
        assert mock_get.call_count == 3

    @patch("toolregistry_hub.fetch.time.sleep")
    @patch("toolregistry_hub.fetch._http_get")
    def test_exponential_backoff_delays(self, mock_get, mock_sleep):
        """Verify exponential backoff delays between retries."""
        mock_get.side_effect = HttpConnectionError("Connection refused")

        _fetch_raw("https://example.com")

        delays = [call.args[0] for call in mock_sleep.call_args_list]
        assert delays == [1.0, 2.0]

    @patch("toolregistry_hub.fetch._http_get")
    def test_passes_proxy(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = "<html></html>"
        mock_response.headers = {"content-type": "text/html"}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        _fetch_raw("https://example.com", proxy="http://proxy:8080")

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

    @pytest.mark.parametrize(
        "tag,attrs,html_template",
        [
            ("main", None, "<main>{content}</main>"),
            ("article", None, "<article>{content}</article>"),
            ("div", {"class": "content"}, '<div class="content">{content}</div>'),
            (
                "div",
                {"class": "post-content"},
                '<div class="post-content">{content}</div>',
            ),
            (
                "div",
                {"class": "entry-content"},
                '<div class="entry-content">{content}</div>',
            ),
            (
                "div",
                {"class": "article-body"},
                '<div class="article-body">{content}</div>',
            ),
            (
                "div",
                {"class": "article-content"},
                '<div class="article-content">{content}</div>',
            ),
            ("div", {"id": "content"}, '<div id="content">{content}</div>'),
            (
                "section",
                {"class": "content"},
                '<section class="content">{content}</section>',
            ),
            (
                "div",
                {"class": "markdown-body"},
                '<div class="markdown-body">{content}</div>',
            ),
            ("div", {"class": "post"}, '<div class="post">{content}</div>'),
            ("div", {"class": "entry"}, '<div class="entry">{content}</div>'),
            (
                "div",
                {"class": "page-content"},
                '<div class="page-content">{content}</div>',
            ),
            (
                "div",
                {"class": "main-content"},
                '<div class="main-content">{content}</div>',
            ),
            (
                "div",
                {"id": "main-content"},
                '<div id="main-content">{content}</div>',
            ),
            (
                "div",
                {"class": "blog-post"},
                '<div class="blog-post">{content}</div>',
            ),
            (
                "div",
                {"class": "post-body"},
                '<div class="post-body">{content}</div>',
            ),
            (
                "div",
                {"class": "story-body"},
                '<div class="story-body">{content}</div>',
            ),
        ],
    )
    def test_soup_selector_finds_content(self, tag, attrs, html_template):
        """Each selector in _SOUP_CONTENT_SELECTORS should extract content."""
        inner = "<p>Target content from this container.</p>"
        container = html_template.format(content=inner)
        html = f"""
        <html><body>
            <div class="sidebar">Sidebar noise</div>
            {container}
        </body></html>
        """
        result = _extract_with_soup(html)
        assert "Target content" in result

    def test_soup_selectors_constant_is_used(self):
        """Verify _SOUP_CONTENT_SELECTORS is a non-empty list of tuples."""
        assert len(_SOUP_CONTENT_SELECTORS) > 3
        for entry in _SOUP_CONTENT_SELECTORS:
            assert isinstance(entry, tuple)
            assert len(entry) == 2


# ============================================================
# _extract integration tests
# ============================================================


class TestExtract:
    """Integration tests for the _extract function."""

    @patch("toolregistry_hub.fetch._get_content_with_jina_reader")
    @patch("toolregistry_hub.fetch._extract_with_soup")
    @patch("toolregistry_hub.fetch._extract_with_readability")
    @patch("toolregistry_hub.fetch._fetch_raw")
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
    @patch("toolregistry_hub.fetch._fetch_raw")
    @patch("toolregistry_hub.fetch._get_content_with_markdown_negotiation")
    def test_readability_sufficient_content(
        self, mock_md, mock_fetch, mock_readability, mock_soup, mock_jina
    ):
        mock_md.return_value = ""
        mock_fetch.return_value = ("<html>...</html>", "text/html")
        mock_readability.return_value = "This is a long enough article. " * 10
        mock_soup.return_value = "Short soup."
        result = _extract("https://example.com")
        assert "long enough article" in result
        mock_jina.assert_not_called()

    @patch("toolregistry_hub.fetch._get_content_with_jina_reader")
    @patch("toolregistry_hub.fetch._extract_with_soup")
    @patch("toolregistry_hub.fetch._extract_with_readability")
    @patch("toolregistry_hub.fetch._fetch_raw")
    @patch("toolregistry_hub.fetch._get_content_with_markdown_negotiation")
    def test_readability_fails_soup_sufficient(
        self, mock_md, mock_fetch, mock_readability, mock_soup, mock_jina
    ):
        mock_md.return_value = ""
        mock_fetch.return_value = ("<html>...</html>", "text/html")
        mock_readability.return_value = ""
        mock_soup.return_value = "Soup extracted content is good enough. " * 10
        result = _extract("https://example.com")
        assert "Soup extracted" in result
        mock_jina.assert_not_called()

    @patch("toolregistry_hub.fetch._get_content_with_jina_reader")
    @patch("toolregistry_hub.fetch._extract_with_soup")
    @patch("toolregistry_hub.fetch._extract_with_readability")
    @patch("toolregistry_hub.fetch._fetch_raw")
    @patch("toolregistry_hub.fetch._get_content_with_markdown_negotiation")
    def test_local_spa_shell_triggers_jina(
        self, mock_md, mock_fetch, mock_readability, mock_soup, mock_jina
    ):
        mock_md.return_value = ""
        mock_fetch.return_value = ("<html>...</html>", "text/html")
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
    @patch("toolregistry_hub.fetch._fetch_raw")
    @patch("toolregistry_hub.fetch._get_content_with_markdown_negotiation")
    def test_no_html_triggers_jina(
        self, mock_md, mock_fetch, mock_readability, mock_soup, mock_jina
    ):
        mock_md.return_value = ""
        mock_fetch.return_value = ("", "")
        mock_jina.return_value = "# Jina Content\nFetched via Jina. " * 10

        result = _extract("https://example.com")
        assert "Jina Content" in result
        mock_readability.assert_not_called()
        mock_soup.assert_not_called()

    @patch("toolregistry_hub.fetch._get_content_with_jina_reader")
    @patch("toolregistry_hub.fetch._extract_with_soup")
    @patch("toolregistry_hub.fetch._extract_with_readability")
    @patch("toolregistry_hub.fetch._fetch_raw")
    @patch("toolregistry_hub.fetch._get_content_with_markdown_negotiation")
    def test_jina_failure_falls_back_to_local(
        self, mock_md, mock_fetch, mock_readability, mock_soup, mock_jina
    ):
        mock_md.return_value = ""
        mock_fetch.return_value = ("<html>...</html>", "text/html")
        mock_readability.return_value = "Short low quality"
        mock_soup.return_value = ""
        mock_jina.return_value = ""

        result = _extract("https://example.com")
        assert "Short low quality" in result

    @patch("toolregistry_hub.fetch._get_content_with_jina_reader")
    @patch("toolregistry_hub.fetch._extract_with_soup")
    @patch("toolregistry_hub.fetch._extract_with_readability")
    @patch("toolregistry_hub.fetch._fetch_raw")
    @patch("toolregistry_hub.fetch._get_content_with_markdown_negotiation")
    def test_all_strategies_fail(
        self, mock_md, mock_fetch, mock_readability, mock_soup, mock_jina
    ):
        mock_md.return_value = ""
        mock_fetch.return_value = ("", "")
        mock_jina.return_value = ""

        result = _extract("https://example.com")
        assert result == "Unable to fetch content"

    @patch("toolregistry_hub.fetch._get_content_with_jina_reader")
    @patch("toolregistry_hub.fetch._extract_with_soup")
    @patch("toolregistry_hub.fetch._extract_with_readability")
    @patch("toolregistry_hub.fetch._fetch_raw")
    @patch("toolregistry_hub.fetch._get_content_with_markdown_negotiation")
    def test_non_html_content_type_short_circuits(
        self, mock_md, mock_fetch, mock_readability, mock_soup, mock_jina
    ):
        """Non-HTML content types should be returned directly."""
        mock_md.return_value = ""
        json_body = '{"results": [{"id": 1, "title": "Test"}]}'
        mock_fetch.return_value = (json_body, "application/json")

        result = _extract("https://api.example.com/data")
        assert "results" in result
        # HTML extraction should be skipped entirely
        mock_readability.assert_not_called()
        mock_soup.assert_not_called()
        mock_jina.assert_not_called()

    @patch("toolregistry_hub.fetch._get_content_with_jina_reader")
    @patch("toolregistry_hub.fetch._extract_with_soup")
    @patch("toolregistry_hub.fetch._extract_with_readability")
    @patch("toolregistry_hub.fetch._fetch_raw")
    @patch("toolregistry_hub.fetch._get_content_with_markdown_negotiation")
    def test_plain_text_content_type_short_circuits(
        self, mock_md, mock_fetch, mock_readability, mock_soup, mock_jina
    ):
        """text/plain should be returned directly without HTML extraction."""
        mock_md.return_value = ""
        plain_body = "This is a plain text file with enough content. " * 5
        mock_fetch.return_value = (plain_body, "text/plain")

        result = _extract("https://example.com/readme.txt")
        assert "plain text file" in result
        mock_readability.assert_not_called()
        mock_soup.assert_not_called()
        mock_jina.assert_not_called()

    @pytest.mark.parametrize("content_type", sorted(_NON_HTML_CONTENT_TYPES))
    @patch("toolregistry_hub.fetch._get_content_with_jina_reader")
    @patch("toolregistry_hub.fetch._extract_with_soup")
    @patch("toolregistry_hub.fetch._extract_with_readability")
    @patch("toolregistry_hub.fetch._fetch_raw")
    @patch("toolregistry_hub.fetch._get_content_with_markdown_negotiation")
    def test_all_non_html_types_short_circuit(
        self,
        mock_md,
        mock_fetch,
        mock_readability,
        mock_soup,
        mock_jina,
        content_type,
    ):
        """Every registered non-HTML content type should bypass extraction."""
        mock_md.return_value = ""
        mock_fetch.return_value = ("some content body", content_type)

        result = _extract("https://example.com/file")
        assert "some content body" in result
        mock_readability.assert_not_called()
        mock_soup.assert_not_called()

    @patch("toolregistry_hub.fetch._get_content_with_jina_reader")
    @patch("toolregistry_hub.fetch._extract_with_soup")
    @patch("toolregistry_hub.fetch._extract_with_readability")
    @patch("toolregistry_hub.fetch._fetch_raw")
    @patch("toolregistry_hub.fetch._get_content_with_markdown_negotiation")
    def test_html_content_type_uses_extraction_pipeline(
        self, mock_md, mock_fetch, mock_readability, mock_soup, mock_jina
    ):
        """text/html should go through the normal extraction pipeline."""
        mock_md.return_value = ""
        mock_fetch.return_value = ("<html><body>Page</body></html>", "text/html")
        mock_readability.return_value = "Extracted article content. " * 10
        mock_soup.return_value = ""

        result = _extract("https://example.com")
        assert "Extracted article" in result
        mock_readability.assert_called_once()


# ============================================================
# Jina API key tests
# ============================================================


class TestJinaApiKey:
    """Tests for Jina API key support in Fetch."""

    @patch("toolregistry_hub.fetch._http_post")
    def test_api_key_in_authorization_header(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"code": 200, "data": {"content": "test"}}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        _jina_reader_request("https://example.com", api_key="test-key-123")

        call_kwargs = mock_post.call_args
        headers = call_kwargs.kwargs.get("headers") or call_kwargs[1].get("headers")
        assert headers["Authorization"] == "Bearer test-key-123"

    @patch("toolregistry_hub.fetch._http_post")
    def test_no_api_key_no_authorization_header(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"code": 200, "data": {"content": "test"}}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        _jina_reader_request("https://example.com")

        call_kwargs = mock_post.call_args
        headers = call_kwargs.kwargs.get("headers") or call_kwargs[1].get("headers")
        assert "Authorization" not in headers

    @patch("toolregistry_hub.fetch._http_post")
    def test_401_marks_key_failed(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = HTTPError(
            401, "Unauthorized", "https://r.jina.ai/"
        )
        mock_post.return_value = mock_response

        parser = APIKeyParser(api_keys="key1,key2")
        _jina_reader_request(
            "https://example.com",
            api_key="key1",
            api_key_parser=parser,
        )

        assert "key1" in parser._failed_keys

    @patch("toolregistry_hub.fetch._http_post")
    def test_429_marks_key_rate_limited(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.raise_for_status.side_effect = HTTPError(
            429, "Too Many Requests", "https://r.jina.ai/"
        )
        mock_post.return_value = mock_response

        parser = APIKeyParser(api_keys="key1,key2")
        _jina_reader_request(
            "https://example.com",
            api_key="key1",
            api_key_parser=parser,
        )

        assert "key1" in parser._failed_keys
        reason, _, ttl = parser._failed_keys["key1"]
        assert reason == "rate limited"
        assert ttl == 300.0

    @patch("toolregistry_hub.fetch._http_post")
    def test_500_does_not_mark_key_failed(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = HTTPError(
            500, "Server Error", "https://r.jina.ai/"
        )
        mock_post.return_value = mock_response

        parser = APIKeyParser(api_keys="key1")
        _jina_reader_request(
            "https://example.com",
            api_key="key1",
            api_key_parser=parser,
        )

        assert "key1" not in parser._failed_keys

    def test_fetch_instance_with_api_keys(self):
        fetcher = Fetch(api_keys="key1,key2,key3")
        assert fetcher.api_key_parser is not None
        assert len(fetcher.api_key_parser.api_keys) == 3

    def test_fetch_instance_without_api_keys(self):
        with patch.dict("os.environ", {}, clear=False):
            import os

            os.environ.pop("JINA_API_KEY", None)
            fetcher = Fetch()
            assert fetcher.api_key_parser is None

    @patch.dict("os.environ", {"JINA_API_KEY": "env-key-1,env-key-2"})
    def test_fetch_instance_from_env(self):
        fetcher = Fetch()
        assert fetcher.api_key_parser is not None
        assert len(fetcher.api_key_parser.api_keys) == 2

    def test_is_configured_always_true(self):
        fetcher = Fetch()
        assert fetcher._is_configured() is True

    def test_is_configured_true_with_keys(self):
        fetcher = Fetch(api_keys="key1")
        assert fetcher._is_configured() is True
