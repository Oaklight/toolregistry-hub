# Brave Search

Brave search provides functionality to perform web searches using the Brave Search API. Brave Search offers independent search results without Google dependency and good privacy features.

## Class Overview

- `BraveSearch` - A class that provides Brave search functionality

## Detailed API

### BraveSearch Class

`BraveSearch` is a class that provides Brave search functionality, inheriting from `BaseSearch`.

#### Initialization Parameters

- `api_keys: Optional[str] = None` - Comma-separated Brave API keys. If not provided, will try to get from BRAVE_API_KEY env var
- `rate_limit_delay: float = 1.0` - Delay between requests in seconds to avoid rate limits

#### Methods

- `search(query: str, max_results: int = 5, timeout: float = TIMEOUT_DEFAULT, **kwargs) -> List[SearchResult]`: Execute search and return results
- `_search_impl(query: str, **kwargs) -> List[SearchResult]`: Implement specific search logic
- `_parse_results(raw_results: Dict) -> List[SearchResult]`: Parse raw search results
- `_wait_for_rate_limit()`: Wait for rate limit

## Setup

1. Sign up at <https://api.search.brave.com/> to get an API key
2. Set your API key as an environment variable:

   ```bash
   export BRAVE_API_KEY="your-brave-api-key-here"
   ```

## Usage Examples

### Basic Usage

```python
from toolregistry_hub.websearch import BraveSearch

# Create Brave search instance
brave_search = BraveSearch()

# Execute search
results = brave_search.search("Python programming", max_results=5)

# Process search results
for result in results:
    print(f"Title: {result.title}")
    print(f"URL: {result.url}")
    print(f"Content: {result.content}")
    print(f"Score: {result.score}")
    print("-" * 50)
```

### Using Multiple API Keys

```python
from toolregistry_hub.websearch import BraveSearch

# Create search instance with multiple API keys for load balancing
api_keys = "key1,key2,key3"
brave_search = BraveSearch(api_keys=api_keys)

# Execute search
results = brave_search.search("machine learning tutorial", max_results=10)

# Process search results
for result in results:
    print(f"Title: {result.title}")
    print(f"URL: {result.url}")
    print(f"Content: {result.content}")
    print("-" * 50)
```

### Custom Rate Limiting

```python
from toolregistry_hub.websearch import BraveSearch

# Create search instance with custom rate limiting
brave_search = BraveSearch(rate_limit_delay=2.0)

# Execute search
results = brave_search.search("deep learning frameworks", max_results=5)

# Process search results
for result in results:
    print(f"Title: {result.title}")
    print(f"URL: {result.url}")
    print(f"Content: {result.content}")
    print("-" * 50)
```

### Advanced Search Parameters

```python
from toolregistry_hub.websearch import BraveSearch

# Create Brave search instance
brave_search = BraveSearch()

# Execute search with advanced parameters
results = brave_search.search(
    "artificial intelligence",
    max_results=15,
    country="US",
    search_lang="en",
    safesearch="strict",
    freshness="pd"  # Past day
)

# Process search results
for result in results:
    print(f"Title: {result.title}")
    print(f"URL: {result.url}")
    print(f"Content: {result.content}")
    print(f"Score: {result.score}")
    print("-" * 50)
```

### Fetching Web Page Content

```python
from toolregistry_hub.websearch import BraveSearch
from toolregistry_hub.websearch.base import BaseSearch

# Create Brave search instance
brave_search = BraveSearch()

# Execute search
results = brave_search.search("Python tutorial", max_results=1)

if results:
    # Get full web page content of the first result
    url = results[0].url
    content = BaseSearch._fetch_webpage_content(url)
    print(f"Web page content length: {len(content)} characters")
    print(f"Web page content preview: {content[:200]}...")
```

## API Parameters

The Brave Search API supports various parameters that can be passed as keyword arguments:

- `country`: Country code for localized results (e.g., "US", "GB", "DE")
- `search_lang`: Language for search results (e.g., "en", "es", "fr")
- `safesearch`: Safe search level ("off", "moderate", "strict")
- `freshness`: Time filter for results ("pd" for past day, "pw" for past week, "pm" for past month, "py" for past year)
- `result_filter`: Filter results by type
- `count`: Number of results per request (max 20)
- `offset`: Offset for pagination

For complete API documentation, refer to: <https://api-dashboard.search.brave.com/app/documentation/web-search/query>

## Features

- **Independent Results**: Brave Search provides its own index, not relying on Google
- **Privacy-Focused**: No user tracking or data collection
- **High Quality**: AI-powered ranking and spam filtering
- **Rate Limiting**: Built-in rate limiting to respect API limits
- **Multiple API Keys**: Support for round-robin API key usage
- **Flexible Parameters**: Support for all Brave Search API parameters

## Navigation

- [Back to Web Search Homepage](index.md)
- [Back to Home](../readme_en.md)
- [View Navigation Page](../navigation.md)
- [Search Result Types](search_result.md)
- [Base Search Class](base_search.md)
- [Bing Search](bing.md)
- [SearXNG Search](searxng.md)
- [Tavily Search](tavily.md)
- [Legacy Web Search](legacy.md)
