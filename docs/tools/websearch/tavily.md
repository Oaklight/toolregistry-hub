# Tavily 搜索

Tavily 搜索提供了使用 Tavily Search API 进行网络搜索的功能。Tavily 提供 AI 驱动的搜索，具有 LLM 生成的答案和针对 AI 应用优化的高质量结果。

## 类概览

- `TavilySearch` - 提供 Tavily 搜索功能的类

## 详细 API

### TavilySearch 类

`TavilySearch` 是一个提供 Tavily 搜索功能的类，继承自 `BaseSearch`。

#### 初始化参数

- `api_keys: Optional[str] = None` - 逗号分隔的 Tavily API 密钥。如果未提供，将尝试从 TAVILY_API_KEY 环境变量获取
- `rate_limit_delay: float = 0.5` - 请求之间的延迟时间（秒），用于避免速率限制

#### 方法

- `search(query: str, max_results: int = 5, timeout: float = TIMEOUT_DEFAULT, **kwargs) -> List[SearchResult]`: 执行搜索并返回结果
- `_search_impl(query: str, **kwargs) -> List[SearchResult]`: 实现具体的搜索逻辑
- `_parse_results(raw_results: Dict) -> List[SearchResult]`: 解析原始搜索结果
- `_wait_for_rate_limit()`: 等待速率限制

## 设置

1. 在 <https://tavily.com/> 注册以获取 API 密钥
2. 设置环境变量：

   ```bash
   export TAVILY_API_KEY="tvly-your-api-key-here"
   ```

## 免费额度

Tavily Search 提供适中的免费额度：

- **注册后可获得每月 1,000 次免费搜索**
- **适合个人项目和小型应用测试**
- **支持 AI 生成答案功能**

### 最大化免费使用

1. **多API密钥轮换**：使用多个API密钥进行负载均衡，进一步扩展免费配额容量
2. **规划搜索频率**：智能控制搜索频率，避免浪费配额

!!! note "免费额度政策"
   所有免费额度信息可能因供应商政策变更而有所不同。信息在编写时是准确的。

## 使用示例

### 基本使用

```python
from toolregistry_hub.websearch import TavilySearch

# 创建 Tavily 搜索实例
tavily_search = TavilySearch()

# 执行搜索
results = tavily_search.search("Python programming", max_results=5)

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
from toolregistry_hub.websearch import TavilySearch

# 创建使用多个 API 密钥进行负载均衡的搜索实例
api_keys = "tvly-key1,tvly-key2,tvly-key3"
tavily_search = TavilySearch(api_keys=api_keys)

# 执行搜索
results = tavily_search.search("machine learning tutorial", max_results=10)

# 处理搜索结果
for result in results:
    print(f"标题: {result.title}")
    print(f"URL: {result.url}")
    print(f"内容: {result.content}")
    print("-" * 50)
```

### 自定义速率限制

```python
from toolregistry_hub.websearch import TavilySearch

# 创建自定义速率限制的搜索实例
tavily_search = TavilySearch(rate_limit_delay=1.0)

# 执行搜索
results = tavily_search.search("deep learning frameworks", max_results=5)

# 处理搜索结果
for result in results:
    print(f"标题: {result.title}")
    print(f"URL: {result.url}")
    print(f"内容: {result.content}")
    print("-" * 50)
```

### 带 AI 答案的高级搜索

```python
from toolregistry_hub.websearch import TavilySearch

# 创建 Tavily 搜索实例
tavily_search = TavilySearch()

# 执行带 AI 生成答案的搜索
results = tavily_search.search(
    "What is artificial intelligence?",
    max_results=5,
    include_answer=True,
    search_depth="advanced",
    topic="general"
)

# 处理搜索结果（第一个结果可能是 AI 生成的答案）
for result in results:
    print(f"标题: {result.title}")
    print(f"URL: {result.url}")
    print(f"内容: {result.content}")
    print(f"评分: {result.score}")
    print("-" * 50)
```

### 域名过滤

```python
from toolregistry_hub.websearch import TavilySearch

# 创建 Tavily 搜索实例
tavily_search = TavilySearch()

# 执行带域名过滤的搜索
results = tavily_search.search(
    "Python tutorials",
    max_results=5,
    include_domains=["python.org", "realpython.com", "docs.python.org"],
    exclude_domains=["spam-site.com"]
)

# 处理搜索结果
for result in results:
    print(f"标题: {result.title}")
    print(f"URL: {result.url}")
    print(f"内容: {result.content}")
    print("-" * 50)
```

### 新闻和研究搜索

```python
from toolregistry_hub.websearch import TavilySearch

# 创建 Tavily 搜索实例
tavily_search = TavilySearch()

# 执行新闻搜索
news_results = tavily_search.search(
    "latest AI developments",
    max_results=5,
    topic="news",
    search_depth="advanced"
)

# 执行研究搜索
research_results = tavily_search.search(
    "quantum computing research papers",
    max_results=5,
    topic="research",
    search_depth="advanced",
    include_raw_content=True
)

print("=== News Results ===")
for result in news_results:
    print(f"标题: {result.title}")
    print(f"URL: {result.url}")
    print(f"内容: {result.content}")
    print("-" * 50)

print("\n=== Research Results ===")
for result in research_results:
    print(f"标题: {result.title}")
    print(f"URL: {result.url}")
    print(f"内容: {result.content}")
    print("-" * 50)
```

### 获取网页内容

```python
from toolregistry_hub.websearch import TavilySearch
from toolregistry_hub.websearch.base import BaseSearch

# 创建 Tavily 搜索实例
tavily_search = TavilySearch()

# 执行搜索
results = tavily_search.search("Python tutorials", max_results=1)

if results:
    # 获取第一个结果的完整网页内容
    url = results[0].url
    if url:  # 检查 URL 是否存在（AI 答案可能没有 URL）
        content = BaseSearch._fetch_webpage_content(url)
        print(f"Web page content length: {len(content)} 字符")
        print(f"Web page content preview: {content[:200]}...")
```

## API 参数

Tavily Search API 支持各种参数，可以作为关键字参数传递：

- `max_results`: 返回的最大结果数量（0-20）
- `topic`: 搜索主题（"general", "news", "research"）
- `search_depth`: 搜索深度（"basic", "advanced"）
- `include_answer`: 是否包含 AI 生成的答案（布尔值）
- `include_domains`: 搜索中包含的域名列表
- `exclude_domains`: 搜索中排除的域名列表
- `include_raw_content`: 是否包含原始 HTML 内容（布尔值）

完整的 API 文档请参考：<https://docs.tavily.com/documentation/api-reference/endpoint/search>

## 特性

- **AI 驱动的答案**: 获取针对您查询的 LLM 生成答案
- **高质量结果**: 针对 AI 应用和研究进行优化
- **灵活的搜索深度**: 在基础和高级搜索模式之间选择
- **主题专业化**: 针对一般、新闻和研究主题的专业搜索
- **域名过滤**: 包含或排除特定域名
- **速率限制**: 内置速率限制以遵守 API 限制
- **多 API 密钥**: 支持轮询使用 API 密钥
- **原始内容**: 可选择包含原始 HTML 内容以进行进一步处理

## AI 答案功能

当设置 `include_answer=True` 时，Tavily 提供 AI 生成的答案作为第一个结果。此答案：

- 标题为"AI Generated Answer"
- 包含对您查询的全面回应
- 没有 URL（空字符串）
- 评分为 1.0
- 后面跟着常规搜索结果

此功能特别适用于：

- 研究查询
- 事实性问题
- 需要综合的复杂主题
- 教育内容
