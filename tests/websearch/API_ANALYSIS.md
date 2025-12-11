# Google Search APIs 数据结构分析

基于实际 API 调用的详细分析报告。

## 执行摘要

两个 API 都返回了丰富的 Google 搜索结果数据,但我们当前的 parsing 逻辑**只提取了基本的有机搜索结果**,忽略了大量有价值的额外信息。

## Bright Data API 数据结构

### 顶层字段

```json
{
  "general": {...},        // ✅ 未使用 - 搜索元数据
  "input": {...},          // ✅ 未使用 - 请求信息
  "navigation": [...],     // ✅ 未使用 - 导航链接(Images, Videos, News等)
  "organic": [...],        // ✅ 已使用 - 有机搜索结果
  "perspectives": {...},   // ✅ 未使用 - 观点/视角
  "knowledge": {...},      // ✅ 未使用 - 知识图谱
  "overview": {...},       // ✅ 未使用 - AI概览
  "pagination": {...},     // ✅ 未使用 - 分页信息
  "related": [...]         // ✅ 未使用 - 相关搜索
}
```

### 有机搜索结果字段 (organic[])

当前使用的字段:

- ✅ `title` - 标题
- ✅ `link` - URL
- ✅ `description` - 描述

**被忽略的有价值字段**:

- ❌ `source` - 来源网站名称 (如 "Python.org", "Wikipedia")
- ❌ `display_link` - 显示的链接格式
- ❌ `rank` - 结果排名
- ❌ `global_rank` - 全局排名
- ❌ `extensions` - 扩展信息(如 sitelinks)
  - `type` - 扩展类型
  - `text` - 扩展文本
  - `link` - 扩展链接
  - `rank` - 扩展排名

### 示例有机结果

```json
{
  "link": "https://www.python.org/",
  "source": "Python.org",
  "display_link": "https://www.python.org",
  "title": "Welcome to Python.org",
  "description": "Python is a programming language...",
  "extensions": [
    {
      "type": "site_link",
      "text": "Python For Beginners",
      "link": "https://www.python.org/about/gettingstarted/",
      "rank": 1
    }
  ],
  "rank": 2,
  "global_rank": 2
}
```

### 其他被忽略的顶层数据

1. **navigation** - 搜索类型导航

   - AI Mode, Images, Videos, Shopping, News 等

2. **pagination** - 分页信息

   - `current` - 当前页码
   - `next` - 下一页 URL
   - `other_pages` - 其他页面链接

3. **related_questions** - 相关问题

   ```json
   [
     { "question": "What is Python programming used for?" },
     { "question": "Is Python difficult to learn?" }
   ]
   ```

4. **related_searches** - 相关搜索

   ```json
   [
     {
       "query": "Python Programming book",
       "link": "https://..."
     }
   ]
   ```

5. **things_to_know** - 知识要点

   - 包含按钮和子主题

6. **search_information** - 搜索信息
   - 结果状态、显示的查询、总结果数等

## Scrapeless API 数据结构

### 顶层字段

```json
{
  "organic_results": [...],     // ✅ 已使用 - 有机搜索结果
  "related_searches": [...],    // ✅ 未使用 - 相关搜索
  "related_questions": [...],   // ✅ 未使用 - 相关问题
  "pagination": {...},          // ✅ 未使用 - 分页信息
  "search_information": {...}   // ✅ 未使用 - 搜索信息
}
```

### 有机搜索结果字段 (organic_results[])

当前使用的字段:

- ✅ `title` - 标题
- ✅ `link` - URL
- ✅ `snippet` - 描述片段
- ✅ `position` - 位置(用于计算 score)

**被忽略的有价值字段**:

- ❌ `source` - 来源网站名称
- ❌ `redirect_link` - Google 重定向链接
- ❌ `favicon` - 网站图标(base64 编码)
- ❌ `snippet_highlighted_words` - 高亮的关键词
- ❌ `site_links` - 站点链接
  - `inline` - 内联链接数组
    - `title` - 链接标题
    - `link` - 链接 URL

### 示例有机结果

```json
{
  "position": 2,
  "title": "Welcome to Python.org",
  "link": "https://www.python.org/",
  "redirect_link": "https://www.google.com/url?...",
  "favicon": "data:image/png;base64,...",
  "snippet": "Python is a programming language...",
  "snippet_highlighted_words": ["Python is a programming language"],
  "site_links": {
    "inline": [
      {
        "title": "Python For Beginners",
        "link": "https://www.python.org/about/gettingstarted/"
      }
    ]
  },
  "source": "Python.org"
}
```

## 两个 API 的对比

| 特性          | Bright Data           | Scrapeless                  | 当前使用         |
| ------------- | --------------------- | --------------------------- | ---------------- |
| **基本字段**  |
| 标题          | `title`               | `title`                     | ✅               |
| URL           | `link`                | `link`                      | ✅               |
| 描述          | `description`         | `snippet`                   | ✅               |
| **排名/位置** |
| 位置          | `rank`, `global_rank` | `position`                  | ⚠️ 仅 Scrapeless |
| **来源信息**  |
| 来源名称      | `source`              | `source`                    | ❌               |
| 显示链接      | `display_link`        | -                           | ❌               |
| 网站图标      | -                     | `favicon`                   | ❌               |
| **扩展信息**  |
| 站点链接      | `extensions[]`        | `site_links.inline[]`       | ❌               |
| 高亮词        | -                     | `snippet_highlighted_words` | ❌               |
| 重定向链接    | -                     | `redirect_link`             | ❌               |
| **其他数据**  |
| 相关搜索      | `related_searches`    | `related_searches`          | ❌               |
| 相关问题      | `related_questions`   | `related_questions`         | ❌               |
| 分页信息      | `pagination`          | `pagination`                | ❌               |

## 关键发现

### 1. 丢失的有价值信息

我们当前的 parsing 逻辑忽略了以下重要信息:

1. **来源标识** (`source`)

   - 可以帮助用户快速识别结果来源
   - 提高结果的可信度展示

2. **站点链接** (`extensions`/`site_links`)

   - 提供快速导航到子页面
   - 增强用户体验

3. **排名信息** (`rank`/`position`)

   - Bright Data: 有 `rank` 和 `global_rank`
   - Scrapeless: 有 `position`
   - 可用于更准确的相关性评分

4. **相关搜索和问题**

   - 可以提供搜索建议
   - 帮助用户细化查询

5. **高亮关键词** (Scrapeless)
   - 显示匹配的搜索词
   - 帮助用户快速定位相关内容

### 2. 字段命名差异

虽然两个 API 的核心数据相似,但字段命名有差异:

| 概念     | Bright Data   | Scrapeless        |
| -------- | ------------- | ----------------- |
| 结果数组 | `organic`     | `organic_results` |
| 描述     | `description` | `snippet`         |
| 排名     | `rank`        | `position`        |
| 站点链接 | `extensions`  | `site_links`      |

### 3. 独有字段

**Bright Data 独有**:

- `display_link` - 格式化的显示链接
- `global_rank` - 全局排名
- `navigation` - 搜索类型导航
- `knowledge` - 知识图谱
- `overview` - AI 概览
- `things_to_know` - 知识要点

**Scrapeless 独有**:

- `favicon` - 网站图标
- `redirect_link` - Google 重定向链接
- `snippet_highlighted_words` - 高亮词列表

## 建议的改进

### 1. 扩展 SearchResult 数据模型

```python
@dataclass
class SearchResult:
    title: str
    url: str
    content: str
    score: float

    # 新增字段
    source: Optional[str] = None              # 来源网站名称
    position: Optional[int] = None            # 搜索结果位置
    site_links: Optional[List[Dict]] = None   # 站点链接
    highlighted_words: Optional[List[str]] = None  # 高亮关键词
    favicon: Optional[str] = None             # 网站图标
```

### 2. 创建通用 Parser

设计一个配置驱动的 parser 来处理两种 API 格式:

```python
class GoogleAPIConfig:
    results_key: str                    # "organic" or "organic_results"
    url_keys: List[str]                 # ["link", "url"]
    description_keys: List[str]         # ["description", "snippet"]
    source_key: str = "source"
    position_key: Optional[str] = None  # "rank" or "position"
    sitelinks_key: Optional[str] = None # "extensions" or "site_links"
```

### 3. 利用额外数据

考虑返回更丰富的搜索结果:

- 相关搜索建议
- 相关问题
- 分页信息
- 知识图谱(如果可用)

## 命名方案建议

基于两个 API 都是 Google 搜索的不同实现,建议使用:

```
search_google_brightdata    # 通过Bright Data的Google搜索
search_google_scrapeless    # 通过Scrapeless的Google搜索
```

或者更简洁的:

```
search_brightdata_google    # Bright Data提供的Google搜索
search_scrapeless_google    # Scrapeless提供的Google搜索
```

**推荐**: 第二种方案,因为它:

1. 强调服务提供商(主要差异点)
2. 明确指出是 Google 搜索
3. 与现有的 `search_scrapeless_google` 保持一致

## 下一步行动

1. ✅ 确认是否需要扩展 `SearchResult` 模型
2. ✅ 设计通用的 Google 搜索结果 parser
3. ✅ 实现配置驱动的 parsing 逻辑
4. ✅ 重构两个实现使用通用 parser
5. ✅ 添加对额外字段的支持
6. ✅ 更新 API 文档说明新增字段
7. ✅ 编写测试验证新功能
