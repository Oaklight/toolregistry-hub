"""Unit tests for WebSearchBing module."""

from unittest.mock import Mock, patch, MagicMock
import httpx
from toolregistry.hub.websearch.websearch_bing import WebSearchBing, _WebSearchEntryBing


class TestWebSearchEntryBing:
    """Test cases for _WebSearchEntryBing class."""
    
    def test_create_entry(self):
        """Test creating a Bing search entry."""
        entry = _WebSearchEntryBing(
            url="https://example.com",
            title="Example Title",
            content="Example content"
        )
        
        assert entry["url"] == "https://example.com"
        assert entry["title"] == "Example Title"
        assert entry["content"] == "Example content"


class TestWebSearchBing:
    """Test cases for WebSearchBing class."""
    
    def test_init_default(self):
        """Test WebSearchBing initialization with defaults."""
        searcher = WebSearchBing()
        
        assert searcher.bing_base_url == "https://www.bing.com/search"
        assert searcher.proxy is None
    
    def test_init_custom_base_url(self):
        """Test WebSearchBing initialization with custom base URL."""
        custom_url = "https://bing.co.uk"
        searcher = WebSearchBing(bing_base_url=custom_url)
        
        assert searcher.bing_base_url == "https://bing.co.uk/search"
    
    def test_init_with_proxy(self):
        """Test WebSearchBing initialization with proxy."""
        proxy = "http://proxy.example.com:8080"
        searcher = WebSearchBing(proxy=proxy)
        
        assert searcher.proxy == proxy
    
    def test_extract_real_url_normal_url(self):
        """Test extracting real URL from normal URL."""
        normal_url = "https://example.com/page"
        result = WebSearchBing._extract_real_url(normal_url)
        
        assert result == normal_url
    
    def test_extract_real_url_bing_redirect_base64(self):
        """Test extracting real URL from Bing redirect with base64 encoding."""
        # Mock a Bing redirect URL with base64 encoded target
        import base64
        target_url = "https://example.com"
        encoded = base64.b64encode(target_url.encode()).decode()
        bing_url = f"https://www.bing.com/ck/a?u=a1{encoded}&p=something"
        
        result = WebSearchBing._extract_real_url(bing_url)
        
        assert result == target_url
    
    def test_extract_real_url_bing_redirect_unquote(self):
        """Test extracting real URL from Bing redirect with URL encoding."""
        from urllib.parse import quote
        target_url = "https://example.com/path with spaces"
        encoded_url = quote(target_url)
        bing_url = f"https://www.bing.com/ck/a?u={encoded_url}&p=something"
        
        result = WebSearchBing._extract_real_url(bing_url)
        
        # Should fall back to unquoting since base64 decode will fail
        assert "example.com" in result
    
    def test_extract_real_url_invalid_base64(self):
        """Test extracting real URL with invalid base64."""
        bing_url = "https://www.bing.com/ck/a?u=a1invalid_base64&p=something"

        result = WebSearchBing._extract_real_url(bing_url)

        # The implementation returns the encoded part when base64 fails, then tries URL unquoting
        # which returns just the 'u' parameter value
        assert result == "a1invalid_base64"
    
    def test_extract_real_url_no_u_parameter(self):
        """Test extracting real URL when no 'u' parameter exists."""
        bing_url = "https://www.bing.com/ck/a?p=something&q=query"
        
        result = WebSearchBing._extract_real_url(bing_url)
        
        assert result == bing_url
    
    @patch('toolregistry.hub.websearch.websearch_bing.WebSearchBing._meta_search_bing')
    @patch('toolregistry.hub.websearch.websearch_bing.filter_search_results')
    @patch('toolregistry.hub.websearch.websearch_bing.ProcessPoolExecutor')
    def test_search_success(self, mock_executor, mock_filter, mock_meta_search):
        """Test successful search operation."""
        # Mock meta search results
        mock_meta_search.return_value = [
            _WebSearchEntryBing(url="https://example1.com", title="Title 1", content="Content 1"),
            _WebSearchEntryBing(url="https://example2.com", title="Title 2", content="Content 2")
        ]
        
        # Mock filter results
        mock_filter.return_value = [
            {"url": "https://example1.com", "title": "Title 1", "content": "Content 1"},
            {"url": "https://example2.com", "title": "Title 2", "content": "Content 2"}
        ]
        
        # Mock executor
        mock_executor_instance = MagicMock()
        mock_executor.return_value.__enter__.return_value = mock_executor_instance
        mock_executor_instance.map.return_value = [
            {"url": "https://example1.com", "title": "Title 1", "content": "Enriched 1", "excerpt": "Content 1"},
            {"url": "https://example2.com", "title": "Title 2", "content": "Enriched 2", "excerpt": "Content 2"}
        ]
        
        searcher = WebSearchBing()
        results = searcher.search("test query", number_results=2)
        
        assert len(results) == 2
        assert results[0]["url"] == "https://example1.com"
        assert results[1]["title"] == "Title 2"
    
    @patch('toolregistry.hub.websearch.websearch_bing.WebSearchBing._meta_search_bing')
    def test_search_request_error(self, mock_meta_search):
        """Test search with request error."""
        mock_meta_search.side_effect = httpx.RequestError("Network error")
        
        searcher = WebSearchBing()
        results = searcher.search("test query")
        
        assert results == []
    
    @patch('toolregistry.hub.websearch.websearch_bing.WebSearchBing._meta_search_bing')
    def test_search_http_error(self, mock_meta_search):
        """Test search with HTTP error."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_meta_search.side_effect = httpx.HTTPStatusError(
            "Too Many Requests", 
            request=Mock(), 
            response=mock_response
        )
        
        searcher = WebSearchBing()
        results = searcher.search("test query")
        
        assert results == []
    
    @patch('toolregistry.hub.websearch.websearch_bing.httpx.Client')
    def test_meta_search_bing(self, mock_client):
        """Test _meta_search_bing method."""
        # Mock response
        mock_response = Mock()
        mock_response.text = '''
        <li class="b_algo">
            <h2><a href="https://example.com">Example Title</a></h2>
            <div class="b_caption">
                <p>Example description</p>
            </div>
        </li>
        '''
        
        # Mock client
        mock_client_instance = MagicMock()
        mock_client.return_value.__enter__.return_value = mock_client_instance
        mock_client_instance.get.return_value = mock_response
        
        results = WebSearchBing._meta_search_bing("test query", num_results=1)
        
        assert isinstance(results, list)
        mock_client_instance.get.assert_called()
    
    def test_parse_bing_entries_valid_html(self):
        """Test parsing valid Bing search results HTML."""
        html = '''
        <li class="b_algo">
            <h2><a href="https://example.com">Example Title</a></h2>
            <div class="b_caption">
                <p>Example description</p>
            </div>
        </li>
        '''
        
        fetched_links = set()
        results = list(WebSearchBing._parse_bing_entries(html, fetched_links, 5))
        
        assert len(results) == 1
        assert results[0]["url"] == "https://example.com"
        assert results[0]["title"] == "Example Title"
        assert results[0]["content"] == "Example description"
    
    def test_parse_bing_entries_with_redirect_url(self):
        """Test parsing Bing entries with redirect URLs."""
        import base64
        target_url = "https://example.com"
        encoded = base64.b64encode(target_url.encode()).decode()
        redirect_url = f"https://www.bing.com/ck/a?u=a1{encoded}"
        
        html = f'''
        <li class="b_algo">
            <h2><a href="{redirect_url}">Example Title</a></h2>
            <div class="b_caption">
                <p>Example description</p>
            </div>
        </li>
        '''
        
        fetched_links = set()
        results = list(WebSearchBing._parse_bing_entries(html, fetched_links, 5))
        
        assert len(results) == 1
        assert results[0]["url"] == target_url
        assert results[0]["title"] == "Example Title"
    
    def test_parse_bing_entries_empty_html(self):
        """Test parsing empty HTML."""
        html = "<html><body></body></html>"
        
        fetched_links = set()
        results = list(WebSearchBing._parse_bing_entries(html, fetched_links, 5))
        
        assert len(results) == 0
    
    def test_parse_bing_entries_malformed_html(self):
        """Test parsing malformed HTML."""
        html = '''
        <li class="b_algo">
            <h2><!-- Missing link --></h2>
            <div class="b_caption">
                <!-- Missing paragraph -->
            </div>
        </li>
        '''
        
        fetched_links = set()
        results = list(WebSearchBing._parse_bing_entries(html, fetched_links, 5))
        
        # Should return 0 results due to missing required elements
        assert len(results) == 0
    
    def test_parse_bing_entries_duplicate_links(self):
        """Test parsing HTML with duplicate links."""
        html = '''
        <li class="b_algo">
            <h2><a href="https://example.com">Title 1</a></h2>
            <div class="b_caption">
                <p>Description 1</p>
            </div>
        </li>
        <li class="b_algo">
            <h2><a href="https://example.com">Title 2</a></h2>
            <div class="b_caption">
                <p>Description 2</p>
            </div>
        </li>
        '''
        
        fetched_links = set()
        results = list(WebSearchBing._parse_bing_entries(html, fetched_links, 5))
        
        # Should only return one result due to duplicate URL filtering
        assert len(results) == 1
        assert "https://example.com" in fetched_links
    
    def test_parse_bing_entries_max_results(self):
        """Test parsing HTML with max results limit."""
        html = '''
        <li class="b_algo">
            <h2><a href="https://example1.com">Title 1</a></h2>
            <div class="b_caption">
                <p>Description 1</p>
            </div>
        </li>
        <li class="b_algo">
            <h2><a href="https://example2.com">Title 2</a></h2>
            <div class="b_caption">
                <p>Description 2</p>
            </div>
        </li>
        '''
        
        fetched_links = set()
        results = list(WebSearchBing._parse_bing_entries(html, fetched_links, 1))
        
        # Should only return 1 result due to max_results limit
        assert len(results) == 1
    
    @patch('toolregistry.hub.websearch.websearch_bing.filter_search_results')
    @patch('toolregistry.hub.websearch.websearch_bing.WebSearchBing._meta_search_bing')
    def test_search_with_custom_timeout(self, mock_meta_search, mock_filter):
        """Test search with custom timeout."""
        mock_meta_search.return_value = []
        mock_filter.return_value = []
        
        searcher = WebSearchBing()
        searcher.search("test", timeout=30)
        
        # Verify meta_search was called with custom timeout
        call_args = mock_meta_search.call_args
        assert call_args[1]['timeout'] == 30


class TestWebSearchBingIntegration:
    """Integration tests for WebSearchBing."""
    
    def test_search_method_signature(self):
        """Test search method accepts all expected parameters."""
        searcher = WebSearchBing()
        
        # This should not raise any errors
        with patch('toolregistry.hub.websearch.websearch_bing.WebSearchBing._meta_search_bing') as mock_search:
            mock_search.return_value = []
            
            searcher.search(
                query="test",
                number_results=5,
                threshold=0.3,  # This parameter is kept for compatibility but not used
                timeout=10
            )
            
            assert mock_search.called
    
    def test_url_extraction_edge_cases(self):
        """Test URL extraction with various edge cases."""
        # Test with malformed URL
        malformed_url = "not_a_url"
        result = WebSearchBing._extract_real_url(malformed_url)
        assert result == malformed_url
        
        # Test with empty string
        result = WebSearchBing._extract_real_url("")
        assert result == ""
        
        # Test with None (should handle gracefully)
        try:
            result = WebSearchBing._extract_real_url(None)
            # If it doesn't raise an exception, that's fine too
        except (TypeError, AttributeError):
            # Expected behavior for None input
            pass