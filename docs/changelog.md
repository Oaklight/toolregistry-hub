---
title: 更新日志
summary: toolregistry-hub 项目的版本更新历史和变更记录
description: 详细记录了 toolregistry-hub 从 0.4.14 版本以来的所有功能更新、修复和改进
keywords: changelog, 更新日志, 版本历史, 变更记录
author: Oaklight
---

# 更新日志

本页面记录了 toolregistry-hub 项目从首个正式发布版本 0.4.14 以来的所有重要变更。

## [0.5.4.post1] - 2026-01-13

### 🐛 修复

- **版本端点可见性**
	- 使用 `include_in_schema=False` 从 OpenAPI 文档中隐藏版本端点（`/version/` 和 `/version/check`）
	- 版本端点保持完全功能，可通过 HTTP 请求正常访问
	- 防止版本端点在 MCP 模式下被暴露为 LLM 工具

## [0.5.4] - 2026-01-13

### 🔄 重构

- **认知工具统一架构**
	- 将 reason 和 think 端点合并为单一的 think 端点，整合结构化推理与探索性思考功能
	- 合并思考模式：分析、假设、规划、验证、修正（结构化）与头脑风暴、心理模拟、换位思考、直觉（探索性）
	- 简化 API 表面，移除独立的 /reason 端点，更新请求模型
	- 统一参数命名：'thought' → 'thought_process'，'thinking_type' → 'thinking_mode'
	- 重构测试套件，覆盖所有思考模式和参数组合
	- 更新文档，反映 "recall + think" 的双工具认知架构

### ✨ 新功能

- **PyPI 版本检查与更新通知**
	- 添加完整的 PyPI 版本检查系统，参考 argo-proxy 实现
	- 新增 `version_check.py` 模块，支持异步 PyPI API 调用和智能版本比较
	- 实现预发布版本支持（alpha、beta、rc）和事件循环安全处理
	- 添加 `/version/` 和 `/version/check` API 端点，返回版本信息和更新状态
	- CLI 新增 `--version` 参数，显示当前版本并检查更新
	- 启动横幅增强，自动显示版本信息和更新通知
	- 使用标准库实现版本比较，无需额外依赖
	- 包含完整的同步测试套件（10个测试）

- **ASCII 艺术横幅**
	- 添加新的 banner.py 模块，包含 ASCII 艺术横幅
	- 实现居中对齐和一致的边框样式（80字符宽度）
	- 在 CLI 启动时显示横幅，可通过 show_banner=False 参数禁用

### 📝 文档改进

- **网页搜索时间敏感查询指导**
	- 在所有网页搜索类 docstring 中添加重要提示
	- 强调 LLM 无时间感知能力，训练数据可能过时
	- 要求处理"最近新闻"等查询时先使用时间工具获取当前时间
	- 应用于所有搜索提供商类

- **日期时间工具文档增强**
	- 为 now() 和 convert_timezone() 方法添加详细描述
	- 扩展参数文档，包含时区格式示例
	- 路由描述直接引用方法 docstrings，提升一致性

### 🔧 维护

- **版本属性修复**
	- 更新 pyproject.toml 使用 __version__ 属性替代 version
	- 在 __init__.py 中添加 __version__ 变量，遵循 Python 版本约定
	- 保留 version 变量以保持向后兼容性

## [0.5.3] - 2025-12-13

### 🔧 重构

- **多API密钥管理系统**
	- 将分散的API密钥实现整合为统一的APIKeyParser工具
	- 替换网络搜索引擎中分散的API密钥管理为统一系统
	- 在所有搜索提供商中实现一致的API密钥轮换和错误处理
	- 重构所有网络搜索引擎（Brave、Brightdata、Scrapeless、Tavily）以使用集中式API密钥管理
	- 提升搜索引擎的可靠性和性能
	- 为API密钥解析器添加速率限制支持

- **工具模块结构**
	- 将工具模块迁移到包结构，提升组织性
	- 添加fn_namespace.py模块用于函数命名空间工具
	- 改进模块导入和依赖关系
	- 简化从pyproject.toml中提取版本的过程
	- 更新构建配置，提升可重现性

- **版本管理系统**
	- 配置pyproject.toml使用从toolregistry_hub.version动态加载版本
	- 从pyproject.toml中移除硬编码版本，使用setuptools动态版本属性
	- 通过在`__init__.py`中设置单一版本来源来集中版本管理
	- 通过setuptools动态版本支持改进构建流程

### 🐛 修复

- **Docker 构建流程**
	- 修复Dockerfile中包含服务器扩展包(fastapi, uvicorn, fastmcp)的包安装
	- 改进Makefile构建逻辑，提升包安装处理
	- 移除冗余的docker/requirements.txt文件
	- 增强本地wheel、特定版本和从PyPI最新版本的包安装逻辑

- **类型注解与兼容性**
	- 解决pyright兼容性的类型注解和参数命名问题
	- 修复server_core.py和websearch模块中的类型提示
	- 改进测试兼容性和类型安全

### 📝 文档

- **Docker 文档**
	- 添加全面的Docker文档和迁移指南
	- 添加中英文Docker README文件
	- 提供OpenWebUI工具服务器迁移文档

## [0.5.2] - 2025-12-12

### ✨ 新功能

- **单位转换器 API 路由**
	- 添加单位转换器 API 路由
	- 重构单位转换器，使用基类和工具方法
	- 更新单位转换器测试

- **网络搜索增强**
	- 添加 Scrapeless DeepSERP API (Google SERP) 集成
	- 添加 Bright Data (Google SERP) 搜索集成
	- 实现通用 Google 搜索结果解析器
	- 添加 Bright Data 引擎测试（Bing 和 Yandex）
	- 为 Bing 搜索添加环境变量支持

### ⚠️ 弃用

- **Bing 搜索**：由于机器人检测问题，标记 BingSearch 为已弃用

### 📝 文档改进

- 更新 README 中的徽章样式
- 添加 DeepWiki 徽章到文档
- 更新项目描述和 README 文件
- 将 references 目录添加到 gitignore

## [0.5.1] - 2025-12-05

### 🔐 安全与认证

- **MCP 服务器认证** (#15)
	- 为 MCP 服务器添加 Bearer Token 认证支持
	- 实现 `DebugTokenVerifier` 用于 MCP 认证
	- 支持基于 Token 配置的认证和开放模式
	- 添加全面的认证事件日志记录
	- 将 Token 验证移至 FastAPI 全局依赖项
	- 重构认证架构，解耦路由和认证关注点

### 📋 任务管理增强

- **Todo List 工具增强** (#15)
	- 添加 Todo List 工具，支持灵活的输入格式
	- 支持字典格式和简单字符串格式 `"[id] content (status)"`
	- 实现全面的输入验证和详细的错误消息
	- 增强状态选项，添加 "pending" 状态
	- 支持多种输出格式：'simple'（无输出）、'markdown' 和 'ascii'
	- 添加 Markdown 表格生成 API 端点
	- 改进文档和类型注解

### 🌐 服务器功能

- **架构重构**
	- 创建 `server_core.py` 模块提供基础 FastAPI 应用
	- 从所有路由中移除认证依赖
	- 支持创建认证和非认证服务器变体
	- 改进路由发现日志逻辑
	- 优化服务器架构，提升可维护性

### 🕐 日期时间功能

- **API 增强**
	- 为 `time_now` 端点添加 `TimeNowRequest` 模型
	- 使用结构化请求体替代查询参数
	- 保持与现有时区名称功能的向后兼容性
	- 改进 API 文档结构

### 📝 文档改进

- **项目文档**
	- 更新项目描述和 README 文件
	- 将 README 引用从 `README.md` 改为 `readme_en.md`
	- 更新 PyPI 和 GitHub 徽章链接
	- 改进文档视觉一致性

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
