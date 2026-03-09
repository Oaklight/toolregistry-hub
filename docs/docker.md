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
- [`compose.yaml`](../../docker/compose.yaml) - 生产环境 Docker Compose 配置
- [`compose.dev.yaml`](../../docker/compose.dev.yaml) - 开发环境 Docker Compose 配置
- [`.env.sample`](../../docker/.env.sample) - 环境变量示例文件
- [`Makefile`](../../docker/Makefile) - Docker 镜像构建自动化

## 快速开始

最快的入门方式是使用预构建的 Docker 镜像和 Docker Compose：

1. 基于示例创建 `.env` 文件
2. （可选）创建 `tools.jsonc` 文件以自定义加载的工具（参见下方[工具配置](#工具配置)）
3. 使用 Docker Compose 启动服务器：`docker-compose up -d`

服务器将在 `http://localhost:8000` 可用。

## 环境变量

主要环境变量：

- `API_BEARER_TOKEN`：API 访问认证令牌
- `SEARXNG_URL`：SearXNG 搜索引擎 URL
- `BRAVE_API_KEY`：Brave 搜索 API 密钥，支持逗号分隔多个密钥（轮询使用）
- `TAVILY_API_KEY`：Tavily 搜索 API 密钥，支持逗号分隔多个密钥（轮询使用）

## 服务器模式

Docker 容器支持所有服务器模式：

### OpenAPI 模式（默认）

```bash
docker run -p 8000:8000 oaklight/toolregistry-hub-server:latest
```

### MCP 模式与 HTTP 传输

```bash
docker run -p 8000:8000 oaklight/toolregistry-hub-server:latest toolregistry-server --host=0.0.0.0 --port=8000 --mode=mcp
```

### MCP 模式与 SSE 传输

```bash
docker run -p 8000:8000 oaklight/toolregistry-hub-server:latest toolregistry-server --host=0.0.0.0 --port=8000 --mode=mcp --mcp-transport=sse
```

## 工具配置

您可以使用 `tools.jsonc` 配置文件自定义启动时加载的工具。Docker Compose 文件会自动将 `./tools.jsonc` 挂载到容器中。

### 设置步骤

1. 复制示例配置：

    ```bash
    cd docker/
    cp ../tools.jsonc.example tools.jsonc
    ```

2. 编辑 `tools.jsonc` 自定义配置：

    ```jsonc
    {
      // 拒绝列表模式：除列出的工具外，所有工具均启用
      "mode": "denylist",
      "disabled": [
        "filesystem",  // 安全敏感
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

## 生产部署建议

对于生产环境，请考虑以下几点：

1. **使用反向代理**：在容器前部署 Caddy、Nginx 或 Apache
2. **启用 HTTPS**：配置 SSL/TLS 以确保安全通信
3. **设置监控**：实施健康检查和监控
4. **配置日志**：设置集中式日志记录
5. **使用 Docker Swarm 或 Kubernetes**：用于高可用性和扩展

## 故障排除

常见问题及解决方案：

1. **容器无法启动** - 使用 `docker logs toolregistry-hub-server` 检查日志
2. **无法连接到服务器** - 确保端口正确映射
3. **认证问题** - 验证 `API_BEARER_TOKEN` 是否正确设置
4. **搜索功能不工作** - 确认搜索服务的 API 密钥是否有效
