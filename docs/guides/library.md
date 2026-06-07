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
    | **Usage** | `from toolregistry_hub import ...` | `toolregistry-hub openapi` |
    | **Best for** | Scripts, notebooks, AI agents, embedding in your app | Remote access, multi-client, MCP integration |
    | **Latency** | Direct function call | HTTP / stdio round-trip |
    | **Dependencies** | Minimal (mostly stdlib) | FastAPI, uvicorn, or MCP SDK |

!!! tip "New here?"
    See [Installation](../get-started/installation.md) and [Quick Start](../get-started/quickstart.md) first.

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

BashTool has a built-in deny list that blocks dangerous commands (`rm -rf /`, `sudo`, fork bombs, etc.). See the [Bash Tool](../tools/bash_tool.md) page for the full security model.

### Web Search & Fetch

```python
from toolregistry_hub import Fetch, BraveSearch, TavilySearch
from toolregistry_hub.websearch import WebSearch

# Fetch and extract content from a URL
content = Fetch().fetch_content("https://example.com")

# Fetch with Jina Reader API key (optional, for authenticated access)
fetcher = Fetch(api_keys=["jina_key1", "jina_key2"])
content = fetcher.fetch_content("https://example.com")

# Unified web search — auto-selects the best available engine
ws = WebSearch()
results = ws.search("Python 3.12 new features", max_results=5)
for r in results:
    print(f"{r.title}: {r.url}")

# Specify a particular engine
results = ws.search("Python async", engine="brave", max_results=5)

# List available engines and their configuration status
engines = ws.list_engines()

# Direct engine usage (requires API keys via environment variables)
results = BraveSearch().search("Python 3.12 new features", max_results=5)
for r in results:
    print(f"{r.title}: {r.url}")
```

### Scheduling

```python
from toolregistry_hub import CronTool

# Schedule a recurring prompt (every 5 minutes)
job = CronTool.create(cron="*/5 * * * *", prompt="Check server health")

# Schedule a one-shot reminder
job = CronTool.create(
    cron="30 14 28 4 *",
    prompt="Deploy release to staging",
    recurring=False,
)

# List and manage scheduled jobs
jobs = CronTool.list()
CronTool.delete(job_id="abc123")
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

Some tools require API keys. Tools without key requirements (Calculator, DateTime, FileOps, BashTool, etc.) work out of the box.

See **[Environment Variables Reference](../reference/environment.md)** for the full list.

## See Also

- **[Tools Reference](../tools/)** — detailed API docs for each tool
- **[Server Mode](server.md)** — deploy as REST API or MCP server
- **[Ecosystem](../ecosystem.md)** — how hub fits into the toolregistry family
