---
title: 服务器配置
summary: 配置认证、工具加载和自定义工具注册
description: 设置 Bearer Token 认证、控制加载哪些工具、注册自定义工具，以及使用部署配置文件。
keywords: server, configuration, authentication, tools.jsonc, custom tools, profiles
author: Oaklight
---

# 服务器配置

本指南涵盖认证、工具选择、自定义工具注册和部署配置文件。如需启动服务器，请参阅**[启动服务器](../get-started/server.md)**。

## 认证

服务器支持可选的 Bearer Token 认证。

### 配置

=== "单个令牌"

    ```bash
    export API_BEARER_TOKEN="your-secret-token"
    ```

=== "多个令牌"

    ```bash
    export API_BEARER_TOKEN="token1,token2,token3"
    ```

=== "令牌文件"

    ```bash
    export API_BEARER_TOKENS_FILE="/path/to/tokens.txt"
    ```

    文件中每行一个令牌。

### 使用

```http
Authorization: Bearer your-valid-token
```

如果未设置任何令牌变量，则不启用认证。

也可以通过 CLI 直接指定令牌文件：

```bash
toolregistry-hub openapi --tokens /path/to/tokens.txt
```

## 工具配置

通过 `tools.jsonc` 文件控制加载哪些工具：

```bash
# 从工作目录自动发现
cp tools.jsonc.example tools.jsonc

# 或通过 CLI 指定
toolregistry-hub openapi --config path/to/tools.jsonc
```

### 拒绝列表模式（默认）

加载所有工具，排除明确禁用的：

```jsonc
{
  "mode": "denylist",
  "disabled": ["file_ops"]  // 禁用特定工具
}
```

### 允许列表模式

仅加载指定的工具：

```jsonc
{
  "mode": "allowlist",
  "enabled": ["calculator", "datetime", "unit_converter"]
}
```

## 自定义工具注册

可以在内置工具之外注册自定义工具类：

```jsonc
{
  "tools": [
    {"class": "toolregistry_hub.calculator.Calculator", "namespace": "calculator"},
    {"class": "my_package.MyTool", "namespace": "my_tool"}
  ]
}
```

自定义类需遵循与内置工具相同的接口。每个工具类在指定的命名空间下注册。

## 部署配置文件

`--profile` 参数根据部署场景过滤注册的工具：

| 配置文件 | 效果                                     |
| -------- | ---------------------------------------- |
| `remote` | 禁用本地文件系统/Shell/定时任务工具       |
| `local`  | 仅保留本地工具；禁用网络工具             |
| *(无)*   | 注册所有工具（默认）                     |

```bash
# 远程部署 — 禁用文件系统和 Shell 访问
toolregistry-hub openapi --profile remote

# 仅本地 — 禁用网络搜索和抓取
toolregistry-hub mcp --profile local
```

## 错误处理

标准 HTTP 状态码：

| 状态码 | 含义                    |
| ------ | ----------------------- |
| `200`  | 成功                    |
| `400`  | 请求错误 / 参数无效     |
| `401`  | 认证失败                |
| `500`  | 服务器内部错误          |

错误响应格式：`{"detail": "错误描述"}`。

## 故障排除

| 问题             | 解决方案                                              |
| ---------------- | ----------------------------------------------------- |
| 依赖安装失败     | 确保 Python 3.10+                                     |
| 端口被占用       | 使用 `--port` 指定其他端口                            |
| 搜索工具不可用   | 设置 API 密钥 — 见[环境变量](../reference/environment.md) |
| 认证失败         | 检查 `API_BEARER_TOKEN` 和请求头                      |
| MCP 客户端拒绝可空参数 schema | 升级至 `toolregistry>=0.11.2` — 可空字段现在生成简化版 `anyOf` schema，兼容严格 MCP 校验器 |

## 另请参阅

- **[启动服务器](../get-started/server.md)** — 安装和运行
- **[CLI 参考](../reference/cli.md)** — 所有命令行选项
- **[API 端点](../reference/endpoints.md)** — 完整端点列表
- **[Docker 部署](docker.md)** — 容器化部署
- **[环境变量](../reference/environment.md)** — 所有环境变量一览
