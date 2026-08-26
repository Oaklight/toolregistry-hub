---
description: RedditSearch 通过 Arctic Shift API 搜索 Reddit 帖子，该 API 是从 2005 年至今所有公开 Reddit 数据的免费存档。无需 API Key，开箱即用。
keywords: reddit, arctic shift, 搜索, subreddit, 帖子
---

# Reddit 搜索（Arctic Shift）

Reddit 搜索通过 [Arctic Shift API](https://arctic-shift.photon-reddit.com/api/docs) 提供 Reddit 帖子搜索功能，该 API 是从 2005 年至今所有公开 Reddit 数据的免费存档。

## 类概述

- `RedditSearch` - 提供 Reddit 帖子搜索功能的类

## 详细 API

### RedditSearch 类

`RedditSearch` 继承自 `BaseSearch`，提供 Reddit 帖子搜索功能。

#### 初始化参数

- `base_url: str | None = None` - Arctic Shift API 基础 URL，默认使用 `ARCTIC_SHIFT_URL` 环境变量，然后使用公共实例

#### 方法

- `search(query: str, max_results: int = 5, timeout: float = 10.0, **kwargs) -> list[SearchResult]`：执行搜索并返回结果
- `_search_impl(query: str, **kwargs) -> list[SearchResult]`：实现具体搜索逻辑
- `_parse_results(raw_results: dict) -> list[SearchResult]`：解析原始搜索结果

### Subreddit 范围限定

Arctic Shift API 要求关键词搜索必须指定 `subreddit` 或 `author` 参数——不支持全局全文搜索。引擎会自动从查询字符串中解析 subreddit 引用：

- `r/python web scraping` — 在 r/python 中搜索 "web scraping"
- `/r/python web scraping` — 同上
- `subreddit:python web scraping` — 显式限定语法

也可以通过关键字参数传递 `subreddit="python"`。

### 额外参数

以下 Arctic Shift API 参数可通过 `**kwargs` 传递：

| 参数 | 描述 |
|------|------|
| `subreddit` | Subreddit 名称（优先于查询解析的值） |
| `author` | 按帖子作者过滤 |
| `after` | 此日期之后的帖子（支持相对格式如 `7d`） |
| `before` | 此日期之前的帖子 |
| `sort` | 排序方向（`asc` 或 `desc`） |
| `over_18` | 过滤 NSFW 内容 |
| `spoiler` | 过滤剧透标记的帖子 |

## 免费使用

Arctic Shift 完全免费：

- **无需 API Key** — 开箱即用
- **无需 OAuth** — 不需要 Reddit 账号
- **无速率限制困扰** — 动态限制，每秒几个请求是安全的
- **完整存档** — 从 2005 年至今的所有公开 Reddit 数据

!!! note "数据时效性"
    36 小时内的内容，其分数和评论数可能不准确。

## 环境变量

| 变量 | 必需 | 描述 |
|------|------|------|
| `ARCTIC_SHIFT_URL` | 否 | 覆盖 Arctic Shift API 基础 URL（用于自托管实例） |

## 使用示例

### 基本用法

```python
from toolregistry_hub.websearch import RedditSearch

search = RedditSearch()

# 在查询中包含 subreddit
results = search.search("r/python web scraping", max_results=5)

for result in results:
    print(f"标题: {result.title}")
    print(f"URL: {result.url}")
    print(f"内容: {result.content}")
    print("-" * 50)
```

### 使用关键字参数

```python
from toolregistry_hub.websearch import RedditSearch

search = RedditSearch()

# 显式传递 subreddit
results = search.search("web scraping", subreddit="python", max_results=5)

# 按作者搜索
results = search.search("tutorial", author="spez")

# 按日期范围过滤
results = search.search("r/python async", after="30d", before="1d")
```

### 通过统一搜索

```python
from toolregistry_hub.websearch import WebSearch

ws = WebSearch()
results = ws.search("r/python web scraping", engine="reddit", count=5)
```
