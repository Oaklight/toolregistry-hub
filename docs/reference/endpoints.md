---
title: API Endpoints
summary: Complete list of OpenAPI server endpoints
description: Every REST endpoint exposed by the toolregistry-hub OpenAPI server, grouped by tool namespace.
keywords: api, endpoints, rest, openapi, routes
author: Oaklight
---

# API Endpoints

When running in OpenAPI mode, the server exposes the following endpoints. Interactive documentation is available at `/docs` after startup.

## Calculator

| Method | Path | Description |
|--------|------|-------------|
| POST | `/tools/calculator/evaluate` | Evaluate a math expression |
| POST | `/tools/calculator/list_allowed_fns` | List allowed calculator functions |
| POST | `/tools/calculator/help` | Help for a specific function |

## Unit Converter

| Method | Path | Description |
|--------|------|-------------|
| POST | `/tools/unit_converter/convert` | Perform unit conversion |
| POST | `/tools/unit_converter/list_conversions` | List available conversions |
| POST | `/tools/unit_converter/help` | Conversion help info |

## Date & Time

| Method | Path | Description |
|--------|------|-------------|
| POST | `/tools/datetime/now` | Get current time |
| POST | `/tools/datetime/convert_timezone` | Convert between timezones |

## File Operations

| Method | Path | Description |
|--------|------|-------------|
| POST | `/tools/file_ops/edit` | Replace exact string in file (returns unified diff) |
| POST | `/tools/file_ops/read_file` | Read file content |
| POST | `/tools/file_ops/write_file` | Write content to file |
| POST | `/tools/file_ops/append_file` | Append content to file |
| POST | `/tools/file_ops/search_files` | Search for files matching a pattern |
| POST | `/tools/file_ops/make_diff` | Generate a diff between contents |
| POST | `/tools/file_ops/make_git_conflict` | Generate git conflict markers |

## File Reader

| Method | Path | Description |
|--------|------|-------------|
| POST | `/tools/reader/read` | Read text file with line numbers and pagination |
| POST | `/tools/reader/read_pdf` | Read PDF and extract text |
| POST | `/tools/reader/read_notebook` | Read Jupyter notebook cells and outputs |

## File Search

| Method | Path | Description |
|--------|------|-------------|
| POST | `/tools/fs/file_search/glob` | Find files matching a glob pattern |
| POST | `/tools/fs/file_search/grep` | Search file contents using regex |
| POST | `/tools/fs/file_search/tree` | Display directory tree structure |

## Path Info

| Method | Path | Description |
|--------|------|-------------|
| POST | `/tools/fs/path_info/info` | Get file/directory metadata |

## Web Fetch

| Method | Path | Description |
|--------|------|-------------|
| POST | `/tools/web/fetch/fetch_content` | Extract readable content from a URL |

## Web Search

| Method | Path | Description |
|--------|------|-------------|
| POST | `/tools/web/websearch/search` | Unified search (auto-selects engine) |
| POST | `/tools/web/websearch/list_engines` | List available engines and their status |
| POST | `/tools/web/brave_search/search` | Brave Search *(deferred)* |
| POST | `/tools/web/tavily_search/search` | Tavily Search *(deferred)* |
| POST | `/tools/web/searxng_search/search` | SearXNG Search *(deferred)* |
| POST | `/tools/web/scrapeless_search/search` | Scrapeless Search *(deferred)* |
| POST | `/tools/web/brightdata_search/search` | BrightData Search *(deferred)* |
| POST | `/tools/web/serper_search/search` | Serper Search *(deferred)* |

!!! note "Deferred Tools"
    Endpoints marked *(deferred)* are registered but hidden by default when tool discovery is enabled. They become visible through the `discover_tools` tool or when tool discovery is disabled.

## Bash

| Method | Path | Description |
|--------|------|-------------|
| POST | `/tools/bash/execute` | Execute a shell command (with safety validation) |

## Cron

| Method | Path | Description |
|--------|------|-------------|
| POST | `/tools/cron/create` | Schedule a recurring or one-shot prompt *(deferred)* |
| POST | `/tools/cron/list` | List scheduled jobs *(deferred)* |
| POST | `/tools/cron/delete` | Cancel a scheduled job *(deferred)* |

## Think Tool

| Method | Path | Description |
|--------|------|-------------|
| POST | `/tools/think/think` | Structured reasoning / brainstorming |

## Todo List

| Method | Path | Description |
|--------|------|-------------|
| POST | `/tools/todolist/update` | Update or create todo list |
