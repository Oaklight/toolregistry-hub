# 服务器模式

ToolRegistry Hub 提供了服务器模式，允许您通过 REST API 或 MCP (Model Context Protocol) 访问所有工具功能。

## 概述

服务器模式提供两种运行方式：

1. **OpenAPI 模式** - 基于 FastAPI 的 REST API 服务器
2. **MCP 模式** - 基于 Model Context Protocol 的服务器

这两种模式都自动将所有可用的工具暴露为 API 端点，便于远程调用和集成。

## 安装

根据您的需求安装相应的服务器依赖：

```bash
# 仅安装 OpenAPI 服务器 (Python 3.8+)
pip install toolregistry-hub[server_openapi]

# 仅安装 MCP 服务器 (Python 3.10+)
pip install toolregistry-hub[server_mcp]

# 安装所有服务器模式 (Python 3.10+)
pip install toolregistry-hub[server]
```

## 启动服务器

### 命令行启动

安装完成后，您可以使用 `toolregistry-server` 命令启动服务器：

```bash
# 启动 OpenAPI 服务器 (默认模式)
toolregistry-server --mode openapi --host 0.0.0.0 --port 8000

# 启动 MCP 服务器
toolregistry-server --mode mcp --host 0.0.0.0 --port 8000

# 启动 MCP 服务器 (stdio 模式)
toolregistry-server --mode mcp --mcp-transport stdio
```

### 参数说明

- `--host`: 服务器绑定的主机地址 (默认: 0.0.0.0)
- `--port`: 服务器绑定的端口 (默认: 8000)
- `--mode`: 服务器模式，可选值为 `openapi` 或 `mcp` (默认: openapi)
- `--mcp-transport`: MCP 传输模式，可选值为 `streamable-http`、`sse` 或 `stdio` (默认: streamable-http)

### 程序内启动

您也可以在 Python 代码中直接启动服务器：

```python
# 启动 OpenAPI 服务器
from toolregistry_hub.server.server_openapi import app
import uvicorn

uvicorn.run(app, host="0.0.0.0", port=8000)

# 启动 MCP 服务器
from toolregistry_hub.server.server_mcp import mcp_app

# HTTP 传输模式
mcp_app.run(transport="streamable-http", host="0.0.0.0", port=8000)

# stdio 传输模式
mcp_app.run()
```

## API 端点

### OpenAPI 模式

在 OpenAPI 模式下，所有工具都作为 REST API 端点提供。启动服务器后，您可以通过以下地址访问：

- 服务器地址: `http://localhost:8000`
- API 文档: `http://localhost:8000/docs`
- OpenAPI 规范: `http://localhost:8000/openapi.json`

### 主要 API 端点

#### 计算器工具

- `POST /calc/help` - 获取特定计算器函数的帮助信息
- `POST /calc/allowed_fns` - 获取允许的计算器函数列表
- `POST /calc/evaluate` - 计算数学表达式

#### 思考工具

- `POST /think` - 处理思考请求

#### 网络搜索工具

- `POST /web/search_bing` - 使用 Bing 进行网络搜索
- `POST /web/search_brave` - 使用 Brave 进行网络搜索
- `POST /web/search_searxng` - 使用 SearXNG 进行网络搜索
- `POST /web/search_tavily` - 使用 Tavily 进行网络搜索

#### 日期时间工具

- `POST /time/now` - 获取当前时间
- `POST /time/convert` - 时区转换

#### 网页获取工具

- `POST /fetch_webpage` - 提取网页内容

## 认证

服务器支持基于 Bearer Token 的认证。您可以通过设置 `API_BEARER_TOKEN` 环境变量来启用认证：

```bash
export API_BEARER_TOKEN="your-secret-token"
```

设置后，所有 API 请求都需要在 Header 中包含有效的 Bearer Token：

```http
Authorization: Bearer your-secret-token
```

如果未设置 `API_BEARER_TOKEN` 环境变量，则不需要认证。

## 示例

### 使用 curl 调用 API

```bash
# 计算数学表达式
curl -X POST "http://localhost:8000/calc/evaluate" \
  -H "Content-Type: application/json" \
  -d '{"expression": "2 + 2 * 3"}'

# 获取当前时间
curl -X POST "http://localhost:8000/time/now" \
  -H "Content-Type: application/json" \
  -d '{}'

# 使用 Bing 搜索
curl -X POST "http://localhost:8000/web/search_bing" \
  -H "Content-Type: application/json" \
  -d '{"query": "python programming", "max_results": 5}'
```

### 使用 Python 调用 API

```python
import requests
import json

# API 基础 URL
base_url = "http://localhost:8000"

# 计算数学表达式
response = requests.post(
    f"{base_url}/calc/evaluate",
    json={"expression": "2 + 2 * 3"}
)
result = response.json()
print(f"计算结果: {result['result']}")

# 获取当前时间
response = requests.post(
    f"{base_url}/time/now",
    json={}
)
current_time = response.json()
print(f"当前时间: {current_time['current_time']}")

# 使用 Bing 搜索
response = requests.post(
    f"{base_url}/web/search_bing",
    json={"query": "python programming", "max_results": 5}
)
search_results = response.json()
print(f"搜索结果: {json.dumps(search_results, indent=2)}")
```

## 错误处理

服务器使用标准的 HTTP 状态码来表示请求的结果：

- `200` - 请求成功
- `400` - 请求参数错误
- `401` - 认证失败
- `500` - 服务器内部错误

错误响应格式如下：

```json
{
  "detail": "错误描述信息"
}
```

## 环境变量

除了 `API_BEARER_TOKEN` 外，您还可以设置其他环境变量来配置服务器：

- `API_BEARER_TOKEN` - Bearer Token，用于 API 认证
- 其他工具特定的环境变量（如搜索 API 密钥等）

## 故障排除

### 常见问题

1. **依赖安装失败**

   - 确保您的 Python 版本符合要求
   - OpenAPI 模式需要 Python 3.8+
   - MCP 模式需要 Python 3.10+

2. **端口被占用**

   - 使用 `--port` 参数指定其他端口
   - 或者停止占用该端口的其他服务

3. **搜索功能不可用**

   - 检查是否设置了相应的 API 密钥
   - 查看服务器日志获取详细错误信息

4. **认证失败**
   - 检查 `API_BEARER_TOKEN` 环境变量是否正确设置
   - 确保请求 Header 中包含正确的 Bearer Token

### 日志

服务器使用 `loguru` 进行日志记录。启动服务器后，您可以在控制台看到详细的日志信息，包括：

- 服务器启动信息
- 路由注册信息
- 请求处理日志
- 错误信息

## 开发和扩展

### 添加新的 API 端点

要添加新的 API 端点，您可以在 `src/toolregistry_hub/server/routes/` 目录下创建新的路由模块。路由模块应该：

1. 定义请求和响应模型
2. 创建 APIRouter 实例
3. 实现路由处理函数
4. 使用 `get_security_dependencies()` 获取认证依赖

示例路由模块：

```python
from fastapi import APIRouter
from pydantic import BaseModel, Field
from ..auth import get_security_dependencies

# 请求模型
class MyRequest(BaseModel):
    param: str = Field(..., description="参数描述")

# 响应模型
class MyResponse(BaseModel):
    result: str = Field(..., description="结果描述")

# 创建路由
router = APIRouter(prefix="/mytool", tags=["mytool"])
security_deps = get_security_dependencies()

@router.post("/endpoint", dependencies=security_deps, response_model=MyResponse)
def my_endpoint(data: MyRequest) -> MyResponse:
    # 实现您的逻辑
    return MyResponse(result=f"处理结果: {data.param}")
```

### 测试

您可以使用 `pytest` 和 `httpx` 来测试 API 端点：

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

## 部署

### Docker 部署

您可以使用 Docker 来部署服务器：

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["toolregistry-server", "--mode", "openapi", "--host", "0.0.0.0", "--port", "8000"]
```

### 生产环境

在生产环境中，建议使用：

1. **WSGI 服务器** - 如 Gunicorn 或 uWSGI
2. **反向代理** - 如 Nginx 或 Apache
3. **负载均衡** - 如果需要高可用性
4. **监控和日志** - 如 Prometheus 和 ELK Stack

示例 Gunicorn 启动命令：

```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker toolregistry_hub.server.server_openapi:app
```
