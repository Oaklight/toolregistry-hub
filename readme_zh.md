# ToolRegistry Hub 文档

[English version](docs/readme_en.md) | [中文版](docs/readme_zh.md)

欢迎使用 ToolRegistry Hub 文档！本文档提供了对项目中所有工具的详细说明。

## 工具概览

ToolRegistry Hub 是一个提供各种实用工具的 Python 库，旨在支持各种常见任务。以下是主要工具类别：

- [计算器工具](docs/zh/calculator.md) - 提供各种数学计算功能
- [日期时间工具](docs/zh/datetime.md) - 处理日期、时间和时区转换
- [文件操作工具](docs/zh/file_ops.md) - 提供文件内容操作功能
- [文件系统工具](docs/zh/filesystem.md) - 提供文件系统操作功能
- [网络搜索工具](docs/zh/websearch/index.md) - 提供网络搜索功能
- [单位转换工具](docs/zh/unit_converter.md) - 提供各种单位之间的转换
- [其他工具](docs/zh/other_tools.md) - 其他实用工具
- [服务器模式](docs/zh/server.md) - REST API 和 MCP 服务器
- [Docker 部署](docs/zh/docker.md) - Docker 容器化部署

## 导航

查看[导航页面](docs/zh/navigation.md)以获取完整的文档结构和导航链接。

## 快速入门

要使用 ToolRegistry Hub，首先需要安装该库：

```bash
pip install toolregistry-hub
```

然后，您可以导入并使用所需的工具：

```python
from toolregistry_hub import Calculator, DateTime, FileOps, FileSystem

# 使用计算器
result = Calculator.evaluate("2 + 2 * 3")
print(result)  # 输出: 8

# 获取当前时间
current_time = DateTime.now()
print(current_time)
```

## 文档结构

本文档按工具类别组织，每个工具类别有自己的页面，详细说明了该类别下的所有工具、方法和用法示例。

## 贡献

如果您想为 ToolRegistry Hub 做出贡献，请参阅 [GitHub 仓库](https://github.com/Oaklight/toolregistry-hub)。
