# 搜索结果类型

搜索结果类型定义了网络搜索工具返回的数据结构。

## 类概览

搜索结果主要使用以下类：

- `SearchResult` - 表示单个搜索结果的数据类

## 详细 API

### SearchResult 类

`SearchResult` 是一个表示单个搜索结果的数据类。

#### 属性

- `title: str` - 搜索结果的标题
- `url: str` - 搜索结果的 URL
- `content: str` - 搜索结果的内容或描述
- `excerpt: str` - 搜索结果的摘要，通常与 content 相同

## 使用示例

```python
from toolregistry_hub.websearch import BingSearch
from toolregistry_hub.websearch.search_result import SearchResult

# 使用Bing搜索
bing_search = BingSearch()
results = bing_search.search("Python programming", number_results=5)

# 处理搜索结果
for result in results:
    print(f"标题: {result.title}")
    print(f"URL: {result.url}")
    print(f"摘要: {result.excerpt}")
    print(f"内容: {result.content}")
    print("-" * 50)

# 手动创建搜索结果
custom_result = SearchResult(
    title="Python Official Website",
    url="https://www.python.org",
    content="Python is a widely used interpreted, high-level, and general-purpose programming language.",
    excerpt="Python is a widely used interpreted, high-level, and general-purpose programming language."
)
print(f"Custom result: {custom_result.title} - {custom_result.url}")
```
