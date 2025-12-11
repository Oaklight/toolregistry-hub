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

[![Docker Image Version](https://img.shields.io/docker/v/oaklight/toolregistry-hub-server?label=Docker&logo=docker)](https://hub.docker.com/r/oaklight/toolregistry-hub-server)
[![PyPI version](https://badge.fury.io/py/toolregistry-hub.svg?icon=si%3Apython)](https://badge.fury.io/py/toolregistry-hub)
[![GitHub version](https://badge.fury.io/gh/oaklight%2Ftoolregistry-hub.svg?icon=si%3Agithub)](https://badge.fury.io/gh/oaklight%2Ftoolregistry-hub)

**A curated collection of utility tools extracted from [ToolRegistry](https://toolregistry.readthedocs.io/)** - designed for efficiency, reliability, and ease of use.

## 🚀 Quick Start

```bash
pip install toolregistry-hub
```

```python
from toolregistry_hub import Calculator, DateTime, FileOps

# Mathematical calculations
result = Calculator.evaluate("2 + 3 * 4")
print(result)  # Output: 14

# Get current time
current_time = DateTime.now()
print(current_time)

# File operations
content = FileOps.read_file("example.txt")
```

## 🛠️ Available Tools

ToolRegistry Hub provides essential utility tools. **Explore the [Tools](tools/) section for detailed documentation of each tool.**

- **Calculator Tools** - Mathematical calculations and expression evaluation
- **Date Time Tools** - Date, time, and timezone handling
- **File Operations** - File content manipulation
- **File System** - File system operations
- **Web Search Tools** - Multi-engine web search capabilities
- **Unit Converter** - Convert between various units
- **Think Tool** - Simple reasoning and brainstorming
- **Web Fetch Tool** - Extract content from webpages

## 🚀 Server Mode

Run as a standalone server with REST API or MCP (Model Context Protocol) support:

```bash
# Start REST API server
toolregistry-server --mode openapi --port 8000

# Start MCP server
toolregistry-server --mode mcp --port 8000
```

## 🌟 Why ToolRegistry Hub?

- **🔧 Focused**: Curated collection of essential utility tools
- **⚡ Efficient**: Optimized for performance and reliability
- **🔌 Integrable**: Works standalone or as part of [ToolRegistry](https://toolregistry.readthedocs.io/) ecosystem
- **🌐 Accessible**: REST API, MCP server, and direct Python usage
- **📚 Documented**: Comprehensive documentation in multiple languages
- **🎯 Production Ready**: Battle-tested in real-world applications

## 🤝 Get Involved

- **[GitHub Repository](https://github.com/Oaklight/toolregistry-hub)** - Source code and issues
- **[中文文档](../zh/)** - Chinese documentation
- **[Tools Documentation](tools/)** - Complete tool reference

---

_ToolRegistry Hub: Making utility tools accessible and reliable._
