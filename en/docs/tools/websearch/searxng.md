# SearXNG Search

SearXNG search provides functionality to perform web searches using the SearXNG meta search engine.

## Class Overview

- `SearXNGSearch` - A class that provides SearXNG search functionality

## Detailed API

### SearXNGSearch Class

`SearXNGSearch` is a class that provides SearXNG search functionality, inheriting from `BaseSearch`.

#### Initialization Parameters

- `base_url: Optional[str] = None` - Base URL of the SearXNG instance, defaults to built-in instance

#### Methods

- `search(query: str, number_results: int = 5, timeout: Optional[float] = None, **kwargs) -> List[SearchResult]`: Execute search and return results
- `_search_impl(query: str, **kwargs) -> List[SearchResult]`: Implement specific search logic
- `_parse_results(raw_results: Dict) -> List[SearchResult]`: Parse raw search results

## Usage Examples

### Basic Usage

```python
from toolregistry_hub.websearch import SearXNGSearch

# Create SearXNG search instance
searxng_search = SearXNGSearch()

# Execute search
results = searxng_search.search("Python programming", number_results=5)

# Process search results
for result in results:
    print(f"Title: {result.title}")
    print(f"URL: {result.url}")
    print(f"Excerpt: {result.excerpt}")
    print("-" * 50)
```

### Using Custom SearXNG Instance

```python
from toolregistry_hub.websearch import SearXNGSearch

# Create search instance using custom SearXNG instance
searxng_search = SearXNGSearch(base_url="https://your-searxng-instance.com")

# Execute search
results = searxng_search.search("machine learning tutorial", number_results=3)

# Process search results
for result in results:
    print(f"Title: {result.title}")
    print(f"URL: {result.url}")
    print(f"Excerpt: {result.excerpt}")
    print("-" * 50)
```

### Setting Timeout

```python
from toolregistry_hub.websearch import SearXNGSearch

# Create SearXNG search instance
searxng_search = SearXNGSearch()

# Execute search with timeout
results = searxng_search.search("deep learning frameworks", number_results=5, timeout=10.0)

# Process search results
for result in results:
    print(f"Title: {result.title}")
    print(f"URL: {result.url}")
    print(f"Excerpt: {result.excerpt}")
    print("-" * 50)
```

### Fetching Web Page Content

```python
from toolregistry_hub.websearch import SearXNGSearch
from toolregistry_hub.websearch.base import BaseSearch

# Create SearXNG search instance
searxng_search = SearXNGSearch()

# Execute search
results = searxng_search.search("Python tutorial", number_results=1)

if results:
    # Get full web page content of the first result
    url = results[0].url
    content = BaseSearch._fetch_webpage_content(url)
    print(f"Web page content length: {len(content)} characters")
    print(f"Web page content preview: {content[:200]}...")
```

## Introduction to SearXNG

SearXNG is a self-hosted meta search engine that can aggregate results from multiple search engines, providing a privacy-protected search experience. The main advantages of using SearXNG include:

1. **Privacy Protection** - SearXNG does not track users and does not store search history
2. **Multi-engine Aggregation** - Can get results from multiple search engines simultaneously
3. **Self-hosted** - Can deploy SearXNG instances on your own server
4. **Customizable** - Can customize search engines, result presentation, etc.

## Legacy SearXNG Search

Legacy SearXNG search functionality is provided in the `websearch_legacy` module using the `WebSearchSearXNG` class. For more information, please refer to the [Legacy Web Search](legacy.md) documentation.

## Navigation

- [Back to Web Search Homepage](index.md)
- [Back to Home](../readme_en.md)
- [View Navigation Page](../navigation.md)
- [Search Result Types](search_result.md)
- [Base Search Class](base_search.md)
- [Bing Search](bing.md)
- [Legacy Web Search](legacy.md)
