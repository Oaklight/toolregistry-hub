# openwebui-tool-server Migration Update

**⚠️ Important Migration Notice: Project migrated to ToolRegistry Hub**

## 🚀 New Project Information

- **GitHub Repo**: https://github.com/Oaklight/toolregistry-hub
- **NEW Docker Image**: [`oaklight/toolregistry-hub-server:latest`](https://hub.docker.com/r/oaklight/toolregistry-hub-server)

[中文](https://github.com/Oaklight/toolregistry-hub/blob/master/README_zh.md) | [English](https://github.com/Oaklight/toolregistry-hub/blob/master/README_en.md)

**New Docker Image**: `oaklight/toolregistry-hub-server:latest`

## 🔄 Migration Command Updates

### Start Server (Python)

```bash
# Old command
python main.py --port 8000 --host 0.0.0.0 --mode <openapi|mcp>

# New command
toolregistry-server --host=0.0.0.0 --port=8000 --mode <openapi|mcp>
```

### Docker Start (Recommended)

**OpenAPI Mode (default):**

```bash
docker run -d -p 8000:8000 \
    --name toolregistry-hub-server \
   -e API_BEARER_TOKEN="your_token_here" \
   -e SEARXNG_URL="https://searxng.url" \
   -e BRAVE_API_KEY="your_brave_key" \
   -e TAVILY_API_KEY="your_tavily_key" \
   oaklight/toolregistry-hub-server:latest
```

**MCP Streamable HTTP Mode:**

```bash
docker run -d -p 8000:8000 \
    --name toolregistry-hub-mcp \
   -e API_BEARER_TOKEN="your_token_here" \
   -e SEARXNG_URL="https://searxng.url" \
   oaklight/toolregistry-hub-server:latest \
   toolregistry-server --host=0.0.0.0 --port=8000 --mode=mcp
```

**MCP SSE Mode:**

```bash
docker run -d -p 8000:8000 \
    --name toolregistry-hub-sse \
   -e API_BEARER_TOKEN="your_token_here" \
   -e SEARXNG_URL="https://searxng.url" \
   oaklight/toolregistry-hub-server:latest \
   toolregistry-server --host=0.0.0.0 --port=8000 --mode=mcp --mcp-transport=sse
```

Or use docker compose:

```bash
# Download config
cp .env.sample .env  # Edit API keys
docker compose up -d
```

## 🔍 API Documentation

Once the server is running, visit the following URLs:

1. **OpenAPI Interactive Documentation (Swagger UI)**
   Open your browser and go to:
   [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

2. **OpenAPI Documentation (ReDoc)**
   View the ReDoc documentation at:
   [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## ⚙️ Environment Variable Configuration

### API_BEARER_TOKEN

- **Purpose**: Token to secure API endpoints
- **OpenAPI Mode**: Recommended to set for production endpoint protection
- **MCP Mode**: Typically runs without authentication (`API_BEARER_TOKEN` unset)

### SEARXNG_URL

- **Purpose**: SearXNG base URL for privacy-respecting metasearch engine
- **Behavior**:
  - Enables `/search_searxng` tool when set
  - Returns 503 error when not set

### New Environment Variables

**BRAVE_API_KEY**: Brave search API key  
**TAVILY_API_KEY**: Tavily search API key

## 📋 Mode Switching

**OpenAPI Mode (default):**

```yaml
command:
  ["toolregistry-server", "--host=0.0.0.0", "--port=8000", "--mode=openapi"]
```

**MCP Streamable HTTP Mode:**

```yaml
command: ["toolregistry-server", "--host=0.0.0.0", "--port=8000", "--mode=mcp"]
```

**MCP SSE Mode:**

```yaml
command:
  [
    "toolregistry-server",
    "--host=0.0.0.0",
    "--port=8000",
    "--mode=mcp",
    "--mcp-transport=sse",
  ]
```

## 🆕 New Features

- **More Search Engines**: Bing, Brave, SearXNG, Tavily
- **Enhanced Calculator**: More mathematical functions
- **File Operations**: Enhanced file read/write and management
- **Think Tool**: Reasoning log recording
- **Kanban Board**: Project-scoped task tracking
- **Web Fetch**: Content extraction tools

## 📚 Complete Documentation

- **ReadTheDocs**: [https://toolregistry-hub.readthedocs.io/en/latest/](https://toolregistry-hub.readthedocs.io/en/latest/)
- **Chinese Docs**: [https://toolregistry-hub.readthedocs.io/zh-cn/latest/](https://toolregistry-hub.readthedocs.io/zh-cn/latest/)

---

**Migration Tip**: Replace all `oaklight/openwebui-tool-server:latest` with `oaklight/toolregistry-hub-server:latest`

---

# openwebui-tool-server 迁移更新

**⚠️ 重要迁移通知：项目已迁移到 ToolRegistry Hub**

## 🚀 新项目信息

- **GitHub Repo**: https://github.com/Oaklight/toolregistry-hub
- **新的 Docker Image**: [`oaklight/toolregistry-hub-server:latest`](https://hub.docker.com/r/oaklight/toolregistry-hub-server)

[中文](https://github.com/Oaklight/toolregistry-hub/blob/master/README_zh.md) | [English](https://github.com/Oaklight/toolregistry-hub/blob/master/README_en.md)

**新的 Docker Image**: `oaklight/toolregistry-hub-server:latest`

## 🔄 迁移命令更新

### 启动服务器（Python）

```bash
# 原有命令
python main.py --port 8000 --host 0.0.0.0 --mode <openapi|mcp>

# 新命令
toolregistry-server --host=0.0.0.0 --port=8000 --mode <openapi|mcp>
```

### Docker 启动（推荐）

**OpenAPI 模式 (默认):**

```bash
docker run -d -p 8000:8000 \
    --name toolregistry-hub-server \
   -e API_BEARER_TOKEN="your_token_here" \
   -e SEARXNG_URL="https://searxng.url" \
   -e BRAVE_API_KEY="your_brave_key" \
   -e TAVILY_API_KEY="your_tavily_key" \
   oaklight/toolregistry-hub-server:latest
```

**MCP Streamable HTTP 模式:**

```bash
docker run -d -p 8000:8000 \
    --name toolregistry-hub-mcp \
   -e API_BEARER_TOKEN="your_token_here" \
   -e SEARXNG_URL="https://searxng.url" \
   oaklight/toolregistry-hub-server:latest \
   toolregistry-server --host=0.0.0.0 --port=8000 --mode=mcp
```

**MCP SSE 模式:**

```bash
docker run -d -p 8000:8000 \
    --name toolregistry-hub-sse \
   -e API_BEARER_TOKEN="your_token_here" \
   -e SEARXNG_URL="https://searxng.url" \
   oaklight/toolregistry-hub-server:latest \
   toolregistry-server --host=0.0.0.0 --port=8000 --mode=mcp --mcp-transport=sse
```

或使用 docker compose:

```bash
# 下载配置
cp .env.sample .env  # 编辑 API 密钥
docker compose up -d
```

## 🔍 API 文档

服务器运行后，访问以下 URLs：

1. **OpenAPI 交互式文档 (Swagger UI)**
   浏览器访问：
   [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

2. **OpenAPI 文档 (ReDoc)**
   [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## ⚙️ 环境变量配置

### API_BEARER_TOKEN

- **用途**: 保护 API 端点的令牌
- **OpenAPI 模式**: 推荐设置以保护生产环境端点
- **MCP 模式**: 通常无认证运行 (`API_BEARER_TOKEN` 不设置)

### SEARXNG_URL

- **用途**: SearXNG 基础 URL，用于隐私保护的元搜索引擎
- **行为**:
  - 设置后启用 `/search_searxng` 工具
  - 未设置时，该端点返回 503 错误

### 新增环境变量

**BRAVE_API_KEY**: Brave 搜索 API 密钥  
**TAVILY_API_KEY**: Tavily 搜索 API 密钥

## 📋 模式切换

**OpenAPI 模式 (默认):**

```yaml
command:
  ["toolregistry-server", "--host=0.0.0.0", "--port=8000", "--mode=openapi"]
```

**MCP Streamable HTTP 模式:**

```yaml
command: ["toolregistry-server", "--host=0.0.0.0", "--port=8000", "--mode=mcp"]
```

**MCP SSE 模式:**

```yaml
command:
  [
    "toolregistry-server",
    "--host=0.0.0.0",
    "--port=8000",
    "--mode=mcp",
    "--mcp-transport=sse",
  ]
```

## 🆕 新增功能

- **更多搜索引擎**: Bing、Brave、SearXNG、Tavily
- **增强计算器**: 支持更多数学函数
- **文件操作**: 增强的文件读写和管理功能
- **思考工具**: 推理日志记录
- **待办列表**: 任务管理功能
- **网页抓取**: 内容提取工具

## 📚 完整文档

- **ReadTheDocs**: [https://toolregistry-hub.readthedocs.io/en/latest/](https://toolregistry-hub.readthedocs.io/en/latest/)
- **中文文档**: [https://toolregistry-hub.readthedocs.io/zh-cn/latest/](https://toolregistry-hub.readthedocs.io/zh-cn/latest/)

---

**迁移提示**: 将所有 `oaklight/openwebui-tool-server:latest` 替换为 `oaklight/toolregistry-hub-server:latest`
