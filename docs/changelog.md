---
title: 更新日志
summary: toolregistry-hub 项目的版本更新历史和变更记录
description: 详细记录了 toolregistry-hub 从 0.4.14 版本以来的所有功能更新、修复和改进
keywords: changelog, 更新日志, 版本历史, 变更记录
author: Oaklight
---

# 更新日志

本页面记录了 toolregistry-hub 项目从首个正式发布版本 0.4.14 以来的所有重要变更。

## [0.5.0] - 2025-11-11

### 🔐 安全与认证

- **多 Bearer Token 认证** (#11)
  - 支持通过环境变量或文件配置多个 Bearer Token
  - 支持 `API_BEARER_TOKEN` 环境变量（逗号分隔）
  - 支持 `API_BEARER_TOKENS_FILE` 文件配置（每行一个 Token）
  - 添加 Token 缓存机制提升效率
  - 增强认证日志和调试功能
  - 新增独立的多 Token 认证测试套件

### 🌐 服务器功能 (#9)

- **REST API 服务器**
  - 新增 `toolregistry-server` CLI 命令行工具
  - 支持 OpenAPI 和 MCP 两种服务模式
  - 为每个工具提供独立的 REST API 端点：
    - 计算器 API (`/calculator`)
    - 日期时间 API (`/datetime`)
    - 网页抓取 API (`/fetch`)
    - 思考工具 API (`/think`)
    - 网络搜索 API (`/websearch`)
  - 自动路由发现和注册机制
  - 递归路由发现支持嵌套模块

### 🐳 Docker 支持

- **完整的容器化部署方案**
  - 添加 Dockerfile 用于构建容器镜像
  - 提供 `.env.sample` 环境变量参考
  - 添加 `requirements.txt` 依赖安装文件
  - 提供 `compose.yaml` 和 `compose.dev.yaml` 编排配置
  - 添加构建和推送自动化 Makefile
  - 优化 `.dockerignore` 减少镜像大小

### 🔍 现代化网络搜索 (#8)

- **新搜索引擎支持**

  - 添加 Brave Search API 集成
  - 添加 Tavily Search API 集成
  - 添加 SearXNG 搜索引擎支持
  - 重构 Bing 搜索为现代化实现

- **统一搜索架构**

  - 引入 `BaseSearch` 抽象基类
  - 标准化搜索 API 方法签名
  - 使用 `SearchResult` 数据类提供类型安全
  - 统一头部生成和内容获取逻辑

- **高级搜索功能**

  - 多 API Key 支持（Brave 和 Tavily）
  - 分页支持，最多可获取 180 条结果
  - 灵活的搜索参数和过滤选项
  - 改进的结果解析和错误处理

- **用户代理优化**

  - 使用 `ua-generator` 替代 `fake-useragent`
  - 动态用户代理生成提升反爬虫能力
  - 增强浏览器指纹识别真实性

- **模块重构**
  - 现代搜索引擎移至 `websearch/` 目录
  - 旧版搜索实现移至 `websearch_legacy/` 目录
  - 清理过时的 Google 搜索模块

### 🕐 时区功能增强 (#5)

- **时区支持**

  - `DateTime.now()` 支持指定时区参数
  - 新增 `convert_timezone()` 时区转换功能
  - 支持 IANA 时区名称（如 "Asia/Shanghai"）
  - 支持 UTC/GMT 偏移格式（如 "UTC+5:30", "GMT-3"）
  - 处理分数小时偏移（如尼泊尔 UTC+5:45）

- **Python 兼容性**
  - 通过 `backports.zoneinfo` 支持 Python 3.8
  - 统一时区解析逻辑
  - 改进错误处理和异常信息

### 📚 文档重构 (#10)

- **文档结构优化**
  - 重构文档结构，提升可读性
  - 添加多语言文档支持
  - 详细的 Docker 部署指南
  - 网络搜索引擎使用文档
  - API 端点和配置说明

### 🧪 测试改进 (#12)

- **测试覆盖增强**
  - 添加 0.4.16a0 版本测试
  - 多 Token 认证测试套件
  - 时区功能单元测试
  - 网络搜索引擎测试

### 🔄 重构

- **think_tool**: 简化 think 方法返回类型
  - 将返回类型从 `Dict[str, str]` 改为 `None`
  - 移除未使用的 typing 导入
  - 移除思考日志返回值，因为它未被使用

### 📚 文档

- **文档托管**: 迁移文档到 ReadTheDocs 托管平台

## [0.4.15] - 2025-08-11

### ✨ 新功能

- **DateTime 工具**: 添加用于获取当前时间的 DateTime 实用工具
- **ThinkTool**: 新增推理和头脑风暴工具，为 AI 工具集成提供认知处理空间

### 📝 文档改进

- 增强工具描述和使用示例
- 更新独立性声明和包上下文
- 改进 README 文档结构

### 🔧 维护

- 版本号提升至 0.4.15
- 依赖项更新和优化

## [0.4.14] - 首个正式发布版本

### 🎉 初始发布

- 基础工具集合
- 核心功能实现
- 基本文档结构
- 测试框架建立

---

## 版本说明

### 语义化版本控制

本项目遵循 [语义化版本控制](https://semver.org/lang/zh-CN/) 规范：

- **主版本号**：不兼容的 API 修改
- **次版本号**：向下兼容的功能性新增
- **修订号**：向下兼容的问题修正

### 变更类型图例

- 🎉 **新功能** - 新增功能或特性
- 🔄 **重构** - 代码重构，不影响功能
- 🐛 **修复** - 错误修复
- 📚 **文档** - 文档更新
- 🔐 **安全** - 安全相关改进
- 🌐 **服务器** - 服务器功能
- 🐳 **Docker** - 容器化相关
- 🔍 **搜索** - 搜索功能相关
- 🕐 **时区** - 时区功能相关
- 🧪 **测试** - 测试相关改进
- 🔧 **维护** - 维护性更新

### 获取更新

要获取最新版本，请使用：

```bash
pip install --upgrade toolregistry-hub
```

### 反馈和建议

如果您发现任何问题或有改进建议，请在我们的 [GitHub 仓库](https://github.com/OakLight/toolregistry-hub) 提交 Issue。
