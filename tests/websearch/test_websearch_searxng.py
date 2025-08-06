"""Unit tests for WebSearchSearXNG module."""

from unittest.mock import Mock, patch, MagicMock
import httpx
from toolregistry_hub.websearch.websearch_searxng import WebSearchSearXNG, _WebSearchEntrySearXNG


class TestWebSearchEntrySearXNG:
    """Test cases for _WebSearchEntrySearXNG class."""
    
    def test_create_entry(self):
        """Test creating a SearXNG search entry."""
        entry = _WebSearchEntrySearXNG(
            content="Example content",
            engine="google",
            template="results.html",
            parsed_url=["https", "example.com", "/path"],
            engines=["google", "bing"],
            positions=[1, 2],
            score=0.8,
            category="general"
        )
        
        assert entry["content"] == "Example content"
        assert entry["engine"] == "google"
        assert entry["score"] == 0.8
        assert entry["category"] == "general"


class TestWebSearchSearXNG:
    """Test cases for WebSearchSearXNG class."""
    
    def test_init_default(self):
        """Test WebSearchSearXNG initialization with defaults."""
        searcher = WebSearchSearXNG("http://localhost:8080")
        
        assert searcher.searxng_base_url == "http://localhost:8080/search"
        assert searcher.proxy is None
    
    def test_init_custom_base_url(self):
        """Test WebSearchSearXNG initialization with custom base URL."""
        custom_url = "https://searx.example.com"
        searcher = WebSearchSearXNG(custom_url)
        
        assert searcher.searxng_base_url == "https://searx.example.com/search"
    
    def test_init_with_proxy(self):
        """Test WebSearchSearXNG initialization with proxy."""
        proxy = "http://proxy.example.com:8080"
        searcher = WebSearchSearXNG("http://localhost:8080", proxy=proxy)
        
        assert searcher.proxy == proxy
    
    def test_init_base_url_with_search_path(self):
        """Test initialization when base URL already has /search path."""
        searcher = WebSearchSearXNG("http://localhost:8080/search")
        
        assert searcher.searxng_base_url == "http://localhost:8080/search"
    
    @patch('toolregistry_hub.websearch.websearch_searxng.WebSearchSearXNG._meta_search_searxng')
    @patch('toolregistry_hub.websearch.websearch_searxng.filter_search_results')
    @patch('toolregistry_hub.websearch.websearch_searxng.ProcessPoolExecutor')
    def test_search_success(self, mock_executor, mock_filter, mock_meta_search):
        """Test successful search operation."""
        # Mock meta search results
        mock_meta_search.return_value = [
            {
                "url": "https://example1.com",
                "title": "Title 1",
                "content": "Content 1",
                "score": 0.8,
                "engines": ["google"]
            },
            {
                "url": "https://example2.com",
                "title": "Title 2",
                "content": "Content 2",
                "score": 0.7,
                "engines": ["bing"]
            }
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
        
        searcher = WebSearchSearXNG("http://localhost:8080")
        results = searcher.search("test query", number_results=2)
        
        assert len(results) == 2
        assert results[0]["url"] == "https://example1.com"
        assert results[1]["title"] == "Title 2"
    
    @patch('toolregistry_hub.websearch.websearch_searxng.WebSearchSearXNG._meta_search_searxng')
    def test_search_with_threshold_filtering(self, mock_meta_search):
        """Test search with score threshold filtering."""
        # Mock results with different scores
        mock_meta_search.return_value = [
            {"url": "https://high-score.com", "title": "High Score", "content": "Content", "score": 0.8},
            {"url": "https://low-score.com", "title": "Low Score", "content": "Content", "score": 0.1},
            {"url": "https://medium-score.com", "title": "Medium Score", "content": "Content", "score": 0.5}
        ]
        
        with patch('toolregistry_hub.websearch.websearch_searxng.filter_search_results') as mock_filter:
            with patch('toolregistry_hub.websearch.websearch_searxng.ProcessPoolExecutor'):
                mock_filter.return_value = []  # Empty after filtering
                
                searcher = WebSearchSearXNG("http://localhost:8080")
                results = searcher.search("test query", threshold=0.3)
                
                # Should filter out the low score result (0.1 < 0.3)
                # Only high-score (0.8) and medium-score (0.5) should be passed to filter
                filtered_input = mock_filter.call_args[0][0]
                scores = [item.get("score", 0) for item in filtered_input]
                assert all(score >= 0.3 for score in scores)
    
    @patch('toolregistry_hub.websearch.websearch_searxng.WebSearchSearXNG._meta_search_searxng')
    def test_search_request_error(self, mock_meta_search):
        """Test search with request error."""
        mock_meta_search.side_effect = httpx.RequestError("Network error")
        
        searcher = WebSearchSearXNG("http://localhost:8080")
        results = searcher.search("test query")
        
        assert results == []
    
    @patch('toolregistry_hub.websearch.websearch_searxng.WebSearchSearXNG._meta_search_searxng')
    def test_search_http_error(self, mock_meta_search):
        """Test search with HTTP error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_meta_search.side_effect = httpx.HTTPStatusError(
            "Internal Server Error", 
            request=Mock(), 
            response=mock_response
        )
        
        searcher = WebSearchSearXNG("http://localhost:8080")
        results = searcher.search("test query")
        
        assert results == []
    
    @patch('toolregistry_hub.websearch.websearch_searxng.httpx.get')
    def test_meta_search_searxng_success(self, mock_get):
        """Test _meta_search_searxng method with successful response."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "results": [
                {
                    "url": "https://example1.com",
                    "title": "Title 1",
                    "content": "Content 1",
                    "score": 0.8,
                    "engines": ["google"]
                },
                {
                    "url": "https://example2.com",
                    "title": "Title 2",
                    "content": "Content 2",
                    "score": 0.6,
                    "engines": ["bing"]
                }
            ]
        }
        mock_get.return_value = mock_response
        
        results = WebSearchSearXNG._meta_search_searxng(
            "test query",
            searxng_base_url="http://localhost:8080/search"
        )
        
        assert len(results) == 2
        assert results[0]["score"] == 0.8  # Should be sorted by score (descending)
        assert results[1]["score"] == 0.6
        
        # Verify the request was made correctly
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[0][0] == "http://localhost:8080/search"
        assert call_args[1]["params"]["q"] == "test query"
        assert call_args[1]["params"]["format"] == "json"
    
    @patch('toolregistry_hub.websearch.websearch_searxng.httpx.get')
    def test_meta_search_searxng_with_params(self, mock_get):
        """Test _meta_search_searxng method with custom parameters."""
        mock_response = Mock()
        mock_response.json.return_value = {"results": []}
        mock_get.return_value = mock_response
        
        WebSearchSearXNG._meta_search_searxng(
            "test query",
            num_results=10,
            proxy="http://proxy.example.com:8080",
            timeout=30,
            searxng_base_url="http://localhost:8080/search"
        )
        
        call_args = mock_get.call_args
        assert call_args[1]["proxy"] == "http://proxy.example.com:8080"
        assert call_args[1]["timeout"] == 30
    
    @patch('toolregistry_hub.websearch.websearch_searxng.httpx.get')
    def test_meta_search_searxng_empty_results(self, mock_get):
        """Test _meta_search_searxng method with empty results."""
        mock_response = Mock()
        mock_response.json.return_value = {"results": []}
        mock_get.return_value = mock_response
        
        results = WebSearchSearXNG._meta_search_searxng("test query")
        
        assert results == []
    
    @patch('toolregistry_hub.websearch.websearch_searxng.httpx.get')
    def test_meta_search_searxng_no_results_key(self, mock_get):
        """Test _meta_search_searxng method when response has no 'results' key."""
        mock_response = Mock()
        mock_response.json.return_value = {"error": "No results found"}
        mock_get.return_value = mock_response
        
        results = WebSearchSearXNG._meta_search_searxng("test query")
        
        assert results == []
    
    @patch('toolregistry_hub.websearch.websearch_searxng.httpx.get')
    def test_meta_search_searxng_result_limiting(self, mock_get):
        """Test that results are limited to num_results."""
        # Create more results than requested
        mock_results = [
            {"url": f"https://example{i}.com", "title": f"Title {i}", "score": 1.0 - i*0.1}
            for i in range(15)
        ]
        
        mock_response = Mock()
        mock_response.json.return_value = {"results": mock_results}
        mock_get.return_value = mock_response
        
        results = WebSearchSearXNG._meta_search_searxng("test query", num_results=5)
        
        assert len(results) == 5
        # Should be sorted by score (descending)
        assert results[0]["score"] == 1.0
        assert results[4]["score"] == 0.6
    
    @patch('toolregistry_hub.websearch.websearch_searxng.filter_search_results')
    @patch('toolregistry_hub.websearch.websearch_searxng.WebSearchSearXNG._meta_search_searxng')
    def test_search_with_custom_timeout(self, mock_meta_search, mock_filter):
        """Test search with custom timeout."""
        mock_meta_search.return_value = []
        mock_filter.return_value = []
        
        searcher = WebSearchSearXNG("http://localhost:8080")
        searcher.search("test", timeout=30)
        
        # Verify meta_search was called with custom timeout
        call_args = mock_meta_search.call_args
        assert call_args[1]['timeout'] == 30
    
    @patch('toolregistry_hub.websearch.websearch_searxng.filter_search_results')
    @patch('toolregistry_hub.websearch.websearch_searxng.WebSearchSearXNG._meta_search_searxng')
    def test_search_result_limiting(self, mock_meta_search, mock_filter):
        """Test that search results are limited to requested number."""
        # Mock more results than requested
        mock_meta_search.return_value = [
            {"url": f"https://example{i}.com", "title": f"Title {i}", "content": f"Content {i}", "score": 0.8}
            for i in range(10)
        ]
        
        mock_filter.return_value = [
            {"url": f"https://example{i}.com", "title": f"Title {i}", "content": f"Content {i}"}
            for i in range(10)
        ]
        
        with patch('toolregistry_hub.websearch.websearch_searxng.ProcessPoolExecutor') as mock_executor:
            mock_executor_instance = MagicMock()
            mock_executor.return_value.__enter__.return_value = mock_executor_instance
            mock_executor_instance.map.return_value = [
                {"url": f"https://example{i}.com", "title": f"Title {i}", "content": f"Content {i}"}
                for i in range(3)  # Return only 3 results
            ]
            
            searcher = WebSearchSearXNG("http://localhost:8080")
            results = searcher.search("test", number_results=3)
            
            assert len(results) == 3


class TestWebSearchSearXNGIntegration:
    """Integration tests for WebSearchSearXNG."""
    
    def test_search_method_signature(self):
        """Test search method accepts all expected parameters."""
        searcher = WebSearchSearXNG("http://localhost:8080")
        
        # This should not raise any errors
        with patch('toolregistry_hub.websearch.websearch_searxng.WebSearchSearXNG._meta_search_searxng') as mock_search:
            mock_search.return_value = []
            
            searcher.search(
                query="test",
                number_results=5,
                threshold=0.3,
                timeout=10
            )
            
            assert mock_search.called
    
    def test_alias_compatibility(self):
        """Test that WebSearchSearxng alias works."""
        from toolregistry_hub.websearch.websearch_searxng import WebSearchSearxng
        
        # Should be the same class
        assert WebSearchSearxng is WebSearchSearXNG
    
    @patch('toolregistry_hub.websearch.websearch_searxng.httpx.get')
    def test_score_sorting(self, mock_get):
        """Test that results are properly sorted by score."""
        # Mock results with mixed scores
        mock_results = [
            {"url": "https://low.com", "title": "Low", "score": 0.3},
            {"url": "https://high.com", "title": "High", "score": 0.9},
            {"url": "https://medium.com", "title": "Medium", "score": 0.6}
        ]
        
        mock_response = Mock()
        mock_response.json.return_value = {"results": mock_results}
        mock_get.return_value = mock_response
        
        results = WebSearchSearXNG._meta_search_searxng("test query")
        
        # Should be sorted by score in descending order
        assert results[0]["score"] == 0.9
        assert results[1]["score"] == 0.6
        assert results[2]["score"] == 0.3
    
    def test_url_stripping(self):
        """Test that base URL is properly stripped of trailing slashes."""
        searcher1 = WebSearchSearXNG("http://localhost:8080/")
        searcher2 = WebSearchSearXNG("http://localhost:8080")
        
        assert searcher1.searxng_base_url == searcher2.searxng_base_url
        assert searcher1.searxng_base_url == "http://localhost:8080/search"