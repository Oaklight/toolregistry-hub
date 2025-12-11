# Google Search APIs 调试指南

本指南帮助您查看 Bright Data 和 Scrapeless API 返回的完整原始数据结构。

## 目的

通过详细的调试日志,我们可以:

1. 查看 API 返回的完整 JSON 结构
2. 识别我们当前 parsing 逻辑可能遗漏的字段
3. 对比两个 API 的数据格式差异
4. 为设计通用 parser 提供依据

## 前置条件

确保已设置相应的 API 密钥:

```bash
# Bright Data
export BRIGHTDATA_API_KEY="your-brightdata-api-key"
export BRIGHTDATA_ZONE="your-zone-name"  # 可选,默认为 mcp_unlocker

# Scrapeless
export SCRAPELESS_API_KEY="your-scrapeless-api-key"
```

## 运行调试测试

### 方法 1: 使用 pytest (推荐)

```bash
# 进入项目根目录
cd /home/pding/projects/toolregistry-hub/master

# 运行调试测试,显示详细输出
python -m pytest tests/websearch/test_debug_google_apis.py -v -s

# 只测试 Bright Data
python -m pytest tests/websearch/test_debug_google_apis.py::TestBrightDataDebug -v -s

# 只测试 Scrapeless
python -m pytest tests/websearch/test_debug_google_apis.py::TestScrapelessDebug -v -s
```

### 方法 2: 直接运行脚本

```bash
# 进入项目根目录
cd /home/pding/projects/toolregistry-hub/master

# 直接运行调试脚本
python tests/websearch/test_debug_google_apis.py
```

### 方法 3: 使用 proxychains (如遇网络问题)

```bash
# 使用代理运行测试
proxychains python -m pytest tests/websearch/test_debug_google_apis.py -v -s
```

## 查看输出

调试日志会显示以下信息:

### 1. 完整响应结构

```
Bright Data raw response keys: ['organic', 'images', 'pagination', 'related', ...]
Bright Data full response: {
  "organic": [...],
  "images": [...],
  ...
}
```

### 2. 有机搜索结果数量

```
Number of organic results: 10
```

### 3. 第一个结果的完整结构

```
First organic result structure: {
  "title": "...",
  "link": "...",
  "description": "...",
  "position": 1,
  ...
}
```

### 4. 每个结果的字段列表

```
Organic result #0 fields: ['title', 'link', 'description', 'position', ...]
Organic result #0 full data: {
  "title": "...",
  ...
}
```

## 分析要点

运行测试后,请关注以下问题:

1. **顶层字段**: 除了 `organic`/`organic_results`,还有哪些顶层字段?

   - `images`, `videos`, `news`?
   - `knowledge_graph`, `featured_snippet`?
   - `related_searches`, `people_also_ask`?

2. **有机结果字段**: 每个有机搜索结果包含哪些字段?

   - 基本字段: `title`, `link`/`url`, `description`/`snippet`
   - 额外字段: `position`, `source`, `date`, `thumbnail`?
   - 富媒体: `sitelinks`, `rating`, `price`?

3. **字段命名差异**:

   - Bright Data vs Scrapeless 的字段名是否一致?
   - 哪些字段是通用的,哪些是特定 API 独有的?

4. **数据丢失**:
   - 我们当前的 parsing 逻辑是否忽略了有价值的信息?
   - 是否有字段可以提供更好的搜索结果质量?

## 下一步

根据调试输出:

1. 记录两个 API 返回的完整字段列表
2. 识别被忽略但有价值的字段
3. 设计通用的 parser 来处理两种 API 格式
4. 决定是否需要扩展 `SearchResult` 数据模型

## 示例输出

预期会看到类似这样的详细日志:

```
2025-12-11 17:48:00 | DEBUG    | websearch_brightdata:_search_impl:223 - Bright Data raw response keys: ['organic', 'images', 'pagination', 'related']
2025-12-11 17:48:00 | DEBUG    | websearch_brightdata:_search_impl:224 - Bright Data full response: {
  "organic": [
    {
      "title": "Python Programming Language",
      "link": "https://www.python.org/",
      "description": "The official home of the Python Programming Language...",
      "position": 1
    }
  ],
  "images": [...],
  "pagination": {"current_page": 1, "total_pages": 10},
  "related": ["python tutorial", "python download"]
}
```

## 故障排除

### API 密钥未设置

```
ValueError: Bright Data API token is required. Set BRIGHTDATA_API_KEY environment variable
```

**解决**: 设置相应的环境变量

### 网络超时

```
Bright Data API request timed out after 10s
```

**解决**: 使用 `proxychains` 或增加 timeout 参数

### 认证失败

```
Authentication failed. Check your BRIGHTDATA_API_KEY
```

**解决**: 验证 API 密钥是否正确且有效
