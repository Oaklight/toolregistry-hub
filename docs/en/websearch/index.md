# Web Search Tools

The web search tools provide functionality to perform web searches through various search engines. This module supports multiple search engines, including Bing, Google, SearXNG, and Tavily.

## Module Overview

The web search tools mainly include the following two versions:

1. **New Web Search Module** (`websearch`) - Provides a unified search engine abstraction layer and more advanced features
2. **Legacy Web Search Module** (`websearch_legacy`) - Provides basic web search functionality

## Search Engine Support

Currently supported search engines include:

- [Bing Search](bing.md) - Using Bing search engine
- [SearXNG Search](searxng.md) - Using SearXNG meta search engine
- [Brave Search](brave.md) - Using Brave search engine
- [Tavily Search](tavily.md) - Using Tavily search API

## Basic Usage

```python
from toolregistry_hub.websearch import BingSearch, SearXNGSearch

# Using Bing search
bing_search = BingSearch()
results = bing_search.search("Python programming", number_results=5)
for result in results:
    print(f"Title: {result.title}")
    print(f"URL: {result.url}")
    print(f"Excerpt: {result.excerpt}")
    print("-" * 50)

# Using SearXNG search
searxng_search = SearXNGSearch()
results = searxng_search.search("machine learning tutorial", number_results=3)
for result in results:
    print(f"Title: {result.title}")
    print(f"URL: {result.url}")
    print(f"Excerpt: {result.excerpt}")
    print("-" * 50)
```

## Detailed Documentation

- [Search Result Types](search_result.md) - Data structure of search results
- [Base Search Class](base_search.md) - Base class for all search engines
- [Bing Search](bing.md) - Implementation of Bing search engine
- [SearXNG Search](searxng.md) - Implementation of SearXNG search engine
- [Brave Search](brave.md) - Implementation of Brave search engine
- [Tavily Search](tavily.md) - Implementation of Tavily search API
- [Legacy Web Search](legacy.md) - Documentation of the legacy web search module

## Architecture Upgrade Plan

The web search module is undergoing an architecture upgrade. Detailed information can be found in the [Architecture Upgrade Plan](plan.md).

## Navigation

- [Back to Home](../readme_en.md)
- [View Navigation Page](../navigation.md)
- [Calculator Tools](../calculator.md)
- [Date Time Tools](../datetime.md)
- [File Operations Tools](../file_ops.md)
- [File System Tools](../filesystem.md)
- [Unit Converter Tools](../unit_converter.md)
- [Other Tools](../other_tools.md)
