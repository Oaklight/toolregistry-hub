---
title: Admin 面板
summary: 以独立服务运行 ToolRegistry admin 面板与 Kanban 标签页
description: toolregistry-hub admin 在自己的进程中提供核心 admin 面板，并挂载 Kanban 扩展。它与 MCP 守护进程共享同一个 SQLite 文件，工具与人都看到同一块看板。
keywords: admin 面板, 看板, 独立服务, systemd, token, board
author: Oaklight
---

# Admin 面板

`toolregistry-hub admin` 在独立进程中提供 ToolRegistry admin 面板。MCP 服务与面板互不影响：重启其中一个不会中断另一个，会话重连时面板仍然在线。

面板总是挂载 **Kanban** 标签页，数据来自 `board-*` MCP 工具写入的同一个 SQLite 文件。

## 命令

```bash
toolregistry-hub admin \
  --host 127.0.0.1 \
  --port 8081 \
  --config ~/.config/toolregistry-hub/tools-local.jsonc \
  --db ~/.local/state/toolregistry-hub/board.sqlite3 \
  --token-file ~/.config/toolregistry-hub/admin-token
```

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--host` | `127.0.0.1` | 监听地址 |
| `--port` | `8081` | 监听端口；端口被占用时面板会另选端口并打印实际 URL |
| `--token` | — | 面板 Bearer token |
| `--token-file` | — | 从第一个非空行读取 token |
| `--config` | 自动发现 | 面板工具页加载的配置 |
| `--db` | 共享默认路径 | 看板数据库路径 |
| `--no-banner` | 关闭 | 不打印 Hub banner |

规则：

- `--token` 与 `--token-file` 互斥。
- 非 loopback 的 `--host` 且没有 token 会被拒绝：面板暴露的是可写看板。

token 只生成一次，权限 `0600`：

```bash
install -m 600 /dev/null ~/.config/toolregistry-hub/admin-token
python -c 'import secrets; print(secrets.token_hex(24))' \
  > ~/.config/toolregistry-hub/admin-token
```

面板的 HTML 外壳与静态资源不需要 token；所有 `/api/*` 与 `/ext/board/*` 调用都需要。浏览器只询问一次，之后使用会话 cookie。

## systemd 用户单元

```ini
[Unit]
Description=ToolRegistry Hub kanban admin panel (127.0.0.1:8081)
After=network.target toolregistry-hub-mcp.service
Wants=toolregistry-hub-mcp.service

[Service]
Type=simple
WorkingDirectory=/home/pding
UMask=0077
Environment=TOOLREGISTRY_HUB_BOARD_DB=/home/pding/.local/state/toolregistry-hub/board.sqlite3
ExecStartPre=/usr/bin/install -d -m 700 /home/pding/.local/state/toolregistry-hub
ExecStart=/path/to/toolregistry-hub admin --host 127.0.0.1 --port 8081 \
    --config /home/pding/.config/toolregistry-hub/tools-local.jsonc \
    --db /home/pding/.local/state/toolregistry-hub/board.sqlite3 \
    --token-file /home/pding/.config/toolregistry-hub/admin-token
Restart=always
RestartSec=3

[Install]
WantedBy=default.target
```

```bash
systemctl --user daemon-reload
systemctl --user enable --now toolregistry-hub-admin
journalctl --user -u toolregistry-hub-admin -n 30 --no-pager
```

把同一个 `TOOLREGISTRY_HUB_BOARD_DB` 也加到 MCP 单元。两个进程解析到不同路径时，会出现两块互不相通的看板，且没有任何报错。

## Kanban 标签页

一次显示一个项目：

- 项目下拉、**新建项目**、**刷新**；
- 五个列始终存在，即使为空；
- 卡片显示 id、标题、内容、优先级、截止日、负责人、标签和链接；
- 卡片上的状态下拉用于在列之间移动；
- **编辑**打开内联表单，可改全部可编辑字段；
- **删除**在确认后软删除条目；
- 每列底部有 **新建条目** 表单，状态预填为该列。

本版本不支持拖拽。条目表已预留 `position` 列。

## API

标签页调用 `/ext/board` 下的这些路由：

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| GET | `/projects` | 项目及各列计数 |
| POST | `/projects` | 新建项目 |
| PATCH | `/projects/<key>` | 重命名 |
| DELETE | `/projects/<key>?force=1` | 归档，`force` 时删除 |
| GET | `/board?project=KAN` | 固定五列及条目 |
| GET | `/entries?project=&status=&include_deleted=` | 过滤条目 |
| POST | `/entries` | 新建条目 |
| GET | `/entries/<ref>` | 单条目 |
| PATCH | `/entries/<ref>` | 更新可编辑字段 |
| DELETE | `/entries/<ref>` | 软删除 |
| GET | `/meta` | schema 版本；loopback 时附数据库路径 |

两个写入路由都会拒绝未知字段，因此 `created_at`、`updated_at`、`closed_at`、`deleted_at` 会报错而不是被静默丢弃。

`PATCH` 的字段语义统一：省略该键或传 `null` 表示不修改，传空字符串或空数组表示清空，`title` 不允许清空。`status` 与其他字段一起校验，因此带非法状态的请求不会写入任何字段。存储层失败时返回 503，并使用面板的 JSON 错误结构。

## 另见

- [看板工具](../tools/board.md)
- [服务指南](../server.md)
