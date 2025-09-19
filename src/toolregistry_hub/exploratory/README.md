# Search API Demo Tools

This directory contains working demo implementations of three different search APIs that can replace Google Search to avoid bot detection issues:

- **Tavily Search API** - AI-powered search with LLM-generated answers
- **Brave Search API** - Independent search engine with good privacy features
- **SearXNG** - Open-source metasearch engine (self-hosted)

## Quick Start

### 1. Install Dependencies

```bash
pip install httpx loguru
```

### 2. Set Up API Keys

#### Tavily Search API

1. Sign up at [https://tavily.com/](https://tavily.com/)
2. Get your API key from the dashboard
3. Set environment variable:

```bash
export TAVILY_API_KEY="tvly-your-api-key-here"
```

#### Brave Search API

1. Sign up at [https://api.search.brave.com/](https://api.search.brave.com/)
2. Subscribe to a plan (Free tier available)
3. Get your API key from the API Keys section
4. Set environment variable:

```bash
export BRAVE_API_KEY="your-brave-api-key-here"
```

#### SearXNG

1. Set up a SearXNG instance (local or remote)
   - Local: Follow [installation guide](https://docs.searxng.org/admin/installation.html)
   - Docker: `docker run -d -p 8080:8080 searxng/searxng`
2. Set environment variable:

```bash
export SEARXNG_URL="http://localhost:8080"
```

### 3. Run the Demo

```bash
# Test individual search engines
python websearch_tavily.py
python websearch_brave.py
python websearch_searxng.py

# Compare all engines
python demo_search_comparison.py
```

## API Comparison

| Feature                | Tavily         | Brave               | SearXNG            |
| ---------------------- | -------------- | ------------------- | ------------------ |
| **Cost**               | Paid (credits) | Paid (subscription) | Free (self-hosted) |
| **Setup Complexity**   | Easy           | Easy                | Medium             |
| **AI Answers**         | ✅ Built-in    | ❌                  | ❌                 |
| **Privacy**            | Good           | Excellent           | Excellent          |
| **Rate Limits**        | Credit-based   | Plan-based          | Self-controlled    |
| **Result Quality**     | High           | High                | Variable           |
| **Freshness**          | Good           | Good                | Depends on engines |
| **Specialized Search** | Limited        | News, Local         | Images, News, etc. |

## Usage Examples

### Basic Search

```python
from websearch_tavily import TavilySearch
from websearch_brave import BraveSearch
from websearch_searxng import SearXNGSearch

# Tavily Search (with rate limiting for API limits)
tavily = TavilySearch(rate_limit_delay=0.6)  # 600ms between requests
results = tavily.search("python web scraping", max_results=5)

# Brave Search (with rate limiting for free tier: 1 req/sec)
brave = BraveSearch(rate_limit_delay=1.2)  # 1.2s between requests
results = brave.search("python web scraping", max_results=5)

# SearXNG Search (no rate limiting needed for self-hosted)
searxng = SearXNGSearch()
results = searxng.search("python web scraping", max_results=5)

# All return the same format:
for result in results:
    print(f"Title: {result['title']}")
    print(f"URL: {result['url']}")
    print(f"Content: {result['content']}")
    print(f"Score: {result['score']}")
```

### Advanced Features

#### Tavily - AI-Generated Answers

```python
tavily = TavilySearch()
response = tavily.search_with_answer("What is machine learning?")
print(f"AI Answer: {response['answer']}")
print(f"Supporting results: {len(response['results'])}")
```

#### Brave - News Search

```python
brave = BraveSearch()
news = brave.search_news("technology trends", max_results=5)
for article in news:
    print(f"News: {article['title']}")
```

#### SearXNG - Image Search

```python
searxng = SearXNGSearch()
images = searxng.search_images("python logo", max_results=5)
for image in images:
    print(f"Image: {image['title']} - {image['url']}")
```

## Configuration Options

### Tavily Search Parameters

- `search_depth`: "basic" (1 credit) or "advanced" (2 credits)
- `include_answer`: Include AI-generated answer
- `include_images`: Include image search results
- `max_results`: 0-20 results

### Brave Search Parameters

- `country`: Country code for localized results
- `search_lang`: Language for search results
- `safesearch`: "off", "moderate", "strict"
- `freshness`: Time-based filtering
- `max_results`: 1-20 results

### SearXNG Parameters

- `categories`: Comma-separated categories
- `engines`: Specific search engines to use
- `language`: Language code
- `safesearch`: 0=off, 1=moderate, 2=strict
- `max_results`: No hard limit

## Error Handling

All implementations include comprehensive error handling:

```python
try:
    results = search_engine.search("query")
    if not results:
        print("No results found")
except ValueError as e:
    print(f"Configuration error: {e}")
except Exception as e:
    print(f"Search failed: {e}")
```

## Performance Considerations

### Tavily

- **Pros**: Fast, high-quality results, AI answers
- **Cons**: Credit-based pricing, rate limits
- **Rate Limits**: Varies by plan, built-in rate limiting available
- **Best for**: Applications needing AI-enhanced search

### Brave

- **Pros**: Independent results, good performance, privacy-focused
- **Cons**: Subscription required, strict rate limits on free tier
- **Rate Limits**: Free tier: 1 request/second, paid plans: higher limits
- **Best for**: Production applications with consistent usage

### SearXNG

- **Pros**: Free, customizable, no rate limits
- **Cons**: Requires hosting, variable quality, setup complexity
- **Rate Limits**: None (self-hosted)
- **Best for**: Development, testing, privacy-critical applications

### Rate Limiting Features

All API-based tools include built-in rate limiting:

```python
# Configure rate limiting to avoid 429 errors
tavily = TavilySearch(rate_limit_delay=0.6)  # 600ms delay
brave = BraveSearch(rate_limit_delay=1.2)    # 1.2s delay for free tier

# Rate limiting is automatic and logs when delays occur
```

## Troubleshooting

### Common Issues

1. **API Key Errors**

   ```bash
   # Check environment variables
   echo $TAVILY_API_KEY
   echo $BRAVE_API_KEY
   echo $SEARXNG_URL
   ```

2. **SearXNG Connection Issues**

   ```python
   searxng = SearXNGSearch()
   if searxng.test_connection():
       print("Connected successfully")
   else:
       print("Connection failed")
   ```

3. **Rate Limiting**

   - Tavily: Monitor credit usage, 429 errors indicate rate limits
   - Brave: Free tier limited to 1 req/sec, paid plans have higher limits
   - SearXNG: No limits (self-hosted)
   - **Solution**: Use built-in `rate_limit_delay` parameter

4. **Empty Results**
   - Check query formatting
   - Verify API keys are valid
   - Test with simple queries first

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Integration with Existing Code

To integrate with the existing [`websearch`](../websearch/) module:

1. **Replace Google Search**: Use these implementations instead of Google Search API
2. **Maintain Interface**: All tools return the same result format
3. **Add Fallbacks**: Implement multiple search engines for redundancy

```python
def search_with_fallback(query, max_results=5):
    engines = [TavilySearch(), BraveSearch(), SearXNGSearch()]

    for engine in engines:
        try:
            results = engine.search(query, max_results)
            if results:
                return results
        except Exception:
            continue

    return []
```

## Next Steps

1. **Choose Primary Engine**: Based on your requirements and budget
2. **Implement Fallbacks**: Use multiple engines for reliability
3. **Add Caching**: Cache results to reduce API calls
4. **Monitor Usage**: Track API usage and costs
5. **Optimize Queries**: Fine-tune search parameters for your use case

## API Documentation Links

- [Tavily API Docs](https://docs.tavily.com/documentation/api-reference/endpoint/search)
- [Brave Search API Docs](https://api-dashboard.search.brave.com/app/documentation/web-search/get-started)
- [SearXNG API Docs](https://docs.searxng.org/dev/search_api.html)
