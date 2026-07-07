---
title: 示例
---

# 示例

本页展示 ToolRegistry Hub 工具的常见使用场景。更多细节参阅各工具的文档页面。

## 计算器

```python
from toolregistry_hub import Calculator

# 基本运算
Calculator.evaluate("2 ** 10")              # 1024
Calculator.evaluate("sqrt(2) * pi")         # 4.4428...

# 三角函数
Calculator.evaluate("sin(pi/6)")            # 0.5
Calculator.evaluate("atan2(1, 1) * 180/pi") # 45.0
```

## 文件操作

```python
from toolregistry_hub import FileSearch, FileReader, FileOps

# 在项目中搜索 TODO 注释
FileSearch.grep(r"TODO|FIXME", path="src/", include="*.py")

# 查看目录结构
FileSearch.tree("src/", max_depth=2)

# 读取文件片段
FileReader.read("README.md", limit=30)

# 安全字符串替换
FileOps.edit("config.py",
             old_string="DEBUG = True",
             new_string="DEBUG = False")
```

## 网络搜索与抓取

```python
from toolregistry_hub import Fetch
from toolregistry_hub.websearch import WebSearch

# 抓取网页内容（自动提取正文）
fetch = Fetch()
result = fetch.fetch_content("https://example.com")

# 网络搜索
ws = WebSearch(provider="brave", api_key="YOUR_KEY")
results = ws.search("Python asyncio tutorial", max_results=5)
for r in results:
    print(r.title, r.url)
```

## Bash 工具

```python
from toolregistry_hub import BashTool

bash = BashTool()

# 执行命令
bash.execute("ls -la /tmp")

# 带超时
bash.execute("sleep 10 && echo done", timeout=5)
```

## 日期时间

```python
from toolregistry_hub import DateTime

# 当前时间
DateTime.now("Asia/Shanghai")

# 时区转换
DateTime.convert_timezone("14:30", "America/Chicago", "Asia/Tokyo")

# 日期差
DateTime.date_diff("2025-01-01", "2025-12-31")
```

## 与 ToolRegistry 集成

Hub 工具可以直接注册到 `ToolRegistry`，通过 LLM 函数调用使用：

```python
from toolregistry import ToolRegistry
from toolregistry_hub import Calculator, DateTime

registry = ToolRegistry()
registry.register(Calculator.evaluate)
registry.register(DateTime.now)

# 生成 OpenAI 兼容的工具定义
tools = registry.get_tools_json()
```

参见 [库使用方式](../guides/library.md) 和 [服务器模式](../guides/server.md) 了解更多集成方式。
