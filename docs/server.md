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
# Install full server - OpenAPI + MCP (Python 3.10+)
pip install toolregistry-hub[server]

# Install OpenAPI server only
pip install toolregistry-hub[server_openapi]

# Install MCP server only (Python 3.10+)
pip install toolregistry-hub[server_mcp]
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

#### Bash Tool

- `POST /tools/bash/execute` - Execute a shell command (with safety validation)

#### Calculator Tools

- `POST /tools/calculator/help` - Get help information for specific calculator functions
- `POST /tools/calculator/list_allowed_fns` - Get list of allowed calculator functions
- `POST /tools/calculator/evaluate` - Evaluate mathematical expressions

#### Think Tool

- `POST /tools/think/think` - Process thinking requests

#### Web Tools

- `POST /tools/web/fetch/fetch_content` - Extract content from webpages
- `POST /tools/web/brave_search/search` - Search the web using Brave
- `POST /tools/web/searxng_search/search` - Search the web using SearXNG
- `POST /tools/web/tavily_search/search` - Search the web using Tavily
- `POST /tools/web/scrapeless_search/search` - Search the web using Scrapeless
- `POST /tools/web/brightdata_search/search` - Search the web using BrightData

#### Date Time Tools

- `POST /tools/datetime/now` - Get current time
- `POST /tools/datetime/convert_timezone` - Convert time zones

#### Todo List Tool

- `POST /tools/todolist/update` - Update todo list

#### Unit Converter Tool

- `POST /tools/unit_converter/help` - Get unit conversion help information
- `POST /tools/unit_converter/list_conversions` - List available unit conversions
- `POST /tools/unit_converter/convert` - Perform unit conversion

#### Filesystem Tools

- `POST /tools/filesystem/exists` - Check if a path exists
- `POST /tools/filesystem/is_file` - Check if a path is a file
- `POST /tools/filesystem/is_dir` - Check if a path is a directory
- `POST /tools/filesystem/list_dir` - List directory contents
- `POST /tools/filesystem/create_file` - Create a file
- `POST /tools/filesystem/create_dir` - Create a directory
- `POST /tools/filesystem/copy` - Copy a file or directory
- `POST /tools/filesystem/move` - Move a file or directory
- `POST /tools/filesystem/delete` - Delete a file or directory
- `POST /tools/filesystem/get_size` - Get file or directory size
- `POST /tools/filesystem/get_last_modified_time` - Get last modified time
- `POST /tools/filesystem/join_paths` - Join path components
- `POST /tools/filesystem/get_absolute_path` - Get absolute path

#### File Operations Tools

- `POST /tools/file_ops/edit` - Replace exact string in file (returns unified diff)
- `POST /tools/file_ops/read_file` - Read file content
- `POST /tools/file_ops/write_file` - Write content to a file
- `POST /tools/file_ops/append_file` - Append content to a file
- `POST /tools/file_ops/search_files` - Search for files matching a pattern
- `POST /tools/file_ops/make_diff` - Generate a diff between contents
- `POST /tools/file_ops/make_git_conflict` - Generate git conflict markers
- `POST /tools/file_ops/validate_path` - Validate a file path

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
curl -H "Authorization: Bearer token1" http://localhost:8000/tools/calculator/evaluate
curl -H "Authorization: Bearer token2" http://localhost:8000/tools/calculator/evaluate
curl -H "Authorization: Bearer token3" http://localhost:8000/tools/calculator/evaluate
```

## Examples

### Using curl to Call API

```bash
# Calculate mathematical expression
curl -X POST "http://localhost:8000/tools/calculator/evaluate" \
  -H "Content-Type: application/json" \
  -d '{"expression": "2 + 2 * 3"}'

# Get current time
curl -X POST "http://localhost:8000/tools/datetime/now" \
  -H "Content-Type: application/json" \
  -d '{}'

# Search using Brave
curl -X POST "http://localhost:8000/tools/web/brave_search/search" \
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
    f"{base_url}/tools/calculator/evaluate",
    json={"expression": "2 + 2 * 3"}
)
result = response.json()
print(f"Calculation result: {result['result']}")

# Get current time
response = requests.post(
    f"{base_url}/tools/datetime/now",
    json={}
)
current_time = response.json()
print(f"Current time: {current_time['current_time']}")

# Search using Brave
response = requests.post(
    f"{base_url}/tools/web/brave_search/search",
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

## Tool Configuration

The server supports a JSONC (JSON with Comments) configuration file to control which tools are loaded and how they behave at startup.

### Configuration File

Create a `tools.jsonc` file in the working directory, or specify a custom path:

```bash
# Auto-discovered from working directory
cp tools.jsonc.example tools.jsonc

# Or specify via CLI option
toolregistry-server --tools-config path/to/tools.jsonc

# Or specify via environment variable
TOOLS_CONFIG=path/to/tools.jsonc toolregistry-server
```

### Configuration Fields

#### Mode and Filtering

The `mode`, `disabled`, and `enabled` fields control which registered tools are active:

```jsonc
{
  // "denylist" (default): all tools enabled except those in "disabled"
  // "allowlist": only tools in "enabled" are active
  "mode": "denylist",

  // Denylist mode — disable specific tools by namespace
  "disabled": [
    "filesystem",
    "file_ops"
  ]

  // Allowlist mode — enable only specific tools
  // "enabled": ["calculator", "datetime", "unit_converter"]
}
```

- **`mode`**: Either `"denylist"` (default) or `"allowlist"`
- **`disabled`**: List of tool namespaces to disable (used in denylist mode)
- **`enabled`**: List of tool namespaces to enable (used in allowlist mode)

#### Custom Tool Registration List

The `tools` field allows you to customize which tool classes are registered at startup. Each entry specifies a Python class import path and a namespace:

```jsonc
{
  "tools": [
    {"class": "toolregistry_hub.calculator.Calculator", "namespace": "calculator"},
    {"class": "toolregistry_hub.datetime_utils.DateTime", "namespace": "datetime"},
    // ... add or remove tools as needed
  ],
  "mode": "denylist",
  "disabled": ["filesystem", "file_ops"]
}
```

- **`class`**: Fully qualified Python class path (e.g., `toolregistry_hub.calculator.Calculator`)
- **`namespace`**: Namespace for the tool in the registry (e.g., `calculator`, `web/brave_search`)

If the `tools` field is omitted, the server uses the built-in default tool list (all available tools). This field is useful when you want to:

- Add custom tool classes without modifying source code
- Remove tools you don't need to reduce the attack surface
- Reorder tools for specific use cases

## Environment Variables

You can set the following environment variables to configure the server:

### Authentication Related

- `API_BEARER_TOKEN` - Bearer Token for API authentication (supports single token or comma-separated multiple tokens)
- `API_BEARER_TOKENS_FILE` - Path to token file, with one token per line

### Tool Environment Variables

The following environment variables are used by specific tools. Tools with missing required environment variables are automatically disabled at startup.

| Environment Variable | Required By | Description |
|---------------------|-------------|-------------|
| `BRAVE_API_KEY` | Brave Search | Brave Search API key ([get one](https://api.search.brave.com/)) |
| `TAVILY_API_KEY` | Tavily Search | Tavily Search API key ([get one](https://tavily.com/)) |
| `SEARXNG_URL` | SearXNG Search | SearXNG instance URL (e.g., `http://localhost:8080`) |
| `BRIGHTDATA_API_KEY` | BrightData Search | Bright Data API key ([get one](https://brightdata.com/)) |
| `SCRAPELESS_API_KEY` | Scrapeless Search | Scrapeless API key ([get one](https://scrapeless.com/)) |

!!! note "Auto-Disable Behavior"
    When the server starts, it checks each tool's required environment variables. Tools with missing variables are automatically registered but disabled. They will not appear in the tool list returned to clients. You can enable them later by setting the required environment variables and restarting the server.

## Troubleshooting

### Common Issues

1. **Dependency Installation Failed**

   - Ensure your Python version meets requirements
   - Both OpenAPI and MCP modes require Python 3.10+

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
    response = client.post("/tools/calculator/evaluate", json={"expression": "2 + 2"})
    assert response.status_code == 200
    assert response.json()["result"] == 4
```

## Deployment

For Docker deployment and production environment setup, please refer to the [Docker Deployment](docker.md) documentation.
