---
title: 定时任务工具
summary: 基于 cron 表达式的定时提示执行
description: CronTool 为 Agent 工作流提供基于 cron 的任务调度，支持循环和一次性调度、持久化存储以及 7 天自动过期。
keywords: cron, 调度器, 定时任务, 循环任务, 一次性任务, agent, 自动化
author: Oaklight
---

# 定时任务工具

定时任务工具为 Agent 驱动的工作流提供基于 cron 的提示调度。任务触发时通过 Agent 运行时注入的回调函数发送提示，实现无需人工干预的定时触发操作。

???+ note "更新日志"
    0.8.0 首次发布，支持 cron 调度、持久化存储和 7 天 TTL

## 概览

CronTool 类提供以下功能：

- **Cron 调度**：标准 5 字段 cron 表达式（分 时 日 月 周）
- **循环任务**：在每次 cron 匹配时触发，直到被删除或自动过期
- **一次性任务**：在下次匹配时触发一次后自动删除
- **持久化存储**：可选将任务持久化到 JSON 文件，进程重启后恢复
- **7 天 TTL**：循环任务在 7 天后自动过期，防止资源无限积累
- **后台执行**：调度器在守护线程中运行，不阻塞主线程

## 快速开始

```python
from toolregistry_hub.cron_tool import CronTool

# 创建调度器（通常由 Agent 运行时提供 on_trigger）
cron = CronTool(on_trigger=lambda prompt: print(f"触发: {prompt}"))

# 调度循环任务 — 每 5 分钟
job = cron.create("*/5 * * * *", "检查部署状态")
print(job)
# {'job_id': 'a1b2c3d4', 'cron': '*/5 * * * *', 'recurring': True,
#  'durable': False, 'next_fire_time': '2026-04-28T10:05:00'}

# 调度一次性提醒
cron.create("30 14 28 4 *", "5 分钟后团队站会", recurring=False)

# 列出所有任务
print(cron.list())

# 取消任务
cron.delete(job["job_id"])
```

## API 参考

### `CronTool(on_trigger, jobs_file)`

初始化调度器。

**参数：**

- `on_trigger` (Callable[[str], None], 可选): 任务触发时调用的回调函数，接收提示字符串。若为 `None`，触发的提示将被静默丢弃。
- `jobs_file` (str | Path, 可选): 用于持久化任务的 JSON 文件路径。若为 `None`，不支持持久化任务。

### `CronTool.create(cron, prompt, recurring, durable)`

调度一个按 cron 计划触发的提示。

**参数：**

- `cron` (str): 标准 5 字段 cron 表达式（如 `"*/5 * * * *"`、`"0 9 * * 1-5"`）
- `prompt` (str): 任务触发时传递的提示字符串
- `recurring` (bool): `True`（默认）表示每次匹配时触发；`False` 表示触发一次后自动删除
- `durable` (bool): `True` 表示将任务持久化到磁盘，进程重启后恢复。需要设置 `jobs_file`

**返回：** 包含 `job_id`、`cron`、`recurring`、`durable` 和 `next_fire_time` 的字典

**异常：**

- `InvalidCronExpression`: cron 表达式无法解析时抛出
- `ValueError`: `durable=True` 但未配置 `jobs_file` 时抛出

### `CronTool.delete(job_id)`

取消已调度的任务。

**参数：**

- `job_id` (str): `create()` 返回的任务 ID

**返回：** 描述已删除任务的字典

**异常：** 任务 ID 未找到时抛出 `ValueError`

### `CronTool.list()`

以文本表格格式列出所有已调度的任务。

**返回：** 包含任务详情（ID、cron 表达式、循环、持久化、下次触发时间、提示预览）的格式化字符串。若为空则返回 `"No scheduled jobs."`。

### `CronTool.shutdown()`

停止调度器并清理资源。

## Cron 表达式格式

标准 5 字段格式：`分 时 日 月 周`

| 字段 | 取值范围 | 特殊字符 |
|------|---------|----------|
| 分钟 | 0-59 | `*` `,` `-` `/` |
| 小时 | 0-23 | `*` `,` `-` `/` |
| 日 | 1-31 | `*` `,` `-` `/` |
| 月 | 1-12 | `*` `,` `-` `/` |
| 周 | 0-6（0=周日）| `*` `,` `-` `/` |

**示例：**

| 表达式 | 说明 |
|--------|------|
| `*/5 * * * *` | 每 5 分钟 |
| `0 9 * * 1-5` | 工作日 9:00 |
| `30 14 * * *` | 每天 14:30 |
| `0 0 1 * *` | 每月 1 日 0:00 |
| `15 10 28 4 *` | 4 月 28 日 10:15（一次性） |

## 持久化

默认情况下，任务仅在当前会话中有效——进程退出后丢失。设置 `durable=True` 可将任务持久化到 JSON 文件：

```python
cron = CronTool(
    on_trigger=my_callback,
    jobs_file=".claude/scheduled_tasks.json",
)

# 此任务在重启后恢复
cron.create("0 9 * * *", "每日状态报告", durable=True)
```

下次启动时，持久化任务自动重新加载。过期任务（超过 7 天）在加载时被清除。

## TTL 自动过期

循环任务在创建后 **7 天**自动过期。任务过期时：

1. 最后一次触发
2. 从调度器中移除
3. 如果是持久化任务，从持久化文件中移除

这防止了长时间运行的会话中资源无限积累。一次性任务不受 TTL 限制——它们在触发后自行删除。

## 与 Agent 运行时集成

`on_trigger` 回调是与 Agent 运行时的集成点。运行时提供此回调来处理触发的提示：

```python
def handle_prompt(prompt: str) -> None:
    """将提示加入队列供 Agent 处理。"""
    agent.enqueue(prompt)

cron = CronTool(on_trigger=handle_prompt)
```

未提供 `on_trigger` 时，触发的提示将被静默丢弃。这在测试场景或仅使用调度器进行计时而无需提示传递时很有用。
