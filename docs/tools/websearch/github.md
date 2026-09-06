---
description: GitHubSearch 通过 GitHub REST 搜索 API 搜索 GitHub 仓库。无需认证即可开箱使用，可选 PAT 认证以获得更高速率限制。
keywords: github, 搜索, 仓库, api, stars, 语言, 主题
---

# GitHub 搜索

GitHub 搜索通过 [GitHub REST 搜索 API](https://docs.github.com/en/rest/search/search#search-repositories) 提供 GitHub 仓库搜索功能。

## 类概述

- `GitHubSearch` - 提供 GitHub 仓库搜索功能的类

## 详细 API

### GitHubSearch 类

`GitHubSearch` 继承自 `BaseSearch`，提供 GitHub 仓库搜索功能，支持可选的 PAT 认证和密钥轮转。

#### 初始化参数

- `api_keys: str | None = None` - 逗号分隔的 GitHub 个人访问令牌。回退到 `GITHUB_TOKENS` 环境变量，然后使用未认证访问
- `rate_limit_delay: float = 1.0` - 请求之间的延迟秒数

#### 方法

- `search(query: str, max_results: int = 5, timeout: float = 10.0, **kwargs) -> list[SearchResult]`：执行搜索并返回结果
- `_search_impl(query: str, **kwargs) -> list[SearchResult]`：实现具体搜索逻辑，支持密钥轮转
- `_parse_results(raw_results: dict) -> list[SearchResult]`：解析原始搜索结果

### 查询语法

查询字符串直接传递给 GitHub 搜索 API，因此可以使用 [GitHub 搜索限定符](https://docs.github.com/en/search-github/searching-on-github/searching-for-repositories)：

- `machine learning language:python` — 关于机器学习的 Python 仓库
- `web framework stars:>1000` — 热门 Web 框架
- `topic:deep-learning language:python` — 标记为 deep-learning 的仓库
- `org:google language:go` — Google 的 Go 仓库

### 额外参数

以下参数可通过 `**kwargs` 传递：

| 参数 | 描述 |
|------|------|
| `sort` | 排序字段：`stars`、`forks`、`help-wanted-issues`、`updated` |
| `order` | 排序方向：`desc`（默认）或 `asc` |
| `page` | 分页页码 |

## 免费使用

GitHub 搜索 API 无需任何认证即可使用：

- **无需 API Key** — 开箱即用
- **未认证**：每分钟 10 次搜索请求
- **已认证**（使用 PAT）：每个令牌每分钟 30 次搜索请求
- **密钥轮转**：跨多个 PAT 分配负载以获得更高的聚合吞吐量

!!! note "领域特定引擎"
    GitHub 搜索是领域特定引擎，搜索的是仓库而非通用网页内容。它不包含在 `"auto"` 或 `"parallel"` 引擎链中——需要通过 `engine="github"` 显式选择。

## 环境变量

| 变量 | 必需 | 描述 |
|------|------|------|
| `GITHUB_TOKENS` | 否 | 逗号分隔的 GitHub 个人访问令牌，用于获得更高速率限制 |

## 使用示例

### 基本用法

```python
from toolregistry_hub.websearch import GitHubSearch

search = GitHubSearch()

# 使用 GitHub 限定符搜索
results = search.search("machine learning language:python stars:>1000", max_results=5)

for result in results:
    print(f"仓库: {result.title}")
    print(f"URL: {result.url}")
    print(f"信息: {result.content}")
    print("-" * 50)
```

### 按 Stars 排序

```python
from toolregistry_hub.websearch import GitHubSearch

search = GitHubSearch()

# 查找最多 Star 的 Python Web 框架
results = search.search(
    "web framework language:python",
    max_results=10,
    sort="stars",
    order="desc",
)
```

### 使用认证

```python
import os
os.environ["GITHUB_TOKENS"] = "ghp_token1,ghp_token2"

from toolregistry_hub.websearch import GitHubSearch

search = GitHubSearch()
# 自动使用 PAT 并进行密钥轮转
results = search.search("topic:machine-learning stars:>5000")
```

### 通过统一搜索

```python
from toolregistry_hub.websearch import WebSearch

ws = WebSearch()
results = ws.search("machine learning language:python", engine="github", count=5)
```
