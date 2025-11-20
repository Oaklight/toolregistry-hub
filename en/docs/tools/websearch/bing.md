# Bing Search

Bing search provides functionality to perform web searches using the Microsoft Bing search engine.

## Class Overview

- `BingSearch` - A class that provides Bing search functionality

## Detailed API

### BingSearch Class

`BingSearch` is a class that provides Bing search functionality, inheriting from `BaseSearch`.

#### Initialization Parameters

- `rate_limit_delay: float = 1.0` - Delay time between requests (seconds)
- `timeout: Optional[float] = None` - Request timeout time (seconds)
- `max_retries: int = 3` - Maximum number of retries
- `proxy: Optional[str] = None` - Proxy server URL

#### Methods

- `search(query: str, number_results: int = 5, timeout: Optional[float] = None, **kwargs) -> List[SearchResult]`: Execute search and return results
- `_search_impl(query: str, **kwargs) -> List[SearchResult]`: Implement specific search logic
- `_parse_results(raw_results: Dict) -> List[SearchResult]`: Parse raw search results
- `_extract_real_url(bing_url: str) -> str`: Extract real URL from Bing redirect URL
- `_wait_for_rate_limit()`: Wait for rate limit

## Usage Examples

### Basic Usage

```python
from toolregistry_hub.websearch import BingSearch

# Create Bing search instance
bing_search = BingSearch()

# Execute search
results = bing_search.search("Python programming", number_results=5)

# Process search results
for result in results:
    print(f"Title: {result.title}")
    print(f"URL: {result.url}")
    print(f"Excerpt: {result.excerpt}")
    print("-" * 50)
```

### Using Proxy

```python
from toolregistry_hub.websearch import BingSearch

# Create Bing search instance using proxy
bing_search = BingSearch(proxy="http://your-proxy-server:port")

# Execute search
results = bing_search.search("machine learning tutorial", number_results=3)

# Process search results
for result in results:
    print(f"Title: {result.title}")
    print(f"URL: {result.url}")
    print(f"Excerpt: {result.excerpt}")
    print("-" * 50)
```

### Custom Timeout and Retries

```python
from toolregistry_hub.websearch import BingSearch

# Create Bing search instance with custom timeout and retries
bing_search = BingSearch(timeout=5.0, max_retries=2)

# Execute search
results = bing_search.search("deep learning frameworks", number_results=5, timeout=10.0)

# Process search results
for result in results:
    print(f"Title: {result.title}")
    print(f"URL: {result.url}")
    print(f"Excerpt: {result.excerpt}")
    print("-" * 50)
```

### Fetching Web Page Content

```python
from toolregistry_hub.websearch import BingSearch
from toolregistry_hub.websearch.base import BaseSearch

# Create Bing search instance
bing_search = BingSearch()

# Execute search
results = bing_search.search("Python tutorial", number_results=1)

if results:
    # Get full web page content of the first result
    url = results[0].url
    content = BaseSearch._fetch_webpage_content(url)
    print(f"Web page content length: {len(content)} characters")
    print(f"Web page content preview: {content[:200]}...")
```

## Legacy Bing Search

Legacy Bing search functionality is provided in the `websearch_legacy` module using the `WebSearchBing` class. For more information, please refer to the [Legacy Web Search](legacy.md) documentation.
