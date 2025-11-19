# Search Result Types

Search result types define the data structure returned by web search tools.

## Class Overview

Search results mainly use the following classes:

- `SearchResult` - A data class representing a single search result

## Detailed API

### SearchResult Class

`SearchResult` is a data class representing a single search result.

#### Attributes

- `title: str` - The title of the search result
- `url: str` - The URL of the search result
- `content: str` - The content or description of the search result
- `excerpt: str` - The excerpt of the search result, usually the same as content

## Usage Examples

```python
from toolregistry_hub.websearch import BingSearch
from toolregistry_hub.websearch.search_result import SearchResult

# Using Bing search
bing_search = BingSearch()
results = bing_search.search("Python programming", number_results=5)

# Process search results
for result in results:
    print(f"Title: {result.title}")
    print(f"URL: {result.url}")
    print(f"Excerpt: {result.excerpt}")
    print(f"Content: {result.content}")
    print("-" * 50)

# Manually create search result
custom_result = SearchResult(
    title="Python Official Website",
    url="https://www.python.org",
    content="Python is a widely used interpreted, high-level, and general-purpose programming language.",
    excerpt="Python is a widely used interpreted, high-level, and general-purpose programming language."
)
print(f"Custom result: {custom_result.title} - {custom_result.url}")
```

## Navigation

- [Back to Web Search Homepage](index.md)
- [Back to Home](../readme_en.md)
- [View Navigation Page](../navigation.md)
- [Base Search Class](base_search.md)
- [Bing Search](bing.md)
- [SearXNG Search](searxng.md)
- [Legacy Web Search](legacy.md)
