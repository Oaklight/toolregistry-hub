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
- [`compose.yaml`](../../docker/compose.yaml) - Production Docker Compose configuration
- [`compose.dev.yaml`](../../docker/compose.dev.yaml) - Development Docker Compose configuration
- [`.env.sample`](../../docker/.env.sample) - Sample environment variables file
- [`Makefile`](../../docker/Makefile) - Build automation for Docker images
- [`requirements.txt`](../../docker/requirements.txt) - Python dependencies for the container

## Quick Start

The quickest way to get started is using the pre-built Docker image with Docker Compose:

1. Create a `.env` file based on the sample
2. Start the server using Docker Compose: `docker-compose up -d`

The server will be available at `http://localhost:8000`.

## Environment Variables

Key environment variables:

- `API_BEARER_TOKEN`: Authentication token for API access
- `SEARXNG_URL`: URL for SearXNG search engine
- `BRAVE_API_KEY`: API key for Brave search, supporting comma separating multiple keys (round robin)
- `TAVILY_API_KEY`: API key for Tavily search, supporting comma separating multiple keys (round robin)

## Server Modes

The Docker container supports all server modes:

### OpenAPI Mode (Default)

```bash
docker run -p 8000:8000 oaklight/toolregistry-hub-server:latest
```

### MCP Mode with HTTP Transport

```bash
docker run -p 8000:8000 oaklight/toolregistry-hub-server:latest toolregistry-server --host=0.0.0.0 --port=8000 --mode=mcp
```

### MCP Mode with SSE Transport

```bash
docker run -p 8000:8000 oaklight/toolregistry-hub-server:latest toolregistry-server --host=0.0.0.0 --port=8000 --mode=mcp --mcp-transport=sse
```

## Production Deployment Recommendations

For production environments, consider the following:

1. **Use a Reverse Proxy**: Deploy Caddy, Nginx or Apache in front of the container
2. **Enable HTTPS**: Configure SSL/TLS for secure communication
3. **Set Up Monitoring**: Implement health checks and monitoring
4. **Configure Logging**: Set up centralized logging
5. **Use Docker Swarm or Kubernetes**: For high availability and scaling

## Troubleshooting

Common issues and solutions:

1. **Container fails to start** - Check logs with `docker logs toolregistry-hub-server`
2. **Cannot connect to the server** - Ensure ports are correctly mapped
3. **Authentication issues** - Verify `API_BEARER_TOKEN` is set correctly
4. **Search functionality not working** - Confirm API keys for search services are valid
