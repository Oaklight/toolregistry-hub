# 网络搜索工具

网络搜索工具提供了通过各种搜索引擎进行网络搜索的功能。该模块支持多种搜索引擎，包括 Bing、Google、SearXNG 和 Tavily 等。

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
from toolregistry_hub.websearch import BingSearch, SearXNGSearch

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
results = searxng_search.search("机器学习教程", number_results=3)
for result in results:
    print(f"标题: {result.title}")
    print(f"URL: {result.url}")
    print(f"摘要: {result.excerpt}")
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

## 导航

- [返回首页](../index.md)
- [查看导航页面](../navigation.md)
- [计算器工具](../calculator.md)
- [日期时间工具](../datetime.md)
- [文件操作工具](../file_ops.md)
- [文件系统工具](../filesystem.md)
- [单位转换工具](../unit_converter.md)
- [其他工具](../other_tools.md)
