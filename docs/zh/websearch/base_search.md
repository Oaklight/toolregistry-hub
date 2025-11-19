# 基础搜索类

基础搜索类是所有搜索引擎实现的抽象基类，定义了搜索引擎必须实现的接口。

## 类概览

- `BaseSearch` - 所有搜索引擎的抽象基类

## 详细 API

### BaseSearch 类

`BaseSearch` 是一个抽象基类，定义了所有搜索引擎必须实现的接口。

#### 属性

- `_headers` - 搜索请求使用的 HTTP 头信息

#### 方法

- `search(query: str, number_results: int = 5, timeout: Optional[float] = None, **kwargs) -> List[SearchResult]`: 执行搜索并返回结果
- `_parse_results(raw_results: Any) -> List[SearchResult]`: 解析原始搜索结果为 SearchResult 对象列表
- `_search_impl(query: str, **kwargs) -> List[SearchResult]`: 实现具体的搜索逻辑
- `_fetch_webpage_content(url: str, timeout: Optional[float] = None) -> str`: 获取网页内容

## 实现自定义搜索引擎

要实现自定义搜索引擎，需要继承`BaseSearch`类并实现其抽象方法：

```python
from typing import Any, List, Optional
from toolregistry_hub.websearch.base import BaseSearch
from toolregistry_hub.websearch.search_result import SearchResult

class MyCustomSearch(BaseSearch):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    @property
    def _headers(self) -> dict:
        """返回搜索请求使用的HTTP头信息"""
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Authorization": f"Bearer {self.api_key}" if self.api_key else ""
        }

    def _search_impl(self, query: str, **kwargs) -> List[SearchResult]:
        """实现具体的搜索逻辑"""
        # 这里实现具体的搜索逻辑
        # 例如，发送HTTP请求到搜索API
        # ...

        # 返回模拟结果
        return [
            SearchResult(
                title="示例结果1",
                url="https://example.com/1",
                content="这是示例结果1的内容",
                excerpt="这是示例结果1的摘要"
            ),
            SearchResult(
                title="示例结果2",
                url="https://example.com/2",
                content="这是示例结果2的内容",
                excerpt="这是示例结果2的摘要"
            )
        ]

    def _parse_results(self, raw_results: Any) -> List[SearchResult]:
        """解析原始搜索结果为SearchResult对象列表"""
        # 这里实现解析逻辑
        # ...

        # 返回模拟结果
        return [
            SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                content=item.get("content", ""),
                excerpt=item.get("excerpt", "")
            )
            for item in raw_results.get("items", [])
        ]
```

## 使用示例

```python
# 创建自定义搜索引擎实例
my_search = MyCustomSearch(api_key="your_api_key")

# 执行搜索
results = my_search.search("Python programming", number_results=5)

# 处理搜索结果
for result in results:
    print(f"标题: {result.title}")
    print(f"URL: {result.url}")
    print(f"摘要: {result.excerpt}")
    print("-" * 50)
```

## 导航

- [返回网络搜索主页](index.md)
- [返回首页](../index.md)
- [查看导航页面](../navigation.md)
- [搜索结果类型](search_result.md)
- [Bing 搜索](bing.md)
- [SearXNG 搜索](searxng.md)
- [旧版网络搜索](legacy.md)
