---
title: 快速上手
summary: 60 秒体验 ToolRegistry Hub 工具
description: 动手体验最常用的 hub 工具 — 计算器、日期时间、文件搜索、网页抓取和 Shell 执行。
keywords: quickstart, tutorial, getting started, examples, python
author: Oaklight
---

# 快速上手

本页帮你在一分钟内从零开始写出可运行的代码。完整工具目录请参阅 **[工具](../tools/)**。

## 前提条件

请先完成 [安装](installation.md)。

## 试试看

### 数学与单位

```python
from toolregistry_hub import Calculator, UnitConverter

Calculator.evaluate("sqrt(144) + 2**3")          # 20.0
Calculator.evaluate("log(100, 10) + sin(pi/2)")  # 3.0

UnitConverter.convert(100, "celsius_to_fahrenheit")  # 212.0
```

### 日期与时间

```python
from toolregistry_hub import DateTime

DateTime.now("Asia/Shanghai")                                   # 上海当前时间
DateTime.convert_timezone("14:30", "America/Chicago", "Asia/Tokyo")  # 时区转换
```

### 文件

```python
from toolregistry_hub import FileSearch, FileReader, FileOps

FileSearch.grep(r"TODO", path="src/")               # 在源码中查找 TODO
FileSearch.tree("src/", max_depth=2)                 # 目录概览
FileReader.read("config.py", limit=20)               # 前 20 行
FileOps.edit("config.py",
             old_string="DEBUG = True",
             new_string="DEBUG = False")              # 安全字符串替换
```

### 网络

```python
from toolregistry_hub import Fetch
from toolregistry_hub.websearch import WebSearch

Fetch().fetch_content("https://example.com")         # 提取页面内容

ws = WebSearch()
results = ws.search("Python 3.12 新特性", max_results=3)
for r in results:
    print(f"{r.title}: {r.url}")
```

!!! note "API 密钥"
    网络搜索工具需要设置环境变量中的 API 密钥。无需密钥的工具（Calculator、DateTime、FileOps 等）开箱即用。完整列表见[环境变量](../reference/environment.md)。

### Shell

```python
from toolregistry_hub import BashTool

result = BashTool.execute("python --version", timeout=10)
print(result["stdout"])  # Python 3.11.5
```

### 启动服务器

```bash
pip install toolregistry-hub[server]
toolregistry-hub openapi --port 8000
# → API 文档地址：http://localhost:8000/docs
```

## 接下来做什么？

| 我想…                          | 前往                                        |
|-------------------------------|---------------------------------------------|
| 浏览所有可用工具                | [工具](../tools/)                           |
| 作为 Python 导入使用            | [库使用方式](../guides/library.md)           |
| 部署为 REST API 或 MCP          | [服务器模式](../guides/server.md)            |
| 在 Docker 中运行               | [Docker 部署](../guides/docker.md)           |
| 注册工具到 Agent               | [库使用方式 → AI Agent](../guides/library.md#在-ai-agent-中使用) |
