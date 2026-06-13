# Docker 部署

本文档提供了使用 Docker 部署 ToolRegistry Hub 服务器的相关信息。

## 概述

ToolRegistry Hub 提供了 Docker 支持，便于部署和容器化。这种方法具有以下优势：

- 在不同平台上提供一致的环境
- 简化依赖管理
- 便于扩展和部署
- 与主机系统隔离

## Docker 文件

项目在 `docker/` 目录中包含几个与 Docker 相关的文件：

- [`Dockerfile`](../../docker/Dockerfile) - 容器定义
- [`compose.yaml`](../../docker/compose.yaml) - Docker Compose 配置（含 Caddy 网关）
- [`.env.sample`](../../docker/.env.sample) - 环境变量示例文件
- [`Caddyfile`](../../docker/Caddyfile) - Caddy 反向代理配置
- [`Makefile`](../../docker/Makefile) - 构建自动化和部署目标

## 快速开始

最快的入门方式是使用预构建的 Docker 镜像和 Docker Compose：

1. 基于示例创建 `.env` 文件
2. （可选）创建 `tools.jsonc` 文件以自定义加载的工具（参见下方[工具配置](#工具配置)）
3. 使用 Docker Compose 启动服务器：`docker-compose up -d`

服务器将在 `http://localhost:8000`（或 `GATEWAY_PORT` 指定的端口）可用。

## 环境变量

主要环境变量：

- `API_BEARER_TOKEN`：API 访问认证令牌
- `GATEWAY_PORT`：Caddy 网关外部端口（默认：8000）
- `IMAGE_TAG`：Docker 镜像标签（默认：`latest`）
- `SEARXNG_URL`：SearXNG 搜索引擎 URL
- `BRAVE_API_KEY`：Brave 搜索 API 密钥，支持逗号分隔多个密钥（轮询使用）
- `TAVILY_API_KEY`：Tavily 搜索 API 密钥，支持逗号分隔多个密钥（轮询使用）
- `JINA_API_KEY`：可选的 Jina Reader API 密钥，用于认证请求（逗号分隔支持多密钥轮转）
- `CDP_ENDPOINT`：可选的 CDP 兼容浏览器 WebSocket URL，用于自托管 SPA 渲染（例如 `ws://localhost:9222`）
- `WEBSEARCH_PRIORITY`：逗号分隔的引擎优先级顺序（auto 模式）
- `WEBSEARCH_PARALLEL_ENGINES`：逗号分隔的并行查询引擎（默认：`brightdata,brave`）

## 架构

### Caddy 网关

Docker Compose 服务栈使用 Caddy 反向代理作为统一入口。三个服务后端统一到单一外部端口：

| 路径 | 后端 | 说明 |
|------|------|------|
| `/mcp` | MCP streamable-http | 主要 MCP 端点 |
| `/sse` | MCP SSE | Server-Sent Events 传输 |
| `/docs` | OpenAPI | 交互式 API 文档 |
| `/openapi` | → `/docs` | 便捷重定向 |
| `/*` | OpenAPI | 默认后端 |

所有后端配置了 `flush_interval -1`，防止 SSE/流式传输缓冲。

后端服务使用 `expose` 而非 `ports`——不直接暴露到宿主机，仅通过 Caddy 网关访问。

## 服务器模式

使用 Caddy 网关时，所有模式通过单一端口同时可用。单独使用时：

### OpenAPI 模式（默认）

```bash
docker run -p 8000:8000 oaklight/toolregistry-hub-server:latest
```

### MCP 模式与可流式 HTTP 传输

```bash
docker run -p 8000:8000 oaklight/toolregistry-hub-server:latest toolregistry-hub mcp --transport=streamable-http --host=0.0.0.0 --port=8000
```

### MCP 模式与 SSE 传输

```bash
docker run -p 8000:8000 oaklight/toolregistry-hub-server:latest toolregistry-hub mcp --transport=sse --host=0.0.0.0 --port=8000
```

## 工具配置

您可以使用 `tools.jsonc` 配置文件自定义启动时加载的工具。Docker Compose 文件会自动将 `./tools.jsonc` 挂载到容器中。

### 设置步骤

1. 下载示例配置：

    ```bash
    # 通过 jsDelivr CDN（推荐，适用于无法直接访问 GitHub 的地区）
    curl -o tools.jsonc https://cdn.jsdelivr.net/gh/Oaklight/toolregistry-hub@master/tools.jsonc.example

    # 或直接从 GitHub 下载
    curl -o tools.jsonc https://raw.githubusercontent.com/Oaklight/toolregistry-hub/master/tools.jsonc.example

    # 确保容器用户（appuser, uid=10001）可以读取该文件
    chmod 644 tools.jsonc
    ```

2. 编辑 `tools.jsonc` 自定义配置：

    ```jsonc
    {
      // 拒绝列表模式：除列出的工具外，所有工具均启用
      "mode": "denylist",
      "disabled": [
        "file_ops"     // 安全敏感
      ]
    }
    ```

3. 重启容器：

    ```bash
    docker compose restart
    ```

### 配置选项

- **`mode`**：`"denylist"`（默认）或 `"allowlist"`
- **`disabled`**：要禁用的命名空间（拒绝列表模式）
- **`enabled`**：要启用的命名空间（允许列表模式）
- **`tools`**：自定义工具类列表（可选，覆盖内置默认值）

完整配置详情请参阅[服务器模式 - 工具配置](server.md#工具配置)文档。

!!! tip "无配置文件"
    如果没有 `tools.jsonc` 文件，服务器将使用默认设置加载所有可用工具。如果文件不存在，卷挂载将被忽略。

## 开发部署

Makefile 包含 `deploy-dev` 目标，用于构建并部署到远程服务器：

```bash
make deploy-dev SSH_TARGET=your-server
```

该目标会：

1. 从当前源码构建 Python wheel
2. 在本地构建 Docker 镜像
3. 通过 SSH 以 zstd 压缩传输镜像
4. 重启远程 Docker Compose 服务栈
5. 运行健康检查

## 生产部署建议

对于生产环境，请考虑以下几点：

1. **启用 HTTPS**：配置 Caddy 的域名以自动获取 TLS 证书
2. **设置监控**：实施健康检查和监控
3. **配置日志**：设置集中式日志记录
4. **使用 Docker Swarm 或 Kubernetes**：用于高可用性和扩展

## 故障排除

常见问题及解决方案：

1. **容器无法启动** - 使用 `docker logs toolregistry-hub-server` 检查日志
2. **无法连接到服务器** - 确保端口正确映射
3. **认证问题** - 验证 `API_BEARER_TOKEN` 是否正确设置
4. **搜索功能不工作** - 确认搜索服务的 API 密钥是否有效
