---
title: 学术搜索
summary: 通过 OpenAlex 和 arXiv 搜索学术论文
---

# 学术搜索

`academics` 命名空间提供跨多个引擎的学术论文搜索。

## 引擎

| 引擎 | 数据源 | 需要认证 | 免费额度 |
|------|--------|----------|---------|
| OpenAlex | [openalex.org](https://openalex.org/) | 否 | 无限制（polite pool） |
| arXiv | [arxiv.org](https://arxiv.org/) | 否 | 无限制 |

## 环境变量

| 变量 | 说明 |
|------|------|
| `OPENALEX_MAILTO` | OpenAlex polite pool 邮箱（可获更高速率限制，推荐设置） |
| `ACADEMIC_SEARCH_PRIORITY` | 引擎优先级，逗号分隔（默认：`openalex,arxiv`） |

## 使用方式

```python
from toolregistry_hub.academics import AcademicSearch

search = AcademicSearch()
results = search.search("transformer attention mechanism", engine="openalex", count=5)
for r in results:
    print(f"{r.title} — {r.url}")
```

### API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/tools/academics/search` | 搜索学术论文 |
| POST | `/tools/academics/list_engines` | 列出可用的学术搜索引擎 |

### 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `query` | string | 必填 | 搜索查询 |
| `engine` | string | `"auto"` | 使用的引擎：`auto`、`openalex`、`arxiv` |
| `count` | integer | `5` | 结果数量（最大 20） |

### 结果字段

每条结果包含：`title`、`authors`、`abstract`、`url`、`year`、`venue`、`doi`、`pdf_url`、`cited_by_count`、`source`。
