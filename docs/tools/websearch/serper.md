# Serper Search

Serper search provides functionality to perform web searches using the Serper API to retrieve Google search results.

## Class Overview

- `SerperSearch` - A class that provides Serper search functionality

## Detailed API

### SerperSearch Class

`SerperSearch` is a class that provides Serper search functionality, inheriting from `BaseSearch`.

#### Initialization Parameters

- `api_keys: Optional[str] = None` - Comma-separated Serper API keys. If not provided, will try to get from SERPER_API_KEY env var
- `rate_limit_delay: float = 1.0` - Delay between requests in seconds to avoid rate limits

#### Methods

- `search(query: str, max_results: int = 5, timeout: float = TIMEOUT_DEFAULT, **kwargs) -> List[SearchResult]`: Execute search and return results
- `_search_impl(query: str, **kwargs) -> List[SearchResult]`: Implement specific search logic
- `_parse_results(raw_results: Dict) -> List[SearchResult]`: Parse raw search results
- `_wait_for_rate_limit()`: Wait for rate limit

## Setup

1. Sign up at <https://serper.dev/> to get an API key
2. Set your API key as an environment variable:

   ```bash
   export SERPER_API_KEY="your-serper-api-key-here"
   ```

## Free Tier

- **2,500 free queries per month**
- No credit card required

!!! note "Free Tier Policy"
   All free tier information may be subject to provider policy changes. Information is accurate at the time of writing.

## Usage Examples

### Basic Usage

```python
from toolregistry_hub.websearch import SerperSearch

# Create Serper search instance
serper_search = SerperSearch()

# Execute search
results = serper_search.search("Python programming", max_results=5)

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
from toolregistry_hub.websearch import SerperSearch

# Create search instance with multiple API keys for load balancing
api_keys = "key1,key2,key3"
serper_search = SerperSearch(api_keys=api_keys)

# Execute search
results = serper_search.search("machine learning tutorial", max_results=10)

# Process search results
for result in results:
    print(f"Title: {result.title}")
    print(f"URL: {result.url}")
    print(f"Content: {result.content}")
    print("-" * 50)
```

### Advanced Search Parameters

```python
from toolregistry_hub.websearch import SerperSearch

serper_search = SerperSearch()

# Execute search with advanced parameters
results = serper_search.search(
    "artificial intelligence",
    max_results=15,
    gl="us",                           # Country code
    hl="en",                           # Language code
    location="Austin, Texas",          # Location for localized results
)

for result in results:
    print(f"Title: {result.title}")
    print(f"URL: {result.url}")
    print(f"Content: {result.content}")
    print("-" * 50)
```

## API Parameters

The Serper API supports the following keyword arguments:

- `gl`: Country code for localized results (e.g., "us", "uk", "cn")
- `hl`: Language for search results (e.g., "en", "zh", "es")
- `location`: Location string for localized results (e.g., "Austin, Texas")
- `autocorrect`: Enable/disable spell correction (boolean)
- `page`: Result page number (1-based)
- `num`: Number of results per request (max 100)

For complete API documentation, refer to: <https://serper.dev/playground>

## Features

- **Google Search Results**: Returns Google search results
- **Rate Limiting**: Built-in rate limiting to respect API limits
- **Multiple API Keys**: Support for round-robin API key usage
- **Flexible Parameters**: Support for country, language, and location targeting
