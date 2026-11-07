---
title: CLI 参考
summary: toolregistry-hub 完整命令行参考
description: toolregistry-hub 服务器的所有 CLI 命令、标志和选项。
keywords: cli, command line, options, flags, openapi, mcp
author: Oaklight
---

# CLI 参考

`toolregistry-hub` 命令以 OpenAPI 或 MCP 模式启动 hub 服务器。

## 概要

```
toolregistry-hub [OPTIONS] COMMAND [COMMAND-OPTIONS]
```

## 全局选项

| 标志 | 描述 |
|------|------|
| `--version` / `-V` | 显示版本并退出 |
| `--no-banner` | 禁用启动横幅 |

## 命令

### `openapi`

启动基于 FastAPI 的 OpenAPI (REST) 服务器。

```bash
toolregistry-hub openapi [OPTIONS]
```

| 选项 | 默认值 | 描述 |
|------|--------|------|
| `--host HOST` | `0.0.0.0` | 绑定地址 |
| `--port PORT` | `8000` | 绑定端口 |
| `--env PATH` | `.env` | `.env` 文件路径 |
| `--no-env` | — | 跳过加载 `.env` |
| `--config PATH` | — | 工具配置文件（JSON、JSONC 或 YAML） |
| `--tokens PATH` | — | Bearer 令牌文件（每行一个） |
| `--admin-port PORT` | — | 在指定端口启用管理面板 |
| `--tool-discovery` / `--no-tool-discovery` | 启用 | 通过 `discover_tools` 渐进式工具披露 |
| `--think-augment` / `--no-think-augment` | 启用 | 向工具 schema 注入 `toolcall_reason` 属性 |
| `--profile {remote,local}` | 无 | 部署 profile 过滤（见下方） |
| `--config-reload` / `--no-config-reload` | 关闭 | 配置文件变更时自动重载（轮询检测，按进程生效；#144） |
| `--reload` | — | 开发环境自动重载 |

### `mcp`

启动 MCP (Model Context Protocol) 服务器。

```bash
toolregistry-hub mcp [OPTIONS]
```

| 选项 | 默认值 | 描述 |
|------|--------|------|
| `--transport {stdio,sse,streamable-http}` | `stdio` | MCP 传输类型 |
| `--host HOST` | `127.0.0.1` | 绑定地址（SSE / streamable-http） |
| `--port PORT` | `8000` | 绑定端口（SSE / streamable-http） |
| `--env PATH` | `.env` | `.env` 文件路径 |
| `--no-env` | — | 跳过加载 `.env` |
| `--config PATH` | — | 工具配置文件（JSON、JSONC 或 YAML） |
| `--admin-port PORT` | — | 在指定端口启用管理面板 |
| `--tool-discovery` / `--no-tool-discovery` | 启用 | 通过 `discover_tools` 渐进式工具披露 |
| `--think-augment` / `--no-think-augment` | 启用 | 向工具 schema 注入 `toolcall_reason` 属性 |
| `--profile {remote,local}` | 无 | 部署 profile 过滤（见下方） |
| `--config-reload` / `--no-config-reload` | 关闭 | 配置文件变更时自动重载（轮询检测，按进程生效；#144） |

### 配置热重载

使用 `--config-reload` 时，`openapi` 和 `mcp` 会启动后台 watcher，轮询配置文件（`--config`）并对运行中的注册表做 source 级 diff：新增 source 会被注册，删除 source 会被注销，离开配置范围的 source 会被禁用，声明变化会被重新注册。非法配置只记录日志并被忽略，当前注册表继续服务。Hub 默认元数据（`tags`、`defer`、`title`、`search_hint` 与执行提示）只应用于本次 reload 注册的工具，已存在的工具保持管理面板修改后的值。reload 注册的新 source 会重新套用 `--profile` 过滤，被排除的工具保持禁用。watcher 按进程生效且默认关闭，多个服务之间不做协调。

已知限制：从文件中删除 `tool_metadata` 条目后，该项设置不会回滚，直到进程重启。这些字段同样可由管理面板写入，reload 无法区分文件写入的值与之后的面板编辑；如需恢复，请在面板中重置。

一个成功注册但未产出任何工具的 source，在声明不变时不会被再次拉取。如果 MCP 服务器后来才 advertise 工具，需要显式修改 source 声明（或重启进程）才能注册。

## 部署 Profile

`--profile` 标志过滤注册的工具：

| Profile | 效果 |
|---------|------|
| `remote` | 禁用服务器本地文件系统/Shell/定时任务工具 |
| `local` | 仅保留本机工具；禁用网络工具 |
| *(无)* | 所有工具均注册（默认） |
