# Scrapeless Google 搜索

Scrapeless Google 搜索提供了使用 Scrapeless DeepSERP API 进行 Google 网络搜索的功能。Scrapeless 提供强大的网页抓取能力,内置反机器人绕过,并返回结构化的、预解析的搜索结果,无需 HTML 解析。

## 概述

- **提供商**: Scrapeless DeepSERP API
- **搜索引擎**: 仅支持 Google
- **架构**: 使用通用的 [`GoogleResultParser`](../../websearch/google_parser.md)
- **评分**: 基于位置的相关性评分

## 类概览

- `ScrapelessSearch` - 提供 Scrapeless DeepSERP API Google 搜索功能的类

## 架构

Scrapeless 搜索实现使用了**通用的 Google 结果解析器** ([`GoogleResultParser`](../../websearch/google_parser.md)),它可以:

- 处理不同 API 响应格式的差异
- 基于搜索位置提供一致的结果评分
- 简化维护并减少代码重复
- 便于集成新的 Google 搜索提供商

## 设置

1. 在 <https://app.scrapeless.com/> 注册以获取 API 密钥
2. 设置环境变量:

   ```bash
   export SCRAPELESS_API_KEY="your-scrapeless-api-key-here"
   ```

## 使用示例

### 基本 Google 搜索

```python
from toolregistry_hub.websearch import ScrapelessSearch

# 创建 Scrapeless 搜索实例
scrapeless_search = ScrapelessSearch()

# 执行 Google 搜索
results = scrapeless_search.search("Python 编程", max_results=5)

# 处理搜索结果
for result in results:
    print(f"标题: {result.title}")
    print(f"URL: {result.url}")
    print(f"内容: {result.content}")
    print(f"评分: {result.score}")  # 基于位置的评分
    print("-" * 50)
```

### 使用语言和国家参数搜索

```python
from toolregistry_hub.websearch import ScrapelessSearch

# 创建搜索实例
scrapeless_search = ScrapelessSearch()

# 美国英文搜索
us_results = scrapeless_search.search(
    "人工智能",
    max_results=10,
    language="en",
    country="us"
)

# 中国中文搜索
cn_results = scrapeless_search.search(
    "人工智能",
    max_results=10,
    language="zh-CN",
    country="cn"
)

# 西班牙西班牙语搜索
es_results = scrapeless_search.search(
    "inteligencia artificial",
    max_results=10,
    language="es",
    country="es"
)

# 处理结果
for result in cn_results:
    print(f"中国结果: {result.title} (评分: {result.score})")
    print(f"URL: {result.url}")
    print("-" * 50)
```

### 自定义 API 配置

```python
from toolregistry_hub.websearch import ScrapelessSearch

# 创建自定义配置的搜索实例
scrapeless_search = ScrapelessSearch(
    api_key="your-api-key-here",
    base_url="https://api.scrapeless.com"
)

# 使用自定义超时执行搜索
results = scrapeless_search.search(
    "深度学习框架",
    max_results=15,
    timeout=30.0,
    language="zh-CN",
    country="cn"
)

# 处理搜索结果
for result in results:
    print(f"标题: {result.title}")
    print(f"URL: {result.url}")
    print(f"内容: {result.content[:150]}...")
    print(f"评分: {result.score}")
    print("-" * 50)
```

### 多地区搜索对比

```python
from toolregistry_hub.websearch import ScrapelessSearch

# 创建搜索实例
scrapeless_search = ScrapelessSearch()

query = "气候变化"
regions = [
    ("zh-CN", "cn"),
    ("en", "us"),
    ("en", "uk"),
    ("ja", "jp")
]

# 跨多个地区搜索
all_results = {}
for language, country in regions:
    results = scrapeless_search.search(
        query,
        max_results=5,
        language=language,
        country=country
    )
    all_results[f"{language}_{country}"] = results
    print(f"\n=== {language.upper()} / {country.upper()} 结果 ===")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.title} (评分: {result.score})")
        print(f"   {result.url}")
```

## API 参数

Scrapeless Google 搜索支持以下参数:

- `query`: 搜索查询字符串(必需)
- `max_results`: 返回的最大结果数(默认: 5,推荐: 1-20)
- `timeout`: 请求超时时间(秒)(默认: 10.0)
- `language`: 搜索结果的语言代码(默认: "en")
  - 示例: "en"、"zh-CN"、"es"、"fr"、"de"、"ja"、"ko"
- `country`: 搜索本地化的国家代码(默认: "us")
  - 示例: "us"、"uk"、"cn"、"jp"、"de"、"fr"、"es"

## 结果评分

结果根据其在搜索结果中的位置进行评分:

- 位置 1: score = 0.95
- 位置 2: score = 0.90
- 位置 3: score = 0.85
- 以此类推...

评分公式为: `score = 1.0 - (position * 0.05)`,限制在 0.0 到 1.0 之间。

这基于 Google 的排名准确反映了结果的相关性。

## 特性

- **仅支持 Google 搜索**: 通过 DeepSERP API 专门用于 Google 搜索
- **结构化结果**: 返回预解析的结构化数据,无需 HTML 解析
- **反机器人绕过**: 内置绕过反爬虫措施的能力
- **多语言支持**: 支持多种语言的搜索和正确的本地化
- **国家定位**: 获取特定地区的搜索结果
- **错误处理**: 全面的错误处理和日志记录
- **超时控制**: 可配置的请求超时
- **易于集成**: 与其他搜索提供商兼容的简单 API
- **通用解析器**: 使用共享的解析逻辑以保持一致性

## 技术细节

### 工作原理

Scrapeless Google 搜索使用 DeepSERP API (`scraper.google.search`),它会:

1. 发送您的搜索查询以及语言和国家参数
2. 在 Google 服务器上执行搜索
3. 绕过反机器人保护机制
4. 返回结构化的、预解析的搜索结果
5. 您无需进行 HTML 解析

### 请求负载

该工具向 Scrapeless API 发送以下结构的请求:

```json
{
  "actor": "scraper.google.search",
  "input": {
    "q": "您的搜索查询",
    "hl": "zh-CN",
    "gl": "cn"
  },
  "async": false
}
```

### 响应格式

DeepSERP API 返回结构化数据:

```json
{
  "organic_results": [
    {
      "position": 1,
      "title": "结果标题",
      "link": "https://example.com",
      "snippet": "结果描述...",
      "redirect_link": "https://...",
      "snippet_highlighted_words": ["关键词1", "关键词2"],
      "source": "example.com"
    }
  ]
}
```

### 通用解析器配置

Scrapeless 搜索使用 [`GoogleResultParser`](../../websearch/google_parser.md) 及以下配置:

```python
SCRAPELESS_CONFIG = GoogleAPIConfig(
    results_key="organic_results",
    url_keys=["link", "redirect_link"],
    description_keys=["snippet", "description"],
    position_key="position",
    use_position_scoring=True,
)
```

此配置告诉解析器:
- 在哪里找到有机搜索结果(`organic_results` 数组)
- 检查哪些字段获取 URL(先尝试 `link`,然后是 `redirect_link`)
- 检查哪些字段获取描述(先尝试 `snippet`,然后是 `description`)
- 如何计算相关性评分(基于 `position` 字段)

## 错误处理

该工具处理各种错误场景:

- **401 未授权**: 无效的 API 密钥
- **429 速率限制**: 请求过多
- **超时**: 请求超过超时限制
- **JSON 解析错误**: 格式错误的 API 响应

所有错误都会被记录并返回空结果列表。

## 最佳实践

1. **API 密钥安全**: 将 API 密钥存储在环境变量中,而不是代码中
2. **速率限制**: 注意 API 速率限制和使用配额
3. **超时设置**: 根据网络条件调整超时时间
4. **结果限制**: 使用合理的 `max_results` 值(推荐 1-20)
5. **语言/国家**: 根据使用场景选择合适的语言和国家代码
6. **错误处理**: 在处理之前始终检查结果是否为空

## 限制

- 每次查询推荐的最大结果数: 20
- 仅支持 Google 搜索(不支持 Bing、DuckDuckGo 等)
- API 使用受 Scrapeless 定价和配额限制
- 某些查询可能会根据地区或内容受到限制

## 测试

运行测试:

```bash
# 运行所有 Scrapeless 测试
pytest tests/websearch/test_websearch_scrapeless.py -v

# 运行特定测试
pytest tests/websearch/test_websearch_scrapeless.py::TestScrapelessSearch::test_search_basic -v

# 运行调试测试以查看原始 API 响应
python tests/websearch/test_debug_google_apis.py
```

## 相关资源

- [Scrapeless API 文档](https://docs.scrapeless.com/)
- [通用 Google 解析器文档](../../websearch/google_parser.md)
- [Scrapeless 控制台](https://app.scrapeless.com/)

## API 文档

完整的 Scrapeless API 文档请参考: <https://docs.scrapeless.com/>