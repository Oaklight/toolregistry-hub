# 旧版网络搜索

旧版网络搜索模块 (`websearch_legacy`) 提供了基础的网络搜索功能，支持多种搜索引擎。

## 类概览

旧版网络搜索模块主要包含以下类：

- `WebSearchGeneral` - 所有搜索引擎的抽象基类
- `WebSearchBing` - 提供 Bing 搜索功能的类
- `WebSearchGoogle` - 提供 Google 搜索功能的类
- `WebSearchSearXNG` - 提供 SearXNG 搜索功能的类

## 详细 API

### WebSearchGeneral 类

`WebSearchGeneral` 是一个抽象基类，定义了所有搜索引擎必须实现的接口。

#### 方法

- `search(query: str, num_results: int = 5, **kwargs) -> List[dict]`: 执行搜索并返回结果
- `_fetch_webpage_content(url: str, timeout: Optional[float] = None) -> str`: 获取网页内容

### WebSearchBing 类

`WebSearchBing` 是一个提供 Bing 搜索功能的类，继承自 `WebSearchGeneral`。

#### 初始化参数

- `timeout: float = 3.0` - 请求超时时间（秒）
- `proxy: Optional[str] = None` - 代理服务器 URL

#### 方法

- `search(query: str, num_results: int = 5, **kwargs) -> List[dict]`: 执行搜索并返回结果
- `_meta_search_bing(query: str, num_results: int, timeout: float, proxy: Optional[str]) -> List[dict]`: 执行 Bing 搜索
- `_parse_bing_entries(entries: List[dict], num_results: int) -> List[dict]`: 解析 Bing 搜索结果
- `_extract_real_url(bing_url: str) -> str`: 从 Bing 重定向 URL 中提取真实 URL

### WebSearchGoogle 类

`WebSearchGoogle` 是一个提供 Google 搜索功能的类，继承自 `WebSearchGeneral`。

#### 初始化参数

- `timeout: float = 3.0` - 请求超时时间（秒）
- `proxy: Optional[str] = None` - 代理服务器 URL

#### 方法

- `search(query: str, num_results: int = 5, **kwargs) -> List[dict]`: 执行搜索并返回结果
- `_meta_search_google(query: str, num_results: int, timeout: float, proxy: Optional[str]) -> List[dict]`: 执行 Google 搜索
- `_parse_google_entries(entries: List[dict], num_results: int) -> List[dict]`: 解析 Google 搜索结果

### WebSearchSearXNG 类

`WebSearchSearXNG` 是一个提供 SearXNG 搜索功能的类，继承自 `WebSearchGeneral`。

#### 初始化参数

- `base_url: Optional[str] = None` - SearXNG 实例的基础 URL，默认使用内置实例
- `timeout: float = 3.0` - 请求超时时间（秒）
- `proxy: Optional[str] = None` - 代理服务器 URL

#### 方法

- `search(query: str, num_results: int = 5, **kwargs) -> List[dict]`: 执行搜索并返回结果
- `_meta_search_searxng(query: str, num_results: int, timeout: float, proxy: Optional[str]) -> List[dict]`: 执行 SearXNG 搜索

## 使用示例

### 使用 Bing 搜索

```python
from toolregistry_hub.websearch_legacy import WebSearchBing

# 创建Bing搜索实例
bing_search = WebSearchBing()

# 执行搜索
results = bing_search.search("Python programming", num_results=5)

# 处理搜索结果
for result in results:
    print(f"标题: {result['title']}")
    print(f"URL: {result['url']}")
    print(f"摘要: {result['excerpt']}")
    print("-" * 50)
```

### 使用 Google 搜索

```python
from toolregistry_hub.websearch_legacy import WebSearchGoogle

# 创建Google搜索实例
google_search = WebSearchGoogle()

# 执行搜索
results = google_search.search("机器学习教程", num_results=3)

# 处理搜索结果
for result in results:
    print(f"标题: {result['title']}")
    print(f"URL: {result['url']}")
    print(f"摘要: {result['excerpt']}")
    print("-" * 50)
```

### 使用 SearXNG 搜索

```python
from toolregistry_hub.websearch_legacy import WebSearchSearXNG

# 创建SearXNG搜索实例
searxng_search = WebSearchSearXNG()

# 执行搜索
results = searxng_search.search("深度学习框架", num_results=5)

# 处理搜索结果
for result in results:
    print(f"标题: {result['title']}")
    print(f"URL: {result['url']}")
    print(f"摘要: {result['excerpt']}")
    print("-" * 50)
```

### 获取网页内容

```python
from toolregistry_hub.websearch_legacy import WebSearchBing, WebSearchGeneral

# 创建Bing搜索实例
bing_search = WebSearchBing()

# 执行搜索
results = bing_search.search("Python教程", num_results=1)

if results:
    # 获取第一个结果的完整网页内容
    url = results[0]['url']
    content = WebSearchGeneral._fetch_webpage_content(url)
    print(f"网页内容长度: {len(content)} 字符")
    print(f"网页内容预览: {content[:200]}...")
```

## 搜索结果过滤

旧版网络搜索模块还提供了搜索结果过滤功能，可以过滤掉不需要的搜索结果。

```python
from toolregistry_hub.websearch_legacy import WebSearchBing
from toolregistry_hub.websearch_legacy.filter import filter_search_results

# 创建Bing搜索实例
bing_search = WebSearchBing()

# 执行搜索
results = bing_search.search("Python programming", num_results=10)

# 过滤搜索结果
filtered_results = filter_search_results(results)
print(f"过滤前结果数: {len(results)}")
print(f"过滤后结果数: {len(filtered_results)}")
```

## 导航

- [返回网络搜索主页](index.md)
- [返回首页](../index.md)
- [查看导航页面](../navigation.md)
- [搜索结果类型](search_result.md)
- [基础搜索类](base_search.md)
- [Bing 搜索](bing.md)
- [SearXNG 搜索](searxng.md)
