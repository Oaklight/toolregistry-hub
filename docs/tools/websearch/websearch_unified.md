---
title: 统一网络搜索
summary: 所有搜索引擎的统一入口，支持自动选择和降级
description: WebSearch 将所有可用的搜索引擎封装在单一的 search() 方法后，支持引擎选择器、自动优先级链，以及面向 LLM 客户端的动态注解收窄。
keywords: 网络搜索, 统一搜索, 自动选择, 引擎选择器, 降级, 多引擎
author: Oaklight
---

# 统一网络搜索

`WebSearch` 类提供了统一的入口，将查询分发到任何已配置的搜索引擎。你可以让它自动选择最佳可用引擎，也可以指定特定引擎并启用优雅降级。

???+ note "更新日志"
    未发布 — 新增统一 WebSearch 入口 ([#88](https://github.com/Oaklight/toolregistry-hub/pull/88))  
    未发布 — 并行多引擎搜索 + BM25 去重 ([#142](https://github.com/Oaklight/toolregistry-hub/pull/142))  
    未发布 — 去重时 URL 归一化 ([#143](https://github.com/Oaklight/toolregistry-hub/pull/143))

## 概览

- **自动模式**：`engine="auto"` 按优先级顺序尝试已配置的引擎，返回第一个成功的结果
- **并行模式**：`engine="parallel"` 并发查询多个引擎，按 URL 去重并使用 BM25 重新排序，获取更高质量的结果
- **指定引擎**：设置 `engine="brave"`（或其他引擎）进行确定性路由
- **降级模式**：设置 `fallback=True`，指定引擎失败时自动降级到自动链
- **动态 Schema**：`engine` 参数的可接受值在运行时收窄为仅包含已配置 API key 的引擎，LLM 客户端看到的 JSON schema 更精确
- **可配置优先级**：通过 `WEBSEARCH_PRIORITY` 环境变量覆盖默认引擎顺序

## 快速开始

```python
from toolregistry_hub.websearch import WebSearch

ws = WebSearch()

# 自动选择最佳已配置引擎
results = ws.search("Python 3.13 新特性", count=5)

# 并行模式：查询多个引擎，去重并重新排序
results = ws.search("机器学习", engine="parallel", count=10)

# 使用指定引擎
results = ws.search("机器学习", engine="tavily")

# 指定引擎 + 降级到自动链
results = ws.search("量子计算", engine="brave", fallback=True)

# 查看哪些引擎可用
print(ws.list_engines())
# {'brave': True, 'tavily': True, 'searxng': False, ...}
```

## API 参考

### `WebSearch(priority)`

初始化统一搜索封装。

**参数：**

- `priority` (str, 可选): 逗号分隔的引擎名称优先级顺序。回退到 `WEBSEARCH_PRIORITY` 环境变量，再回退到默认顺序。

### `WebSearch.search(query, *, count, engine, fallback, timeout)`

通过选定引擎执行网络搜索。

**参数：**

- `query` (str): 搜索查询字符串
- `count` (int): 返回结果数量（默认 5，最大 20）
- `engine` (str): 使用的引擎。`"auto"`（默认）按优先级尝试已配置引擎。`"parallel"` 并发查询多个引擎并使用 BM25 重新排序。可选值：`"brave"`、`"tavily"`、`"searxng"`、`"brightdata"`、`"scrapeless"`、`"serper"`
- `fallback` (bool): 指定引擎失败时，`True` 自动尝试下一个可用引擎，`False`（默认）抛出错误
- `timeout` (float): 单次请求超时秒数。默认：10.0

**返回：** `list[SearchResult]` — 每个结果包含 `title`、`url`、`content` 和 `score`

**异常：**

- `ValueError`: 未知引擎名称或空查询
- `RuntimeError`: 无可用引擎（自动模式），或指定引擎不可用且 `fallback=False`

### `WebSearch.list_engines()`

列出所有已知引擎及其配置状态。

**返回：** `dict[str, bool]` — 引擎名称到配置状态的映射

## 引擎优先级

默认优先级顺序（付费/高质量优先）：

1. `tavily`
2. `brave`
3. `serper`
4. `brightdata`
5. `scrapeless`
6. `searxng`

通过环境变量覆盖：

```bash
export WEBSEARCH_PRIORITY="searxng,brave,tavily"
```

或在构造时指定：

```python
ws = WebSearch(priority="searxng,brave")
```

## 自动模式行为

当 `engine="auto"` 时：

1. 按优先级顺序尝试引擎
2. 跳过未配置的引擎（缺少 API key）
3. 如果引擎返回空结果，尝试下一个
4. 如果引擎抛出异常，尝试下一个
5. 如果所有引擎都失败，抛出 `RuntimeError` 并附带最后一个错误

## 并行模式

当 `engine="parallel"` 时：

1. 通过 `ThreadPoolExecutor` 并发查询 `WEBSEARCH_PARALLEL_ENGINES` 中列出的所有引擎
2. 未配置的引擎自动跳过；单个引擎失败会记录日志但不会终止搜索
3. 结果按归一化后的 URL 去重（去除 `www.` 前缀、末尾斜杠、跟踪参数如 `utm_*`、`fbclid`、`gclid`）
4. 重复 URL 保留内容最长的结果
5. 剩余结果使用 BM25 对原始查询评分并降序排列
6. 如果所有并行引擎返回空结果或失败，自动回退到 auto 模式

配置并行查询的引擎：

```bash
# 默认：brightdata,brave
export WEBSEARCH_PARALLEL_ENGINES="brightdata,brave,tavily"
```

## 降级行为

指定引擎并设置 `fallback=True` 时：

```python
# 如果 brave 不可用，自动尝试其他引擎
results = ws.search("query", engine="brave", fallback=True)
```

失败的引擎会从降级自动链中排除，避免重复尝试。

## 动态注解收窄

构造时，`WebSearch` 探测哪些引擎已配置，并动态收窄 `engine` 参数的类型注解。这意味着：

- **IDE 自动补全**显示完整菜单（所有引擎）
- **LLM JSON schema**（运行时生成）仅显示已配置的引擎
- **不同实例**可以有不同的可用引擎

```python
# 服务器设置了 BRAVE_API_KEY 和 TAVILY_API_KEY
ws = WebSearch()
# LLM 客户端看到: engine: Literal["auto", "brave", "tavily"]
# 而非完整的 7 引擎菜单
```

## 服务端模式

在服务端模式下，`WebSearch` 注册在 `web/websearch` 命名空间。6 个独立引擎工具标记为 deferred —— 可通过 `discover_tools` 发现，但不包含在初始 schema 中。这减少了 schema 大小，同时保持所有引擎可访问。

```
POST /tools/web/websearch/search
POST /tools/web/websearch/list_engines
```
