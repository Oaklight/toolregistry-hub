---
title: Web Fetch Tool
summary: Fetch web page content from URLs
description: The Fetch class provides functionality to fetch web page content from URLs with timeout and proxy support.
keywords: web, fetch, content, url, http
author: ToolRegistry Hub Team
---

# Web Fetch Tool

The web content fetching tool provides functionality to fetch web page content from URLs.

## Overview

The `Fetch` class is designed for retrieving content from web pages. It supports:

- HTTP/HTTPS URL fetching
- Configurable timeout settings
- Proxy support
- Content extraction and cleaning
- Error handling for network issues

## Class Reference

### Fetch

A class that provides web content fetching functionality.

#### Methods

##### `fetch_content(url: str, timeout: float = 10.0, proxy: Optional[str] = None) -> str`

Fetch web page content from URL.

**Parameters:**
- `url` (str): The URL to fetch content from
- `timeout` (float, optional): Request timeout in seconds. Defaults to 10.0
- `proxy` (Optional[str], optional): Proxy server to use. Defaults to None

**Returns:**
- `str`: The extracted content from the web page

**Raises:**
- `requests.RequestException`: If the request fails
- `ValueError`: If the URL is invalid

**Example:**
```python
from toolregistry_hub import Fetch

# Fetch web page content
content = Fetch.fetch_content("https://www.example.com")
print(f"Web page content length: {len(content)} characters")
print(f"Web page content preview: {content[:200]}...")
```

## Use Cases

### Basic Web Content Fetching

```python
from toolregistry_hub import Fetch

# Fetch content from a website
try:
    content = Fetch.fetch_content("https://httpbin.org/html")
    print(f"Successfully fetched {len(content)} characters")
    print("Content preview:", content[:100])
except Exception as e:
    print(f"Failed to fetch content: {e}")
```

### Using Custom Timeout

```python
from toolregistry_hub import Fetch

# Fetch with custom timeout
try:
    content = Fetch.fetch_content(
        "https://httpbin.org/delay/5", 
        timeout=10.0
    )
    print("Content fetched successfully")
except Exception as e:
    print(f"Request timed out or failed: {e}")
```

### Using Proxy

```python
from toolregistry_hub import Fetch

# Fetch through a proxy
try:
    content = Fetch.fetch_content(
        "https://httpbin.org/ip",
        proxy="http://proxy.example.com:8080"
    )
    print("Content fetched through proxy:", content)
except Exception as e:
    print(f"Proxy request failed: {e}")
```

### Content Analysis

```python
from toolregistry_hub import Fetch
import re

# Fetch and analyze content
def analyze_webpage(url):
    try:
        content = Fetch.fetch_content(url)
        
        # Basic content analysis
        word_count = len(content.split())
        char_count = len(content)
        
        # Extract potential email addresses
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)
        
        # Extract potential URLs
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', content)
        
        return {
            'word_count': word_count,
            'char_count': char_count,
            'emails_found': len(emails),
            'urls_found': len(urls),
            'content_preview': content[:200]
        }
    except Exception as e:
        return {'error': str(e)}

# Analyze a webpage
result = analyze_webpage("https://www.example.com")
print("Analysis result:", result)
```

## Error Handling

The `fetch_content` method can raise various exceptions. Here's how to handle them:

```python
from toolregistry_hub import Fetch
import requests

def safe_fetch(url, timeout=10.0, proxy=None):
    try:
        content = Fetch.fetch_content(url, timeout=timeout, proxy=proxy)
        return {'success': True, 'content': content}
    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'Request timed out'}
    except requests.exceptions.ConnectionError:
        return {'success': False, 'error': 'Connection failed'}
    except requests.exceptions.HTTPError as e:
        return {'success': False, 'error': f'HTTP error: {e}'}
    except ValueError as e:
        return {'success': False, 'error': f'Invalid URL: {e}'}
    except Exception as e:
        return {'success': False, 'error': f'Unexpected error: {e}'}

# Safe fetching with error handling
result = safe_fetch("https://www.example.com")
if result['success']:
    print(f"Content fetched: {len(result['content'])} characters")
else:
    print(f"Failed to fetch: {result['error']}")
```

## Best Practices

1. **Set Appropriate Timeouts**: Use reasonable timeout values to avoid hanging requests
2. **Handle Exceptions**: Always wrap fetch calls in try-except blocks
3. **Respect Rate Limits**: Don't make too many requests in quick succession
4. **Check Content Size**: Be aware of large content that might consume memory
5. **Validate URLs**: Ensure URLs are properly formatted before fetching

## Security Considerations

- Be cautious when fetching content from untrusted sources
- Validate and sanitize any content before processing
- Consider using HTTPS URLs when possible
- Be aware of potential security risks when using proxies

## Navigation

- [Back to Home](index.md)
- [Think Tool](think_tool.md)
- [Other Tools](other_tools.md)
- [Calculator Tools](calculator.md)