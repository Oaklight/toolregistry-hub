---
title: Home
summary: A comprehensive Python library providing various utility tools
description: ToolRegistry Hub is a Python library that provides various utility tools designed to support common tasks including calculations, file operations, web search, and more.
keywords: python, tools, utilities, calculator, file operations, web search
author: Oaklight
hide:
  - navigation
---

# ToolRegistry Hub

[![PyPI version](https://img.shields.io/pypi/v/toolregistry-hub?color=green)](https://pypi.org/project/toolregistry-hub/)
[![Docker Image](https://img.shields.io/docker/v/oaklight/toolregistry-hub-server?label=docker&color=green)](https://hub.docker.com/r/oaklight/toolregistry-hub-server)

**A curated collection of AI-agent-ready utility tools** — use them as a Python library or deploy as a server. Part of the [ToolRegistry](https://toolregistry.readthedocs.io/) ecosystem.

## Two Ways to Use

=== "As a Python Library"

    ```bash
    pip install toolregistry-hub
    ```

    ```python
    from toolregistry_hub import Calculator, DateTime, BashTool, FileSearch

    Calculator.evaluate("sqrt(144) + 2**3")   # 20.0
    DateTime.now("Asia/Shanghai")              # current time in Shanghai
    BashTool.execute("git status")             # safe shell execution
    FileSearch.grep(r"TODO", path="src/")      # search code
    ```

    Every tool is a plain Python class with static methods — no instantiation, no state, no server needed. **[Learn more →](library.md)**

=== "As a Server"

    ```bash
    pip install toolregistry-hub[server]

    # REST API server
    toolregistry-server --mode openapi --port 8000

    # MCP server (for AI agents)
    toolregistry-server --mode mcp --port 8000
    ```

    All tools are auto-exposed as API endpoints. **[Learn more →](server.md)**

## Available Tools

| Category | Tools | Highlights |
|----------|-------|------------|
| **Calculation** | [Calculator](tools/calculator.md), [UnitConverter](tools/unit_converter.md) | Expression evaluation, 100+ unit conversions |
| **Date & Time** | [DateTime](tools/datetime.md) | Timezone-aware time, cross-timezone conversion |
| **File Management** | [FileOps](tools/file_ops.md), [FileReader](tools/file_reader.md), [FileSearch](tools/file_search.md), [PathInfo](tools/path_info.md) | Exact-string edit, glob/grep/tree, PDF & notebook reading |
| **Shell** | [BashTool](tools/bash_tool.md) | Shell execution with built-in deny list security |
| **Web** | [Fetch](tools/websearch/web_fetch_tool.md), [BraveSearch](tools/websearch/brave.md), [TavilySearch](tools/websearch/tavily.md), ... | Content extraction, multi-engine search |
| **Cognitive** | [ThinkTool](tools/think_tool.md), [TodoList](tools/todo_list.md) | Structured reasoning, task management |

**Explore the [Tools](tools/) section for detailed documentation.**

## Why ToolRegistry Hub?

- **Dual-mode** — same tools work as library imports and as server endpoints
- **Agent-ready** — designed for LLM function calling with proper schemas
- **Secure** — BashTool deny list, FileOps safety caps, no arbitrary code execution
- **Minimal dependencies** — most tools use only the Python standard library
- **Batteries included** — 15+ tools covering files, search, compute, and more

## Ecosystem

ToolRegistry Hub is part of a three-package ecosystem. See the [Ecosystem](ecosystem.md) page for details.

| Package | Role |
|---------|------|
| [toolregistry](https://toolregistry.readthedocs.io/) | Core tool management library |
| [toolregistry-server](https://toolregistry-server.readthedocs.io/) | OpenAPI & MCP server adapters |
| **toolregistry-hub** | Ready-to-use utility tools |

## Get Involved

- **[GitHub Repository](https://github.com/Oaklight/toolregistry-hub)** - Source code and issues
- **[中文文档](../zh/)** - Chinese documentation
- **[Tools Documentation](tools/)** - Complete tool reference

---

_ToolRegistry Hub: Making utility tools accessible and reliable._
