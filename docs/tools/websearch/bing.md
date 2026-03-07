# Bing Search (Removed)

!!! danger "Removed"
    **Bing Search has been removed as of version 0.6.0.**

    It was previously deprecated in version 0.5.2 due to frequent bot detection issues and has now been fully removed from the codebase.

    **Recommended alternatives:**

    - [Brave Search](brave.md) - For general web search
    - [Tavily Search](tavily.md) - For AI-optimized search
    - [SearXNG Search](searxng.md) - For privacy-focused search
    - [BrightData Search](brightdata.md) or [Scrapeless Search](scrapeless.md) - For Google results

## Migration Guide

If you were using `BingSearch`, please migrate to one of the recommended alternatives above.

### Before (Deprecated)

```python
from toolregistry_hub.websearch import BingSearch

search = BingSearch()
results = search.search("query", max_results=5)
```

### After (Recommended)

```python
from toolregistry_hub.websearch import BraveSearch

search = BraveSearch()  # Requires BRAVE_API_KEY env var
results = search.search("query", max_results=5)
```

## Legacy Bing Search

Legacy Bing search functionality is still available in the `websearch_legacy` module using the `WebSearchBing` class. For more information, please refer to the [Legacy Web Search](legacy.md) documentation.