# ToolRegistry Hub 服务器

[![Docker Image Version](https://img.shields.io/docker/v/oaklight/toolregistry-hub-server?label=Docker&logo=docker)](https://hub.docker.com/r/oaklight/toolregistry-hub-server)
[![GitHub](https://img.shields.io/badge/GitHub-Oaklight/toolregistry--hub-blue?logo=github)](https://github.com/Oaklight/toolregistry-hub)
[![文档](https://img.shields.io/badge/文档-ReadTheDocs-blue?logo=readthedocs)](https://toolregistry-hub.readthedocs.io/zh-cn/latest/)

[文档](https://toolregistry-hub.readthedocs.io/zh-cn/latest/) | [English Documentation](https://toolregistry-hub.readthedocs.io/en/latest/) | [GitHub](https://github.com/Oaklight/toolregistry-hub)

ToolRegistry Hub 服务器支持 **MCP (Model Context Protocol)** 和 **OpenAPI** 模式。它**取代**了 [oaklight/openwebui-tool-server](https://github.com/Oaklight/openwebui-tool-server)。

## 主要特性

- 计算器、日期时间、网络搜索 (Brave/SearXNG/Tavily/Google)、文件操作、思考工具、待办列表、网页抓取等。
- 完整列表：[文档](https://toolregistry-hub.readthedocs.io/zh-cn/latest/)。

## Docker 快速命令

**OpenAPI 模式 (默认):**

```
docker run -d --name toolregistry-hub -p 8000:8000 \
  -e API_BEARER_TOKEN=your_token_here \
  oaklight/toolregistry-hub-server:latest
```

访问：http://localhost:8000/docs

**MCP Streamable HTTP:**

```
docker run -d --name toolregistry-hub-mcp -p 8001:8000 \
  -e API_BEARER_TOKEN=your_token_here \
  oaklight/toolregistry-hub-server:latest \
  toolregistry-server --host=0.0.0.0 --port=8000 --mode=mcp
```

**MCP SSE:**

```
docker run -d --name toolregistry-hub-sse -p 8002:8000 \
  -e API_BEARER_TOKEN=your_token_here \
  oaklight/toolregistry-hub-server:latest \
  toolregistry-server --host=0.0.0.0 --port=8000 --mode=mcp --mcp-transport=sse
```

将 `your_token_here` 替换为 [tokens.txt.example](tokens.txt.example) 中的令牌。更多环境变量见 [.env.sample](.env.sample)。

## Docker Compose (所有模式)

```
cp .env.sample .env  # 编辑 API 密钥
docker compose up -d
```

- OpenAPI: localhost:55093/docs
- MCP HTTP: localhost:55094
- MCP SSE: localhost:55095

开发构建：`docker compose -f compose.dev.yaml up`

## 从源码构建

```
git clone https://github.com/Oaklight/toolregistry-hub
cd docker
docker build -t toolregistry-hub .
docker run -p 8000:8000 --env-file .env toolregistry-hub
```

## 许可证

MIT
