# 网络搜索工具

网络搜索工具提供了通过各种搜索引擎进行网络搜索的功能。该模块支持多种搜索引擎，包括 Brave、SearXNG、Tavily 和 Google（通过 BrightData/Scrapeless）。

!!! note "Bing 搜索已废弃"
    Bing 搜索因频繁遇到机器人检测问题已被废弃。请使用其他搜索提供商。

## 免费额度汇总

以下是各搜索提供商免费额度的快速概览：

| 提供商 | 免费额度 | 月度限制 | 备注 |
|----------|-----------|---------------|-------|
| **Brave Search** | ✅ 有 | 4,000 次查询 | 两个独立计划（各 2,000 次） |
| **Bright Data** | ✅ 有 | 5,000 次查询 | 无需验证 |
| **Tavily** | ✅ 有 | 1,000 次查询 | AI 优化搜索 |
| **Scrapeless** | ❌ 无 | - | 价格实惠的付费计划 |
| **SearXNG** | ✅ 免费 | 无限制 | 自托管，开源 |

!!! tip "最大化免费使用"
    - **多 API 密钥轮转**：所有提供商都支持多个 API 密钥进行负载均衡
    - **SearXNG 用于高容量**：考虑自托管 SearXNG 以获得无限免费搜索

!!! note "免费额度政策"
    所有免费额度信息可能因供应商政策变更而有所不同。信息在编写时是准确的。

## 模块概览

网络搜索工具主要包含以下两个版本：

1. **新版网络搜索模块** (`websearch`) - 提供统一的搜索引擎抽象层和更先进的功能
2. **旧版网络搜索模块** (`websearch_legacy`) - 提供基础的网络搜索功能

## 搜索引擎支持

当前支持的搜索引擎包括：

- [Brave 搜索](brave.md) - 使用 Brave 搜索引擎（推荐）
- [Tavily 搜索](tavily.md) - 使用 Tavily 搜索 API（AI 优化）
- [SearXNG 搜索](searxng.md) - 使用 SearXNG 元搜索引擎（注重隐私）
- [BrightData 搜索](brightdata.md) - 使用 BrightData 获取 Google 搜索结果
- [Scrapeless 搜索](scrapeless.md) - 使用 Scrapeless Universal API，支持多个搜索引擎
- [Bing 搜索](bing.md) - ⚠️ **已废弃** - 使用 Bing 搜索引擎（不推荐）

## 基本使用

```python
from toolregistry_hub.websearch import BraveSearch, SearXNGSearch, TavilySearch, BrightDataSearch, ScrapelessSearch

# 使用 Brave 搜索（推荐）
brave_search = BraveSearch()
results = brave_search.search("Python programming", max_results=5)
for result in results:
    print(f"标题: {result.title}")
    print(f"URL: {result.url}")
    print(f"内容: {result.content}")
    print(f"评分: {result.score}")
    print("-" * 50)

# 使用SearXNG搜索
searxng_search = SearXNGSearch()
results = searxng_search.search("machine learning tutorial", max_results=3)
for result in results:
    print(f"标题: {result.title}")
    print(f"URL: {result.url}")
    print(f"摘要: {result.excerpt}")
    print("-" * 50)

# 使用Brave搜索
brave_search = BraveSearch()
results = brave_search.search("artificial intelligence", max_results=5)
for result in results:
    print(f"标题: {result.title}")
    print(f"URL: {result.url}")
    print(f"内容: {result.content}")
    print(f"评分: {result.score}")
    print("-" * 50)

# 使用Tavily搜索
tavily_search = TavilySearch()
results = tavily_search.search("quantum computing", max_results=5)
for result in results:
    print(f"标题: {result.title}")
    print(f"URL: {result.url}")
    print(f"内容: {result.content}")
    print(f"评分: {result.score}")
    print("-" * 50)

# 使用Bright Data Google搜索
brightdata_search = BrightDataSearch()
results = brightdata_search.search("web scraping", max_results=5)
for result in results:
    print(f"Title: {result.title}")
    print(f"URL: {result.url}")
    print(f"Content: {result.content}")
    print(f"Score: {result.score}")
    print("-" * 50)

# 使用Scrapeless Google搜索
scrapeless_search = ScrapelessSearch()
results = scrapeless_search.search("网页抓取", max_results=5)
for result in results:
    print(f"标题: {result.title}")
    print(f"URL: {result.url}")
    print(f"内容: {result.content}")
    print(f"评分: {result.score}")
    print("-" * 50)
```

## 详细文档

- [搜索结果类型](search_result.md) - 搜索结果的数据结构
- [基础搜索类](base_search.md) - 所有搜索引擎的基类
- [Brave 搜索](brave.md) - Brave 搜索引擎的实现（推荐）
- [Tavily 搜索](tavily.md) - Tavily 搜索 API 的实现
- [SearXNG 搜索](searxng.md) - SearXNG 搜索引擎的实现
- [BrightData 搜索](brightdata.md) - BrightData 获取 Google 搜索结果的实现
- [Scrapeless 搜索](scrapeless.md) - Scrapeless DeepSERP API 的实现
- [Bing 搜索](bing.md) - ⚠️ **已废弃** Bing 搜索引擎的实现
- [旧版网络搜索](legacy.md) - 旧版网络搜索模块的文档
