---
title: 首页
summary: ToolRegistry Hub - 提供各种实用工具的 Python 库
description: ToolRegistry Hub 是一个 Python 库，提供各种实用工具，旨在支持计算、文件操作、网络搜索等常见任务。
keywords: python, 工具, 实用程序, 计算器, 文件操作, 网络搜索
author: Oaklight
hide:
  - navigation
---

# ToolRegistry Hub

[![Docker Image Version](https://img.shields.io/docker/v/oaklight/toolregistry-hub-server?label=Docker&logo=docker)](https://hub.docker.com/r/oaklight/toolregistry-hub-server)
[![PyPI version](https://badge.fury.io/py/toolregistry-hub.svg?icon=si%3Apython)](https://badge.fury.io/py/toolregistry-hub)
[![GitHub version](https://badge.fury.io/gh/oaklight%2Ftoolregistry-hub.svg?icon=si%3Agithub)](https://badge.fury.io/gh/oaklight%2Ftoolregistry-hub)

**从 [ToolRegistry](https://toolregistry.readthedocs.io/) 中提取的精选实用工具集合** - 专为效率、可靠性和易用性而设计。

## 🚀 快速开始

```bash
pip install toolregistry-hub
```

```python
from toolregistry_hub import Calculator, DateTime, FileOps

# 数学计算
result = Calculator.evaluate("2 + 3 * 4")
print(result)  # 输出: 14

# 获取当前时间
current_time = DateTime.now()
print(current_time)

# 文件操作
content = FileOps.read_file("example.txt")
```

## 🛠️ 可用工具

ToolRegistry Hub 提供核心实用工具。**探索 [工具](tools/) 部分以获取每个工具的详细文档。**

- **计算器工具** - 数学计算和表达式求值
- **日期时间工具** - 日期、时间和时区处理
- **文件操作** - 文件内容操作
- **文件系统** - 文件系统操作
- **网络搜索工具** - 多引擎网络搜索功能
- **单位转换** - 在各种单位之间转换
- **思考工具** - 简单推理和头脑风暴
- **网页获取工具** - 从网页提取内容

## 🚀 服务器模式

使用 REST API 或 MCP（模型上下文协议）支持运行独立服务器：

```bash
# 启动 REST API 服务器
toolregistry-server --mode openapi --port 8000

# 启动 MCP 服务器
toolregistry-server --mode mcp --port 8000
```

## 🌟 为什么选择 ToolRegistry Hub？

- **🔧 专注**: 精选的核心实用工具集合
- **⚡ 高效**: 为性能和可靠性优化
- **🔌 可集成**: 可独立使用或作为 [ToolRegistry](https://toolregistry.readthedocs.io/) 生态系统的一部分
- **🌐 易访问**: REST API、MCP 服务器和直接 Python 使用
- **📚 文档完善**: 多语言的全面文档
- **🎯 生产就绪**: 在实际应用中经过实战测试

## 生态系统

ToolRegistry Hub 是三包生态系统的一部分。详情请参阅[生态系统](ecosystem.md)页面。

| 包名 | 角色 |
|------|------|
| [toolregistry](https://toolregistry.readthedocs.io/zh/) | 核心工具管理库 |
| [toolregistry-server](https://toolregistry-server.readthedocs.io/zh/) | OpenAPI 和 MCP 服务器适配器 |
| **toolregistry-hub** | 即用型实用工具 |

## 🤝 参与进来

- **[GitHub 仓库](https://github.com/Oaklight/toolregistry-hub)** - 源代码和问题
- **[English Documentation](../en/)** - 英文文档
- **[工具文档](tools/)** - 完整的工具参考

---

_ToolRegistry Hub: 让实用工具变得可访问且可靠。_
