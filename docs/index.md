---
title: 首页
summary: 面向 LLM Agent 的即用工具集合
description: ToolRegistry Hub 提供精选的 AI Agent 就绪工具集合，涵盖网络搜索、文件操作、代码执行、定时任务等。
keywords: python, 工具, 实用程序, 计算器, 文件操作, 网络搜索
author: Oaklight
hide:
  - navigation
---

# ToolRegistry Hub

[![PyPI version](https://img.shields.io/pypi/v/toolregistry-hub?color=green)](https://pypi.org/project/toolregistry-hub/)
[![Docker Image](https://img.shields.io/docker/v/oaklight/toolregistry-hub-server?label=docker&color=green)](https://hub.docker.com/r/oaklight/toolregistry-hub-server)

**面向 LLM Agent 的即用工具集合** — 网络搜索、文件操作、代码执行等。可作为 Python 库直接使用，也可部署为服务器。[ToolRegistry](https://toolregistry.readthedocs.io/) 生态系统的一部分。

## 两种使用方式

=== "作为 Python 库"

    ```bash
    pip install toolregistry-hub
    ```

    ```python
    from toolregistry_hub import Calculator, DateTime, BashTool, FileSearch

    Calculator.evaluate("sqrt(144) + 2**3")   # 20.0
    DateTime.now("Asia/Shanghai")              # 上海当前时间
    BashTool.execute("git status")             # 安全的 Shell 执行
    FileSearch.grep(r"TODO", path="src/")      # 搜索代码
    ```

    每个工具都是带静态方法的普通 Python 类 — 无需实例化、无需管理状态、无需启动服务器。**[了解更多 →](library.md)**

=== "作为服务器"

    ```bash
    pip install toolregistry-hub[server]

    # REST API 服务器
    toolregistry-server --mode openapi --port 8000

    # MCP 服务器（用于 AI Agent）
    toolregistry-server --mode mcp --port 8000
    ```

    所有工具自动暴露为 API 端点。**[了解更多 →](server.md)**

## 可用工具

| 类别 | 工具 | 亮点 |
|------|------|------|
| **计算** | [Calculator](tools/calculator.md)、[UnitConverter](tools/unit_converter.md) | 表达式求值、100+ 种单位转换 |
| **日期时间** | [DateTime](tools/datetime.md) | 时区感知、跨时区转换 |
| **文件管理** | [FileOps](tools/file_ops.md)、[FileReader](tools/file_reader.md)、[FileSearch](tools/file_search.md)、[PathInfo](tools/path_info.md) | 精确字符串替换、glob/grep/tree、PDF 和 Notebook 读取 |
| **Shell** | [BashTool](tools/bash_tool.md) | 内置拒绝列表的安全 Shell 执行 |
| **网络** | [Fetch](tools/websearch/web_fetch_tool.md)、[BraveSearch](tools/websearch/brave.md)、[TavilySearch](tools/websearch/tavily.md)… | 内容提取、多引擎搜索 |
| **认知** | [ThinkTool](tools/think_tool.md)、[TodoList](tools/todo_list.md) | 结构化推理、任务管理 |

**探索 [工具](tools/) 部分获取详细文档。**

## 为什么选择 ToolRegistry Hub？

- **双模式** — 同一套工具既能 import 使用，又能部署为服务端点
- **Agent 就绪** — 为 LLM function calling 设计，附带规范的工具 schema
- **安全** — BashTool 拒绝列表、FileOps 安全上限、无任意代码执行
- **极少依赖** — 大部分工具仅使用 Python 标准库
- **开箱即用** — 15+ 工具覆盖文件、搜索、计算等场景

## 生态系统

ToolRegistry Hub 是三包生态系统的一部分。详情请参阅[生态系统](ecosystem.md)页面。

| 包名 | 角色 |
|------|------|
| [toolregistry](https://toolregistry.readthedocs.io/zh/) | 核心工具管理库 |
| [toolregistry-server](https://toolregistry-server.readthedocs.io/zh/) | OpenAPI 和 MCP 服务器适配器 |
| **toolregistry-hub** | 即用型实用工具 |

## 参与进来

- **[GitHub 仓库](https://github.com/Oaklight/toolregistry-hub)** - 源代码和问题
- **[English Documentation](../en/)** - 英文文档
- **[工具文档](tools/)** - 完整的工具参考

---

_ToolRegistry Hub: 让实用工具变得可访问且可靠。_
