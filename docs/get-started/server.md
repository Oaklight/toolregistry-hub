---
title: 启动服务器
summary: 启动 ToolRegistry Hub 服务器并发送第一个请求
description: 一分钟内启动 OpenAPI 或 MCP 服务器，然后调用一个工具端点。
keywords: server, quickstart, openapi, mcp, first request
author: Oaklight
---

# 启动服务器

ToolRegistry Hub 可以将所有工具暴露为网络端点 — OpenAPI (REST) 服务器或 MCP 服务器。本页引导你从安装到完成第一次请求。

## 安装服务器依赖

```bash
# 完整服务器（OpenAPI + MCP，Python 3.10+）
pip install toolregistry-hub[server]

# 仅 OpenAPI
pip install toolregistry-hub[server_openapi]

# 仅 MCP（Python 3.10+）
pip install toolregistry-hub[server_mcp]
```

## 启动服务器

### OpenAPI

```bash
toolregistry-hub openapi --host 0.0.0.0 --port 8000
```

启动后：

- API 根路径：`http://localhost:8000`
- 交互式文档：`http://localhost:8000/docs`
- OpenAPI 规范：`http://localhost:8000/openapi.json`

### MCP

```bash
# 可流式 HTTP（推荐用于远程客户端）
toolregistry-hub mcp --transport streamable-http --host 0.0.0.0 --port 8000

# SSE 传输
toolregistry-hub mcp --transport sse --host 0.0.0.0 --port 8000

# Stdio 传输（用于本地 Agent 集成）
toolregistry-hub mcp --transport stdio
```

## 发送第一个请求

### curl

```bash
curl -X POST "http://localhost:8000/tools/calculator/evaluate" \
  -H "Content-Type: application/json" \
  -d '{"expression": "2 + 2 * 3"}'
```

### Python

```python
import requests

response = requests.post(
    "http://localhost:8000/tools/calculator/evaluate",
    json={"expression": "2 + 2 * 3"},
)
print(response.json())  # {"result": "8"}
```

## 下一步

| 我想…                              | 前往                                                  |
| ---------------------------------- | ----------------------------------------------------- |
| 配置认证或工具加载                 | [服务器配置](../guides/server.md)                     |
| 使用 Docker 运行                   | [Docker 部署](../guides/docker.md)                    |
| 查看所有 CLI 参数                  | [CLI 参考](../reference/cli.md)                       |
| 浏览所有端点                       | [API 端点](../reference/endpoints.md)                 |
| 作为 Python 库直接使用             | [库使用方式](../guides/library.md)                    |
