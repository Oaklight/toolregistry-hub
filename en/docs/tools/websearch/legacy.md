# Legacy Web Search

The legacy web search module (`websearch_legacy`) provides basic web search functionality, supporting multiple search engines.

## Class Overview

The legacy web search module mainly includes the following classes:

- `WebSearchGeneral` - Abstract base class for all search engines
- `WebSearchBing` - A class that provides Bing search functionality
- `WebSearchGoogle` - A class that provides Google search functionality
- `WebSearchSearXNG` - A class that provides SearXNG search functionality

## Detailed API

### WebSearchGeneral Class

`WebSearchGeneral` is an abstract base class that defines the interface that all search engines must implement.

#### Methods

- `search(query: str, num_results: int = 5, **kwargs) -> List[dict]`: Execute search and return results
- `_fetch_webpage_content(url: str, timeout: Optional[float] = None) -> str`: Fetch web page content

### WebSearchBing Class

`WebSearchBing` is a class that provides Bing search functionality, inheriting from `WebSearchGeneral`.

#### Initialization Parameters

- `timeout: float = 3.0` - Request timeout time (seconds)
- `proxy: Optional[str] = None` - Proxy server URL

#### Methods

- `search(query: str, num_results: int = 5, **kwargs) -> List[dict]`: Execute search and return results
- `_meta_search_bing(query: str, num_results: int, timeout: float, proxy: Optional[str]) -> List[dict]`: Execute Bing search
- `_parse_bing_entries(entries: List[dict], num_results: int) -> List[dict]`: Parse Bing search results
- `_extract_real_url(bing_url: str) -> str`: Extract real URL from Bing redirect URL

### WebSearchGoogle Class

`WebSearchGoogle` is a class that provides Google search functionality, inheriting from `WebSearchGeneral`.

#### Initialization Parameters

- `timeout: float = 3.0` - Request timeout time (seconds)
- `proxy: Optional[str] = None` - Proxy server URL

#### Methods

- `search(query: str, num_results: int = 5, **kwargs) -> List[dict]`: Execute search and return results
- `_meta_search_google(query: str, num_results: int, timeout: float, proxy: Optional[str]) -> List[dict]`: Execute Google search
- `_parse_google_entries(entries: List[dict], num_results: int) -> List[dict]`: Parse Google search results

### WebSearchSearXNG Class

`WebSearchSearXNG` is a class that provides SearXNG search functionality, inheriting from `WebSearchGeneral`.

#### Initialization Parameters

- `base_url: Optional[str] = None` - Base URL of the SearXNG instance, defaults to built-in instance
- `timeout: float = 3.0` - Request timeout time (seconds)
- `proxy: Optional[str] = None` - Proxy server URL

#### Methods

- `search(query: str, num_results: int = 5, **kwargs) -> List[dict]`: Execute search and return results
- `_meta_search_searxng(query: str, num_results: int, timeout: float, proxy: Optional[str]) -> List[dict]`: Execute SearXNG search

## Usage Examples

### Using Bing Search

```python
from toolregistry_hub.websearch_legacy import WebSearchBing

# Create Bing search instance
bing_search = WebSearchBing()

# Execute search
results = bing_search.search("Python programming", num_results=5)

# Process search results
for result in results:
    print(f"Title: {result['title']}")
    print(f"URL: {result['url']}")
    print(f"Excerpt: {result['excerpt']}")
    print("-" * 50)
```

### Using Google Search

```python
from toolregistry_hub.websearch_legacy import WebSearchGoogle

# Create Google search instance
google_search = WebSearchGoogle()

# Execute search
results = google_search.search("machine learning tutorial", num_results=3)

# Process search results
for result in results:
    print(f"Title: {result['title']}")
    print(f"URL: {result['url']}")
    print(f"Excerpt: {result['excerpt']}")
    print("-" * 50)
```

### Using SearXNG Search

```python
from toolregistry_hub.websearch_legacy import WebSearchSearXNG

# Create SearXNG search instance
searxng_search = WebSearchSearXNG()

# Execute search
results = searxng_search.search("deep learning frameworks", num_results=5)

# Process search results
for result in results:
    print(f"Title: {result['title']}")
    print(f"URL: {result['url']}")
    print(f"Excerpt: {result['excerpt']}")
    print("-" * 50)
```

### Fetching Web Page Content

```python
from toolregistry_hub.websearch_legacy import WebSearchBing, WebSearchGeneral

# Create Bing search instance
bing_search = WebSearchBing()

# Execute search
results = bing_search.search("Python tutorial", num_results=1)

if results:
    # Get full web page content of the first result
    url = results[0]['url']
    content = WebSearchGeneral._fetch_webpage_content(url)
    print(f"Web page content length: {len(content)} characters")
    print(f"Web page content preview: {content[:200]}...")
```

## Search Result Filtering

The legacy web search module also provides search result filtering functionality, which can filter out unwanted search results.

```python
from toolregistry_hub.websearch_legacy import WebSearchBing
from toolregistry_hub.websearch_legacy.filter import filter_search_results

# Create Bing search instance
bing_search = WebSearchBing()

# Execute search
results = bing_search.search("Python programming", num_results=10)

# Filter search results
filtered_results = filter_search_results(results)
print(f"Results before filtering: {len(results)}")
print(f"Results after filtering: {len(filtered_results)}")
```
