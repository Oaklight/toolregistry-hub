---
title: Examples
summary: Practical code examples — from basic usage to server deployment and custom tools
description: Get familiar with ToolRegistry Hub through runnable snippets.
keywords: examples, code, python, server, docker, custom tool
author: Oaklight
---

# Examples

Complete, copy-pasteable examples for common use cases.

---

## Basic Library Usage

### Calculator

```python
from toolregistry_hub import Calculator

Calculator.evaluate("sqrt(144) + 2**3")          # 20.0
Calculator.evaluate("log(100, 10) + sin(pi/2)")  # 3.0
Calculator.list_allowed_fns()                     # list every supported function
Calculator.help("log")                            # help for one function
```

### Date & Time

```python
from toolregistry_hub import DateTime

DateTime.now()                                                   # current time (UTC)
DateTime.now("Asia/Shanghai")                                    # current time in Shanghai
DateTime.convert_timezone("14:30", "America/Chicago", "Asia/Tokyo")  # timezone conversion
```

### File Operations

```python
from toolregistry_hub import FileOps, FileReader, FileSearch, PathInfo

# Search
FileSearch.grep(r"TODO", path="src/")
FileSearch.tree("src/", max_depth=2)
py_files = FileSearch.glob("**/*.py", path="src/")

# Read
content = FileReader.read("config.py", limit=20)

# Edit (safe string replacement)
diff = FileOps.edit("config.py",
                    old_string="DEBUG = True",
                    new_string="DEBUG = False")
print(diff)

# Metadata
info = PathInfo.info("/path/to/file")
```

---

## Web Search (multiple engines)

```python
from toolregistry_hub import Fetch
from toolregistry_hub.websearch import WebSearch

# Fetch a page
Fetch().fetch_content("https://example.com")

# Unified search — picks whichever engine is configured
ws = WebSearch()
results = ws.search("Python 3.12 new features", max_results=3)
for r in results:
    print(f"{r.title}: {r.url}")
```

!!! tip "Choosing an engine"
    ```python
    from toolregistry_hub.websearch import BraveSearch, TavilySearch

    brave = BraveSearch()          # needs BRAVE_API_KEY
    tavily = TavilySearch()        # needs TAVILY_API_KEY

    results = brave.search("MCP protocol", max_results=5)
    ```

    The environment variable each engine needs is listed in the
    [environment reference](../reference/environment.md).

---

## Server Deployment

### OpenAPI mode

```bash
pip install toolregistry-hub[server]

# Start — every tool is loaded by default
toolregistry-hub openapi --port 8000
# → Swagger UI: http://localhost:8000/docs
```

```python
# Client call
import requests

resp = requests.post("http://localhost:8000/call/Calculator/evaluate",
                     json={"expression": "2**10"})
print(resp.json())  # {"result": 1024}
```

### MCP mode

```bash
# stdio transport (for AI agents)
toolregistry-hub mcp

# SSE transport
toolregistry-hub mcp --transport sse --port 8080
```

---

## Docker Quick Start

```bash
docker run -d \
  -p 8000:8000 \
  -e API_BEARER_TOKEN=my-secret \
  oaklight/toolregistry-hub:latest \
  openapi --host 0.0.0.0
```

```bash
# Verify
curl -H "Authorization: Bearer my-secret" \
     http://localhost:8000/call/Calculator/evaluate \
     -d '{"expression": "1+1"}'
```

---

## Registering Custom Tools

Register your own tool classes through `tools.jsonc`:

```jsonc
// tools.jsonc
{
  "tools": [
    {
      "module": "my_tools.weather",
      "class": "WeatherTool"
    }
  ]
}
```

```python
# my_tools/weather.py
class WeatherTool:
    @staticmethod
    def get_weather(city: str) -> str:
        """Get the weather for a city"""
        return f"{city}: sunny, 25°C"
```

```bash
toolregistry-hub openapi --tools-config tools.jsonc --port 8000
# WeatherTool is now available through the API
```

---

## Using the Hub in an AI Agent

Combine the [ToolRegistry](https://toolregistry.readthedocs.io/) core library with the hub tools:

```python
from toolregistry import ToolRegistry
from toolregistry_hub import Calculator, DateTime

registry = ToolRegistry()
registry.register_from_class(Calculator)
registry.register_from_class(DateTime)

# Export in OpenAI function-calling format
tools_schema = registry.get_tools_json()
```

---

## More

- [Quick Start](../get-started/quickstart.md) — running in 60 seconds
- [Library Usage](../guides/library.md) — the complete library-mode guide
- [Server Configuration](../guides/server.md) — auth, config files, custom tools
- [Docker Deployment](../guides/docker.md) — production deployment
