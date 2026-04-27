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

## 概览

- **自动模式**：`engine="auto"` 按优先级顺序尝试已配置的引擎，返回第一个成功的结果
- **指定引擎**：设置 `engine="brave"`（或其他引擎）进行确定性路由
- **降级模式**：设置 `fallback=True`，指定引擎失败时自动降级到自动链
- **动态 Schema**：`engine` 参数的可接受值在运行时收窄为仅包含已配置 API key 的引擎，LLM 客户端看到的 JSON schema 更精确
- **可配置优先级**：通过 `WEBSEARCH_PRIORITY` 环境变量覆盖默认引擎顺序

## 快速开始

```python
from toolregistry_hub.websearch import WebSearch

ws = WebSearch()

# 自动选择最佳已配置引擎
results = ws.search("Python 3.13 新特性", max_results=5)

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

### `WebSearch.search(query, *, engine, fallback, max_results, timeout, **kwargs)`

通过选定引擎执行网络搜索。

**参数：**

- `query` (str): 搜索查询字符串
- `engine` (str): 使用的引擎。`"auto"`（默认）按优先级尝试已配置引擎。可选值：`"brave"`、`"tavily"`、`"searxng"`、`"brightdata"`、`"scrapeless"`、`"serper"`
- `fallback` (bool): 指定引擎不可用或失败时，`False`（默认）抛出错误；`True` 降级到自动链
- `max_results` (int): 最大结果数（建议 1-20）。默认：5
- `timeout` (float): 单次请求超时秒数。默认：10.0
- `**kwargs`: 引擎特定参数，原样转发

**返回：** `list[SearchResult]`

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
