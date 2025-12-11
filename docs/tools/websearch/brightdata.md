# Bright Data Google 搜索

本文档介绍如何使用 Bright Data SERP API 进行 Google 搜索。

## 概述

Bright Data 是一个企业级的网页数据平台，提供强大的反爬虫绕过能力。通过集成 Bright Data 的 SERP API，我们可以:

- ✅ 绕过 Google 的反爬虫机制
- ✅ 获取结构化的搜索结果
- ✅ 支持分页查询
- ✅ 无需担心 IP 封禁或 CAPTCHA
- ✅ **统一的解析逻辑**，与其他 Google 搜索提供商保持一致

## 架构

Bright Data 搜索实现使用了**通用的 Google 结果解析器** ([`GoogleResultParser`](../../websearch/google_parser.md))，它可以:

- 处理不同 API 响应格式的差异
- 基于搜索位置提供一致的结果评分
- 简化维护并减少代码重复
- 便于集成新的 Google 搜索提供商

## 配置

### 1. 获取 API Token

1. 访问 [Bright Data](https://brightdata.com) 并注册账号
2. 在控制台中创建 API Token
3. (可选)创建或使用现有的 Web Unlocker Zone

### 2. 设置环境变量

```bash
# 必需: API Token
export BRIGHTDATA_API_KEY="your_api_token_here"

# 可选: 自定义 Zone(默认为 mcp_unlocker)
export BRIGHTDATA_ZONE="your_zone_name"
```

或者在 `.env` 文件中配置:

```env
BRIGHTDATA_API_KEY=your_api_token_here
BRIGHTDATA_ZONE=mcp_unlocker
```

## 使用方法

### Python API

```python
from toolregistry_hub.websearch import BrightDataSearch

# 初始化搜索客户端
search = BrightDataSearch()

# 基本搜索
results = search.search("python web scraping"， max_results=10)

for result in results:
    print(f"标题: {result.title}")
    print(f"URL: {result.url}")
    print(f"内容: {result.content[:200]}...")
    print(f"评分: {result.score}")  # 基于搜索位置的评分
    print("-" * 50)

# 分页搜索(获取第2页结果)
results_page2 = search.search(
    "artificial intelligence"，
    max_results=10，
    cursor="1"  # 页码从 0 开始
)

# 自定义超时
results = search.search(
    "machine learning"，
    max_results=5，
    timeout=30.0
)
```

### REST API

#### 端点

```
POST /api/v1/search/brightdata
```

#### 请求示例

```bash
curl -X POST "http://localhost:8000/api/v1/search/brightdata" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_auth_token" \
  -d '{
    "query": "python web scraping"，
    "max_results": 10，
    "timeout": 10.0，
    "cursor": "0"
  }'
```

#### 请求参数

| 参数          | 类型    | 必需 | 默认值 | 说明                     |
| ------------- | ------- | ---- | ------ | ------------------------ |
| `query`       | string  | ✅   | -      | 搜索查询字符串           |
| `max_results` | integer | ❌   | 5      | 返回结果数量(1-20)       |
| `timeout`     | float   | ❌   | 10.0   | 请求超时时间(秒)         |
| `cursor`      | string  | ❌   | "0"    | 分页游标(页码，从 0 开始) |

#### 响应示例

```json
{
  "results": [
    {
      "title": "Python Web Scraping Tutorial"，
      "url": "https://example.com/tutorial"，
      "content": "Learn how to scrape websites using Python..."，
      "score": 0.95
    }，
    {
      "title": "Best Python Scraping Libraries"，
      "url": "https://example.com/libraries"，
      "content": "A comprehensive guide to Python scraping tools..."，
      "score": 0.9
    }
  ]
}
```

**注意**: `score` 字段现在反映了搜索结果的位置(位置越靠前，评分越高)。

## 高级用法

### 批量搜索

```python
from toolregistry_hub.websearch import BrightDataSearch

search = BrightDataSearch()

queries = ["python"， "javascript"， "golang"]
all_results = []

for query in queries:
    results = search.search(query， max_results=5)
    all_results.extend(results)

print(f"总共获取了 {len(all_results)} 个结果")
```

### 深度搜索(多页)

```python
from toolregistry_hub.websearch import BrightDataSearch

search = BrightDataSearch()

# 获取前 50 个结果(自动分页)
results = search.search("machine learning"， max_results=50)

# 或者手动控制分页
all_results = []
for page in range(3):  # 获取前3页
    results = search.search(
        "deep learning"，
        max_results=20，
        cursor=str(page)
    )
    all_results.extend(results)
```

### 自定义配置

```python
from toolregistry_hub.websearch import BrightDataSearch

# 使用自定义配置
search = BrightDataSearch(
    api_token="your_custom_token"，
    zone="custom_zone_name"，
    rate_limit_delay=2.0  # 每次请求间隔2秒
)

results = search.search("custom query")
```

## 结果评分

结果根据其在搜索结果中的位置进行评分:

- 位置 1: score = 0.95
- 位置 2: score = 0.90
- 位置 3: score = 0.85
- 以此类推...

评分公式为: `score = 1.0 - (position * 0.05)`，限制在 0.0 到 1.0 之间。

这比固定评分更准确地反映了结果的相关性。

## Zone 说明

**Zone** 是 Bright Data 的核心概念，类似于"代理池"或"服务实例":

- 每个 Zone 有独立的配额和计费
- 默认使用 `mcp_unlocker` zone(Web Unlocker 类型)
- 可以通过 `BRIGHTDATA_ZONE` 环境变量自定义
- **自动创建**: 如果 zone 不存在，系统会自动创建(需要有效的 API key)

### Zone 自动创建

当你初始化 `BrightDataGoogleSearch` 时，系统会:

1. 检查指定的 zone 是否存在
2. 如果不存在，自动创建一个 Web Unlocker 类型的 zone
3. 如果创建失败，会记录警告但继续运行(zone 可能在首次使用时由 Bright Data 创建)

你也可以手动创建 Zone:

1. 登录 [Bright Data 控制台](https://brightdata.com/cp)
2. 点击 "Add" 按钮
3. 选择 "Unlocker zone"
4. 输入 zone 名称并创建
5. 在环境变量中设置该 zone 名称

## 错误处理

### 常见错误

#### 1. 认证失败(401)

```
Authentication failed. Check your BRIGHTDATA_API_KEY
```

**解决方案**: 检查 API token 是否正确设置。

#### 2. Zone 不存在(422)

```
Zone 'your_zone' does not exist. Check your BRIGHTDATA_ZONE configuration
```

**解决方案**: 在 Bright Data 控制台创建该 zone，或使用默认的 `mcp_unlocker`。

#### 3. 速率限制(429)

```
Rate limit exceeded， consider increasing rate_limit_delay
```

**解决方案**: 增加 `rate_limit_delay` 参数值。

#### 4. 超时错误

```
Bright Data API request timed out after 10s
```

**解决方案**: 增加 `timeout` 参数值。

### 错误处理示例

```python
from toolregistry_hub.websearch import BrightDataSearch

try:
    search = BrightDataSearch()
    results = search.search("test query")

    if not results:
        print("未找到结果或发生错误")
    else:
        for result in results:
            print(f"{result.title} (评分: {result.score})")

except ValueError as e:
    print(f"配置错误: {e}")
except Exception as e:
    print(f"搜索失败: {e}")
```

## 性能优化

### 1. 速率限制

```python
# 设置更长的延迟以避免速率限制
search = BrightDataSearch(rate_limit_delay=2.0)
```

### 2. 超时设置

```python
# 对于复杂查询，增加超时时间
results = search.search("complex query"， timeout=30.0)
```

### 3. 批量处理

```python
# 一次性获取更多结果，减少 API 调用次数
results = search.search("query"， max_results=20)
```

## 限制

- 单次请求最多返回 20 个结果
- 总共最多支持 180 个结果(通过分页)
- 受 Bright Data 账户配额限制
- 仅支持 Google 搜索(不支持 Bing、Yandex)

## 测试

运行测试:

```bash
# 运行所有 Bright Data 测试
pytest tests/websearch/test_websearch_brightdata.py -v

# 运行特定测试
pytest tests/websearch/test_websearch_brightdata.py::TestBrightDataSearch::test_search_basic -v

# 运行调试测试以查看原始 API 响应
python tests/websearch/test_debug_google_apis.py
```

## 技术细节

### 通用解析器

Bright Data 搜索使用 [`GoogleResultParser`](../../websearch/google_parser.md) 及以下配置:

```python
BRIGHTDATA_CONFIG = GoogleAPIConfig(
    results_key="organic"，
    url_keys=["link"， "url"]，
    description_keys=["description"， "snippet"]，
    position_key="rank"，
    use_position_scoring=True，
)
```

此配置告诉解析器:

- 在 API 响应中哪里找到有机搜索结果
- 检查哪些字段获取 URL(按优先级顺序)
- 检查哪些字段获取描述
- 如何计算相关性评分

## 相关资源

- [Bright Data 官方文档](https://docs.brightdata.com/)
- [Bright Data API 参考](https://docs.brightdata.com/api-reference)
- [Bright Data 控制台](https://brightdata.com/cp)
- [通用 Google 解析器文档](../../websearch/google_parser.md)

## 许可证

本集成遵循项目的 MIT 许可证。使用 Bright Data 服务需要遵守其服务条款。
