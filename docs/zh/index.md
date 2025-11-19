---
title: 中文文档
summary: ToolRegistry Hub 完整中文文档
description: ToolRegistry Hub 的完整中文文档 - 一个提供各种实用工具的 Python 库
keywords: python, 工具, 实用程序, 文档, 中文
author: ToolRegistry Hub 团队
---

# ToolRegistry Hub 文档

欢迎使用 **ToolRegistry Hub** 的完整文档！这个库提供了各种实用工具，旨在支持 Python 开发中的常见任务。

## 🚀 快速开始

### 安装

```bash
pip install toolregistry-hub
```

### 基本使用

```python
from toolregistry_hub import Calculator, DateTime, FileOps, FileSystem

# 数学计算
result = Calculator.evaluate("2 + 3 * 4")
print(result)  # 输出: 14

# 获取当前时间
current_time = DateTime.now()
print(current_time)

# 文件操作
content = FileOps.read_file("example.txt")
print(content)
```

## 📖 工具分类

### 核心工具

<div class="grid cards" markdown>

-   :material-calculator: **[计算器工具](calculator.md)**

    ---

    数学计算、表达式求值和统计函数。

    [:octicons-arrow-right-24: 了解更多](calculator.md)

-   :material-clock: **[日期时间工具](datetime.md)**

    ---

    日期、时间、时区转换和时间操作。

    [:octicons-arrow-right-24: 了解更多](datetime.md)

-   :material-file-edit: **[文件操作](file_ops.md)**

    ---

    文件内容操作、读取、写入和处理。

    [:octicons-arrow-right-24: 了解更多](file_ops.md)

-   :material-folder: **[文件系统](filesystem.md)**

    ---

    文件系统操作、目录管理和路径工具。

    [:octicons-arrow-right-24: 了解更多](filesystem.md)

</div>

### 高级功能

<div class="grid cards" markdown>

-   :material-web: **[网络搜索工具](websearch/index.md)**

    ---

    多引擎网络搜索，支持 Bing、Brave、SearXNG 和 Tavily。

    [:octicons-arrow-right-24: 探索](websearch/index.md)

-   :material-swap-horizontal: **[单位转换](unit_converter.md)**

    ---

    各种测量单位之间的转换。

    [:octicons-arrow-right-24: 转换](unit_converter.md)

-   :material-tools: **[其他工具](other_tools.md)**

    ---

    额外的实用功能和辅助工具。

    [:octicons-arrow-right-24: 发现](other_tools.md)

</div>

### 部署与集成

<div class="grid cards" markdown>

-   :material-server: **[服务器模式](server.md)**

    ---

    REST API 服务器和 MCP（模型上下文协议）集成。

    [:octicons-arrow-right-24: 部署](server.md)

-   :material-docker: **[Docker 部署](docker.md)**

    ---

    使用 Docker 和 Docker Compose 的容器化部署。

    [:octicons-arrow-right-24: 容器化](docker.md)

</div>

## 🗺️ 导航

- **[导航指南](navigation.md)** - 完整的文档结构和链接
- **[English Documentation](../en/index.md)** - 切换到英文文档

## 📚 API 参考

每个工具类别都提供详细的 API 文档，包括：

- **类概览** - 理解工具架构
- **方法文档** - 详细的参数和返回值描述
- **使用示例** - 实用的代码示例
- **最佳实践** - 推荐的使用模式

## 🔍 搜索

使用顶部导航中的搜索功能，快速查找整个文档中的特定工具、方法或概念。

## 🤝 贡献

发现问题或想要贡献？访问我们的 [GitHub 仓库](https://github.com/Oaklight/toolregistry-hub)：

- 报告错误
- 请求功能
- 提交拉取请求
- 改进文档

---

*准备开始了吗？选择上面的工具类别或浏览[导航指南](navigation.md)获取完整概览。*