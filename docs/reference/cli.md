---
title: CLI 参考
summary: toolregistry-hub 启动器完整命令行参考
description: toolregistry-hub 启动器的所有 CLI 命令、标志和选项。
keywords: cli, command line, options, flags, openapi, mcp, local-hub, hub-shim, keys
author: Oaklight
---

# CLI 参考

`toolregistry-hub` 是 `toolregistry-server` 的启动器。它解析工具预设、把
Hub 命令翻译成等价的服务器命令，并以 Hub 应用对象运行服务器 CLI。

## 概要

```
toolregistry-hub [OPTIONS] COMMAND [COMMAND-OPTIONS]
```

Hub 专属选项可以放在命令之前或之后。

## 启动器行为

- **预设。** 显式 `--config PATH`（或 `--config=PATH`）优先；否则依次检查
  `TOOLS_CONFIG`、工作目录下的 `tools.jsonc` / `tools.yaml` / `tools.yml`，
  最后使用包内 `data/tools.yaml`。命令需要配置时，解析结果会作为
  `--config` 传给服务器。包内预设始终只存在于内存：运行期 source 变更不会
  改写该文件。
- **命令翻译。** 服务器解析之前会先改写 Hub 命令：

| Hub 命令 | 服务器命令 |
|----------|------------|
| `openapi` | `gateway --openapi` |
| `mcp --transport streamable-http` 或 `http` | `gateway --mcp` |
| `mcp --transport sse` | `gateway --sse` |
| `mcp`（stdio 或未指定传输） | `mcp --transport stdio` |
| `gateway`、`local-hub`、`hub-shim`、`keys` | 保持不变 |

- `openapi` 与 HTTP MCP 传输会把 `--backend` 转发给 gateway；stdio 下该标志
  没有意义，会被移除。
- 启动器自己打印 Hub 横幅与更新检查（服务器横幅被抑制），并在启动服务器前
  设置 `TOOLREGISTRY_LOCAL_HUB_COMMAND=toolregistry-hub`。前台进程始终运行
  Hub app，因此 `local-hub run` 不受影响。toolregistry-server 0.9.0 不读取
  该变量：它分离启动的 hub（`local-hub ensure`，或未加 `--no-spawn` 的
  `hub-shim`）实际执行 `toolregistry-server local-hub run --config <预设>`，
  由于服务器会加载 Python 源码，预设工具仍会提供，但 Hub 专属辅助功能
  （discovery 辅助工具、`toolcall_reason` 注入、管理面板）不会应用到该进程。
  这种情况下启动器会在 stderr 打印一条警告。
- `toolregistry-hub <command> --help` 显示翻译后命令的服务器选项；
  `toolregistry-hub --help` 列出 Hub 命令与标志。

## 全局选项

| 标志 | 描述 |
|------|------|
| `--version` / `-V` | 显示 Hub 版本（含更新检查）并退出 |
| `--no-banner` | 禁用启动横幅 |

## Hub 选项

| 标志 | 默认值 | 描述 |
|------|--------|------|
| `--admin-port PORT` | — | 在指定端口启用核心管理面板 |
| `--tool-discovery` / `--no-tool-discovery` | 启用 | 通过 `discover_tools` 渐进式工具披露 |
| `--think-augment` / `--no-think-augment` | 启用 | 向工具 schema 注入 `toolcall_reason` 属性 |

## 命令

### `openapi`

通过 gateway 启动 OpenAPI (REST) 服务器，只启用 OpenAPI 前端。默认使用
FastAPI 后端；`--backend httpserver` 选择零依赖后端。

```bash
toolregistry-hub openapi [OPTIONS]
```

| 选项 | 默认值 | 描述 |
|------|--------|------|
| `--host HOST` | `0.0.0.0` | 绑定地址 |
| `--port PORT` | `8000` | 绑定端口 |
| `--backend {fastapi,httpserver}` | `fastapi` | OpenAPI 服务器后端；`httpserver` 为零依赖后端 |
| `--env PATH` | `.env` | `.env` 文件路径 |
| `--no-env` | — | 跳过加载 `.env` |
| `--config PATH` | 解析后的预设 | 工具配置文件（JSON、JSONC 或 YAML） |
| `--tokens PATH` | — | Bearer 令牌文件（每行一个） |
| `--profile {remote,local}` | 无 | 部署 profile 过滤（见下方） |
| `--config-reload` / `--no-config-reload` | 关闭 | 配置文件变更时自动重载 |
| `--reload` | — | 开发环境自动重载 |

### `mcp`

启动 MCP (Model Context Protocol) 服务器。

`--transport stdio`（默认）由 MCP 服务器直接提供：gateway 没有 stdio 前端。
HTTP 传输（`streamable-http`、`http` 与 `sse`）通过 gateway 提供。

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
| `--config PATH` | 解析后的预设 | 工具配置文件（JSON、JSONC 或 YAML） |
| `--profile {remote,local}` | 无 | 部署 profile 过滤（见下方） |
| `--config-reload` / `--no-config-reload` | 关闭 | 配置文件变更时自动重载 |

### `gateway`

在单进程中同时提供 OpenAPI 与 MCP。这是服务器命令；完整选项见
`toolregistry-hub gateway --help`。

```bash
toolregistry-hub gateway [OPTIONS]
```

### `local-hub`

运行一个由本地客户端共享的常驻 gateway。仅支持 POSIX。

```bash
toolregistry-hub local-hub [run|ensure|stop|status] [OPTIONS]
```

| 选项 | 默认值 | 描述 |
|------|--------|------|
| `action` | `run` | `run` 前台服务；`ensure` 启动分离的 hub 并打印端点；`stop` 发送停止信号；`status` 报告状态 |
| `--name NAME` | `default` | Hub 名称 |
| `--idle-timeout SECONDS` | `0` | 无请求或打开的 MCP 会话超过该秒数后退出；`0` 表示常驻 |
| `--timeout SECONDS` | — | `ensure` 与 `stop` 的等待上限 |
| `--json` | — | 以 JSON 打印状态 |
| `--keys-db PATH` | — | 入站密钥库；以此方式启动的 hub 必须提供 |

启动器在运行服务器前设置 `TOOLREGISTRY_LOCAL_HUB_COMMAND=toolregistry-hub`，
读取该变量的服务器会通过 Hub 启动器以解析后的预设启动分离的 hub。
toolregistry-server 0.9.0 忽略该变量：此时分离的 hub 是
`toolregistry-server local-hub run --config <预设>`，它会提供预设工具（服务器
加载 Python 源码），但不应用 Hub 专属辅助功能（discovery 辅助工具、
`toolcall_reason` 注入、管理面板）。当启动器预期启动分离的 hub 而当前安装的
服务器不读取该变量时，它会在 stderr 打印警告。`run` 动作不受影响：它在启动器
进程内使用 Hub app 提供服务。

### `hub-shim`

把一个本地 hub 暴露给 stdio MCP 客户端。仅支持 POSIX。

```bash
toolregistry-hub hub-shim [OPTIONS]
```

| 选项 | 默认值 | 描述 |
|------|--------|------|
| `--name NAME` | `default` | 要连接的 hub |
| `--key-file PATH` | — | 保存客户端密钥的文件；回退到 `TOOLREGISTRY_HUB_KEY` |
| `--connect-timeout SECONDS` | `5` | 单次连接尝试上限 |
| `--no-spawn` | — | 从不启动 hub；不可用时报告为不可用 |
| `--config PATH` | 解析后的预设 | shim 需要启动 hub 时使用的配置 |
| `--socket PATH` | — | shim 启动的 hub 使用的 Unix socket |
| `--keys-db PATH` | — | shim 启动的 hub 必须使用的密钥库 |

### `keys`

管理入站 API 密钥（`create`、`list`、`get`、`revoke`、`set-concurrency`）。
`keys` 需要 `--db PATH`；`set-concurrency` 使用 `--value N` 或 `--clear`。
该命令原样透传给服务器。

```bash
toolregistry-hub keys <subcommand> [OPTIONS]
```

### 配置热重载

使用 `--config-reload` 时，服务器启动后台 watcher，轮询配置文件
（`--config`）并对运行中的注册表做 source 级 diff：新增 source 会被注册，
删除 source 会被注销，离开配置范围的 source 会被禁用，声明变化会被重新
注册。非法配置只记录日志并被忽略，当前注册表继续服务。默认元数据只应用于
本次 reload 注册的工具，已存在的工具保持管理面板修改后的值。reload 注册的
新 source 会重新套用 `--profile` 过滤，被排除的工具保持禁用。watcher 按
进程生效且默认关闭，多个服务之间不做协调。

已知限制：从文件中删除 `tool_metadata` 条目后，该项设置不会回滚，直到进程
重启。这些字段同样可由管理面板写入，reload 无法区分文件写入的值与之后的
面板编辑；如需恢复，请在面板中重置。

一个成功注册但未产出任何工具的 source，在声明不变时不会被再次拉取。如果
MCP 服务器后来才 advertise 工具，需要显式修改 source 声明（或重启进程）才能
注册。

## 部署 Profile

`--profile` 标志过滤注册的工具：

| Profile | 效果 |
|---------|------|
| `remote` | 禁用服务器本地文件系统/Shell/定时任务工具 |
| `local` | 仅保留本机工具；禁用网络工具 |
| *(无)* | 所有工具均注册（默认） |
