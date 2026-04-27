---
title: Cron Tool
summary: Scheduled prompt execution with cron expressions
description: CronTool provides cron-based task scheduling for agent workflows, supporting recurring and one-shot schedules, durable persistence, and automatic 7-day TTL expiry.
keywords: cron, scheduler, scheduled tasks, recurring jobs, one-shot, agent, automation
author: Oaklight
---

# Cron Tool

The Cron Tool provides cron-based prompt scheduling for agent-driven workflows. Jobs fire prompts via a callback injected by the agent runtime, enabling time-triggered actions without manual intervention.

???+ note "Changelog"
    0.8.0 Initial release with cron scheduling, durable persistence, and 7-day TTL

## Overview

The CronTool class provides:

- **Cron Scheduling**: Standard 5-field cron expressions (minute hour day-of-month month day-of-week)
- **Recurring Jobs**: Fire on every cron match until deleted or auto-expired
- **One-Shot Jobs**: Fire once at the next match, then auto-delete
- **Durable Persistence**: Optionally persist jobs to a JSON file so they survive process restarts
- **7-Day TTL**: Recurring jobs auto-expire after 7 days to bound session lifetime
- **Background Execution**: Scheduler runs in a daemon thread, non-blocking

## Quick Start

```python
from toolregistry_hub.cron_tool import CronTool

# Create a scheduler (typically the agent runtime provides on_trigger)
cron = CronTool(on_trigger=lambda prompt: print(f"Fired: {prompt}"))

# Schedule a recurring job — every 5 minutes
job = cron.create("*/5 * * * *", "Check deployment status")
print(job)
# {'job_id': 'a1b2c3d4', 'cron': '*/5 * * * *', 'recurring': True,
#  'durable': False, 'next_fire_time': '2026-04-28T10:05:00'}

# Schedule a one-shot reminder
cron.create("30 14 28 4 *", "Team standup in 5 minutes", recurring=False)

# List all jobs
print(cron.list())

# Cancel a job
cron.delete(job["job_id"])
```

## API Reference

### `CronTool(on_trigger, jobs_file)`

Initialize the scheduler.

**Parameters:**

- `on_trigger` (Callable[[str], None], optional): Callback invoked when a job fires. Receives the prompt string. If `None`, fired prompts are silently discarded.
- `jobs_file` (str | Path, optional): Path to a JSON file for durable job persistence. If `None`, durable jobs are not supported.

### `CronTool.create(cron, prompt, recurring, durable)`

Schedule a prompt to fire on a cron schedule.

**Parameters:**

- `cron` (str): Standard 5-field cron expression (e.g., `"*/5 * * * *"`, `"0 9 * * 1-5"`)
- `prompt` (str): The prompt string to deliver when the job fires
- `recurring` (bool): If `True` (default), fire on every cron match. If `False`, fire once then auto-delete
- `durable` (bool): If `True`, persist the job to disk so it survives restarts. Requires `jobs_file` to be set

**Returns:** Dict with `job_id`, `cron`, `recurring`, `durable`, and `next_fire_time`

**Raises:**

- `InvalidCronExpression`: If the cron expression cannot be parsed
- `ValueError`: If `durable=True` but no `jobs_file` was configured

### `CronTool.delete(job_id)`

Cancel a scheduled job.

**Parameters:**

- `job_id` (str): The ID returned by `create()`

**Returns:** Dict summarizing the deleted job

**Raises:** `ValueError` if the job ID is not found

### `CronTool.list()`

List all scheduled jobs in a text-formatted table.

**Returns:** A formatted string with job details (ID, cron expression, recurring, durable, next fire time, prompt preview). Returns `"No scheduled jobs."` if empty.

### `CronTool.shutdown()`

Stop the scheduler and clean up resources.

## Cron Expression Format

Standard 5-field format: `minute hour day-of-month month day-of-week`

| Field | Values | Special Characters |
|-------|--------|-------------------|
| Minute | 0-59 | `*` `,` `-` `/` |
| Hour | 0-23 | `*` `,` `-` `/` |
| Day of Month | 1-31 | `*` `,` `-` `/` |
| Month | 1-12 | `*` `,` `-` `/` |
| Day of Week | 0-6 (0=Sunday) | `*` `,` `-` `/` |

**Examples:**

| Expression | Description |
|-----------|-------------|
| `*/5 * * * *` | Every 5 minutes |
| `0 9 * * 1-5` | Weekdays at 9:00 AM |
| `30 14 * * *` | Every day at 2:30 PM |
| `0 0 1 * *` | First day of each month at midnight |
| `15 10 28 4 *` | April 28 at 10:15 AM (one-shot) |

## Durability

By default, jobs are session-only — they are lost when the process exits. Set `durable=True` to persist jobs to a JSON file:

```python
cron = CronTool(
    on_trigger=my_callback,
    jobs_file=".claude/scheduled_tasks.json",
)

# This job survives restarts
cron.create("0 9 * * *", "Daily status report", durable=True)
```

On next startup, durable jobs are automatically reloaded. Expired jobs (older than 7 days) are pruned during reload.

## TTL Auto-Expiry

Recurring jobs automatically expire after **7 days** from creation. When a job expires:

1. It fires one final time
2. It is removed from the scheduler
3. If durable, it is removed from the persistence file

This prevents unbounded resource accumulation in long-running sessions. One-shot jobs are not subject to TTL — they self-delete after firing.

## Integration with Agent Runtimes

The `on_trigger` callback is the integration point with agent runtimes. The runtime provides this callback to handle fired prompts:

```python
def handle_prompt(prompt: str) -> None:
    """Enqueue the prompt for the agent to process."""
    agent.enqueue(prompt)

cron = CronTool(on_trigger=handle_prompt)
```

When no `on_trigger` is provided, fired prompts are silently discarded. This is useful for testing or when the scheduler is used purely for timing without prompt delivery.
