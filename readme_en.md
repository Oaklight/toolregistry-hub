# ToolRegistry Hub Documentation

[![Docker Image Version](https://img.shields.io/docker/v/oaklight/toolregistry-hub-server?label=Docker&logo=docker)](https://hub.docker.com/r/oaklight/toolregistry-hub-server)
[![PyPI version](https://badge.fury.io/py/toolregistry-hub.svg?icon=si%3Apython)](https://badge.fury.io/py/toolregistry-hub)
[![GitHub version](https://badge.fury.io/gh/oaklight%2Ftoolregistry-hub.svg?icon=si%3Agithub)](https://badge.fury.io/gh/oaklight%2Ftoolregistry-hub)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/Oaklight/toolregistry-hub)

[中文版](readme_zh.md) | [English version](readme_en.md)

Welcome to the ToolRegistry Hub documentation! This document provides detailed descriptions of all tools in the project.

## 📚 Documentation

For detailed documentation, please visit our ReadTheDocs pages:

- **English Documentation**: [https://toolregistry-hub.readthedocs.io/en/latest/](https://toolregistry-hub.readthedocs.io/en/latest/)
- **中文文档**: [https://toolregistry-hub.readthedocs.io/zh-cn/latest/](https://toolregistry-hub.readthedocs.io/zh-cn/latest/)

## Tools Overview

ToolRegistry Hub is a Python library that provides various utility tools designed to support common tasks. Here are the main tool categories:

- Calculator Tools - Provides various mathematical calculation functions
- Date Time Tools - Handles date, time, and timezone conversions
- File Operations Tools - Provides file content manipulation functions
- File System Tools - Provides file system operation functions
- Web Search Tools - Provides web search functionality
- Unit Converter Tools - Provides conversions between various units
- Other Tools - Other utility tools
- Server Mode - REST API and MCP server
- Docker Deployment - Docker containerization deployment

For detailed information about each tool category, please refer to the [online documentation](https://toolregistry-hub.readthedocs.io/en/latest/).

## Quick Start

To use ToolRegistry Hub, first install the library:

```bash
pip install toolregistry-hub
```

Then, you can import and use the required tools:

```python
from toolregistry_hub import Calculator, DateTime, FileOps, FileSystem

# Use calculator
result = Calculator.evaluate("2 + 2 * 3")
print(result)  # Output: 8

# Get current time
current_time = DateTime.now()
print(current_time)
```

## Documentation Structure

This documentation is organized by tool categories, with each tool category having its own page that details all tools, methods, and usage examples under that category.

## Contributing

If you want to contribute to ToolRegistry Hub, please refer to the [GitHub repository](https://github.com/Oaklight/toolregistry-hub).
