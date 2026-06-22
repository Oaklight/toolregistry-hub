---
title: 库使用方式
summary: 直接作为 Python 库使用 toolregistry-hub — 无需启动服务器
description: 在你的 Python 代码、脚本或 AI Agent 中直接导入并调用任何工具类，零配置开销。
keywords: python, 库, 导入, 直接使用, 工具, agent
author: Oaklight
---

# 库使用方式

ToolRegistry Hub 首先是一个 **Python 库**。每个工具都可以直接在代码中导入和调用 — 无需服务器、无需 HTTP、无需配置文件。这是使用 hub 最简单、最灵活的方式。

!!! tip "库模式 vs 服务器模式"
    | | 库模式 | 服务器模式 |
    |---|---------|--------|
    | **安装** | `pip install toolregistry-hub` | `pip install toolregistry-hub[server]` |
    | **使用** | `from toolregistry_hub import ...` | `toolregistry-hub openapi` |
    | **适用场景** | 脚本、Notebook、AI Agent、嵌入你的应用 | 远程访问、多客户端、MCP 集成 |
    | **延迟** | 直接函数调用 | HTTP / stdio 往返 |
    | **依赖** | 极少（主要是标准库） | FastAPI、uvicorn 或 MCP SDK |

!!! tip "初次使用？"
    请先阅读[安装](../get-started/installation.md)和[快速上手](../get-started/quickstart.md)。

## 可用工具

### 计算与转换

```python
from toolregistry_hub import Calculator, UnitConverter

# 计算器 — 求值表达式，内置数学函数
Calculator.evaluate("log(100, 10) + sin(pi/2)")  # 3.0
Calculator.list_allowed_fns()  # 列出所有可用函数
Calculator.help("log")  # 获取特定函数的帮助

# 单位转换器 — 在单位之间转换
UnitConverter.convert(100, "celsius_to_fahrenheit")  # 212.0
UnitConverter.list_conversions(category="temperature")
```

### 日期与时间

```python
from toolregistry_hub import DateTime

# 当前时间（默认：UTC）
DateTime.now()

# 指定时区的当前时间
DateTime.now("America/New_York")

# 时区转换
DateTime.convert_timezone("14:30", "America/Chicago", "Asia/Tokyo")
```

### 文件操作

```python
from toolregistry_hub import FileOps, FileReader, FileSearch, PathInfo

# 精确字符串替换编辑文件
diff = FileOps.edit("config.py", old_string="DEBUG = True", new_string="DEBUG = False")
print(diff)  # unified diff 格式输出

# 带行号读取文件
content = FileReader.read("src/main.py", limit=50)

# 读取 Jupyter Notebook
nb = FileReader.read_notebook("analysis.ipynb")

# 搜索文件
py_files = FileSearch.glob("**/*.py", path="src/")
matches = FileSearch.grep(r"def test_", path="tests/")
tree = FileSearch.tree("src/", max_depth=3)

# 一次调用获取文件元数据
info = PathInfo.info("/path/to/file")
# → {exists, type, size, last_modified, permissions}
```

### Shell 执行

```python
from toolregistry_hub import BashTool

result = BashTool.execute("python --version", timeout=30, cwd="/my/project")
print(result)
# {
#     "stdout": "Python 3.11.5\n",
#     "stderr": "",
#     "exit_code": 0,
#     "timed_out": False
# }
```

BashTool 内置拒绝列表，会阻止危险命令（`rm -rf /`、`sudo`、fork bomb 等）。详见 [Bash 工具](../tools/bash_tool.md) 页面的完整安全模型。

### 网络搜索与抓取

```python
from toolregistry_hub import Fetch, BraveSearch, TavilySearch
from toolregistry_hub.websearch import WebSearch

# 抓取并提取 URL 内容
content = Fetch().fetch_content("https://example.com")

# 使用 Jina Reader API 密钥抓取（可选，用于认证访问）
fetcher = Fetch(api_keys=["jina_key1", "jina_key2"])
content = fetcher.fetch_content("https://example.com")

# 统一网络搜索 — 自动选择最佳可用引擎
ws = WebSearch()
results = ws.search("Python 3.12 新特性", max_results=5)
for r in results:
    print(f"{r.title}: {r.url}")

# 指定特定引擎
results = ws.search("Python 异步编程", engine="brave", max_results=5)

# 列出可用引擎及其配置状态
engines = ws.list_engines()

# 直接使用引擎（需要通过环境变量设置 API 密钥）
results = BraveSearch().search("Python 3.12 new features", max_results=5)
for r in results:
    print(f"{r.title}: {r.url}")
```

### 定时任务

```python
from toolregistry_hub import CronTool

# 创建定时任务（每 5 分钟执行）
job = CronTool.create(cron="*/5 * * * *", prompt="检查服务器健康状态")

# 创建一次性提醒
job = CronTool.create(
    cron="30 14 28 4 *",
    prompt="部署发布到预生产环境",
    recurring=False,
)

# 列出和管理定时任务
jobs = CronTool.list()
CronTool.delete(job_id="abc123")
```

### 认知工具

```python
from toolregistry_hub import ThinkTool, TodoList

# 结构化思考（作为 LLM 工具非常有用）
ThinkTool.think(
    thinking_mode="planning",
    focus_area="数据库迁移",
    thought_process="我们需要从 SQLite 迁移到 PostgreSQL..."
)

# 任务管理
TodoList.update([
    "[db-migrate] 规划 schema 变更 (planned)",
    "[db-migrate] 编写迁移脚本 (in-progress)",
])
```

## 在 AI Agent 中使用

hub 在嵌入 AI Agent 流水线时最能发挥优势。每个工具都是带静态方法的普通 Python 类，可以注册到任何 Agent 框架：

```python
from toolregistry import ToolRegistry
from toolregistry_hub import Calculator, FileOps, BashTool, FileSearch

# 用选定的工具构建注册表
registry = ToolRegistry()
registry.register_static_tools(Calculator, namespace="calculator")
registry.register_static_tools(FileOps, namespace="file_ops")
registry.register_static_tools(BashTool, namespace="bash")
registry.register_static_tools(FileSearch, namespace="file_search")

# 为 LLM 生成工具 schema
tools_json = registry.get_tools_json(format="openai")
```

或使用 hub 内置的注册表一次加载所有工具：

```python
from toolregistry_hub.server.registry import get_registry

registry = get_registry()  # 所有工具已注册就绪
```

### 运行时标签更新

`toolregistry` v0.11.2 起，工具标签支持运行时可变 —— 无需重新注册即可在注册后调整工具的 `ToolTag` 标签：

```python
from toolregistry import ToolRegistry
from toolregistry.utils.tool_metadata import ToolTag
from toolregistry_hub import BashTool

registry = ToolRegistry()
registry.register_static_tools(BashTool, namespace="bash")

# 在验证环境后，于运行时将 BashTool 标记为特权工具
tool = registry["bash-execute"]
tool.metadata.tags = {ToolTag.PRIVILEGED, ToolTag.DESTRUCTIVE}
```

适用于需要根据运行时上下文（用户角色、部署环境等）动态管控高权限工具，而无需重建注册表的场景。

## 环境变量

部分工具需要 API 密钥。无需密钥的工具（Calculator、DateTime、FileOps、BashTool 等）开箱即用。

完整列表请参阅 **[环境变量参考](../reference/environment.md)**。

## 另请参阅

- **[工具参考](../tools/)** — 每个工具的详细 API 文档
- **[服务器模式](server.md)** — 部署为 REST API 或 MCP 服务器
- **[生态系统](../ecosystem.md)** — hub 在 toolregistry 家族中的定位
