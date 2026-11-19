---
title: 看板工具
summary: 按项目持久化的看板，用于 agent 任务追踪
description: board 工具把项目和条目保存在本地 SQLite 文件中，多个会话共享一块看板，而不是互相覆盖同一份内存 todo 列表。条目带状态、优先级、截止日、标签、负责人和链接，同一份文件同时支撑 admin 面板的 Kanban 标签页。
keywords: 看板, kanban, 项目, 任务追踪, todo 替代, sqlite, admin 面板
author: Oaklight
---

# 看板工具

`board` 命名空间替代了原先无状态的 `todolist-update` 工具。每个项目有自己的条目，所有改动都写入本地 SQLite 文件。MCP 守护进程和 admin 面板打开同一份文件，因此会话里创建的条目可以直接在浏览器里看到。

???+ note "变更记录"
    未发布：替代 `todolist-update`；新增项目、条目、状态、优先级、截止日、标签、负责人、链接，以及 admin 的 Kanban 标签页。

## 为什么替换 todo 工具

`todolist-update` 每次调用都要传完整列表，只返回一句确认，不保存任何内容。两个会话会互相覆盖，模型也无法只改一条。看板工具一次只改一个条目，并保留历史。

## 数据模型

- **项目**由 key（`KAN`）、名称和每项目自增序号组成。
- **条目**属于一个项目，id 为 `<KEY>-<n>`，例如 `KAN-12`。序号永不复用：删除 `KAN-7` 会留下永久空位，过期引用不会指向别的条目。
- 状态即看板的五列，按顺序为：`backlog`、`todo`、`in_progress`、`done`、`cancelled`。
- 条目是**软删除**：保留 id 和时间戳，默认不出现在列表和看板中，除非传入 `include_deleted`。
- 项目默认**归档**；传 `force` 会删除项目及其条目。

### 状态别名

输入别名会先归一化再存储，数据库中永远是规范值。

| 别名 | 存储值 |
| --- | --- |
| `planned` | `todo` |
| `pending`、`in-progress`、`inprogress`、`doing`、`active` | `in_progress` |
| `complete`、`completed`、`closed` | `done` |
| `canceled` | `cancelled` |

优先级接受 `urgent`、`high`、`medium`、`low`，以及别名 `p0`（urgent）、`p1`（high）、`p2`（medium）、`p3`（low）。

### 时间戳

`created_at`、`updated_at`、`closed_at`、`deleted_at` 全部由服务端按 UTC 生成。没有任何工具接受时间戳参数，调用方无法伪造审计历史。`due` 是计划日期（`YYYY-MM-DD`），也是唯一由调用方选择的日期。

## 工具

所有工具都是延迟工具：用 `discover_tools` 发现，用 `call_deferred` 调用。

| 工具 | 用途 |
| --- | --- |
| `board-create_project` | 新建项目（`name`，可选 `key`） |
| `board-list_projects` | 列出项目及各列计数 |
| `board-archive_project` | 归档项目，或传 `force` 删除 |
| `board-create_entry` | 新建条目，支持全部可选字段 |
| `board-get_entry` | 按 id 读取条目 |
| `board-update_entry` | 更新标题、内容、优先级、截止日、标签、负责人、链接 |
| `board-update_status` | 在列之间移动条目 |
| `board-delete_entry` | 软删除条目 |
| `board-list_entries` | 按项目和状态过滤列表 |
| `board-view` | 以 markdown 分列渲染看板 |

`project` 接受 key 或精确名称；`ref` 接受任意大小写的 `KAN-12`。

## 快速示例

```python
from toolregistry_hub import BoardTools

board = BoardTools()  # 共享默认数据库
board.create_project("Kanban Board", key="KAN")
board.create_entry(
    "KAN",
    "渲染看板界面",
    content="五个列和条目表单。",
    status="planned",
    priority="p1",
    due="2026-12-01",
    labels=["ui"],
    assignee="pding",
    links=["https://github.com/Oaklight/toolregistry-hub/pull/1"],
)
board.update_status("KAN-1", "pending")
board.update_entry("KAN-1", content="第一版已合并。")
print(board.view("KAN"))
```

## 存储

单个 SQLite 文件，WAL 模式，权限 `0600`；父目录以 `0700` 创建。路径解析顺序：

1. 显式路径（工具配置中的 `kwargs: {"db": ...}`，或 admin 命令的 `--db`），
2. `TOOLREGISTRY_HUB_BOARD_DB`，
3. `$XDG_STATE_HOME/toolregistry-hub/board.sqlite3`，
4. `~/.local/state/toolregistry-hub/board.sqlite3`。

MCP 守护进程与 admin 进程必须解析到同一文件。请在两个 systemd unit 中都设置该环境变量，避免漂移。

## 并发访问

每次操作单独开连接；WAL 允许工具与 admin 面板同时读写，`busy_timeout` 让写操作等待而不是直接失败。不要把数据库切成 `journal_mode=DELETE`。

## 相关

- [Admin 面板](../guides/admin_panel.md) 中的 Kanban 标签页。
- [Cron 工具](cron_tool.md) 用于定时提示。
