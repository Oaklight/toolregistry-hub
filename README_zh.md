# ToolRegistry Hub

[English](README_en.md) | [中文](README_zh.md)

> **⚠️ 重要说明**：这是一个**独立的包**，可以完全独立使用。此包从 `toolregistry` 0.4.14 版本分离出来，版本格式共享仅出于历史连续性。`toolregistry-hub` **不依赖** `toolregistry`，完全独立且自给自足。可以独立使用或作为主 `toolregistry` 包的子模块。

一个为 LLM 函数调用设计的全面工具集合，从主 ToolRegistry 包中提取出来，提供专注的实用模块。

## 概述

ToolRegistry Hub 提供了一套强大的实用工具，专为 LLM 代理和函数调用场景设计：

- **计算器 (Calculator)**：高级数学运算和表达式求值，支持复杂函数
- **日期时间 (DateTime)**：简单的当前日期和时间工具，提供 ISO 格式输出
- **文件系统 (FileSystem)**：全面的文件和目录操作，增强错误处理
- **文件操作 (FileOps)**：支持差异/补丁的原子文件操作，确保安全文件操作
- **思考工具 (ThinkTool)**：简单的推理和头脑风暴工具，用于结构化思维过程
- **单位转换器 (UnitConverter)**：全面的单位转换工具，涵盖各种计量系统
- **网络搜索 (WebSearch)**：多引擎网络搜索功能，支持内容获取和过滤选项

## 功能特性

### 计算器

- 支持标准和自定义函数的数学表达式求值
- 支持基本算术、幂/根、对数/指数函数
- 统计运算（最小值、最大值、求和、平均值、中位数、众数、标准差）
- 组合数学函数（阶乘、最大公约数、最小公倍数）
- 距离计算和金融计算
- 安全函数执行的表达式求值

### 日期时间

- 获取 ISO 8601 格式的当前 UTC 时间
- 专为 LLM 工具设计的简单专注的日期时间功能
- 静态方法便于集成

### 文件系统

- 创建、读取、更新和删除文件和目录
- 路径操作和验证
- 支持深度控制和隐藏文件过滤的目录列表
- 文件元数据操作（大小、修改时间）
- 跨平台兼容性

### 文件操作

- 原子文件操作，防止数据损坏
- 统一差异和 git 风格冲突解决
- 支持正则表达式模式和上下文的文件搜索
- 带临时文件处理的安全文件写入
- 路径验证工具

### 思考工具

- 用于推理和头脑风暴的简单思维记录
- 专为 Claude 的思维过程设计
- 无状态操作，不进行外部更改

### 单位转换器

- 各种计量单位之间的转换：
  - 温度（摄氏度、华氏度、开尔文）
  - 长度（米、英尺、厘米、英寸）
  - 重量（千克、磅）
  - 时间（秒、分钟）
  - 面积、速度、数据存储、压力、功率、能量
  - 电气、磁性、辐射和光强度单位
- 全面覆盖各种计量系统

### 网络搜索

- 多搜索引擎支持（Google、Bing、SearXNG）
- 网页内容获取和提取
- 结果过滤和排序选项
- 跨不同搜索提供商的统一接口

## 安装

```bash
pip install toolregistry-hub
```

## 快速开始

```python
from toolregistry_hub import Calculator, DateTime, FileSystem, ThinkTool, UnitConverter, WebSearchGoogle

# 数学计算
calc = Calculator()
result = calc.evaluate("sqrt(16) + pow(2, 3)")
print(f"计算结果: {result}")

# 获取当前时间
current_time = DateTime.now()
print(f"当前时间: {current_time}")

# 文件操作
fs = FileSystem()
fs.create_dir("my_project")
fs.create_file("my_project/config.txt")

# 单位转换
converter = UnitConverter()
fahrenheit = converter.celsius_to_fahrenheit(25)
print(f"25°C = {fahrenheit}°F")

# 结构化思考
thought = ThinkTool.think("分析解决这个问题的最佳方法...")
print(f"思考过程: {thought}")

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
