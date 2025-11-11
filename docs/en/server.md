# Server Mode

ToolRegistry Hub provides a server mode that allows you to access all tool functionalities through REST API or MCP (Model Context Protocol).

## Overview

The server mode offers two running methods:

1. **OpenAPI Mode** - REST API server based on FastAPI
2. **MCP Mode** - Server based on Model Context Protocol

Both modes automatically expose all available tools as API endpoints, facilitating remote calls and integration.

## Installation

Install the appropriate server dependencies based on your needs:

```bash
# Install OpenAPI server only (Python 3.8+)
pip install toolregistry-hub[server_openapi]

# Install MCP server only (Python 3.10+)
pip install toolregistry-hub[server_mcp]

# Install all server modes (Python 3.10+)
pip install toolregistry-hub[server]
```

## Starting the Server

### Command Line Startup

After installation, you can use the `toolregistry-server` command to start the server:

```bash
# Start OpenAPI server (default mode)
toolregistry-server --mode openapi --host 0.0.0.0 --port 8000

# Start MCP server
toolregistry-server --mode mcp --host 0.0.0.0 --port 8000

# Start MCP server (stdio mode)
toolregistry-server --mode mcp --mcp-transport stdio
```

### Parameter Description

- `--host`: Host address to bind the server to (default: 0.0.0.0)
- `--port`: Port to bind the server to (default: 8000)
- `--mode`: Server mode, options are `openapi` or `mcp` (default: openapi)
- `--mcp-transport`: MCP transport mode, options are `streamable-http`, `sse`, or `stdio` (default: streamable-http)

### In-Code Startup

You can also start the server directly in Python code:

```python
# Start OpenAPI server
from toolregistry_hub.server.server_openapi import app
import uvicorn

uvicorn.run(app, host="0.0.0.0", port=8000)

# Start MCP server
from toolregistry_hub.server.server_mcp import mcp_app

# HTTP transport mode
mcp_app.run(transport="streamable-http", host="0.0.0.0", port=8000)

# stdio transport mode
mcp_app.run()
```

## API Endpoints

### OpenAPI Mode

In OpenAPI mode, all tools are provided as REST API endpoints. After starting the server, you can access them at:

- Server address: `http://localhost:8000`
- API documentation: `http://localhost:8000/docs`
- OpenAPI specification: `http://localhost:8000/openapi.json`

### Main API Endpoints

#### Calculator Tools

- `POST /calc/help` - Get help information for specific calculator functions
- `POST /calc/allowed_fns` - Get list of allowed calculator functions
- `POST /calc/evaluate` - Evaluate mathematical expressions

#### Think Tool

- `POST /think` - Process thinking requests

#### Web Search Tools

- `POST /web/search_bing` - Search the web using Bing
- `POST /web/search_brave` - Search the web using Brave
- `POST /web/search_searxng` - Search the web using SearXNG
- `POST /web/search_tavily` - Search the web using Tavily

#### Date Time Tools

- `POST /time/now` - Get current time
- `POST /time/convert` - Convert time zones

#### Web Fetch Tool

- `POST /fetch_webpage` - Extract content from webpages

## Authentication

The server supports Bearer Token-based authentication with multiple configuration options:

### Configuration Methods

#### Method 1: Single Token (Backward Compatible)

```bash
export API_BEARER_TOKEN="your-secret-token"
```

#### Method 2: Multiple Tokens (Comma-Separated)

```bash
export API_BEARER_TOKEN="token1,token2,token3,token4"
```

#### Method 3: Token File (One Token Per Line)

```bash
# Create token file
cat > /path/to/tokens.txt << EOF
6Yd9Y7xB4FDUgFVZ3oJh7NEKkqV97o8z9Tup75fZWinJw
8Af2X9cD6GEVhGWA5pKi9OFLlrW89p0a1Vuq87gAXjoKy
4Hg5Z8eF9HIWiHXB6qLj0PGMmsX90q1b2Wvr98hBYkpLz
EOF

# Set environment variable to point to file
export API_BEARER_TOKENS_FILE="/path/to/tokens.txt"
```

### Usage

After configuration, all API requests need to include a valid Bearer Token in the Header:

```http
Authorization: Bearer your-valid-token
```

If no token environment variables are set, no authentication is required.

### Multi-User Scenarios

Multiple token configuration is particularly suitable for multi-user scenarios, allowing you to distribute different tokens to different users:

```bash
# Different users using different tokens
curl -H "Authorization: Bearer token1" http://localhost:8000/calc/evaluate
curl -H "Authorization: Bearer token2" http://localhost:8000/calc/evaluate
curl -H "Authorization: Bearer token3" http://localhost:8000/calc/evaluate
```

## Examples

### Using curl to Call API

```bash
# Calculate mathematical expression
curl -X POST "http://localhost:8000/calc/evaluate" \
  -H "Content-Type: application/json" \
  -d '{"expression": "2 + 2 * 3"}'

# Get current time
curl -X POST "http://localhost:8000/time/now" \
  -H "Content-Type: application/json" \
  -d '{}'

# Search using Bing
curl -X POST "http://localhost:8000/web/search_bing" \
  -H "Content-Type: application/json" \
  -d '{"query": "python programming", "max_results": 5}'
```

### Using Python to Call API

```python
import requests
import json

# API base URL
base_url = "http://localhost:8000"

# Calculate mathematical expression
response = requests.post(
    f"{base_url}/calc/evaluate",
    json={"expression": "2 + 2 * 3"}
)
result = response.json()
print(f"Calculation result: {result['result']}")

# Get current time
response = requests.post(
    f"{base_url}/time/now",
    json={}
)
current_time = response.json()
print(f"Current time: {current_time['current_time']}")

# Search using Bing
response = requests.post(
    f"{base_url}/web/search_bing",
    json={"query": "python programming", "max_results": 5}
)
search_results = response.json()
print(f"Search results: {json.dumps(search_results, indent=2)}")
```

## Error Handling

The server uses standard HTTP status codes to indicate request results:

- `200` - Request successful
- `400` - Request parameter error
- `401` - Authentication failed
- `500` - Server internal error

Error response format is as follows:

```json
{
  "detail": "Error description message"
}
```

## Environment Variables

You can set the following environment variables to configure the server:

### Authentication Related

- `API_BEARER_TOKEN` - Bearer Token for API authentication (supports single token or comma-separated multiple tokens)
- `API_BEARER_TOKENS_FILE` - Path to token file, with one token per line

### Other Configuration

- Other tool-specific environment variables (such as search API keys, etc.)

## Troubleshooting

### Common Issues

1. **Dependency Installation Failed**

   - Ensure your Python version meets requirements
   - OpenAPI mode requires Python 3.8+
   - MCP mode requires Python 3.10+

2. **Port Already in Use**

   - Use the `--port` parameter to specify another port
   - Or stop other services occupying that port

3. **Search Function Not Available**

   - Check if corresponding API keys are set
   - View server logs for detailed error information

4. **Authentication Failed**
   - Check if `API_BEARER_TOKEN` environment variable is set correctly
   - Ensure the request Header includes the correct Bearer Token

### Logging

The server uses `loguru` for logging. After starting the server, you can see detailed log information in the console, including:

- Server startup information
- Route registration information
- Request processing logs
- Error information

## Development and Extension

### Adding New API Endpoints

To add new API endpoints, you can create new route modules in the `src/toolregistry_hub/server/routes/` directory. Route modules should:

1. Define request and response models
2. Create APIRouter instances
3. Implement route handler functions
4. Use `get_security_dependencies()` to get authentication dependencies

Example route module:

```python
from fastapi import APIRouter
from pydantic import BaseModel, Field
from ..auth import get_security_dependencies

# Request model
class MyRequest(BaseModel):
    param: str = Field(..., description="Parameter description")

# Response model
class MyResponse(BaseModel):
    result: str = Field(..., description="Result description")

# Create router
router = APIRouter(prefix="/mytool", tags=["mytool"])
security_deps = get_security_dependencies()

@router.post("/endpoint", dependencies=security_deps, response_model=MyResponse)
def my_endpoint(data: MyRequest) -> MyResponse:
    # Implement your logic
    return MyResponse(result=f"Processing result: {data.param}")
```

### Testing

You can use `pytest` and `httpx` to test API endpoints:

```python
import pytest
from fastapi.testclient import TestClient
from toolregistry_hub.server.server_openapi import app

client = TestClient(app)

def test_calc_evaluate():
    response = client.post("/calc/evaluate", json={"expression": "2 + 2"})
    assert response.status_code == 200
    assert response.json()["result"] == 4
```

## Deployment

For Docker deployment and production environment setup, please refer to the [Docker Deployment](docker.md) documentation.
