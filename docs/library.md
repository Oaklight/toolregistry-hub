---
title: Library Usage
summary: Use toolregistry-hub directly as a Python library — no server required
description: Import and call any tool class in your own Python code, scripts, or AI agents with zero configuration overhead.
keywords: python, library, import, direct usage, tools, agent
author: Oaklight
---

# Library Usage

ToolRegistry Hub is first and foremost a **Python library**. Every tool can be imported and called directly in your code — no server, no HTTP, no configuration files. This is the simplest and most flexible way to use the hub.

!!! tip "Library vs Server"
    | | Library | Server |
    |---|---------|--------|
    | **Install** | `pip install toolregistry-hub` | `pip install toolregistry-hub[server]` |
    | **Usage** | `from toolregistry_hub import ...` | `toolregistry-server --mode openapi` |
    | **Best for** | Scripts, notebooks, AI agents, embedding in your app | Remote access, multi-client, MCP integration |
    | **Latency** | Direct function call | HTTP / stdio round-trip |
    | **Dependencies** | Minimal (mostly stdlib) | FastAPI, uvicorn, or MCP SDK |

## Installation

```bash
pip install toolregistry-hub
```

That's it. No server dependencies, no extra configuration.

## Quick Start

```python
from toolregistry_hub import Calculator, DateTime, BashTool

# Evaluate a math expression
result = Calculator.evaluate("sqrt(144) + 2**3")
print(result)  # 20.0

# Get current time in a timezone
now = DateTime.now("Asia/Shanghai")
print(now)  # 2026-04-01T12:34:56+08:00

# Run a shell command (with built-in safety checks)
output = BashTool.execute("ls -la", timeout=10)
print(output["stdout"])
```

All tool classes use **static methods** — no instantiation needed, no state to manage.

## Available Tools

### Calculation & Conversion

```python
from toolregistry_hub import Calculator, UnitConverter

# Calculator — evaluate expressions with built-in math functions
Calculator.evaluate("log(100, 10) + sin(pi/2)")  # 3.0
Calculator.list_allowed_fns()  # list all available functions
Calculator.help("log")  # get help on a specific function

# UnitConverter — convert between units
UnitConverter.convert(100, "celsius_to_fahrenheit")  # 212.0
UnitConverter.list_conversions(category="temperature")
```

### Date & Time

```python
from toolregistry_hub import DateTime

# Current time (default: UTC)
DateTime.now()

# Current time in a specific timezone
DateTime.now("America/New_York")

# Convert between timezones
DateTime.convert_timezone("14:30", "America/Chicago", "Asia/Tokyo")
```

### File Operations

```python
from toolregistry_hub import FileOps, FileReader, FileSearch, PathInfo

# Edit a file with exact string replacement
diff = FileOps.edit("config.py", old_string="DEBUG = True", new_string="DEBUG = False")
print(diff)  # unified diff output

# Read a file with line numbers
content = FileReader.read("src/main.py", limit=50)

# Read a Jupyter notebook
nb = FileReader.read_notebook("analysis.ipynb")

# Search for files
py_files = FileSearch.glob("**/*.py", path="src/")
matches = FileSearch.grep(r"def test_", path="tests/")
tree = FileSearch.tree("src/", max_depth=3)

# Get file metadata in one call
info = PathInfo.info("/path/to/file")
# → {exists, type, size, last_modified, permissions}
```

### Shell Execution

```python
from toolregistry_hub import BashTool

result = BashTool.execute("python --version", timeout=30, cwd="/my/project")
print(result)
# {
#     "stdout": "Python 3.11.5\n",
#     "stderr": "",
#     "exit_code": 0,
#     "timed_out": False
# }
```

BashTool has a built-in deny list that blocks dangerous commands (`rm -rf /`, `sudo`, fork bombs, etc.). See the [Bash Tool](tools/bash_tool.md) page for the full security model.

### Web Search & Fetch

```python
from toolregistry_hub import Fetch, BraveSearch, TavilySearch

# Fetch and extract content from a URL
content = Fetch.fetch_content("https://example.com")

# Web search (requires API keys via environment variables)
results = BraveSearch().search("Python 3.12 new features", max_results=5)
for r in results:
    print(f"{r.title}: {r.url}")
```

### Cognitive Tools

```python
from toolregistry_hub import ThinkTool, TodoList

# Structured thinking (useful as an LLM tool)
ThinkTool.think(
    thinking_mode="planning",
    focus_area="database migration",
    thought_process="We need to migrate from SQLite to PostgreSQL..."
)

# Task management
TodoList.update([
    "[db-migrate] Plan schema changes (planned)",
    "[db-migrate] Write migration script (in-progress)",
])
```

## Use in AI Agents

The library shines when embedded in AI agent pipelines. Since every tool is a plain Python class with static methods, you can register them with any agent framework:

```python
from toolregistry import ToolRegistry
from toolregistry_hub import Calculator, FileOps, BashTool, FileSearch

# Build a registry with selected tools
registry = ToolRegistry()
registry.register_static_tools(Calculator, namespace="calculator")
registry.register_static_tools(FileOps, namespace="file_ops")
registry.register_static_tools(BashTool, namespace="bash")
registry.register_static_tools(FileSearch, namespace="file_search")

# Generate tool schemas for your LLM
tools_json = registry.get_tools_json(format="openai")
```

Or use the hub's built-in registry that loads all tools at once:

```python
from toolregistry_hub.server.registry import get_registry

registry = get_registry()  # all tools registered and ready
```

## Environment Variables

Some tools require API keys to function. Set them as environment variables or use a `.env` file:

| Variable | Tool | Required |
|----------|------|----------|
| `BRAVE_API_KEY` | BraveSearch | For Brave search |
| `TAVILY_API_KEY` | TavilySearch | For Tavily search |
| `SERPER_API_KEY` | SerperSearch | For Serper search |
| `BRIGHTDATA_API_KEY` | BrightDataSearch | For BrightData search |
| `SEARXNG_BASE_URL` | SearXNGSearch | For self-hosted SearXNG |

Tools without API key requirements (Calculator, DateTime, FileOps, BashTool, etc.) work out of the box with zero configuration.

## See Also

- **[Tools Reference](tools/)** — detailed API docs for each tool
- **[Server Mode](server.md)** — deploy as REST API or MCP server
- **[Ecosystem](ecosystem.md)** — how hub fits into the toolregistry family
