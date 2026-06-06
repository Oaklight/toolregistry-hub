---
title: Quick Start
summary: Try ToolRegistry Hub tools in 60 seconds
description: Hands-on introduction to the most-used hub tools — calculator, datetime, file search, web fetch, and shell execution.
keywords: quickstart, tutorial, getting started, examples, python
author: Oaklight
---

# Quick Start

This page gets you from zero to working code in under a minute. For the full tool catalog, see **[Tools](../tools/)**.

## Prerequisites

```bash
pip install toolregistry-hub
```

## Try It

### Math & Units

```python
from toolregistry_hub import Calculator, UnitConverter

Calculator.evaluate("sqrt(144) + 2**3")          # 20.0
Calculator.evaluate("log(100, 10) + sin(pi/2)")  # 3.0

UnitConverter.convert(100, "celsius_to_fahrenheit")  # 212.0
```

### Date & Time

```python
from toolregistry_hub import DateTime

DateTime.now("Asia/Shanghai")                                   # current time in Shanghai
DateTime.convert_timezone("14:30", "America/Chicago", "Asia/Tokyo")  # timezone conversion
```

### Files

```python
from toolregistry_hub import FileSearch, FileReader, FileOps

FileSearch.grep(r"TODO", path="src/")               # find TODOs in source
FileSearch.tree("src/", max_depth=2)                 # directory overview
FileReader.read("config.py", limit=20)               # first 20 lines
FileOps.edit("config.py",
             old_string="DEBUG = True",
             new_string="DEBUG = False")              # safe string replace
```

### Web

```python
from toolregistry_hub import Fetch
from toolregistry_hub.websearch import WebSearch

Fetch().fetch_content("https://example.com")         # extract page content

ws = WebSearch()
results = ws.search("Python 3.12 new features", max_results=3)
for r in results:
    print(f"{r.title}: {r.url}")
```

!!! note "API Keys"
    Web search tools need API keys set as environment variables. Tools without keys (Calculator, DateTime, FileOps, etc.) work out of the box. See [Environment Variables](../reference/environment.md) for the full list.

### Shell

```python
from toolregistry_hub import BashTool

result = BashTool.execute("python --version", timeout=10)
print(result["stdout"])  # Python 3.11.5
```

### Start a Server

```bash
pip install toolregistry-hub[server]
toolregistry-hub openapi --port 8000
# → API docs at http://localhost:8000/docs
```

## What's Next?

| I want to…                     | Go to                                       |
|--------------------------------|---------------------------------------------|
| Browse all available tools     | [Tools](../tools/)                          |
| Use tools as Python imports    | [Library Usage](../guides/library.md)       |
| Deploy as REST API or MCP      | [Server Mode](../guides/server.md)          |
| Run in Docker                  | [Docker Deployment](../guides/docker.md)    |
| Register tools with an agent   | [Library Usage → AI Agents](../guides/library.md#use-in-ai-agents) |
