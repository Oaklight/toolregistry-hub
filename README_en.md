# ToolRegistry Hub Documentation

[![PyPI version](https://img.shields.io/pypi/v/toolregistry-hub?color=green)](https://pypi.org/project/toolregistry-hub/)
[![Docker Image](https://img.shields.io/docker/v/oaklight/toolregistry-hub-server?label=docker&color=green)](https://hub.docker.com/r/oaklight/toolregistry-hub-server)
[![CI](https://github.com/Oaklight/toolregistry-hub/actions/workflows/ci.yml/badge.svg)](https://github.com/Oaklight/toolregistry-hub/actions/workflows/ci.yml)

[中文版](readme_zh.md) | English version

Welcome to the ToolRegistry Hub documentation! This document provides detailed descriptions of all tools in the project.

## Ecosystem

| Package | Description | PyPI | Docs |
|---------|-------------|------|------|
| [**toolregistry**](https://github.com/Oaklight/ToolRegistry) | Core library — tool registration, schema generation, execution | [![PyPI](https://img.shields.io/pypi/v/toolregistry?color=green)](https://pypi.org/project/toolregistry/) | [Docs](https://toolregistry.readthedocs.io/) |
| [**toolregistry-server**](https://github.com/Oaklight/toolregistry-server) | Server adapters — expose tools via OpenAPI & MCP | [![PyPI](https://img.shields.io/pypi/v/toolregistry-server?color=green)](https://pypi.org/project/toolregistry-server/) | [Docs](https://toolregistry-server.readthedocs.io/) |
| [**toolregistry-hub**](https://github.com/Oaklight/toolregistry-hub) | Ready-to-use tools — calculator, web search, file ops, etc. | [![PyPI](https://img.shields.io/pypi/v/toolregistry-hub?color=green)](https://pypi.org/project/toolregistry-hub/) | [Docs](https://toolregistry-hub.readthedocs.io/) |

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
from toolregistry_hub import Calculator, DateTime, FileOps

# Use calculator
result = Calculator.evaluate("2 + 2 * 3")
print(result)  # Output: 8

# Get current time
current_time = DateTime.now()
print(current_time)
```

## Documentation Structure

This documentation is organized by tool categories, with each tool category having its own page that details all tools, methods, and usage examples under that category.

## Changelog

### Web Fetch Tool — Major Update (PR #140)

**Structured return value**

`fetch_content` now returns a structured `dict` instead of a plain `str`:

```json
{
  "content": "...",
  "url": "https://example.com",
  "strategy": "readability",
  "quality": "high",
  "content_type": "text/html",
  "cached": false,
  "elapsed_ms": 123,
  "metadata": {"readability_score": 174.3, "content_length": 12345}
}
```

**`strategy` parameter**

A new optional `strategy` parameter lets you specify the extraction strategy (default: `"auto"`). Available choices:

| Strategy | Description |
|---|---|
| `auto` | Recommended — tries each fallback in order |
| `markdown` | Cloudflare content negotiation |
| `readability` | Local readability extraction |
| `soup` | Local BeautifulSoup fallback |
| `veilrender` | Remote headless browser (requires `VEILRENDER_ENDPOINT`) |
| `cdp` | Self-hosted Chrome DevTools Protocol (requires `CDP_ENDPOINT`) |
| `jina` | Jina Reader API (always available; optional `JINA_API_KEY` for higher rate limits) |

Available choices are narrowed at runtime: `veilrender` and `cdp` appear only when their respective endpoints are configured.

**Updated fallback chain**

```
markdown → readability → soup → veilrender → cdp → jina → local_fallback
```

**VeilRender fallback**

VeilRender is a new optional remote headless browser fallback for JS-heavy pages and SPAs. Configure via environment variables:

```
VEILRENDER_ENDPOINT=https://your-veilrender-instance
VEILRENDER_TOKEN=your_token_here  # optional
```

## Contributing

If you want to contribute to ToolRegistry Hub, please refer to the [GitHub repository](https://github.com/Oaklight/toolregistry-hub).
