# Browser-Based Web Content Fetching

This module provides a simple browser-based web content fetching system using headless Firefox and Playwright.

## Features

- **Headless Firefox**: Uses real Firefox browser for JavaScript execution
- **Anti-Detection**: Built-in stealth measures to avoid bot detection
- **Content Extraction**: Intelligent content extraction with metadata
- **Quality Assessment**: Automatic content quality scoring
- **Async Support**: Full async/await support for concurrent operations

## Quick Start

### Basic Usage

```python
import asyncio
from toolregistry_hub.browser_use import fetch_url_content

async def main():
    # Fetch content from a single URL
    result = await fetch_url_content("https://example.com")

    if result['success']:
        print(f"Title: {result['title']}")
        print(f"Content: {result['content'][:200]}...")
        print(f"Word count: {result['metadata']['word_count']}")
    else:
        print(f"Error: {result['error']}")

asyncio.run(main())
```

### Advanced Usage with Context Manager

```python
import asyncio
from toolregistry_hub.browser_use import BrowserFetch

async def main():
    async with BrowserFetch(headless=True, timeout=30.0) as fetcher:
        # Fetch multiple URLs with the same browser instance
        urls = ["https://example.com", "https://httpbin.org/html"]

        for url in urls:
            result = await fetcher.fetch_content(url)
            print(f"Fetched {url}: {result['success']}")

asyncio.run(main())
```

### Content Extraction and Processing

```python
import asyncio
from toolregistry_hub.browser_use import fetch_and_extract

async def main():
    # Fetch and extract structured data
    result = await fetch_and_extract("https://example.com")

    if result['success']:
        data = result['structured_data']
        print(f"Title: {data['title']}")
        print(f"Summary: {data['summary']}")
        print(f"Keywords: {', '.join(data['keywords'])}")
        print(f"Quality Score: {data['quality_score']:.2f}")

asyncio.run(main())
```

## API Reference

### BrowserFetch

Main class for browser-based content fetching.

#### Methods

- `__init__(headless=True, timeout=30.0)`: Initialize browser fetcher
- `async start()`: Start the browser instance
- `async close()`: Close the browser instance
- `async fetch_content(url, wait_for_selector=None)`: Fetch content from URL

#### Context Manager Support

```python
async with BrowserFetch() as fetcher:
    result = await fetcher.fetch_content("https://example.com")
```

### ContentExtractor

Utility class for content processing and extraction.

#### Static Methods

- `clean_text(text)`: Clean and normalize text content
- `extract_summary(content, max_length=300)`: Extract summary from content
- `extract_keywords(content, max_keywords=10)`: Extract keywords from content
- `assess_content_quality(content, metadata)`: Assess content quality (0.0-1.0)
- `extract_structured_data(content_result)`: Extract structured data from fetch result

### Convenience Functions

- `fetch_url_content(url, headless=True, timeout=30.0, wait_for_selector=None)`: Fetch content from single URL
- `fetch_and_extract(url, headless=True, timeout=30.0, wait_for_selector=None)`: Fetch and extract structured data

## Configuration

### Browser Settings

The browser is configured with anti-detection measures:

- Custom user agent
- Disabled webdriver flags
- Stealth JavaScript injection
- Standard viewport size (1366x768)

### Timeout Settings

- Default timeout: 30 seconds
- Page load timeout: 30 seconds
- Selector wait timeout: 30 seconds
- Dynamic content wait: 2 seconds

## Error Handling

All functions return structured results with success indicators:

```python
{
    'success': True/False,
    'url': 'original_url',
    'title': 'page_title',
    'content': 'extracted_content',
    'metadata': {...},
    'error': 'error_message'  # Only present if success=False
}
```

## Requirements

Add to your `pyproject.toml`:

```toml
[tool.poetry.dependencies]
playwright = "^1.40.0"
loguru = "^0.7.0"
```

Install Playwright browsers:

```bash
playwright install firefox
```

## Performance Considerations

- Browser startup takes 1-3 seconds
- Page loading varies by site complexity
- Memory usage: ~100-200MB per browser instance
- Recommended: Use context manager for multiple requests
- Consider implementing browser pooling for high-volume usage

## Troubleshooting

### Common Issues

1. **Browser fails to start**: Ensure Playwright Firefox is installed
2. **Timeout errors**: Increase timeout for slow-loading sites
3. **Empty content**: Site may require specific selectors or longer wait times
4. **Memory issues**: Close browser instances properly using context managers

### Debug Mode

Run with visible browser for debugging:

```python
async with BrowserFetch(headless=False) as fetcher:
    result = await fetcher.fetch_content("https://example.com")
```
