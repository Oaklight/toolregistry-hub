---
title: 环境变量
summary: ToolRegistry Hub 使用的所有环境变量
description: 认证、工具 API 密钥和服务器配置环境变量的完整参考。
keywords: environment, variables, api keys, configuration, auth
author: Oaklight
---

# 环境变量

## 认证

| 变量 | 描述 |
|------|------|
| `API_BEARER_TOKEN` | API 认证 Bearer 令牌。单个令牌或逗号分隔的多个令牌。 |
| `API_BEARER_TOKENS_FILE` | 令牌文件路径，每行一个令牌。 |

如果两者均未设置，服务器将不启用认证。

## 工具 API 密钥

| 变量 | 工具 | 描述 |
|------|------|------|
| `BRAVE_API_KEY` | Brave 搜索 | Brave Search API 密钥（[获取](https://api.search.brave.com/)） |
| `TAVILY_API_KEY` | Tavily 搜索 | Tavily API 密钥（[获取](https://tavily.com/)） |
| `SERPER_API_KEY` | Serper 搜索 | Serper API 密钥（[获取](https://serper.dev/)） |
| `BRIGHTDATA_API_KEY` | BrightData 搜索 | Bright Data API 密钥（[获取](https://brightdata.com/)） |
| `SCRAPELESS_API_KEY` | Scrapeless 搜索 | Scrapeless API 密钥（[获取](https://scrapeless.com/)） |
| `SEARXNG_URL` | SearXNG 搜索 | SearXNG 实例 URL（如 `http://localhost:8080`） |
| `SEARXNG_API_KEY` | SearXNG 搜索 | 可选，用于受保护实例的 API 密钥（作为 `X-API-Key` 请求头发送） |
| `JINA_API_KEY` | Fetch（Jina Reader） | 可选；逗号分隔支持多密钥轮转 |
| `CDP_ENDPOINT` | Fetch（CDP 渲染） | 可选，CDP 兼容浏览器的 WebSocket URL（如 `ws://localhost:9222`） |

## 服务器配置

| 变量 | 描述 |
|------|------|
| `WEBSEARCH_PRIORITY` | auto 模式下引擎优先级，逗号分隔（如 `searxng,brave,tavily`） |
| `TOOLS_CONFIG` | `tools.jsonc` 配置文件路径（替代 `--config` CLI 标志） |

## 自动禁用行为

服务器启动时会检查每个工具所需的环境变量。缺少变量的工具会被注册但禁用 — 不会出现在返回给客户端的工具列表中。设置所需变量并重启即可启用。

## 使用 `.env` 文件

服务器默认从当前目录加载 `.env` 文件。可通过以下方式覆盖：

```bash
toolregistry-hub openapi --env /path/to/.env
toolregistry-hub openapi --no-env  # 跳过 .env 加载
```
