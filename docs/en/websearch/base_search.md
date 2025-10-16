# Base Search Class

The base search class is an abstract base class for all search engine implementations, defining the interface that all search engines must implement.

## Class Overview

- `BaseSearch` - Abstract base class for all search engines

## Detailed API

### BaseSearch Class

`BaseSearch` is an abstract base class that defines the interface that all search engines must implement.

#### Attributes

- `_headers` - HTTP headers used for search requests

#### Methods

- `search(query: str, number_results: int = 5, timeout: Optional[float] = None, **kwargs) -> List[SearchResult]`: Execute search and return results
- `_parse_results(raw_results: Any) -> List[SearchResult]`: Parse raw search results into SearchResult object list
- `_search_impl(query: str, **kwargs) -> List[SearchResult]`: Implement specific search logic
- `_fetch_webpage_content(url: str, timeout: Optional[float] = None) -> str`: Fetch web page content

## Implementing Custom Search Engines

To implement a custom search engine, you need to inherit from the `BaseSearch` class and implement its abstract methods:

```python
from typing import Any, List, Optional
from toolregistry_hub.websearch.base import BaseSearch
from toolregistry_hub.websearch.search_result import SearchResult

class MyCustomSearch(BaseSearch):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    @property
    def _headers(self) -> dict:
        """Return HTTP headers used for search requests"""
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Authorization": f"Bearer {self.api_key}" if self.api_key else ""
        }

    def _search_impl(self, query: str, **kwargs) -> List[SearchResult]:
        """Implement specific search logic"""
        # Implement specific search logic here
        # For example, send HTTP request to search API
        # ...

        # Return mock results
        return [
            SearchResult(
                title="Sample Result 1",
                url="https://example.com/1",
                content="This is the content of sample result 1",
                excerpt="This is the excerpt of sample result 1"
            ),
            SearchResult(
                title="Sample Result 2",
                url="https://example.com/2",
                content="This is the content of sample result 2",
                excerpt="This is the excerpt of sample result 2"
            )
        ]

    def _parse_results(self, raw_results: Any) -> List[SearchResult]:
        """Parse raw search results into SearchResult object list"""
        # Implement parsing logic here
        # ...

        # Return mock results
        return [
            SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                content=item.get("content", ""),
                excerpt=item.get("excerpt", "")
            )
            for item in raw_results.get("items", [])
        ]
```

## Usage Example

```python
# Create custom search engine instance
my_search = MyCustomSearch(api_key="your_api_key")

# Execute search
results = my_search.search("Python programming", number_results=5)

# Process search results
for result in results:
    print(f"Title: {result.title}")
    print(f"URL: {result.url}")
    print(f"Excerpt: {result.excerpt}")
    print("-" * 50)
```

## Navigation

- [Back to Web Search Homepage](index.md)
- [Back to Home](../readme_en.md)
- [View Navigation Page](../navigation.md)
- [Search Result Types](search_result.md)
- [Bing Search](bing.md)
- [SearXNG Search](searxng.md)
- [Legacy Web Search](legacy.md)
