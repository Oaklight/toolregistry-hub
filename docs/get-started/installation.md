---
title: 安装
summary: 安装 ToolRegistry Hub — 作为 Python 库或包含服务器扩展
description: toolregistry-hub 的分步安装指南 — 纯库、服务器扩展或 Docker。
keywords: install, pip, python, setup, server, docker
author: Oaklight
---

# 安装

## 仅安装库

```bash
pip install toolregistry-hub
```

即可将所有工具作为 Python 直接导入使用 — 无需服务器，无需额外依赖。

## 包含服务器扩展

如果需要将工具暴露为 REST API 或 MCP 端点：

!!! tip
    **zsh 用户**（macOS 默认 shell）：需要用引号包裹包名，例如 `pip install 'toolregistry-hub[server]'` — zsh 会将 `[]` 解释为通配符。

```bash
# 完整服务器（OpenAPI + MCP，Python 3.10+）
pip install toolregistry-hub[server]

# 仅 OpenAPI 服务器
pip install toolregistry-hub[server_openapi]

# 仅 MCP 服务器（Python 3.10+）
pip install toolregistry-hub[server_mcp]
```

## Docker

Docker Hub 上提供预构建镜像：

```bash
docker run -p 8000:8000 oaklight/toolregistry-hub-server:latest
```

详见 [Docker 部署](../guides/docker.md) 了解 compose 文件和生产环境配置。

## 验证

```python
from toolregistry_hub import Calculator

print(Calculator.evaluate("1 + 1"))  # 2
```

## 下一步

- **[快速上手](quickstart.md)** — 60 秒体验工具
- **[库使用方式](../guides/library.md)** — 完整库使用指南
- **[服务器模式](../guides/server.md)** — 部署为 API 服务器
