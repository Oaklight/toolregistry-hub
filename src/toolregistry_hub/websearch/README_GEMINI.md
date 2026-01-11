# Gemini Google Search

基于 Google Gemini API 的网页搜索实现，利用 Gemini 的内置 [Grounding with Google Search](https://ai.google.dev/gemini-api/docs/google-search) 功能提供免费的网页搜索能力。

## 特性

- 使用 Gemini 的内置 Google Search grounding 功能
- 提供带有来源引用的实时网页搜索结果
- 支持 Google AI Studio 和 Vertex AI 两种方式
- 免费使用（利用 Gemini 的免费额度）
- 返回综合性答案而非原始搜索结果

## 环境要求

- Python 3.8 或更高版本
- Google AI Studio API 密钥（从 [https://aistudio.google.com/](https://aistudio.google.com/) 获取）或 Google Cloud Project（启用 Vertex AI）

## 安装

```bash
pip install toolregistry-hub
```

注意：Gemini 搜索使用 REST API，不需要额外的 SDK 依赖。

## 配置

### 使用 Google AI Studio

```bash
# 设置 API 密钥（必需）
export GEMINI_API_KEY="your-api-key-here"

# 可选：设置模型（默认为 gemini-2.0-flash-exp）
export GEMINI_MODEL="gemini-2.0-flash-exp"
```

## 使用方法

### 基本用法

```python
from toolregistry_hub.websearch import GeminiSearch

# 初始化搜索客户端
search = GeminiSearch()

# 执行搜索
results = search.search("Python web scraping", max_results=5)

# 处理结果
for result in results:
    print(f"标题: {result.title}")
    print(f"URL: {result.url}")
    print(f"内容: {result.content[:200]}...")
    print(f"评分: {result.score}")
    print("-" * 50)
```

### 使用多个 API 密钥（负载均衡）

```python
from toolregistry_hub.websearch import GeminiSearch

# 使用逗号分隔的多个 API 密钥
search = GeminiSearch(
    api_keys="key1,key2,key3",
    rate_limit_delay=1.0  # 每个密钥之间的延迟（秒）
)

results = search.search("artificial intelligence trends")
```

### 使用自定义模型

```python
from toolregistry_hub.websearch import GeminiSearch

# 使用特定的 Gemini 模型
search = GeminiSearch(
    api_keys="your-api-key",
    model="gemini-1.5-pro"  # 或其他可用模型
)

results = search.search("machine learning algorithms")
```


## API 参考

### GeminiSearch 类

#### 初始化参数

- `api_keys` (str, 可选): 逗号分隔的 Gemini API 密钥。如果未提供，将从 `GEMINI_API_KEY` 环境变量获取。
- `model` (str, 可选): 要使用的 Gemini 模型。默认为 `GEMINI_MODEL` 环境变量或 `"gemini-2.0-flash-exp"`。
- `rate_limit_delay` (float, 可选): 请求之间的延迟（秒），用于避免速率限制。默认为 1.0。

#### search 方法

```python
def search(
    query: str,
    *,
    max_results: int = 5,
    timeout: float = 10.0,
    **kwargs
) -> List[SearchResult]
```

**参数:**
- `query` (str): 搜索查询字符串
- `max_results` (int): 返回的最大结果数（注意：实际数量取决于 Gemini 的响应）
- `timeout` (float): 请求超时时间（秒）
- `**kwargs`: 其他参数（当前未使用）

**返回:**
- `List[SearchResult]`: 包含标题、URL、内容和评分的搜索结果列表

## 与其他搜索引擎的区别

与传统搜索 API（如 Brave、Tavily）不同，Gemini 搜索：

1. **返回综合答案**: Gemini 不是返回原始搜索结果列表，而是提供一个综合性的答案，并附带来源引用。
2. **智能内容整合**: 结果是经过 AI 处理和整合的，而不是简单的网页摘要。
3. **免费使用**: 利用 Gemini 的免费额度，无需额外的搜索 API 订阅。
4. **结果格式**: 每个结果包含完整的综合答案，而不是单独的网页片段。

## 注意事项

1. **速率限制**: 免费的 Gemini API 有速率限制。建议使用 `rate_limit_delay` 参数来避免超出限制。
2. **结果数量**: 实际返回的结果数量可能少于 `max_results`，这取决于 Gemini 找到的相关来源数量。
3. **API 密钥安全**: 不要在代码中硬编码 API 密钥。使用环境变量或安全的密钥管理系统。
4. **Vertex AI 认证**: 使用 Vertex AI 时，确保已正确配置 Google Cloud 认证。

## 示例：完整的搜索应用

```python
from toolregistry_hub.websearch import GeminiSearch
import os

def main():
    # 从环境变量获取 API 密钥
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("错误: 请设置 GEMINI_API_KEY 环境变量")
        return
    
    # 初始化搜索
    search = GeminiSearch(
        api_keys=api_key,
        rate_limit_delay=1.0
    )
    
    # 执行搜索
    query = "最新的人工智能发展"
    print(f"搜索: {query}\n")
    
    results = search.search(query, max_results=5)
    
    if not results:
        print("未找到结果")
        return
    
    # 显示结果
    print(f"找到 {len(results)} 个结果:\n")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.title}")
        print(f"   URL: {result.url}")
        print(f"   内容: {result.content[:300]}...")
        print(f"   评分: {result.score:.3f}")
        print()

if __name__ == "__main__":
    main()
```

## 故障排除

### 错误: "API key is required"
- 确保已设置 `GEMINI_API_KEY` 环境变量或在初始化时提供 `api_keys` 参数。


### 搜索返回空结果
- 检查网络连接
- 验证 API 密钥是否有效
- 检查是否超出了速率限制
- 尝试增加 `timeout` 参数

### 速率限制错误
- 增加 `rate_limit_delay` 参数
- 使用多个 API 密钥进行负载均衡
- 考虑升级到付费的 Gemini API 计划

## 相关资源

- [Gemini API 文档](https://ai.google.dev/gemini-api/docs)
- [Grounding with Google Search](https://ai.google.dev/gemini-api/docs/google-search)
- [Google AI Studio](https://aistudio.google.com/)
- [Vertex AI 文档](https://cloud.google.com/vertex-ai/docs)

## 许可证

本项目采用 MIT 许可证。详见 LICENSE 文件。