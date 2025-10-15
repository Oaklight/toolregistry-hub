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
- `url: str` - 搜索结果的URL
- `content: str` - 搜索结果的内容或描述
- `excerpt: str` - 搜索结果的摘要，通常与content相同

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
    title="Python官方网站",
    url="https://www.python.org",
    content="Python是一种广泛使用的解释型、高级和通用的编程语言。",
    excerpt="Python是一种广泛使用的解释型、高级和通用的编程语言。"
)
print(f"自定义结果: {custom_result.title} - {custom_result.url}")
```

## 导航

- [返回网络搜索主页](index.md)
- [返回首页](../index.md)
- [查看导航页面](../navigation.md)
- [基础搜索类](base_search.md)
- [Bing搜索](bing.md)
- [SearXNG搜索](searxng.md)
- [旧版网络搜索](legacy.md)