# Serper 搜索

Serper 搜索提供了通过 Serper API 获取 Google 搜索结果的功能。

## 类概览

- `SerperSearch` - 提供 Serper 搜索功能的类

## 详细 API

### SerperSearch 类

`SerperSearch` 是一个提供 Serper 搜索功能的类，继承自 `BaseSearch`。

#### 初始化参数

- `api_keys: Optional[str] = None` - 逗号分隔的 Serper API 密钥。如果未提供，将尝试从 SERPER_API_KEY 环境变量获取
- `rate_limit_delay: float = 1.0` - 请求之间的延迟时间（秒），用于避免速率限制

#### 方法

- `search(query: str, max_results: int = 5, timeout: float = TIMEOUT_DEFAULT, **kwargs) -> List[SearchResult]`: 执行搜索并返回结果
- `_search_impl(query: str, **kwargs) -> List[SearchResult]`: 实现具体的搜索逻辑
- `_parse_results(raw_results: Dict) -> List[SearchResult]`: 解析原始搜索结果
- `_wait_for_rate_limit()`: 等待速率限制

## 设置

1. 在 <https://serper.dev/> 注册以获取 API 密钥
2. 设置环境变量：

   ```bash
   export SERPER_API_KEY="your-serper-api-key-here"
   ```

## 免费额度

- **每月 2,500 次免费查询**
- 无需信用卡

!!! note "免费额度政策"
    所有免费额度信息可能因供应商政策变更而有所不同。信息在编写时是准确的。

## 使用示例

### 基本使用

```python
from toolregistry_hub.websearch import SerperSearch

# 创建 Serper 搜索实例
serper_search = SerperSearch()

# 执行搜索
results = serper_search.search("Python programming", max_results=5)

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
from toolregistry_hub.websearch import SerperSearch

# 创建使用多个 API 密钥进行负载均衡的搜索实例
api_keys = "key1,key2,key3"
serper_search = SerperSearch(api_keys=api_keys)

# 执行搜索
results = serper_search.search("机器学习教程", max_results=10)

# 处理搜索结果
for result in results:
    print(f"标题: {result.title}")
    print(f"URL: {result.url}")
    print(f"内容: {result.content}")
    print("-" * 50)
```

### 高级搜索参数

```python
from toolregistry_hub.websearch import SerperSearch

serper_search = SerperSearch()

# 使用高级参数执行搜索
results = serper_search.search(
    "人工智能",
    max_results=15,
    gl="cn",                           # 国家代码
    hl="zh",                           # 语言代码
    location="Beijing, China",         # 本地化结果的位置
)

for result in results:
    print(f"标题: {result.title}")
    print(f"URL: {result.url}")
    print(f"内容: {result.content}")
    print("-" * 50)
```

## API 参数

Serper API 支持以下关键字参数：

- `gl`: 国家代码（如 "us", "uk", "cn"）
- `hl`: 语言代码（如 "en", "zh", "es"）
- `location`: 位置字符串（如 "Austin, Texas"）
- `autocorrect`: 启用/禁用拼写纠正（布尔值）
- `page`: 结果页码（从 1 开始）
- `num`: 每次请求的结果数量（最多 100）

完整的 API 文档请参考：<https://serper.dev/playground>

## 特性

- **Google 搜索结果**: 返回 Google 搜索结果
- **速率限制**: 内置速率限制以遵守 API 限制
- **多 API 密钥**: 支持轮询使用 API 密钥
- **灵活参数**: 支持国家、语言和位置定向
