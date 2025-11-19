---
title: English Documentation
summary: Complete documentation for ToolRegistry Hub in English
description: Comprehensive English documentation for ToolRegistry Hub - a Python library providing various utility tools
keywords: python, tools, utilities, documentation, english
author: ToolRegistry Hub Team
---

# ToolRegistry Hub Documentation

Welcome to the comprehensive documentation for **ToolRegistry Hub**! This library provides various utility tools designed to support common tasks in Python development.

## 🚀 Quick Start

### Installation

```bash
pip install toolregistry-hub
```

### Basic Usage

```python
from toolregistry_hub import Calculator, DateTime, FileOps, FileSystem

# Mathematical calculations
result = Calculator.evaluate("2 + 3 * 4")
print(result)  # Output: 14

# Get current time
current_time = DateTime.now()
print(current_time)

# File operations
content = FileOps.read_file("example.txt")
print(content)
```

## 📖 Tool Categories

### Core Utilities

<div class="grid cards" markdown>

-   :material-calculator: **[Calculator Tools](calculator.md)**

    ---

    Mathematical calculations, expression evaluation, and statistical functions.

    [:octicons-arrow-right-24: Learn more](calculator.md)

-   :material-clock: **[Date Time Tools](datetime.md)**

    ---

    Date, time, timezone conversions, and temporal operations.

    [:octicons-arrow-right-24: Learn more](datetime.md)

-   :material-file-edit: **[File Operations](file_ops.md)**

    ---

    File content manipulation, reading, writing, and processing.

    [:octicons-arrow-right-24: Learn more](file_ops.md)

-   :material-folder: **[File System](filesystem.md)**

    ---

    File system operations, directory management, and path utilities.

    [:octicons-arrow-right-24: Learn more](filesystem.md)

</div>

### Advanced Features

<div class="grid cards" markdown>

-   :material-web: **[Web Search Tools](websearch/index.md)**

    ---

    Multi-engine web search with support for Bing, Brave, SearXNG, and Tavily.

    [:octicons-arrow-right-24: Explore](websearch/index.md)

-   :material-swap-horizontal: **[Unit Converter](unit_converter.md)**

    ---

    Convert between various units of measurement.

    [:octicons-arrow-right-24: Convert](unit_converter.md)

-   :material-tools: **[Other Tools](other_tools.md)**

    ---

    Additional utility functions and helper tools.

    [:octicons-arrow-right-24: Discover](other_tools.md)

</div>

### Deployment & Integration

<div class="grid cards" markdown>

-   :material-server: **[Server Mode](server.md)**

    ---

    REST API server and MCP (Model Context Protocol) integration.

    [:octicons-arrow-right-24: Deploy](server.md)

-   :material-docker: **[Docker Deployment](docker.md)**

    ---

    Containerized deployment with Docker and Docker Compose.

    [:octicons-arrow-right-24: Containerize](docker.md)

</div>

## 🗺️ Navigation

- **[Navigation Guide](navigation.md)** - Complete documentation structure and links
- **[中文文档](../zh/index.md)** - Switch to Chinese documentation

## 📚 API Reference

Each tool category provides detailed API documentation including:

- **Class Overview** - Understanding the tool architecture
- **Method Documentation** - Detailed parameter and return value descriptions
- **Usage Examples** - Practical code examples
- **Best Practices** - Recommended usage patterns

## 🔍 Search

Use the search functionality in the top navigation to quickly find specific tools, methods, or concepts across the entire documentation.

## 🤝 Contributing

Found an issue or want to contribute? Visit our [GitHub repository](https://github.com/Oaklight/toolregistry-hub) to:

- Report bugs
- Request features
- Submit pull requests
- Improve documentation

---

*Ready to get started? Choose a tool category above or browse the [navigation guide](navigation.md) for a complete overview.*