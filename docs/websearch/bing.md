# Bing搜索

Bing搜索提供了使用Microsoft Bing搜索引擎进行网络搜索的功能。

## 类概览

- `BingSearch` - 提供Bing搜索功能的类

## 详细 API

### BingSearch 类

`BingSearch` 是一个提供Bing搜索功能的类，继承自 `BaseSearch`。

#### 初始化参数

- `rate_limit_delay: float = 1.0` - 请求之间的延迟时间（秒）
- `timeout: Optional[float] = None` - 请求超时时间（秒）
- `max_retries: int = 3` - 最大重试次数
- `proxy: Optional[str] = None` - 代理服务器URL

#### 方法

- `search(query: str, number_results: int = 5, timeout: Optional[float] = None, **kwargs) -> List[SearchResult]`: 执行搜索并返回结果
- `_search_impl(query: str, **kwargs) -> List[SearchResult]`: 实现具体的搜索逻辑
- `_parse_results(raw_results: Dict) -> List[SearchResult]`: 解析原始搜索结果
- `_extract_real_url(bing_url: str) -> str`: 从Bing重定向URL中提取真实URL
- `_wait_for_rate_limit()`: 等待速率限制

## 使用示例

### 基本使用

```python
from toolregistry_hub.websearch import BingSearch

# 创建Bing搜索实例
bing_search = BingSearch()

# 执行搜索
results = bing_search.search("Python programming", number_results=5)

# 处理搜索结果
for result in results:
    print(f"标题: {result.title}")
    print(f"URL: {result.url}")
    print(f"摘要: {result.excerpt}")
    print("-" * 50)
```

### 使用代理

```python
from toolregistry_hub.websearch import BingSearch

# 创建使用代理的Bing搜索实例
bing_search = BingSearch(proxy="http://your-proxy-server:port")

# 执行搜索
results = bing_search.search("机器学习教程", number_results=3)

# 处理搜索结果
for result in results:
    print(f"标题: {result.title}")
    print(f"URL: {result.url}")
    print(f"摘要: {result.excerpt}")
    print("-" * 50)
```

### 自定义超时和重试

```python
from toolregistry_hub.websearch import BingSearch

# 创建自定义超时和重试的Bing搜索实例
bing_search = BingSearch(timeout=5.0, max_retries=2)

# 执行搜索
results = bing_search.search("深度学习框架", number_results=5, timeout=10.0)

# 处理搜索结果
for result in results:
    print(f"标题: {result.title}")
    print(f"URL: {result.url}")
    print(f"摘要: {result.excerpt}")
    print("-" * 50)
```

### 获取网页内容

```python
from toolregistry_hub.websearch import BingSearch
from toolregistry_hub.websearch.base import BaseSearch

# 创建Bing搜索实例
bing_search = BingSearch()

# 执行搜索
results = bing_search.search("Python教程", number_results=1)

if results:
    # 获取第一个结果的完整网页内容
    url = results[0].url
    content = BaseSearch._fetch_webpage_content(url)
    print(f"网页内容长度: {len(content)} 字符")
    print(f"网页内容预览: {content[:200]}...")
```

## 旧版Bing搜索

旧版Bing搜索功能在 `websearch_legacy` 模块中提供，使用 `WebSearchBing` 类。详细信息请参阅[旧版网络搜索](legacy.md)文档。

## 导航

- [返回网络搜索主页](index.md)
- [返回首页](../index.md)
- [查看导航页面](../navigation.md)
- [搜索结果类型](search_result.md)
- [基础搜索类](base_search.md)
- [SearXNG搜索](searxng.md)
- [旧版网络搜索](legacy.md)