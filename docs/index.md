---
title: 首页
summary: 面向 LLM Agent 的即用型工具集合
description: ToolRegistry Hub 提供精选的 AI Agent 工具集，涵盖网络搜索、文件操作、代码执行、定时任务等。
keywords: python, tools, utilities, calculator, file operations, web search
author: Oaklight
hide:
  - navigation
---

<section class="tr-hero" markdown>
<p class="tr-kicker">精选工具，即装即用</p>

# 无需重造轮子的实用工具。

<p class="tr-hero__desc">将精选的搜索、抓取、日期时间、计算器、文件、Shell 和工作流工具作为本地 Python 导入使用，或通过 ToolRegistry Core 及 MCP/OpenAPI 服务托管。</p>

<p class="tr-badges">
  <a href="https://pypi.org/project/toolregistry-hub/"><img alt="PyPI version" src="https://img.shields.io/pypi/v/toolregistry-hub?labelColor=475569&color=4d7c0f"></a>
  <a href="https://hub.docker.com/r/oaklight/toolregistry-hub-server"><img alt="Docker Image" src="https://img.shields.io/docker/v/oaklight/toolregistry-hub-server?label=docker&labelColor=475569&color=365314"></a>
  <a href="https://opensource.org/licenses/MIT"><img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-365314?labelColor=475569"></a>
</p>

<div class="tr-actions" markdown>
[快速上手](get-started/installation.md){ .tr-button .tr-button--primary }
[浏览工具](tools/){ .tr-button .tr-button--secondary }
[部署服务器](guides/server.md){ .tr-button .tr-button--secondary }
</div>
</section>

## 选择你的路径

<div class="grid cards" markdown>

-   :material-language-python:{ .lg .middle } **作为库使用**

    ---

    在 Python 中直接导入工具 — 无需服务器。

    [:octicons-arrow-right-24: 库使用指南](guides/library.md)

-   :material-server:{ .lg .middle } **部署服务器**

    ---

    将所有工具暴露为 OpenAPI 或 MCP 端点。

    [:octicons-arrow-right-24: 服务器指南](guides/server.md)

-   :material-tools:{ .lg .middle } **浏览工具**

    ---

    15+ 工具，覆盖搜索、文件、计算、Shell 等。

    [:octicons-arrow-right-24: 工具目录](tools/)

-   :material-docker:{ .lg .middle } **Docker 运行**

    ---

    预构建镜像，即时容器化部署。

    [:octicons-arrow-right-24: Docker 指南](guides/docker.md)

</div>

## 快速体验

```python
from toolregistry_hub import Calculator, DateTime, BashTool, FileSearch

Calculator.evaluate("sqrt(144) + 2**3")   # 20.0
DateTime.now("Asia/Shanghai")              # 上海当前时间
BashTool.execute("git status")             # 安全 Shell 执行
FileSearch.grep(r"TODO", path="src/")      # 搜索代码
```

每个工具都是普通 Python 类 — 无需实例化、无需状态、无需服务器。**[快速上手 →](get-started/quickstart.md)**

## 可用工具

| 分类 | 工具 | 亮点 |
|------|------|------|
| **计算** | [计算器](tools/calculator.md)、[单位转换](tools/unit_converter.md) | 表达式求值、100+ 单位转换 |
| **日期时间** | [DateTime](tools/datetime.md) | 时区感知、跨时区转换 |
| **文件管理** | [FileOps](tools/file_ops.md)、[FileReader](tools/file_reader.md)、[FileSearch](tools/file_search.md)、[PathInfo](tools/path_info.md) | 精确字符串编辑、glob/grep/tree、PDF 和 Notebook 读取 |
| **Shell** | [BashTool](tools/bash_tool.md) | 内置拒绝列表的 Shell 执行 |
| **网络** | [Fetch](tools/websearch/web_fetch_tool.md)、[BraveSearch](tools/websearch/brave.md)、[TavilySearch](tools/websearch/tavily.md)、… | 内容提取、多引擎搜索 |
| **认知** | [ThinkTool](tools/think_tool.md)、[TodoList](tools/todo_list.md) | 结构化推理、任务管理 |

**[完整工具目录 →](tools/)**

## 生态系统

ToolRegistry Hub 是三包生态系统的一部分。详见[生态系统](ecosystem.md)页面。

| 包 | 角色 |
|----|------|
| [toolregistry](https://toolregistry.readthedocs.io/) | 核心工具管理库 |
| [toolregistry-server](https://toolregistry-server.readthedocs.io/) | OpenAPI 与 MCP 服务器适配器 |
| **toolregistry-hub** | 即用型实用工具 |

## 参与贡献

- **[GitHub 仓库](https://github.com/Oaklight/toolregistry-hub)** — 源代码和 Issues
- **[English Docs](../en/)** — 英文文档
- **[工具文档](tools/)** — 完整工具参考

---

_ToolRegistry Hub：让实用工具触手可及。_
