# Tavily Search

Tavily search provides functionality to perform web searches using the Tavily Search API. Tavily offers AI-powered search with LLM-generated answers and high-quality results optimized for AI applications.

## Class Overview

- `TavilySearch` - A class that provides Tavily search functionality

## Detailed API

### TavilySearch Class

`TavilySearch` is a class that provides Tavily search functionality, inheriting from `BaseSearch`.

#### Initialization Parameters

- `api_keys: Optional[str] = None` - Comma-separated Tavily API keys. If not provided, will try to get from TAVILY_API_KEY env var
- `rate_limit_delay: float = 0.5` - Delay between requests in seconds to avoid rate limits

#### Methods

- `search(query: str, max_results: int = 5, timeout: float = TIMEOUT_DEFAULT, **kwargs) -> List[SearchResult]`: Execute search and return results
- `_search_impl(query: str, **kwargs) -> List[SearchResult]`: Implement specific search logic
- `_parse_results(raw_results: Dict) -> List[SearchResult]`: Parse raw search results
- `_wait_for_rate_limit()`: Wait for rate limit

## Setup

1. Sign up at <https://tavily.com/> to get an API key
2. Set your API key as an environment variable:

   ```bash
   export TAVILY_API_KEY="tvly-your-api-key-here"
   ```

## Usage Examples

### Basic Usage

```python
from toolregistry_hub.websearch import TavilySearch

# Create Tavily search instance
tavily_search = TavilySearch()

# Execute search
results = tavily_search.search("Python programming", max_results=5)

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
from toolregistry_hub.websearch import TavilySearch

# Create search instance with multiple API keys for load balancing
api_keys = "tvly-key1,tvly-key2,tvly-key3"
tavily_search = TavilySearch(api_keys=api_keys)

# Execute search
results = tavily_search.search("machine learning tutorial", max_results=10)

# Process search results
for result in results:
    print(f"Title: {result.title}")
    print(f"URL: {result.url}")
    print(f"Content: {result.content}")
    print("-" * 50)
```

### Custom Rate Limiting

```python
from toolregistry_hub.websearch import TavilySearch

# Create search instance with custom rate limiting
tavily_search = TavilySearch(rate_limit_delay=1.0)

# Execute search
results = tavily_search.search("deep learning frameworks", max_results=5)

# Process search results
for result in results:
    print(f"Title: {result.title}")
    print(f"URL: {result.url}")
    print(f"Content: {result.content}")
    print("-" * 50)
```

### Advanced Search with AI Answer

```python
from toolregistry_hub.websearch import TavilySearch

# Create Tavily search instance
tavily_search = TavilySearch()

# Execute search with AI-generated answer
results = tavily_search.search(
    "What is artificial intelligence?",
    max_results=5,
    include_answer=True,
    search_depth="advanced",
    topic="general"
)

# Process search results (first result may be AI-generated answer)
for result in results:
    print(f"Title: {result.title}")
    print(f"URL: {result.url}")
    print(f"Content: {result.content}")
    print(f"Score: {result.score}")
    print("-" * 50)
```

### Domain Filtering

```python
from toolregistry_hub.websearch import TavilySearch

# Create Tavily search instance
tavily_search = TavilySearch()

# Execute search with domain filtering
results = tavily_search.search(
    "Python tutorials",
    max_results=5,
    include_domains=["python.org", "realpython.com", "docs.python.org"],
    exclude_domains=["spam-site.com"]
)

# Process search results
for result in results:
    print(f"Title: {result.title}")
    print(f"URL: {result.url}")
    print(f"Content: {result.content}")
    print("-" * 50)
```

### News and Research Search

```python
from toolregistry_hub.websearch import TavilySearch

# Create Tavily search instance
tavily_search = TavilySearch()

# Execute news search
news_results = tavily_search.search(
    "latest AI developments",
    max_results=5,
    topic="news",
    search_depth="advanced"
)

# Execute research search
research_results = tavily_search.search(
    "quantum computing research papers",
    max_results=5,
    topic="research",
    search_depth="advanced",
    include_raw_content=True
)

print("=== News Results ===")
for result in news_results:
    print(f"Title: {result.title}")
    print(f"URL: {result.url}")
    print(f"Content: {result.content}")
    print("-" * 50)

print("\n=== Research Results ===")
for result in research_results:
    print(f"Title: {result.title}")
    print(f"URL: {result.url}")
    print(f"Content: {result.content}")
    print("-" * 50)
```

### Fetching Web Page Content

```python
from toolregistry_hub.websearch import TavilySearch
from toolregistry_hub.websearch.base import BaseSearch

# Create Tavily search instance
tavily_search = TavilySearch()

# Execute search
results = tavily_search.search("Python tutorial", max_results=1)

if results:
    # Get full web page content of the first result
    url = results[0].url
    if url:  # Check if URL exists (AI answers may not have URLs)
        content = BaseSearch._fetch_webpage_content(url)
        print(f"Web page content length: {len(content)} characters")
        print(f"Web page content preview: {content[:200]}...")
```

## API Parameters

The Tavily Search API supports various parameters that can be passed as keyword arguments:

- `max_results`: Maximum number of results to return (0-20)
- `topic`: Search topic ("general", "news", "research")
- `search_depth`: Search depth ("basic", "advanced")
- `include_answer`: Whether to include AI-generated answer (boolean)
- `include_domains`: List of domains to include in search
- `exclude_domains`: List of domains to exclude from search
- `include_raw_content`: Whether to include raw HTML content (boolean)

For complete API documentation, refer to: <https://docs.tavily.com/documentation/api-reference/endpoint/search>

## Features

- **AI-Powered Answers**: Get LLM-generated answers to your queries
- **High-Quality Results**: Optimized for AI applications and research
- **Flexible Search Depth**: Choose between basic and advanced search modes
- **Topic Specialization**: Specialized search for general, news, and research topics
- **Domain Filtering**: Include or exclude specific domains
- **Rate Limiting**: Built-in rate limiting to respect API limits
- **Multiple API Keys**: Support for round-robin API key usage
- **Raw Content**: Option to include raw HTML content for further processing

## AI Answer Feature

When `include_answer=True` is set, Tavily provides an AI-generated answer as the first result. This answer:

- Has the title "AI Generated Answer"
- Contains a comprehensive response to your query
- Has no URL (empty string)
- Has a score of 1.0
- Is followed by regular search results

This feature is particularly useful for:

- Research queries
- Factual questions
- Complex topics requiring synthesis
- Educational content
