# Brave 搜索

Brave 搜索提供了使用 Brave Search API 进行网络搜索的功能。Brave Search 提供独立的搜索结果，不依赖 Google，并具有良好的隐私保护功能。

## 类概览

- `BraveSearch` - 提供 Brave 搜索功能的类

## 详细 API

### BraveSearch 类

`BraveSearch` 是一个提供 Brave 搜索功能的类，继承自 `BaseSearch`。

#### 初始化参数

- `api_keys: Optional[str] = None` - 逗号分隔的 Brave API 密钥。如果未提供，将尝试从 BRAVE_API_KEY 环境变量获取
- `rate_limit_delay: float = 1.0` - 请求之间的延迟时间（秒），用于避免速率限制

#### 方法

- `search(query: str, max_results: int = 5, timeout: float = TIMEOUT_DEFAULT, **kwargs) -> List[SearchResult]`: 执行搜索并返回结果
- `_search_impl(query: str, **kwargs) -> List[SearchResult]`: 实现具体的搜索逻辑
- `_parse_results(raw_results: Dict) -> List[SearchResult]`: 解析原始搜索结果
- `_wait_for_rate_limit()`: 等待速率限制

## 设置

1. 在 <https://api.search.brave.com/> 注册以获取 API 密钥
2. 设置环境变量：

   ```bash
   export BRAVE_API_KEY="your-brave-api-key-here"
   ```

## 使用示例

### 基本使用

```python
from toolregistry_hub.websearch import BraveSearch

# 创建 Brave 搜索实例
brave_search = BraveSearch()

# 执行搜索
results = brave_search.search("Python programming", max_results=5)

# 处理搜索结果
for result in results:
    print(f"标题: {result.title}")
    print(f"URL: {result.url}")
    print(f"内容: {result.content}")
    print(f"评分: {result.score}")
    print("-" * 50)
```

### 使用多个 API 密钥

```python
from toolregistry_hub.websearch import BraveSearch

# 创建使用多个 API 密钥进行负载均衡的搜索实例
api_keys = "key1,key2,key3"
brave_search = BraveSearch(api_keys=api_keys)

# 执行搜索
results = brave_search.search("机器学习教程", max_results=10)

# 处理搜索结果
for result in results:
    print(f"标题: {result.title}")
    print(f"URL: {result.url}")
    print(f"内容: {result.content}")
    print("-" * 50)
```

### 自定义速率限制

```python
from toolregistry_hub.websearch import BraveSearch

# 创建自定义速率限制的搜索实例
brave_search = BraveSearch(rate_limit_delay=2.0)

# 执行搜索
results = brave_search.search("深度学习框架", max_results=5)

# 处理搜索结果
for result in results:
    print(f"标题: {result.title}")
    print(f"URL: {result.url}")
    print(f"内容: {result.content}")
    print("-" * 50)
```

### 高级搜索参数

```python
from toolregistry_hub.websearch import BraveSearch

# 创建 Brave 搜索实例
brave_search = BraveSearch()

# 使用高级参数执行搜索
results = brave_search.search(
    "人工智能",
    max_results=15,
    country="CN",
    search_lang="zh",
    safesearch="strict",
    freshness="pd"  # 过去一天
)

# 处理搜索结果
for result in results:
    print(f"标题: {result.title}")
    print(f"URL: {result.url}")
    print(f"内容: {result.content}")
    print(f"评分: {result.score}")
    print("-" * 50)
```

### 获取网页内容

```python
from toolregistry_hub.websearch import BraveSearch
from toolregistry_hub.websearch.base import BaseSearch

# 创建 Brave 搜索实例
brave_search = BraveSearch()

# 执行搜索
results = brave_search.search("Python教程", max_results=1)

if results:
    # 获取第一个结果的完整网页内容
    url = results[0].url
    content = BaseSearch._fetch_webpage_content(url)
    print(f"网页内容长度: {len(content)} 字符")
    print(f"网页内容预览: {content[:200]}...")
```

## API 参数

Brave Search API 支持各种参数，可以作为关键字参数传递：

- `country`: 本地化结果的国家代码（如 "US", "GB", "DE", "CN"）
- `search_lang`: 搜索结果的语言（如 "en", "es", "fr", "zh"）
- `safesearch`: 安全搜索级别（"off", "moderate", "strict"）
- `freshness`: 结果的时间过滤器（"pd" 表示过去一天，"pw" 表示过去一周，"pm" 表示过去一个月，"py" 表示过去一年）
- `result_filter`: 按类型过滤结果
- `count`: 每次请求的结果数量（最多 20）
- `offset`: 分页偏移量

完整的 API 文档请参考：<https://api-dashboard.search.brave.com/app/documentation/web-search/query>

## 特性

- **独立结果**: Brave Search 提供自己的索引，不依赖 Google
- **隐私保护**: 无用户跟踪或数据收集
- **高质量**: AI 驱动的排名和垃圾邮件过滤
- **速率限制**: 内置速率限制以遵守 API 限制
- **多 API 密钥**: 支持轮询使用 API 密钥
- **灵活参数**: 支持所有 Brave Search API 参数
