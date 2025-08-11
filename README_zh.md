# ToolRegistry Hub

一个为 LLM 函数调用设计的全面工具集合，从主 ToolRegistry 包中提取出来，提供专注的实用模块。

## 版本说明

此包是从 `toolregistry` 分离出来的，初始版本号为 `0.4.14`，以保持与原包 `toolregistry` 的版本号连续性。

## 概述

ToolRegistry Hub 提供了一套强大的实用工具，专为 LLM 代理和函数调用场景设计：

- **计算器 (Calculator)**：高级数学运算和表达式求值，支持复杂函数
- **文件系统 (FileSystem)**：全面的文件和目录操作，增强错误处理
- **文件操作 (FileOps)**：支持差异/补丁的原子文件操作，确保安全文件操作
- **单位转换器 (UnitConverter)**：全面的单位转换工具，涵盖各种计量系统
- **网络搜索 (WebSearch)**：多引擎网络搜索功能，支持内容获取和过滤选项

## 功能特性

### 计算器

- 支持标准和自定义函数的数学表达式求值
- 支持三角函数、对数和统计运算
- 无效表达式的错误处理

### 文件系统

- 创建、读取、更新和删除文件和目录
- 路径操作和验证
- 递归目录操作

### 文件操作

- 原子文件操作，防止数据损坏
- 文件比较和更新的差异和补丁功能
- 带备份选项的安全文件写入

### 单位转换器

- 各种计量单位之间的转换（长度、重量、体积、温度等）
- 支持自定义单位定义
- 批量转换功能

### 网络搜索

- 多搜索引擎支持（Google、Bing、SearXNG）
- 网页内容获取和提取
- 结果过滤和排序选项

## 安装

```bash
pip install toolregistry-hub
```

## 快速开始

```python
from toolregistry_hub import Calculator, FileSystem, WebSearchGoogle

# 数学计算
calc = Calculator()
result = calc.evaluate("sqrt(16) + pow(2, 3)")
print(f"计算结果: {result}")

# 文件操作
fs = FileSystem()
fs.create_dir("my_project")
fs.create_file("my_project/config.txt", content="配置数据")

# 网络搜索
search = WebSearchGoogle()
results = search.search("Python 编程", number_results=3)
for result in results:
    print(f"标题: {result['title']}")
    print(f"URL: {result['url']}")
    print(f"内容: {result['content'][:100]}...")
```

## 与 ToolRegistry 集成

此包设计为与主 ToolRegistry 包无缝协作：

```bash
# 安装带有 hub 工具的 ToolRegistry
pip install toolregistry[hub]
```

## API 文档

详细的 API 文档和高级用法示例，请访问：<https://toolregistry.readthedocs.io/>

## 贡献

我们欢迎贡献！请查看我们的贡献指南了解更多参与方式。

## 许可证

本项目采用 MIT 许可证 - 详情请参见 [LICENSE](LICENSE) 文件。

## 更新日志

请参见 [CHANGELOG.md](CHANGELOG.md) 了解更改列表和版本历史。
