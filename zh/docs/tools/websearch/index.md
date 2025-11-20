# 网络搜索工具

网络搜索工具提供了通过各种搜索引擎进行网络搜索的功能。该模块支持多种搜索引擎，包括 Bing、SearXNG、Brave 和 Tavily。

## 模块概览

网络搜索工具主要包含以下两个版本：

1. **新版网络搜索模块** (`websearch`) - 提供统一的搜索引擎抽象层和更先进的功能
2. **旧版网络搜索模块** (`websearch_legacy`) - 提供基础的网络搜索功能

## 搜索引擎支持

当前支持的搜索引擎包括：

- [Bing 搜索](bing.md) - 使用 Bing 搜索引擎
- [SearXNG 搜索](searxng.md) - 使用 SearXNG 元搜索引擎
- [Brave 搜索](brave.md) - 使用 Brave 搜索引擎
- [Tavily 搜索](tavily.md) - 使用 Tavily 搜索 API

## 基本使用

```python
from toolregistry_hub.websearch import BingSearch, SearXNGSearch, BraveSearch, TavilySearch

# 使用Bing搜索
bing_search = BingSearch()
results = bing_search.search("Python programming", number_results=5)
for result in results:
    print(f"标题: {result.title}")
    print(f"URL: {result.url}")
    print(f"摘要: {result.excerpt}")
    print("-" * 50)

# 使用SearXNG搜索
searxng_search = SearXNGSearch()
results = searxng_search.search("machine learning tutorial", number_results=3)
for result in results:
    print(f"标题: {result.title}")
    print(f"URL: {result.url}")
    print(f"摘要: {result.excerpt}")
    print("-" * 50)

# 使用Brave搜索
brave_search = BraveSearch()
results = brave_search.search("artificial intelligence", number_results=5)
for result in results:
    print(f"标题: {result.title}")
    print(f"URL: {result.url}")
    print(f"内容: {result.content}")
    print(f"评分: {result.score}")
    print("-" * 50)

# 使用Tavily搜索
tavily_search = TavilySearch()
results = tavily_search.search("quantum computing", number_results=5)
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
- [Bing 搜索](bing.md) - Bing 搜索引擎的实现
- [SearXNG 搜索](searxng.md) - SearXNG 搜索引擎的实现
- [Brave 搜索](brave.md) - Brave 搜索引擎的实现
- [Tavily 搜索](tavily.md) - Tavily 搜索 API 的实现
- [旧版网络搜索](legacy.md) - 旧版网络搜索模块的文档

## 架构升级计划

网络搜索模块正在进行架构升级，详细信息可以在[架构升级计划](plan.md)中查看。
