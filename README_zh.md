# ToolRegistry Hub 文档

[![PyPI version](https://img.shields.io/pypi/v/toolregistry-hub?color=green)](https://pypi.org/project/toolregistry-hub/)
[![Docker Image](https://img.shields.io/docker/v/oaklight/toolregistry-hub-server?label=docker&color=green)](https://hub.docker.com/r/oaklight/toolregistry-hub-server)
[![CI](https://github.com/Oaklight/toolregistry-hub/actions/workflows/ci.yml/badge.svg)](https://github.com/Oaklight/toolregistry-hub/actions/workflows/ci.yml)

[English version](readme_en.md) | 中文版

欢迎使用 ToolRegistry Hub 文档！本文档提供了对项目中所有工具的详细说明。

## 生态系统

| 包 | 描述 | PyPI | 文档 |
|---|------|------|------|
| [**toolregistry**](https://github.com/Oaklight/ToolRegistry) | 核心库 — 工具注册、Schema 生成、执行 | [![PyPI](https://img.shields.io/pypi/v/toolregistry?color=green)](https://pypi.org/project/toolregistry/) | [文档](https://toolregistry.readthedocs.io/) |
| [**toolregistry-server**](https://github.com/Oaklight/toolregistry-server) | 服务端适配器 — 通过 OpenAPI 和 MCP 暴露工具 | [![PyPI](https://img.shields.io/pypi/v/toolregistry-server?color=green)](https://pypi.org/project/toolregistry-server/) | [文档](https://toolregistry-server.readthedocs.io/) |
| [**toolregistry-hub**](https://github.com/Oaklight/toolregistry-hub) | 即用工具集 — 计算器、网页搜索、文件操作等 | [![PyPI](https://img.shields.io/pypi/v/toolregistry-hub?color=green)](https://pypi.org/project/toolregistry-hub/) | [文档](https://toolregistry-hub.readthedocs.io/) |

## 📚 文档

如需详细文档，请访问我们的 ReadTheDocs 页面：

- **中文文档**: [https://toolregistry-hub.readthedocs.io/zh-cn/latest/](https://toolregistry-hub.readthedocs.io/zh-cn/latest/)
- **English Documentation**: [https://toolregistry-hub.readthedocs.io/en/latest/](https://toolregistry-hub.readthedocs.io/en/latest/)

## 工具概览

ToolRegistry Hub 是一个提供各种实用工具的 Python 库，旨在支持各种常见任务。以下是主要工具类别：

- 计算器工具 - 提供各种数学计算功能
- 日期时间工具 - 处理日期、时间和时区转换
- 文件操作工具 - 提供文件内容操作功能
- 文件系统工具 - 提供文件系统操作功能
- 网络搜索工具 - 提供网络搜索功能
- 单位转换工具 - 提供各种单位之间的转换
- 其他工具 - 其他实用工具
- 服务器模式 - REST API 和 MCP 服务器
- Docker 部署 - Docker 容器化部署

如需了解每个工具类别的详细信息，请参阅[在线文档](https://toolregistry-hub.readthedocs.io/zh-cn/latest/)。

## 快速入门

要使用 ToolRegistry Hub，首先需要安装该库：

```bash
pip install toolregistry-hub
```

然后，您可以导入并使用所需的工具：

```python
from toolregistry_hub import Calculator, DateTime, FileOps

# 使用计算器
result = Calculator.evaluate("2 + 2 * 3")
print(result)  # 输出: 8

# 获取当前时间
current_time = DateTime.now()
print(current_time)
```

## 文档结构

本文档按工具类别组织，每个工具类别有自己的页面，详细说明了该类别下的所有工具、方法和用法示例。

## 更新日志

### 网页抓取工具重大更新（PR #140）

**结构化返回值**

`fetch_content` 现在返回结构化 `dict`，而不再是纯字符串：

```json
{
  "content": "...",
  "url": "https://example.com",
  "strategy": "readability",
  "quality": "high",
  "content_type": "text/html",
  "cached": false,
  "elapsed_ms": 123,
  "metadata": {"readability_score": 174.3, "content_length": 12345}
}
```

**`strategy` 参数**

新增可选的 `strategy` 参数，用于指定抓取策略（默认值：`"auto"`）。可选值：

| 策略 | 说明 |
|---|---|
| `auto` | 推荐 —— 按顺序尝试各 fallback |
| `markdown` | Cloudflare 内容协商 |
| `readability` | 本地 Readability 解析 |
| `soup` | 本地 BeautifulSoup 降级 |
| `veilrender` | 远程无头浏览器（需配置 `VEILRENDER_ENDPOINT`）|
| `cdp` | 自托管 Chrome DevTools Protocol（需配置 `CDP_ENDPOINT`）|
| `jina` | Jina Reader API（始终可用；可选配置 `JINA_API_KEY` 以提升限速上限）|

可选值在运行时会动态缩窄：`veilrender` 和 `cdp` 仅在配置了对应端点时才会出现。

**更新后的 fallback 链**

```
markdown → readability → soup → veilrender → cdp → jina → local_fallback
```

**VeilRender fallback**

VeilRender 是新增的可选远程无头浏览器 fallback，专为 JS 渲染页面和 SPA 设计。通过环境变量配置：

```
VEILRENDER_ENDPOINT=https://your-veilrender-instance
VEILRENDER_TOKEN=your_token_here  # 可选
```

## 贡献

如果您想为 ToolRegistry Hub 做出贡献，请参阅 [GitHub 仓库](https://github.com/Oaklight/toolregistry-hub)。
