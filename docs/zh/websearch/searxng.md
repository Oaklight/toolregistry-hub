# SearXNG 搜索

SearXNG 搜索提供了使用 SearXNG 元搜索引擎进行网络搜索的功能。

## 类概览

- `SearXNGSearch` - 提供 SearXNG 搜索功能的类

## 详细 API

### SearXNGSearch 类

`SearXNGSearch` 是一个提供 SearXNG 搜索功能的类，继承自 `BaseSearch`。

#### 初始化参数

- `base_url: Optional[str] = None` - SearXNG 实例的基础 URL，默认使用内置实例

#### 方法

- `search(query: str, number_results: int = 5, timeout: Optional[float] = None, **kwargs) -> List[SearchResult]`: 执行搜索并返回结果
- `_search_impl(query: str, **kwargs) -> List[SearchResult]`: 实现具体的搜索逻辑
- `_parse_results(raw_results: Dict) -> List[SearchResult]`: 解析原始搜索结果

## 使用示例

### 基本使用

```python
from toolregistry_hub.websearch import SearXNGSearch

# 创建SearXNG搜索实例
searxng_search = SearXNGSearch()

# 执行搜索
results = searxng_search.search("Python programming", number_results=5)

# 处理搜索结果
for result in results:
    print(f"标题: {result.title}")
    print(f"URL: {result.url}")
    print(f"摘要: {result.excerpt}")
    print("-" * 50)
```

### 使用自定义 SearXNG 实例

```python
from toolregistry_hub.websearch import SearXNGSearch

# 创建使用自定义SearXNG实例的搜索实例
searxng_search = SearXNGSearch(base_url="https://your-searxng-instance.com")

# 执行搜索
results = searxng_search.search("机器学习教程", number_results=3)

# 处理搜索结果
for result in results:
    print(f"标题: {result.title}")
    print(f"URL: {result.url}")
    print(f"摘要: {result.excerpt}")
    print("-" * 50)
```

### 设置超时

```python
from toolregistry_hub.websearch import SearXNGSearch

# 创建SearXNG搜索实例
searxng_search = SearXNGSearch()

# 执行搜索，设置超时
results = searxng_search.search("深度学习框架", number_results=5, timeout=10.0)

# 处理搜索结果
for result in results:
    print(f"标题: {result.title}")
    print(f"URL: {result.url}")
    print(f"摘要: {result.excerpt}")
    print("-" * 50)
```

### 获取网页内容

```python
from toolregistry_hub.websearch import SearXNGSearch
from toolregistry_hub.websearch.base import BaseSearch

# 创建SearXNG搜索实例
searxng_search = SearXNGSearch()

# 执行搜索
results = searxng_search.search("Python教程", number_results=1)

if results:
    # 获取第一个结果的完整网页内容
    url = results[0].url
    content = BaseSearch._fetch_webpage_content(url)
    print(f"网页内容长度: {len(content)} 字符")
    print(f"网页内容预览: {content[:200]}...")
```

## SearXNG 简介

SearXNG 是一个自托管的元搜索引擎，它可以聚合多个搜索引擎的结果，提供隐私保护的搜索体验。使用 SearXNG 的主要优势包括：

1. **隐私保护** - SearXNG 不会跟踪用户，不存储搜索历史
2. **多引擎聚合** - 可以同时从多个搜索引擎获取结果
3. **自托管** - 可以在自己的服务器上部署 SearXNG 实例
4. **自定义** - 可以自定义搜索引擎、结果呈现方式等

## 旧版 SearXNG 搜索

旧版 SearXNG 搜索功能在 `websearch_legacy` 模块中提供，使用 `WebSearchSearXNG` 类。详细信息请参阅[旧版网络搜索](legacy.md)文档。

## 导航

- [返回网络搜索主页](index.md)
- [返回首页](../index.md)
- [查看导航页面](../navigation.md)
- [搜索结果类型](search_result.md)
- [基础搜索类](base_search.md)
- [Bing 搜索](bing.md)
- [旧版网络搜索](legacy.md)
