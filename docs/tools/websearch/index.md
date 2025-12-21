# Web Search Tools

The web search tools provide functionality to perform web searches through various search engines. This module supports multiple search engines, including Brave, SearXNG, Tavily, and Google (via BrightData/Scrapeless).

!!! note "Bing Search Deprecated"
    Bing Search has been deprecated due to frequent bot detection issues. Please use alternative search providers.

## Module Overview

The web search tools mainly include the following two versions:

1. **New Web Search Module** (`websearch`) - Provides a unified search engine abstraction layer and more advanced features
2. **Legacy Web Search Module** (`websearch_legacy`) - Provides basic web search functionality

## Search Engine Support

Currently supported search engines include:

- [Brave Search](brave.md) - Using Brave search engine (Recommended)
- [Tavily Search](tavily.md) - Using Tavily search API (AI-optimized)
- [SearXNG Search](searxng.md) - Using SearXNG meta search engine (Privacy-focused)
- [BrightData Search](brightdata.md) - Using BrightData for Google results
- [Scrapeless Search](scrapeless.md) - Using Scrapeless Universal API with support for multiple search engines
- [Bing Search](bing.md) - ⚠️ **DEPRECATED** - Using Bing search engine (not recommended)

## Basic Usage

```python
from toolregistry_hub.websearch import BraveSearch, SearXNGSearch, TavilySearch, BrightDataSearch, ScrapelessSearch

# Using Brave search (Recommended)
brave_search = BraveSearch()
results = brave_search.search("Python programming", max_results=5)
for result in results:
    print(f"Title: {result.title}")
    print(f"URL: {result.url}")
    print(f"Content: {result.content}")
    print(f"Score: {result.score}")
    print("-" * 50)

# Using SearXNG search
searxng_search = SearXNGSearch()
results = searxng_search.search("machine learning tutorial", number_results=3)
for result in results:
    print(f"Title: {result.title}")
    print(f"URL: {result.url}")
    print(f"Excerpt: {result.excerpt}")
    print("-" * 50)

# Using Brave search
brave_search = BraveSearch()
results = brave_search.search("artificial intelligence", number_results=5)
for result in results:
    print(f"Title: {result.title}")
    print(f"URL: {result.url}")
    print(f"Content: {result.content}")
    print(f"Score: {result.score}")
    print("-" * 50)

# Using Tavily search
tavily_search = TavilySearch()
results = tavily_search.search("quantum computing", number_results=5)
for result in results:
    print(f"Title: {result.title}")
    print(f"URL: {result.url}")
    print(f"Content: {result.content}")
    print(f"Score: {result.score}")
    print("-" * 50)

# Using Bright Data Google search
brightdata_search = BrightDataSearch()
results = brightdata_search.search("web scraping", max_results=5)
for result in results:
    print(f"Title: {result.title}")
    print(f"URL: {result.url}")
    print(f"Content: {result.content}")
    print(f"Score: {result.score}")
    print("-" * 50)

# Using Scrapeless Google search
scrapeless_search = ScrapelessSearch()
results = scrapeless_search.search("web scraping", max_results=5)
for result in results:
    print(f"Title: {result.title}")
    print(f"URL: {result.url}")
    print(f"Content: {result.content}")
    print(f"Score: {result.score}")
    print("-" * 50)
```

## Detailed Documentation

- [Search Result Types](search_result.md) - Data structure of search results
- [Base Search Class](base_search.md) - Base class for all search engines
- [Brave Search](brave.md) - Implementation of Brave search engine (Recommended)
- [Tavily Search](tavily.md) - Implementation of Tavily search API
- [SearXNG Search](searxng.md) - Implementation of SearXNG search engine
- [BrightData Search](brightdata.md) - Implementation of BrightData for Google results
- [Scrapeless Search](scrapeless.md) - Implementation of Scrapeless Universal API
- [Bing Search](bing.md) - ⚠️ **DEPRECATED** Implementation of Bing search engine
- [Legacy Web Search](legacy.md) - Documentation of the legacy web search module
