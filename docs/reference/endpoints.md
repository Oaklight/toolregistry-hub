---
title: API 端点
summary: OpenAPI 服务器完整端点列表
description: toolregistry-hub OpenAPI 服务器暴露的所有 REST 端点，按工具命名空间分组。
keywords: api, endpoints, rest, openapi, routes
author: Oaklight
---

# API 端点

在 OpenAPI 模式下运行时，服务器暴露以下端点。启动后可在 `/docs` 访问交互式文档。

## 计算器

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/tools/calculator/evaluate` | 计算数学表达式 |
| POST | `/tools/calculator/list_allowed_fns` | 列出允许的计算器函数 |
| POST | `/tools/calculator/help` | 获取特定函数的帮助 |

## 单位转换

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/tools/unit_converter/convert` | 执行单位转换 |
| POST | `/tools/unit_converter/list_conversions` | 列出可用转换 |
| POST | `/tools/unit_converter/help` | 转换帮助信息 |

## 日期时间

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/tools/datetime/now` | 获取当前时间 |
| POST | `/tools/datetime/convert_timezone` | 时区转换 |

## 文件操作

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/tools/file_ops/edit` | 精确字符串替换（返回 unified diff） |
| POST | `/tools/file_ops/read_file` | 读取文件内容 |
| POST | `/tools/file_ops/write_file` | 写入文件内容 |
| POST | `/tools/file_ops/append_file` | 追加文件内容 |
| POST | `/tools/file_ops/search_files` | 搜索匹配模式的文件 |
| POST | `/tools/file_ops/make_diff` | 生成内容差异 |
| POST | `/tools/file_ops/make_git_conflict` | 生成 git 冲突标记 |

## 文件读取

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/tools/reader/read` | 读取文本文件（带行号和分页） |
| POST | `/tools/reader/read_pdf` | 读取 PDF 并提取文本 |
| POST | `/tools/reader/read_notebook` | 读取 Jupyter Notebook 单元格和输出 |

## 文件搜索

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/tools/fs/file_search/glob` | 按 glob 模式查找文件 |
| POST | `/tools/fs/file_search/grep` | 使用正则表达式搜索文件内容 |
| POST | `/tools/fs/file_search/tree` | 显示目录树结构 |

## 路径信息

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/tools/fs/path_info/info` | 获取文件/目录元数据 |

## 网页抓取

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/tools/web/fetch/fetch_content` | 从 URL 提取可读内容 |

## 网络搜索

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/tools/web/websearch/search` | 统一搜索（自动选择引擎） |
| POST | `/tools/web/websearch/list_engines` | 列出可用引擎及其状态 |
| POST | `/tools/web/brave_search/search` | Brave 搜索 *（延迟加载）* |
| POST | `/tools/web/tavily_search/search` | Tavily 搜索 *（延迟加载）* |
| POST | `/tools/web/searxng_search/search` | SearXNG 搜索 *（延迟加载）* |
| POST | `/tools/web/scrapeless_search/search` | Scrapeless 搜索 *（延迟加载）* |
| POST | `/tools/web/brightdata_search/search` | BrightData 搜索 *（延迟加载）* |
| POST | `/tools/web/serper_search/search` | Serper 搜索 *（延迟加载）* |

!!! note "延迟加载工具"
    标记为 *（延迟加载）* 的端点已注册但默认隐藏。可通过 `discover_tools` 工具发现，或在禁用工具发现功能时可见。

## Bash

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/tools/bash/execute` | 执行 Shell 命令（带安全验证） |

## 定时任务

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/tools/cron/create` | 创建定时或一次性任务 *（延迟加载）* |
| POST | `/tools/cron/list` | 列出定时任务 *（延迟加载）* |
| POST | `/tools/cron/delete` | 取消定时任务 *（延迟加载）* |

## 思考工具

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/tools/think/think` | 结构化推理/头脑风暴 |

## 待办事项

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/tools/todolist/update` | 更新或创建待办事项列表 |
