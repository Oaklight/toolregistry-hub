# Docker Deployment

This document provides information about deploying ToolRegistry Hub server using Docker.

## Overview

ToolRegistry Hub provides Docker support for easy deployment and containerization. This approach offers several advantages:

- Consistent environment across different platforms
- Simplified dependency management
- Easy scaling and deployment
- Isolation from the host system

## Docker Files

The project includes several Docker-related files in the `docker/` directory:

- [`Dockerfile`](../../docker/Dockerfile) - Container definition
- [`compose.yaml`](../../docker/compose.yaml) - Docker Compose configuration with Caddy gateway
- [`.env.sample`](../../docker/.env.sample) - Sample environment variables file
- [`Caddyfile`](../../docker/Caddyfile) - Caddy reverse proxy configuration
- [`Makefile`](../../docker/Makefile) - Build automation and deployment targets

## Quick Start

The quickest way to get started is using the pre-built Docker image with Docker Compose:

1. Create a `.env` file based on the sample
2. (Optional) Create a `tools.jsonc` file to customize which tools are loaded (see [Tool Configuration](#tool-configuration) below)
3. Start the server using Docker Compose: `docker-compose up -d`

The server will be available at `http://localhost:8000` (or the port set by `GATEWAY_PORT`).

## Environment Variables

Key environment variables:

- `API_BEARER_TOKEN`: Authentication token for API access
- `GATEWAY_PORT`: External port for the Caddy gateway (default: 8000)
- `IMAGE_TAG`: Docker image tag to use (default: `latest`)
- `SEARXNG_URL`: URL for SearXNG search engine
- `BRAVE_API_KEY`: API key for Brave search, supporting comma separating multiple keys (round robin)
- `TAVILY_API_KEY`: API key for Tavily search, supporting comma separating multiple keys (round robin)
- `JINA_API_KEY`: Optional Jina Reader API key for authenticated requests (comma-separated for multi-key rotation)
- `CDP_ENDPOINT`: Optional WebSocket URL of a CDP-compatible browser for self-hosted SPA rendering (e.g., `ws://localhost:9222`)
- `WEBSEARCH_PRIORITY`: Comma-separated engine priority order for auto mode
- `WEBSEARCH_PARALLEL_ENGINES`: Comma-separated engines to query in parallel mode (default: `brightdata,brave`)

## Architecture

### Caddy Gateway

The Docker Compose stack uses a Caddy reverse proxy as a unified entry point. All three service backends run behind a single external port:

| Path | Backend | Description |
|------|---------|-------------|
| `/mcp` | MCP streamable-http | Primary MCP endpoint |
| `/sse` | MCP SSE | Server-Sent Events transport |
| `/docs` | OpenAPI | Interactive API documentation |
| `/openapi` | → `/docs` | Convenience redirect |
| `/*` | OpenAPI | Default backend |

All backends are configured with `flush_interval -1` to prevent SSE/streaming buffering.

Backend services use `expose` instead of `ports` — they are not directly accessible from the host, only through the Caddy gateway.

## Server Modes

With the Caddy gateway, all modes are available simultaneously on a single port. For standalone use without the gateway:

### OpenAPI Mode (Default)

```bash
docker run -p 8000:8000 oaklight/toolregistry-hub-server:latest
```

### MCP Mode with Streamable HTTP Transport

```bash
docker run -p 8000:8000 oaklight/toolregistry-hub-server:latest toolregistry-hub mcp --transport=streamable-http --host=0.0.0.0 --port=8000
```

### MCP Mode with SSE Transport

```bash
docker run -p 8000:8000 oaklight/toolregistry-hub-server:latest toolregistry-hub mcp --transport=sse --host=0.0.0.0 --port=8000
```

## Tool Configuration

You can customize which tools are loaded at startup using a `tools.jsonc` configuration file. The Docker Compose files mount `./tools.jsonc` into the container automatically.

### Setup

1. Download the example configuration:

    ```bash
    # Via jsDelivr CDN (recommended, works in regions where GitHub is not directly accessible)
    curl -o tools.jsonc https://cdn.jsdelivr.net/gh/Oaklight/toolregistry-hub@master/tools.jsonc.example

    # Or directly from GitHub
    curl -o tools.jsonc https://raw.githubusercontent.com/Oaklight/toolregistry-hub/master/tools.jsonc.example

    # Ensure the file is readable by the container user (appuser, uid=10001)
    chmod 644 tools.jsonc
    ```

2. Edit `tools.jsonc` to customize your setup:

    ```jsonc
    {
      // Denylist mode: all tools enabled except those listed
      "mode": "denylist",
      "disabled": [
        "file_ops"     // security sensitive
      ]
    }
    ```

3. Restart the containers:

    ```bash
    docker compose restart
    ```

### Configuration Options

- **`mode`**: `"denylist"` (default) or `"allowlist"`
- **`disabled`**: Namespaces to disable (denylist mode)
- **`enabled`**: Namespaces to enable (allowlist mode)
- **`tools`**: Custom tool class list (optional, overrides built-in defaults)

For full configuration details, see the [Server Mode — Tool Configuration](server.md#tool-configuration) documentation.

!!! tip "No Configuration File"
    If no `tools.jsonc` file is present, the server loads all available tools with default settings. The volume mount will simply be ignored if the file doesn't exist.

## Development Deployment

The Makefile includes a `deploy-dev` target for building and deploying to a remote server:

```bash
make deploy-dev SSH_TARGET=your-server
```

This target:

1. Builds a Python wheel from the current source
2. Builds the Docker image locally
3. Transfers the image via zstd compression over SSH
4. Restarts the remote Docker Compose stack
5. Runs a health check against the deployed service

## Production Deployment Recommendations

For production environments, consider the following:

1. **Enable HTTPS**: Configure Caddy with your domain for automatic TLS
2. **Set Up Monitoring**: Implement health checks and monitoring
3. **Configure Logging**: Set up centralized logging
4. **Use Docker Swarm or Kubernetes**: For high availability and scaling

## Troubleshooting

Common issues and solutions:

1. **Container fails to start** - Check logs with `docker logs toolregistry-hub-server`
2. **Cannot connect to the server** - Ensure ports are correctly mapped
3. **Authentication issues** - Verify `API_BEARER_TOKEN` is set correctly
4. **Search functionality not working** - Confirm API keys for search services are valid
