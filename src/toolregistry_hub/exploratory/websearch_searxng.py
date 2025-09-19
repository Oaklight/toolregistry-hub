"""
SearXNG Search API Demo Implementation

This module provides a simple interface to SearXNG instances for web search functionality.
SearXNG is a free, open-source metasearch engine that aggregates results from multiple search engines.

Setup:
1. Set up a SearXNG instance (local or remote)
2. Set the instance URL as an environment variable:
   export SEARXNG_URL="http://localhost:8080"
   
   Or use a public instance (not recommended for production):
   export SEARXNG_URL="https://search.example.com"

Usage:
    from websearch_searxng import SearXNGSearch
    
    search = SearXNGSearch()
    results = search.search("python web scraping", max_results=5)
    
    for result in results:
        print(f"Title: {result['title']}")
        print(f"URL: {result['url']}")
        print(f"Content: {result['content'][:200]}...")
        print(f"Score: {result['score']}")
        print("-" * 50)

API Documentation: https://docs.searxng.org/dev/search_api.html
SearXNG Setup: https://docs.searxng.org/admin/installation.html
"""

import os
from typing import List, Dict, Optional
import httpx
from loguru import logger


class SearXNGSearch:
    """Simple SearXNG API client for web search functionality."""
    
    def __init__(self, base_url: Optional[str] = None):
        """Initialize SearXNG search client.
        
        Args:
            base_url: SearXNG instance URL. If not provided, will try to get from SEARXNG_URL env var.
        """
        self.base_url = base_url or os.getenv("SEARXNG_URL", "http://localhost:8080")
        self.base_url = self.base_url.rstrip("/")
        
        # Ensure we have the search endpoint
        if not self.base_url.endswith("/search"):
            self.search_url = f"{self.base_url}/search"
        else:
            self.search_url = self.base_url
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9"
        }
    
    def search(
        self, 
        query: str, 
        max_results: int = 5,
        categories: Optional[str] = None,
        engines: Optional[str] = None,
        language: str = "en",
        safesearch: int = 1,
        timeout: float = 10.0
    ) -> List[Dict[str, str]]:
        """Perform a web search using SearXNG API.
        
        Args:
            query: The search query string
            max_results: Maximum number of results to return
            categories: Comma-separated list of categories (e.g., "general,images")
            engines: Comma-separated list of engines (e.g., "google,bing")
            language: Language code for results (e.g., "en", "es")
            safesearch: Safe search level (0=off, 1=moderate, 2=strict)
            timeout: Request timeout in seconds
            
        Returns:
            List of search results with title, url, content, and score
        """
        if not query.strip():
            logger.warning("Empty query provided")
            return []
        
        params = {
            "q": query,
            "format": "json",
            "language": language,
            "safesearch": safesearch
        }
        
        # Add optional parameters
        if categories:
            params["categories"] = categories
        if engines:
            params["engines"] = engines
        
        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.get(
                    self.search_url,
                    headers=self.headers,
                    params=params
                )
                response.raise_for_status()
                
                data = response.json()
                results = self._parse_results(data, max_results)
                
                logger.info(f"SearXNG search for '{query}' returned {len(results)} results")
                return results
                
        except httpx.TimeoutException:
            logger.error(f"SearXNG API request timed out after {timeout}s")
            return []
        except httpx.HTTPStatusError as e:
            logger.error(f"SearXNG API HTTP error {e.response.status_code}: {e.response.text}")
            return []
        except Exception as e:
            logger.error(f"SearXNG API request failed: {e}")
            return []
    
    def _parse_results(self, data: Dict, max_results: int) -> List[Dict[str, str]]:
        """Parse SearXNG API response into standardized format.
        
        Args:
            data: Raw API response data
            max_results: Maximum number of results to return
            
        Returns:
            List of parsed search results
        """
        results = []
        raw_results = data.get("results", [])
        
        # Sort by score if available, otherwise by position
        sorted_results = sorted(
            raw_results, 
            key=lambda x: x.get("score", 0), 
            reverse=True
        )
        
        for item in sorted_results[:max_results]:
            result = {
                "title": item.get("title", "No title"),
                "url": item.get("url", ""),
                "content": item.get("content", "No content available"),
                "score": float(item.get("score", 0.0))
            }
            results.append(result)
        
        return results
    
    def search_with_metadata(self, query: str, max_results: int = 5) -> Dict:
        """Perform search and return results with additional metadata.
        
        Args:
            query: The search query string
            max_results: Maximum number of results to return
            
        Returns:
            Dictionary with 'results', 'query_info', and 'search_metadata' keys
        """
        if not query.strip():
            return {"results": [], "query_info": {}, "search_metadata": {}}
        
        params = {
            "q": query,
            "format": "json"
        }
        
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    self.search_url,
                    headers=self.headers,
                    params=params
                )
                response.raise_for_status()
                
                data = response.json()
                
                return {
                    "results": self._parse_results(data, max_results),
                    "query_info": {
                        "query": data.get("query", query),
                        "number_of_results": data.get("number_of_results", 0)
                    },
                    "search_metadata": {
                        "engines": list(set(r.get("engine", "") for r in data.get("results", []))),
                        "categories": list(set(r.get("category", "") for r in data.get("results", []))),
                        "total_results": len(data.get("results", []))
                    }
                }
                
        except Exception as e:
            logger.error(f"SearXNG search with metadata failed: {e}")
            return {"results": [], "query_info": {}, "search_metadata": {}}
    
    def search_images(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Search for images using SearXNG.
        
        Args:
            query: The search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of image results with title, url, content, and score
        """
        if not query.strip():
            return []
        
        params = {
            "q": query,
            "format": "json",
            "categories": "images"
        }
        
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    self.search_url,
                    headers=self.headers,
                    params=params
                )
                response.raise_for_status()
                
                data = response.json()
                results = []
                
                raw_results = data.get("results", [])[:max_results]
                
                for i, item in enumerate(raw_results):
                    result = {
                        "title": item.get("title", "No title"),
                        "url": item.get("img_src", item.get("url", "")),
                        "content": item.get("content", f"Image result from {item.get('engine', 'unknown')}"),
                        "score": float(item.get("score", 1.0 - i * 0.1))
                    }
                    results.append(result)
                
                logger.info(f"SearXNG image search for '{query}' returned {len(results)} results")
                return results
                
        except Exception as e:
            logger.error(f"SearXNG image search failed: {e}")
            return []
    
    def test_connection(self) -> bool:
        """Test if the SearXNG instance is accessible.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(
                    self.search_url,
                    headers=self.headers,
                    params={"q": "test", "format": "json"}
                )
                response.raise_for_status()
                data = response.json()
                
                # Check if response has expected structure
                if "results" in data:
                    logger.info(f"SearXNG connection test successful: {self.base_url}")
                    return True
                else:
                    logger.warning(f"SearXNG response missing 'results' field: {self.base_url}")
                    return False
                    
        except Exception as e:
            logger.error(f"SearXNG connection test failed for {self.base_url}: {e}")
            return False


def main():
    """Demo usage of SearXNGSearch."""
    try:
        search = SearXNGSearch()
        
        # Test connection first
        print("=== Connection Test ===")
        if not search.test_connection():
            print(f"Failed to connect to SearXNG instance at {search.base_url}")
            print("Please check that:")
            print("1. SearXNG is running")
            print("2. The URL is correct")
            print("3. JSON format is enabled in the instance")
            return
        
        print(f"✓ Connected to SearXNG at {search.base_url}")
        
        # Test basic search
        print("\n=== Basic Search Test ===")
        results = search.search("python programming tutorial", max_results=3)
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['title']}")
            print(f"   URL: {result['url']}")
            print(f"   Score: {result['score']:.3f}")
            print(f"   Content: {result['content'][:150]}...")
        
        # Test search with metadata
        print("\n\n=== Search with Metadata Test ===")
        response = search.search_with_metadata("machine learning", max_results=2)
        
        print(f"Query: {response['query_info'].get('query', 'N/A')}")
        print(f"Total results found: {response['query_info'].get('number_of_results', 0)}")
        print(f"Engines used: {', '.join(response['search_metadata'].get('engines', []))}")
        
        print(f"\nTop {len(response['results'])} results:")
        for result in response['results']:
            print(f"- {result['title']}: {result['url']}")
        
        # Test image search
        print("\n\n=== Image Search Test ===")
        image_results = search.search_images("python logo", max_results=2)
        
        print(f"Found {len(image_results)} image results:")
        for result in image_results:
            print(f"- {result['title']}")
            print(f"  {result['url']}")
        
    except Exception as e:
        print(f"Demo failed: {e}")
        print(f"Make sure SearXNG is running at {os.getenv('SEARXNG_URL', 'http://localhost:8080')}")


if __name__ == "__main__":
    main()