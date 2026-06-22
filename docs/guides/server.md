---
title: 服务器模式
summary: 将 ToolRegistry Hub 工具部署为 REST API 或 MCP 端点
description: 启动 OpenAPI 或 MCP 服务器，将所有 hub 工具暴露为可远程调用的端点。
keywords: server, openapi, mcp, rest api, deployment, fastapi
author: Oaklight
---

# 服务器模式

ToolRegistry Hub 可以将所有工具暴露为网络端点 — OpenAPI (REST) 服务器或 MCP 服务器。两种模式都自动注册所有可用工具，只需选择协议并启动即可。

## 安装

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

## 认证

服务器支持可选的 Bearer Token 认证。

### 配置

=== "单个令牌"

    ```bash
    export API_BEARER_TOKEN="***"
    ```

=== "多个令牌"

    ```bash
    export API_BEARER_TOKEN="token1…ken3"
    ```

=== "令牌文件"

    ```bash
    export API_BEARER_TOKENS_FILE="/path/to/tokens.txt"
    ```

    文件中每行一个令牌。

### 使用

```http
Authorization: Bearer ***
```

如果未设置任何令牌变量，则不启用认证。

## 工具配置

通过 `tools.jsonc` 文件控制加载哪些工具：

```bash
# 从工作目录自动发现
cp tools.jsonc.example tools.jsonc

# 或通过 CLI 指定
toolregistry-hub openapi --config path/to/tools.jsonc
```

### 拒绝列表模式（默认）

```jsonc
{
  "mode": "denylist",
  "disabled": ["file_ops"]  // 禁用特定工具
}
```

### 允许列表模式

```jsonc
{
  "mode": "allowlist",
  "enabled": ["calculator", "datetime", "unit_converter"]
}
```

### 自定义工具注册

```jsonc
{
  "tools": [
    {"class": "toolregistry_hub.calculator.Calculator", "namespace": "calculator"},
    {"class": "my_package.MyTool", "namespace": "my_tool"}
  ]
}
```

## 调用 API

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
    json={"expression": "2 + 2 * 3"}
)
print(response.json())
```

## 错误处理

标准 HTTP 状态码：

| 状态码 | 含义 |
|--------|------|
| `200` | 成功 |
| `400` | 请求错误 / 参数无效 |
| `401` | 认证失败 |
| `500` | 服务器内部错误 |

错误响应格式：`{"detail": "错误描述"}`。

## 故障排除

| 问题 | 解决方案 |
|------|---------|
| 依赖安装失败 | 确保 Python 3.10+ |
| 端口被占用 | 使用 `--port` 指定其他端口 |
| 搜索工具不可用 | 设置 API 密钥 — 见[环境变量](../reference/environment.md) |
| 认证失败 | 检查 `API_BEARER_TOKEN` 和请求头 |
| MCP 客户端拒绝可空参数 schema | 升级至 `toolregistry>=0.11.2` — 可空字段现在生成简化版 `anyOf` schema，兼容严格 MCP 校验器 |

## 另请参阅

- **[CLI 参考](../reference/cli.md)** — 所有命令行选项
- **[API 端点](../reference/endpoints.md)** — 完整端点列表
- **[Docker 部署](docker.md)** — 容器化部署
- **[环境变量](../reference/environment.md)** — 所有环境变量一览
