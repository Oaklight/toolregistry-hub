# ToolRegistry Hub Documentation

[中文版](docs/readme_zh.md) | [English version](docs/readme_en.md)

Welcome to the ToolRegistry Hub documentation! This document provides detailed descriptions of all tools in the project.

## Tools Overview

ToolRegistry Hub is a Python library that provides various utility tools designed to support common tasks. Here are the main tool categories:

- [Calculator Tools](docs/en/calculator.md) - Provides various mathematical calculation functions
- [Date Time Tools](docs/en/datetime.md) - Handles date, time, and timezone conversions
- [File Operations Tools](docs/en/file_ops.md) - Provides file content manipulation functions
- [File System Tools](docs/en/filesystem.md) - Provides file system operation functions
- [Web Search Tools](docs/en/websearch/index.md) - Provides web search functionality
- [Unit Converter Tools](docs/en/unit_converter.md) - Provides conversions between various units
- [Other Tools](docs/en/other_tools.md) - Other utility tools
- [Server Mode](docs/en/server.md) - REST API and MCP server
- [Docker Deployment](docs/en/docker.md) - Docker containerization deployment

## Navigation

View the [navigation page](docs/en/navigation.md) for complete documentation structure and navigation links.

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
