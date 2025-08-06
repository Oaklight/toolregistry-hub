"""Unit tests for WebSearchGoogle module."""

from unittest.mock import Mock, patch, MagicMock
import httpx
from toolregistry_hub.websearch.websearch_google import WebSearchGoogle, _WebSearchEntryGoogle


class TestWebSearchEntryGoogle:
    """Test cases for _WebSearchEntryGoogle class."""
    
    def test_create_entry(self):
        """Test creating a Google search entry."""
        entry = _WebSearchEntryGoogle(
            url="https://example.com",
            title="Example Title",
            content="Example content"
        )
        
        assert entry["url"] == "https://example.com"
        assert entry["title"] == "Example Title"
        assert entry["content"] == "Example content"


class TestWebSearchGoogle:
    """Test cases for WebSearchGoogle class."""
    
    def test_init_default(self):
        """Test WebSearchGoogle initialization with defaults."""
        searcher = WebSearchGoogle()
        
        assert searcher.google_base_url == "https://www.google.com/search"
        assert searcher.proxy is None
    
    def test_init_custom_base_url(self):
        """Test WebSearchGoogle initialization with custom base URL."""
        custom_url = "https://google.co.uk"
        searcher = WebSearchGoogle(google_base_url=custom_url)
        
        assert searcher.google_base_url == "https://google.co.uk/search"
    
    def test_init_with_proxy(self):
        """Test WebSearchGoogle initialization with proxy."""
        proxy = "http://proxy.example.com:8080"
        searcher = WebSearchGoogle(proxy=proxy)
        
        assert searcher.proxy == proxy
    
    def test_init_base_url_with_search_path(self):
        """Test initialization when base URL already has /search path."""
        searcher = WebSearchGoogle(google_base_url="https://www.google.com/search")
        
        assert searcher.google_base_url == "https://www.google.com/search"
    
    @patch('toolregistry_hub.websearch.websearch_google.WebSearchGoogle._meta_search_google')
    @patch('toolregistry_hub.websearch.websearch_google.filter_search_results')
    @patch('toolregistry_hub.websearch.websearch_google.ProcessPoolExecutor')
    def test_search_success(self, mock_executor, mock_filter, mock_meta_search):
        """Test successful search operation."""
        # Mock meta search results
        mock_meta_search.return_value = [
            _WebSearchEntryGoogle(url="https://example1.com", title="Title 1", content="Content 1"),
            _WebSearchEntryGoogle(url="https://example2.com", title="Title 2", content="Content 2")
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
        
        searcher = WebSearchGoogle()
        results = searcher.search("test query", number_results=2)
        
        assert len(results) == 2
        assert results[0]["url"] == "https://example1.com"
        assert results[1]["title"] == "Title 2"
        
        mock_meta_search.assert_called_once()
        mock_filter.assert_called_once()
    
    @patch('toolregistry_hub.websearch.websearch_google.WebSearchGoogle._meta_search_google')
    def test_search_request_error(self, mock_meta_search):
        """Test search with request error."""
        mock_meta_search.side_effect = httpx.RequestError("Network error")
        
        searcher = WebSearchGoogle()
        results = searcher.search("test query")
        
        assert results == []
    
    @patch('toolregistry_hub.websearch.websearch_google.WebSearchGoogle._meta_search_google')
    def test_search_http_error(self, mock_meta_search):
        """Test search with HTTP error."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_meta_search.side_effect = httpx.HTTPStatusError(
            "Too Many Requests", 
            request=Mock(), 
            response=mock_response
        )
        
        searcher = WebSearchGoogle()
        results = searcher.search("test query")
        
        assert results == []
    
    @patch('toolregistry_hub.websearch.websearch_google.httpx.Client')
    def test_meta_search_google(self, mock_client):
        """Test _meta_search_google method."""
        # Mock response
        mock_response = Mock()
        mock_response.text = '''
        <div class="ezO2md">
            <a href="/url?q=https://example.com&amp;sa=U">
                <span class="CVA68e">Example Title</span>
            </a>
            <span class="FrIlee">Example description</span>
        </div>
        '''
        
        # Mock client
        mock_client_instance = MagicMock()
        mock_client.return_value.__enter__.return_value = mock_client_instance
        mock_client_instance.get.return_value = mock_response
        
        results = WebSearchGoogle._meta_search_google("test query", num_results=1)
        
        assert isinstance(results, list)
        mock_client_instance.get.assert_called()
    
    def test_parse_google_entries_valid_html(self):
        """Test parsing valid Google search results HTML."""
        html = '''
        <div class="ezO2md">
            <a href="/url?q=https://example.com&amp;sa=U">
                <span class="CVA68e">Example Title</span>
            </a>
            <span class="FrIlee">Example description</span>
        </div>
        '''
        
        fetched_links = set()
        results = list(WebSearchGoogle._parse_google_entries(html, fetched_links, 5))
        
        assert len(results) == 1
        assert results[0]["url"] == "https://example.com"
        assert results[0]["title"] == "Example Title"
        assert results[0]["content"] == "Example description"
    
    def test_parse_google_entries_empty_html(self):
        """Test parsing empty HTML."""
        html = "<html><body></body></html>"
        
        fetched_links = set()
        results = list(WebSearchGoogle._parse_google_entries(html, fetched_links, 5))
        
        assert len(results) == 0
    
    def test_parse_google_entries_duplicate_links(self):
        """Test parsing HTML with duplicate links."""
        html = '''
        <div class="ezO2md">
            <a href="/url?q=https://example.com&amp;sa=U">
                <span class="CVA68e">Example Title 1</span>
            </a>
            <span class="FrIlee">Description 1</span>
        </div>
        <div class="ezO2md">
            <a href="/url?q=https://example.com&amp;sa=U">
                <span class="CVA68e">Example Title 2</span>
            </a>
            <span class="FrIlee">Description 2</span>
        </div>
        '''
        
        fetched_links = set()
        results = list(WebSearchGoogle._parse_google_entries(html, fetched_links, 5))
        
        # Should only return one result due to duplicate URL filtering
        assert len(results) == 1
        assert "https://example.com" in fetched_links
    
    def test_parse_google_entries_malformed_html(self):
        """Test parsing malformed HTML."""
        html = '''
        <div class="ezO2md">
            <a href="/url?q=https://example.com">
                <!-- Missing title span -->
            </a>
            <!-- Missing description span -->
        </div>
        '''
        
        fetched_links = set()
        results = list(WebSearchGoogle._parse_google_entries(html, fetched_links, 5))
        
        # Should return 0 results due to missing required elements
        assert len(results) == 0
    
    def test_parse_google_entries_max_results(self):
        """Test parsing HTML with max results limit."""
        html = '''
        <div class="ezO2md">
            <a href="/url?q=https://example1.com&amp;sa=U">
                <span class="CVA68e">Title 1</span>
            </a>
            <span class="FrIlee">Description 1</span>
        </div>
        <div class="ezO2md">
            <a href="/url?q=https://example2.com&amp;sa=U">
                <span class="CVA68e">Title 2</span>
            </a>
            <span class="FrIlee">Description 2</span>
        </div>
        '''
        
        fetched_links = set()
        results = list(WebSearchGoogle._parse_google_entries(html, fetched_links, 1))
        
        # Should only return 1 result due to max_results limit
        assert len(results) == 1
    
    @patch('toolregistry_hub.websearch.websearch_google.filter_search_results')
    @patch('toolregistry_hub.websearch.websearch_google.WebSearchGoogle._meta_search_google')
    def test_search_with_custom_timeout(self, mock_meta_search, mock_filter):
        """Test search with custom timeout."""
        mock_meta_search.return_value = []
        mock_filter.return_value = []
        
        searcher = WebSearchGoogle()
        searcher.search("test", timeout=30)
        
        # Verify meta_search was called with custom timeout
        call_args = mock_meta_search.call_args
        assert call_args[1]['timeout'] == 30
    
    @patch('toolregistry_hub.websearch.websearch_google.filter_search_results')
    @patch('toolregistry_hub.websearch.websearch_google.WebSearchGoogle._meta_search_google')
    def test_search_result_limiting(self, mock_meta_search, mock_filter):
        """Test that search results are limited to requested number."""
        # Mock more results than requested
        mock_meta_search.return_value = [
            _WebSearchEntryGoogle(url=f"https://example{i}.com", title=f"Title {i}", content=f"Content {i}")
            for i in range(10)
        ]
        
        mock_filter.return_value = [
            {"url": f"https://example{i}.com", "title": f"Title {i}", "content": f"Content {i}"}
            for i in range(10)
        ]
        
        with patch('toolregistry_hub.websearch.websearch_google.ProcessPoolExecutor') as mock_executor:
            mock_executor_instance = MagicMock()
            mock_executor.return_value.__enter__.return_value = mock_executor_instance
            mock_executor_instance.map.return_value = [
                {"url": f"https://example{i}.com", "title": f"Title {i}", "content": f"Content {i}"}
                for i in range(3)  # Return only 3 results
            ]
            
            searcher = WebSearchGoogle()
            results = searcher.search("test", number_results=3)
            
            assert len(results) == 3


class TestWebSearchGoogleIntegration:
    """Integration tests for WebSearchGoogle."""
    
    def test_search_method_signature(self):
        """Test search method accepts all expected parameters."""
        searcher = WebSearchGoogle()
        
        # This should not raise any errors
        with patch('toolregistry_hub.websearch.websearch_google.WebSearchGoogle._meta_search_google') as mock_search:
            mock_search.return_value = []
            
            searcher.search(
                query="test",
                number_results=5,
                threshold=0.3,  # This parameter is kept for compatibility but not used
                timeout=10
            )
            
            assert mock_search.called