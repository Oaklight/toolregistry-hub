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
# 安装完整服务器 - OpenAPI + MCP (Python 3.10+)
pip install toolregistry-hub[server]

# 仅安装 OpenAPI 服务器
pip install toolregistry-hub[server_openapi]

# 仅安装 MCP 服务器 (Python 3.10+)
pip install toolregistry-hub[server_mcp]
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
- `--tool-discovery` / `--no-tool-discovery`: 启用或禁用工具发现与渐进式披露（默认：启用）。启用后，低频工具标记为延迟加载，可通过 `discover_tools` 工具发现
- `--think-augment` / `--no-think-augment`: 启用或禁用思维增强工具调用（默认：启用）。启用后，向工具 schema 注入 `thought` 属性用于链式思维推理

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

#### Bash 工具

- `POST /tools/bash/execute` - 执行 Shell 命令（带安全验证）

#### 计算器工具

- `POST /tools/calculator/help` - 获取特定计算器函数的帮助信息
- `POST /tools/calculator/list_allowed_fns` - 获取允许的计算器函数列表
- `POST /tools/calculator/evaluate` - 计算数学表达式

#### 思考工具

- `POST /tools/think/think` - 处理思考请求

#### 网络工具

- `POST /tools/web/fetch/fetch_content` - 提取网页内容
- `POST /tools/web/websearch/search` - 统一网络搜索，支持引擎选择器（auto、brave、tavily 等）
- `POST /tools/web/websearch/list_engines` - 列出可用搜索引擎及其配置状态
- `POST /tools/web/brave_search/search` - 使用 Brave 进行网络搜索 *（延迟加载）*
- `POST /tools/web/searxng_search/search` - 使用 SearXNG 进行网络搜索 *（延迟加载）*
- `POST /tools/web/tavily_search/search` - 使用 Tavily 进行网络搜索 *（延迟加载）*
- `POST /tools/web/scrapeless_search/search` - 使用 Scrapeless 进行网络搜索 *（延迟加载）*
- `POST /tools/web/brightdata_search/search` - 使用 BrightData 进行网络搜索 *（延迟加载）*
- `POST /tools/web/serper_search/search` - 使用 Serper 进行网络搜索 *（延迟加载）*

#### 日期时间工具

- `POST /tools/datetime/now` - 获取当前时间
- `POST /tools/datetime/convert_timezone` - 时区转换

#### 待办事项工具

- `POST /tools/todolist/update` - 更新待办事项列表

#### 定时任务工具

- `POST /tools/cron/create` - 创建定时或一次性定时任务 *（延迟加载）*
- `POST /tools/cron/delete` - 取消已计划的任务 *（延迟加载）*
- `POST /tools/cron/list` - 列出所有定时任务 *（延迟加载）*

#### 单位转换工具

- `POST /tools/unit_converter/help` - 获取单位转换帮助信息
- `POST /tools/unit_converter/list_conversions` - 列出可用的单位转换
- `POST /tools/unit_converter/convert` - 执行单位转换

#### 文件读取工具

- `POST /tools/reader/read` - 读取文本文件（带行号和分页）
- `POST /tools/reader/read_pdf` - 读取 PDF 文件并提取文本
- `POST /tools/reader/read_notebook` - 读取 Jupyter Notebook 单元格和输出

#### 文件搜索工具

- `POST /tools/fs/file_search/glob` - 按 glob 模式查找文件
- `POST /tools/fs/file_search/grep` - 使用正则表达式搜索文件内容
- `POST /tools/fs/file_search/tree` - 显示目录树结构

#### 路径信息工具

- `POST /tools/fs/path_info/info` - 获取文件/目录元数据（类型、大小、权限、修改时间）

#### 文件操作工具

- `POST /tools/file_ops/edit` - 精确字符串替换（返回 unified diff）
- `POST /tools/file_ops/read_file` - 读取文件内容
- `POST /tools/file_ops/write_file` - 写入文件内容
- `POST /tools/file_ops/append_file` - 追加文件内容
- `POST /tools/file_ops/search_files` - 搜索匹配模式的文件
- `POST /tools/file_ops/make_diff` - 生成内容差异
- `POST /tools/file_ops/make_git_conflict` - 生成 git 冲突标记
- `POST /tools/file_ops/validate_path` - 验证文件路径

## 认证

服务器支持基于 Bearer Token 的认证。支持多种令牌配置方式：

### 配置方式

#### 方式 1：单个令牌（向后兼容）

```bash
export API_BEARER_TOKEN="your-secret-token"
```

#### 方式 2：多个令牌（逗号分隔）

```bash
export API_BEARER_TOKEN="token1,token2,token3,token4"
```

#### 方式 3：令牌文件（一行一个令牌）

```bash
# 创建令牌文件
cat > /path/to/tokens.txt << EOF
6Yd9Y7xB4FDUgFVZ3oJh7NEKkqV97o8z9Tup75fZWinJw
8Af2X9cD6GEVhGWA5pKi9OFLlrW89p0a1Vuq87gAXjoKy
4Hg5Z8eF9HIWiHXB6qLj0PGMmsX90q1b2Wvr98hBYkpLz
EOF

# 设置环境变量指向文件
export API_BEARER_TOKENS_FILE="/path/to/tokens.txt"
```

### 使用方式

设置后，所有 API 请求都需要在 Header 中包含有效的 Bearer Token：

```http
Authorization: Bearer your-valid-token
```

如果未设置任何令牌环境变量，则不需要认证。

### 多用户场景

多令牌配置特别适合多用户场景，您可以为不同用户分发不同的令牌：

```bash
# 为不同用户配置不同令牌
curl -H "Authorization: Bearer token1" http://localhost:8000/tools/calculator/evaluate
curl -H "Authorization: Bearer token2" http://localhost:8000/tools/calculator/evaluate
curl -H "Authorization: Bearer token3" http://localhost:8000/tools/calculator/evaluate
```

## 示例

### 使用 curl 调用 API

```bash
# 计算数学表达式
curl -X POST "http://localhost:8000/tools/calculator/evaluate" \
  -H "Content-Type: application/json" \
  -d '{"expression": "2 + 2 * 3"}'

# 获取当前时间
curl -X POST "http://localhost:8000/tools/datetime/now" \
  -H "Content-Type: application/json" \
  -d '{}'

# 使用 Brave 搜索
curl -X POST "http://localhost:8000/tools/web/brave_search/search" \
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
    f"{base_url}/tools/calculator/evaluate",
    json={"expression": "2 + 2 * 3"}
)
result = response.json()
print(f"计算结果: {result['result']}")

# 获取当前时间
response = requests.post(
    f"{base_url}/tools/datetime/now",
    json={}
)
current_time = response.json()
print(f"当前时间: {current_time['current_time']}")

# 使用 Brave 搜索
response = requests.post(
    f"{base_url}/tools/web/brave_search/search",
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

## 工具配置

服务器支持 JSONC（带注释的 JSON）配置文件，用于控制启动时加载哪些工具以及它们的行为。

### 配置文件

在工作目录中创建 `tools.jsonc` 文件，或指定自定义路径：

```bash
# 从工作目录自动发现
cp tools.jsonc.example tools.jsonc

# 或通过 CLI 选项指定
toolregistry-server --tools-config path/to/tools.jsonc

# 或通过环境变量指定
TOOLS_CONFIG=path/to/tools.jsonc toolregistry-server
```

### 配置字段

#### 模式与过滤

`mode`、`disabled` 和 `enabled` 字段控制哪些已注册的工具处于活动状态：

```jsonc
{
  // "denylist"（默认）：启用所有工具，除了 "disabled" 中列出的
  // "allowlist"：仅启用 "enabled" 中列出的工具
  "mode": "denylist",

  // 拒绝列表模式 — 按命名空间禁用特定工具
  "disabled": [
    "file_ops"
  ]

  // 允许列表模式 — 仅启用特定工具
  // "enabled": ["calculator", "datetime", "unit_converter"]
}
```

- **`mode`**：`"denylist"`（默认）或 `"allowlist"`
- **`disabled`**：要禁用的工具命名空间列表（在 denylist 模式下使用）
- **`enabled`**：要启用的工具命名空间列表（在 allowlist 模式下使用）

#### 自定义工具注册列表

`tools` 字段允许你自定义启动时注册哪些工具类。每个条目指定一个 Python 类的导入路径和命名空间：

```jsonc
{
  "tools": [
    {"class": "toolregistry_hub.calculator.Calculator", "namespace": "calculator"},
    {"class": "toolregistry_hub.datetime_utils.DateTime", "namespace": "datetime"},
    // ... 根据需要添加或删除工具
  ],
  "mode": "denylist",
  "disabled": ["file_ops"]
}
```

- **`class`**：Python 类的完整导入路径（例如 `toolregistry_hub.calculator.Calculator`）
- **`namespace`**：工具在注册表中的命名空间（例如 `calculator`、`web/brave_search`）

如果省略 `tools` 字段，服务器将使用内置的默认工具列表（所有可用工具）。此字段适用于以下场景：

- 添加自定义工具类而无需修改源代码
- 移除不需要的工具以减少攻击面
- 为特定用例重新排列工具顺序

## 环境变量

您可以设置以下环境变量来配置服务器：

### 认证相关

- `API_BEARER_TOKEN` - Bearer Token，用于 API 认证（支持单个令牌或逗号分隔的多个令牌）
- `API_BEARER_TOKENS_FILE` - 令牌文件路径，文件中每行一个令牌

### 工具环境变量

以下环境变量由特定工具使用。缺少所需环境变量的工具在启动时会被自动禁用。

| 环境变量 | 使用者 | 描述 |
|---------|--------|------|
| `BRAVE_API_KEY` | Brave 搜索 | Brave Search API 密钥（[获取](https://api.search.brave.com/)） |
| `TAVILY_API_KEY` | Tavily 搜索 | Tavily Search API 密钥（[获取](https://tavily.com/)） |
| `SEARXNG_URL` | SearXNG 搜索 | SearXNG 实例 URL（如 `http://localhost:8080`） |
| `SEARXNG_API_KEY` | SearXNG 搜索 | 可选的 API 密钥，用于受保护的 SearXNG 实例（作为 `X-API-Key` 请求头发送） |
| `BRIGHTDATA_API_KEY` | BrightData 搜索 | Bright Data API 密钥（[获取](https://brightdata.com/)） |
| `SCRAPELESS_API_KEY` | Scrapeless 搜索 | Scrapeless API 密钥（[获取](https://scrapeless.com/)） |
| `SERPER_API_KEY` | Serper 搜索 | Serper API 密钥（[获取](https://serper.dev/)） |
| `JINA_API_KEY` | Fetch（Jina Reader） | 可选的 Jina Reader API 密钥，用于认证请求（逗号分隔支持多密钥轮转） |
| `WEBSEARCH_PRIORITY` | 统一网络搜索 | 自动模式下的引擎优先级（逗号分隔，如 `searxng,brave,tavily`） |

!!! note "自动禁用行为"
    服务器启动时会检查每个工具所需的环境变量。缺少变量的工具会被自动注册但禁用，不会出现在返回给客户端的工具列表中。您可以通过设置所需的环境变量并重启服务器来启用它们。

## 故障排除

### 常见问题

1. **依赖安装失败**

   - 确保您的 Python 版本符合要求
   - OpenAPI 和 MCP 模式均需要 Python 3.10+

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

服务器使用内置的结构化日志模块进行日志记录。启动服务器后，您可以在控制台看到详细的日志信息，包括：

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

您可以使用 `pytest` 来测试 API 端点：

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

## 部署

关于 Docker 部署和生产环境设置，请参阅 [Docker 部署](docker.md) 文档。
