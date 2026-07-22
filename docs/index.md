---
title: Home
summary: Ready-to-Use Tool Collection for LLM Agents
description: ToolRegistry Hub provides a curated collection of AI-agent-ready tools for web search, file operations, code execution, scheduling, and more.
keywords: python, tools, utilities, calculator, file operations, web search
author: Oaklight
hide:
  - navigation
---

<section class="tr-hero" markdown>
<p class="tr-kicker">Curated tools, ready to run</p>

# Useful tools without rebuilding the stack.

<p class="tr-hero__desc">Use curated search, fetch, datetime, calculator, file, shell, and workflow tools as local Python imports, with ToolRegistry Core, or as hosted MCP/OpenAPI services.</p>

<p class="tr-badges">
  <a href="https://pypi.org/project/toolregistry-hub/"><img alt="PyPI version" src="https://img.shields.io/pypi/v/toolregistry-hub?labelColor=475569&color=4d7c0f"></a>
  <a href="https://hub.docker.com/r/oaklight/toolregistry-hub-server"><img alt="Docker Image" src="https://img.shields.io/docker/v/oaklight/toolregistry-hub-server?label=docker&labelColor=475569&color=365314"></a>
  <a href="https://opensource.org/licenses/MIT"><img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-365314?labelColor=475569"></a>
</p>

```bash
pip install toolregistry-hub
```

<div class="tr-actions" markdown>
[Get Started](get-started/installation.md){ .tr-button .tr-button--primary }
[Browse Tools](tools/){ .tr-button .tr-button--secondary }
[Deploy Server](guides/server.md){ .tr-button .tr-button--secondary }
</div>
</section>

## Pick Your Path

<div class="grid cards" markdown>

-   :material-language-python:{ .lg .middle } **Use as a Library**

    ---

    Import tools directly in Python — no server needed.

    [:octicons-arrow-right-24: Library Guide](guides/library.md)

-   :material-server:{ .lg .middle } **Deploy a Server**

    ---

    Expose all tools as OpenAPI or MCP endpoints.

    [:octicons-arrow-right-24: Server Guide](guides/server.md)

-   :material-tools:{ .lg .middle } **Browse the Tools**

    ---

    15+ tools for search, files, compute, shell, and more.

    [:octicons-arrow-right-24: Tool Catalog](tools/)

-   :material-docker:{ .lg .middle } **Run in Docker**

    ---

    Pre-built images for instant containerized deployment.

    [:octicons-arrow-right-24: Docker Guide](guides/docker.md)

</div>

## Quick Taste

```python
from toolregistry_hub import Calculator, DateTime, BashTool, FileSearch

Calculator.evaluate("sqrt(144) + 2**3")   # 20.0
DateTime.now("Asia/Shanghai")              # current time in Shanghai
BashTool.execute("git status")             # safe shell execution
FileSearch.grep(r"TODO", path="src/")      # search code
```

Every tool is a plain Python class — no instantiation, no state, no server needed. **[Quick Start →](get-started/quickstart.md)**

## Ecosystem

ToolRegistry Hub is part of a three-package ecosystem. See the [Ecosystem](ecosystem.md) page for details.

| Package | Role |
|---------|------|
| [toolregistry](https://toolregistry.readthedocs.io/) | Core tool management library |
| [toolregistry-server](https://toolregistry-server.readthedocs.io/) | OpenAPI & MCP server adapters |
| **toolregistry-hub** | Ready-to-use utility tools |

## Get Involved

- **[GitHub Repository](https://github.com/Oaklight/toolregistry-hub)** — Source code and issues
- **[中文文档](../zh/)** — Chinese documentation
- **[Tools Documentation](tools/)** — Complete tool reference

---

_ToolRegistry Hub: Making utility tools accessible and reliable._
