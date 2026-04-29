# Bing 搜索（已移除）

!!! danger "已移除"
    **Bing 搜索自 0.6.0 版本起已被移除。**

    此功能在 0.5.2 版本中因频繁遇到机器人检测问题而被废弃，现已从代码库中完全移除。

    **推荐的替代方案：**

    - [Brave 搜索](brave.md) - 用于通用网络搜索
    - [Tavily 搜索](tavily.md) - 用于 AI 优化搜索
    - [SearXNG 搜索](searxng.md) - 用于注重隐私的搜索
    - [BrightData 搜索](brightdata.md) 或 [Scrapeless 搜索](scrapeless.md) - 用于 Google 搜索结果

## 迁移指南

如果您之前使用的是 `BingSearch`，请迁移到上述推荐的替代方案之一。

### 迁移前（已废弃）

```python
from toolregistry_hub.websearch import BingSearch

search = BingSearch()
results = search.search("query", max_results=5)
```

### 迁移后（推荐）

```python
from toolregistry_hub.websearch import BraveSearch

search = BraveSearch()  # 需要设置 BRAVE_API_KEY 环境变量
results = search.search("query", max_results=5)
```

