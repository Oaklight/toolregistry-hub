---
title: 示例
summary: 实用代码示例 — 从基础用法到服务器部署与自定义工具
description: 通过可运行的代码片段快速了解 ToolRegistry Hub 的各种用法。
keywords: examples, 示例, 代码, python, server, docker, custom tool
author: Oaklight
---

# 示例

本页汇集常见使用场景的完整代码示例。每段代码均可直接复制运行。

---

## 基础库用法

### 计算器

```python
from toolregistry_hub import Calculator

Calculator.evaluate("sqrt(144) + 2**3")          # 20.0
Calculator.evaluate("log(100, 10) + sin(pi/2)")  # 3.0
Calculator.list_allowed_fns()                     # 查看所有可用函数
Calculator.help("log")                            # 单个函数帮助
```

### 日期时间

```python
from toolregistry_hub import DateTime

DateTime.now()                                                   # UTC 当前时间
DateTime.now("Asia/Shanghai")                                    # 上海当前时间
DateTime.convert_timezone("14:30", "America/Chicago", "Asia/Tokyo")  # 时区转换
```

### 文件操作

```python
from toolregistry_hub import FileOps, FileReader, FileSearch, PathInfo

# 搜索
FileSearch.grep(r"TODO", path="src/")
FileSearch.tree("src/", max_depth=2)
py_files = FileSearch.glob("**/*.py", path="src/")

# 读取
content = FileReader.read("config.py", limit=20)

# 编辑（安全字符串替换）
diff = FileOps.edit("config.py",
                    old_string="DEBUG = True",
                    new_string="DEBUG = False")
print(diff)

# 元信息
info = PathInfo.info("/path/to/file")
```

---

## 网络搜索（多引擎）

```python
from toolregistry_hub import Fetch
from toolregistry_hub.websearch import WebSearch

# 抓取网页内容
Fetch().fetch_content("https://example.com")

# 统一搜索接口 — 自动选择可用引擎
ws = WebSearch()
results = ws.search("Python 3.12 新特性", max_results=3)
for r in results:
    print(f"{r.title}: {r.url}")
```

!!! tip "指定搜索引擎"
    ```python
    from toolregistry_hub.websearch import BraveSearch, TavilySearch

    brave = BraveSearch()          # 需设置 BRAVE_API_KEY
    tavily = TavilySearch()        # 需设置 TAVILY_API_KEY

    results = brave.search("MCP protocol", max_results=5)
    ```

    各引擎所需环境变量详见 [环境变量参考](../reference/environment.md)。

---

## 服务器部署

### OpenAPI 模式

```bash
pip install toolregistry-hub[server]

# 启动 — 默认加载所有工具
toolregistry-hub openapi --port 8000
# → Swagger UI: http://localhost:8000/docs
```

```python
# 客户端调用
import requests

resp = requests.post("http://localhost:8000/call/Calculator/evaluate",
                     json={"expression": "2**10"})
print(resp.json())  # {"result": 1024}
```

### MCP 模式

```bash
# stdio 传输（供 AI Agent 使用）
toolregistry-hub mcp

# SSE 传输
toolregistry-hub mcp --transport sse --port 8080
```

---

## Docker 快速启动

```bash
docker run -d \
  -p 8000:8000 \
  -e API_BEARER_TOKEN=my-secret \
  oaklight/toolregistry-hub:latest \
  openapi --host 0.0.0.0
```

```bash
# 验证
curl -H "Authorization: Bearer my-secret" \
     http://localhost:8000/call/Calculator/evaluate \
     -d '{"expression": "1+1"}'
```

---

## 自定义工具注册

通过 `tools.jsonc` 注册你自己的工具类：

```jsonc
// tools.jsonc
{
  "tools": [
    {
      "module": "my_tools.weather",
      "class": "WeatherTool"
    }
  ]
}
```

```python
# my_tools/weather.py
class WeatherTool:
    @staticmethod
    def get_weather(city: str) -> str:
        """获取城市天气"""
        return f"{city}: 晴, 25°C"
```

```bash
toolregistry-hub openapi --tools-config tools.jsonc --port 8000
# WeatherTool 现在可通过 API 访问
```

---

## 在 AI Agent 中使用

结合 [ToolRegistry](https://toolregistry.readthedocs.io/) 核心库，将 Hub 工具注册到任意 LLM Agent：

```python
from toolregistry import ToolRegistry
from toolregistry_hub import Calculator, DateTime

registry = ToolRegistry()
registry.register_from_class(Calculator)
registry.register_from_class(DateTime)

# 导出为 OpenAI function-calling 格式
tools_schema = registry.get_tools_json()
```

---

## 更多资源

- [快速开始](../get-started/quickstart.md) — 60 秒上手
- [库使用方式](../guides/library.md) — 完整库模式指南
- [服务器配置](../guides/server.md) — 认证、配置文件、自定义工具
- [Docker 部署](../guides/docker.md) — 生产环境部署
