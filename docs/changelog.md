---
title: 更新日志
summary: toolregistry-hub 项目的版本更新历史和变更记录
description: 详细记录了 toolregistry-hub 从 0.4.14 版本以来的所有功能更新、修复和改进
keywords: changelog, 更新日志, 版本历史, 变更记录
author: Oaklight
---

# 更新日志

本页面记录了 toolregistry-hub 项目从首个正式发布版本 0.4.14 以来的所有重要变更。

## [未发布] - 自 0.8.0 以来

### 新功能

- **工具发现与渐进式披露**
    - 调用 `registry.enable_tool_discovery()` 注册 `discover_tools` 工具，支持 BM25F 全文检索所有已注册工具
    - 低频工具（FileReader、FileSearch、PathInfo、BashTool、CronTool、TodoList、UnitConverter）标记为延迟加载——可通过 `discover_tools` 发现，但智能客户端初始 schema 中不包含
    - 新增 `--tool-discovery / --no-tool-discovery` CLI 参数（默认：启用）

- **思维增强工具调用**
    - 向工具 schema 注入 `thought` 属性，支持链式思维推理（[arXiv:2601.18282](https://arxiv.org/abs/2601.18282)）
    - 内置去重逻辑，当服务端和 harness 同时启用时不会重复注入
    - 新增 `--think-augment / --no-think-augment` CLI 参数（默认：启用）

- **为所有注册工具添加 ToolTag 元数据**
    - 根据工具行为分配 `ToolTag` 标签（`READ_ONLY`、`DESTRUCTIVE`、`NETWORK`、`FILE_SYSTEM`、`PRIVILEGED`）
    - 标签通过 `tool.metadata.tags` 可用于过滤和展示

- **Fetch：Jina API 密钥支持与多密钥轮询**
    - `Fetch` 类现在接受可选的 `api_keys` 参数用于 Jina Reader 认证
    - 回退到 `JINA_API_KEY` 环境变量（逗号分隔多个密钥）
    - 轮询式密钥轮换，自动故障追踪（HTTP 401/403 → 1 小时冷却，HTTP 429 → 5 分钟冷却）

- **Fetch：用户指定提取引擎**
    - 为 `_extract()` 添加 `engine` 参数：`"auto"`（默认回退链）、`"markdown"`、`"readability"`、`"soup"`、`"jina"`
    - 直接引擎模式跳过回退链——仅尝试指定的引擎

- **Fetch：用 readability + soup 替换 BS4 提取管道** ([#87](https://github.com/Oaklight/toolregistry-hub/pull/87), [#83](https://github.com/Oaklight/toolregistry-hub/issues/83))
    - 用多策略管道替换简单的 BeautifulSoup CSS 选择器提取：readability（Mozilla Readability.js 移植，智能文章评分）→ soup（结构化 CSS 降级）
    - HTML 只获取一次，两个本地策略共用；优先使用 readability，除非 soup 提取内容超过 2 倍
    - 从 [zerodep](https://github.com/Oaklight/zerodep) 引入 readability 和 soup 模块到 `_vendor/`，采用嵌套目录布局

- **Fetch：非 HTML 响应的 Content-Type 检测** ([#93](https://github.com/Oaklight/toolregistry-hub/pull/93), [#92](https://github.com/Oaklight/toolregistry-hub/issues/92))
    - 将 `_fetch_html` 重命名为 `_fetch_raw`，返回 `(body, content_type)` 元组
    - 对非 HTML 内容类型（JSON、纯文本、CSV、Markdown、XML、YAML）在 HTML 提取管道前短路返回
    - 防止结构化数据被 readability/soup 提取管道错误处理

- **Fetch：SPA 内容质量检测** ([#96](https://github.com/Oaklight/toolregistry-hub/pull/96), [#94](https://github.com/Oaklight/toolregistry-hub/issues/94))
    - 为 `_is_content_sufficient()` 添加文本结构分析，检测仅包含导航内容的提取结果
    - 启发式算法灵感来自 [jusText](https://github.com/miso-belica/jusText)：若 >70% 的行为短行（<30 字符）且段落级长行（>80 字符）不足 2 行，则判定为导航碎片并拒绝
    - 保守策略：仅在文本超过 5 行时触发，短内容不受影响

- **WebSearch：统一入口与动态引擎选择**
    - 新增 `WebSearch` 类注册到 `web/websearch` 命名空间；原有 6 个 provider 工具（`web/brave_search`、`web/tavily_search` 等）改为 defer，可通过 `discover_tools` 发现
    - `search(query, engine="auto", fallback=False, ...)` —— `engine="auto"` 按优先级尝试已配置的 provider；指定具体 engine 时若未配置则严格报错，或在 `fallback=True` 时降级到 auto 链
    - 通过 `WEBSEARCH_PRIORITY` 环境变量配置优先级（逗号分隔），默认顺序为付费 provider 优先
    - `engine` 参数 `Literal` 注解的实例级动态收窄：构造时 LLM 看到的 JSON schema 只包含当前服务实际配置了 API key 的 engine
    - 新增 `list_engines()` 辅助方法，运行时查询可用 provider

### 代码清理

- 移除 `fetch.py` 中的死代码：`_get_lynx_useragent()`、`HEADERS_LYNX`、`_remove_emojis()`、未使用的 `random` 导入
- 将基于 Lynx 的用户代理生成移至 `_legacy`，为未来 Chrome CDP 实现保留参考
- 将 `Fetch` 从静态工具类转换为实例类，用于管理 API 密钥状态

### 弃用

- **FileSystem 从默认服务端注册表中移除**
    - `FileSystem` 类不再在服务端模式中注册；已由 PathInfo、FileSearch 和 FileReader 替代
    - 该类本身保留以兼容库用户，仍会发出 `DeprecationWarning`

### 内部变更

- 将所有 zerodep 模块（structlog、scheduler、readability、soup）整合到 `_vendor/` 嵌套目录布局 ([#87](https://github.com/Oaklight/toolregistry-hub/pull/87))
- 移除 `beautifulsoup4` 外部依赖；将 `websearch_legacy`（bing、google）迁移至 zerodep soup ([#87](https://github.com/Oaklight/toolregistry-hub/pull/87))
- 排除 `_vendor/` 目录的 ruff UP035 lint 规则和 ty 类型检查
- 重构 CLI，始终使用 CLI 参数构建注册表，而非仅在指定 `--config` 时构建
- 修复 `register_from_class()` 调用中已弃用的 `with_namespace=` 参数（改用 `namespace=`）

### 修复

- **SearXNG：支持可选的 X-API-Key 请求头用于保护实例** ([#85](https://github.com/Oaklight/toolregistry-hub/pull/85))
    - 为 `SearXNGSearch` 添加可选的 `api_key` 参数，支持回退到 `SEARXNG_API_KEY` 环境变量
    - 设置后在 JSON API 请求中发送 `X-API-Key` 请求头；完全向后兼容

## [0.8.0] - 2026-04-06

### 破坏性变更

- **FileOps：用精确字符串替换取代 diff 编辑** ([#70](https://github.com/Oaklight/toolregistry-hub/pull/70), [#62](https://github.com/Oaklight/toolregistry-hub/issues/62))
    - 移除了 `replace_by_diff()` 和 `replace_by_git()` 方法
    - 新增 `edit(file_path, old_string, new_string)` 精确字符串匹配替换
    - 支持 `replace_all` 批量替换和 `start_line` 多匹配消歧
    - 保留文件编码（UTF-8/UTF-8-sig/UTF-16）和行尾（CRLF/LF）
    - 返回 unified diff 格式的变更

### 新功能

- **BashTool：带安全验证的 Shell 命令执行** ([#77](https://github.com/Oaklight/toolregistry-hub/pull/77), [#66](https://github.com/Oaklight/toolregistry-hub/issues/66))
    - 通过 `subprocess.run` 执行 Shell 命令，支持超时和工作目录配置
    - 内置拒绝列表阻止危险模式（rm -rf、sudo、fork bomb、pipe-to-shell、git force push 等）
    - 拒绝列表基于 6 个 AI 编程 CLI 工具的安全调研
    - 上游 `ToolMetadata` 懒加载集成，为未来权限系统做准备
    - stdout/stderr 截断上限 64KB，防止内存溢出

- **FileReader：多格式文件读取** ([#75](https://github.com/Oaklight/toolregistry-hub/pull/75), [#65](https://github.com/Oaklight/toolregistry-hub/issues/65), [#79](https://github.com/Oaklight/toolregistry-hub/pull/79))
    - `read()` — 文本文件，带行号和分页（10MB 上限，默认 2000 行）
    - `read_notebook()` — Jupyter Notebook，显示单元格类型和输出（仅需标准库）
    - `read_pdf()` — PDF 文本提取，通过 pypdf 或 pdfplumber（可选依赖）
    - `read_image()` — 图片文件，返回多模态内容块（`[TextBlock, ImageBlock]`），通过 Pillow 自适应压缩（[#79](https://github.com/Oaklight/toolregistry-hub/pull/79), [#74](https://github.com/Oaklight/toolregistry-hub/issues/74)）
    - 支持 `.png`、`.jpg`、`.jpeg`、`.gif`、`.webp` 格式
    - 超出 base64 大小限制（默认 5 MB）时自动压缩，支持格式特定的质量下限
    - 新增 `reader_image = ["Pillow>=10.0.0"]` 可选依赖组

- **FileSearch：文件发现工具** ([#72](https://github.com/Oaklight/toolregistry-hub/pull/72))
    - `glob()` — 按模式查找文件，按修改时间排序（上限 1000 条）
    - `grep()` — 正则表达式内容搜索，支持文件过滤（上限 200 条）
    - `tree()` — 目录树显示，支持深度控制（上限 2000 条目）

- **PathInfo：统一元数据查询** ([#71](https://github.com/Oaklight/toolregistry-hub/pull/71))
    - 单次 `info()` 调用返回存在性、类型、大小、修改时间和权限
    - 替代 `FileSystem` 的五个独立方法
    - 目录大小递归计算

- **CronTool：定时 Prompt 执行** ([#69](https://github.com/Oaklight/toolregistry-hub/issues/69), [4864ca7](https://github.com/Oaklight/toolregistry-hub/commit/4864ca7))
    - 支持标准 5 字段 cron 表达式调度
    - 循环和一次性两种模式，提供 `on_trigger` 回调用于 agent 运行时集成
    - 循环任务 7 天 TTL 自动过期
    - 可选持久化存储（JSON 文件）
    - 内置 zerodep/scheduler (v0.3.0) 作为内部依赖

- **API 密钥故障转移与认证/限流错误重试** ([#53](https://github.com/Oaklight/toolregistry-hub/issues/53), [29bdd13](https://github.com/Oaklight/toolregistry-hub/commit/29bdd13))
    - `APIKeyParser` 中线程安全的失败密钥追踪，基于 TTL 自动恢复（401/403 为 1 小时，429 为 5 分钟）
    - 修复双重密钥消耗 bug：将 `_headers` 属性替换为 `_build_headers(api_key)` 方法
    - 所有基于 API 密钥的搜索提供商（Brave、Tavily、Serper、Scrapeless、BrightData）新增重试循环，在 401/403/429 错误时自动尝试下一个有效密钥

### 弃用

- **FileSystem 类已弃用** ([#76](https://github.com/Oaklight/toolregistry-hub/pull/76))
    - 由 PathInfo（元数据）、FileSearch（发现）和 FileReader（读取）替代
    - 所有方法发出 `DeprecationWarning` 并附带迁移指引
    - 将在未来的主版本中移除

- **FileOps 旧方法已弃用** ([#76](https://github.com/Oaklight/toolregistry-hub/pull/76))
    - `read_file()` → 请使用 `FileReader.read()`
    - `write_file()` → 修改文件请使用 `FileOps.edit()`

### 内部变更

- **用 vendored zerodep/structlog 替换 loguru** ([#80](https://github.com/Oaklight/toolregistry-hub/pull/80), [7e17fb4](https://github.com/Oaklight/toolregistry-hub/commit/7e17fb4))
    - 移除 `loguru` 外部依赖，替换为 vendored 零依赖 structlog 模块
    - 所有日志现通过内部 `_structlog` 模块的 `get_logger()` 统一管理

### 修复

- **tool_config.py ty 类型检查错误** ([5890365](https://github.com/Oaklight/toolregistry-hub/commit/5890365))
    - 修复 ty 0.0.23 与 0.0.27 之间的字典类型收窄问题

### 构建

- `toolregistry-server` 最低版本提升至 `>=0.1.2`，修复 MCP 参数验证问题

### CI

- 增强上游兼容性测试，覆盖 `toolregistry-server`
- 支持兼容性检查中的多个上游包 ([d8d25e4](https://github.com/Oaklight/toolregistry-hub/commit/d8d25e4))
- 为 upstream-compat 工作流添加版本验证和 issues 权限 ([f590cc0](https://github.com/Oaklight/toolregistry-hub/commit/f590cc0))

## [0.7.0] - 2026-03-18

### 破坏性变更

- **服务器代码迁移至 `toolregistry-server`** ([#56](https://github.com/Oaklight/toolregistry-hub/issues/56), [#57](https://github.com/Oaklight/toolregistry-hub/pull/57))
    - 服务器相关功能（OpenAPI 适配器、MCP 适配器、CLI 服务器命令）已迁移至独立的 `toolregistry-server` 包
    - 依赖服务器功能的用户需单独安装 `toolregistry-server`

- **最低 Python 版本升级至 3.10** ([#54](https://github.com/Oaklight/toolregistry-hub/issues/54))
    - 不再支持 Python 3.8 和 3.9
    - 与 Python 3.9 EOL 及 MCP SDK 要求保持一致

- **`is_configured` 重命名为 `_is_configured`** ([#58](https://github.com/Oaklight/toolregistry-hub/pull/58))
    - 该方法现为私有方法，不再作为工具端点暴露

### 新功能

- **管理面板支持** ([a88ab25](https://github.com/Oaklight/toolregistry-hub/commit/a88ab25))
    - 新增 `--admin-port` 参数以启用服务器管理面板
    - 依赖 `toolregistry-server>=0.1.1`

- **Serper 搜索提供商** ([2305551](https://github.com/Oaklight/toolregistry-hub/commit/2305551))
    - 新增 Serper (serper.dev) 搜索提供商，获取 Google 搜索结果
    - 每月 2,500 次免费查询
    - 支持国家、语言和位置定向

- **`.env` 文件加载支持** ([#59](https://github.com/Oaklight/toolregistry-hub/pull/59))
    - 支持从 `.env` 文件加载环境变量
    - 新增 `--env-file` 和 `--no-env` CLI 选项

### 改进

- **依赖更新**
    - `toolregistry` 最低版本提升至 `>=0.6.0`
    - `toolregistry-server` 最低版本提升至 `>=0.1.1`

- **CI/CD**
    - 新增 ruff/ty CI 工作流用于代码检查和类型检查 ([e5b2f06](https://github.com/Oaklight/toolregistry-hub/commit/e5b2f06))
    - 新增上游兼容性测试工作流 ([79585d2](https://github.com/Oaklight/toolregistry-hub/commit/79585d2))
    - 在根 Makefile 中添加 lint 和 lint-fix 目标

### 重构

- **现代化类型注解至 Python 3.10+**
    - 将旧式 typing 导入替换为 Python 3.10+ 现代语法

- **MCP 服务器 FastMCP 重写**
    - 使用 FastMCP（MCP SDK 官方高级 API）重构 MCP 服务器实现
    - 修复 streamable-http transport 时序问题
    - 修复 ASGI 响应重复发送错误

### 文档

- **Brave Search 定价更新**
    - 记录 Brave Search API 免费计划移除（2026 年 2 月）
    - 更新为积分定价：$5/千次请求，每月赠送 $5 免费积分（约 1,000 次查询）

- **网络搜索文档刷新**
    - 新增 Serper 搜索文档（中/英）
    - 更新免费额度汇总表
    - 移除过时的"（推荐）"标签

## [0.6.0] - 2026-03-10

### 新功能

- **启动工具配置文件（JSONC）** ([#37](https://github.com/Oaklight/toolregistry-hub/issues/37), [#38](https://github.com/Oaklight/toolregistry-hub/pull/38))
    - 支持 JSONC（带注释的 JSON）配置文件，用于声明式指定服务器启动时加载的工具
    - 新增 `tool_config.py` 模块，包含 JSONC 解析器和工具配置加载器
    - 添加 `--tools-config` CLI 选项，用于指定配置文件路径
    - 提供 `tools.jsonc.example` 作为带文档说明的示例配置
    - 优雅降级：未指定配置文件时加载所有工具

- **从 ToolRegistry 自动生成路由** ([#31](https://github.com/Oaklight/toolregistry-hub/issues/31), [#36](https://github.com/Oaklight/toolregistry-hub/pull/36))
    - 新增 `autoroute.py` 模块，从 ToolRegistry 中注册的工具自动生成 FastAPI 路由
    - 内省 ToolRegistry 中注册的工具，自动生成端点处理器
    - 消除手写路由样板代码的需要
    - 将自动路由集成到服务器启动流程，支持回退到手动路由
    - 添加自动路由功能的全面测试

- **工具环境需求声明与中央注册表** ([#30](https://github.com/Oaklight/toolregistry-hub/issues/30), [#35](https://github.com/Oaklight/toolregistry-hub/pull/35))
    - 添加 `@requires_env` 装饰器，用于声明工具类所需的环境变量
    - 添加 `Configurable` 协议，提供 `is_configured()` 方法用于实例状态就绪检查（结构化子类型）
    - 添加 `build_registry()` / `get_registry()` 中央注册表，自动禁用未配置的工具
    - 将 `APIKeyParser` 和 `SearXNGSearch` 验证延迟到调用时，允许在无环境变量时正常初始化

- **WebSearch 工具嵌套命名空间** ([#39](https://github.com/Oaklight/toolregistry-hub/issues/39), [#40](https://github.com/Oaklight/toolregistry-hub/pull/40))
    - 支持嵌套命名空间如 `web/brave_search`，生成 `/tools/web/brave_search/search` 形式的 URL
    - 通过 `_HIDDEN_METHODS` 从 API 端点中隐藏内部方法（`is_configured`）

### 修复

- **Jina Reader 多引擎重试** ([#43](https://github.com/Oaklight/toolregistry-hub/pull/43))
    - 分离 httpx 传输超时与 Jina `X-Timeout`（增加 10 秒缓冲），防止竞态条件
    - 添加 `X-Wait-For-Selector` 请求头，使用常见内容选择器等待动态内容
    - 添加多引擎重试：先尝试 `browser`，失败后回退到 `cf-browser-rendering` 引擎
    - 提取 `_jina_reader_request()` 作为底层单次请求函数

- **Dockerfile 缺少服务器依赖**
    - 本地 wheel 安装路径改为使用 `[server]` extra，替代硬编码依赖列表
    - 确保所有依赖由 `pyproject.toml` 统一管理，防止 Docker 容器中出现 `ModuleNotFoundError`

### 重构

- **移除旧版手写路由文件** ([#39](https://github.com/Oaklight/toolregistry-hub/issues/39), [#40](https://github.com/Oaklight/toolregistry-hub/pull/40))
    - 移除 `calculator.py`、`datetime_tools.py`、`fetch.py`、`think.py`、`todo_list.py`、`unit_converter.py` 及 `routes/websearch/` 目录
    - 替换为从 ToolRegistry 自动生成的路由
    - 简化 `routes/__init__.py`，仅导出 `version_router`
    - `server_core.py` 使用自动生成路由配合 `version_router`

- **移除 BingSearch** ([#34](https://github.com/Oaklight/toolregistry-hub/pull/34))
    - 移除已弃用的 `BingSearch` 类、服务器路由及相关测试
    - 重写和现代化剩余搜索引擎的测试套件

- **重构服务器可选依赖** ([#29](https://github.com/Oaklight/toolregistry-hub/issues/29), [#33](https://github.com/Oaklight/toolregistry-hub/pull/33))
    - 更新 `server_openapi` 和 `server_mcp` extras 要求 `toolregistry>=0.5.0`
    - 重构 `server` extra 使用自引用组合

- 将 pyright 替换为 ty 进行类型检查
- `APIKeyParser.__init__` 不再在缺少密钥时抛出异常，改为延迟到调用时验证

## [0.5.6] - 2026-03-05

### 新功能

- **网页抓取改进**
	- 添加 Cloudflare 内容协商策略用于 Markdown 提取，增加默认超时时间
	- 为 `_extract()` 添加策略追踪日志，提升可观测性和调试能力
	- 改进 Jina Reader 回退机制：修复请求头（移除占位选择器，添加 `X-Engine: browser`、`X-Timeout`），使用 POST 方式发送 JSON 请求体并解析结构化 JSON 响应
	- 添加 `_is_content_sufficient()` 方法评估 BeautifulSoup 内容质量（最小长度阈值 + SPA 空壳页面检测）
	- 改进 `_extract()` 回退逻辑：BS4 低质量内容触发 Jina Reader；若 Jina 也失败，则回退到 BS4 结果
	- 增强日志记录，包含策略选择原因和内容质量指标
	- 添加全面的单元测试（43 个测试用例）

## [0.5.5] - 2026-01-31

### 重构

- **Think 工具增强**
	- 统一 reason 和 think 端点为单一的 think 端点
	- 重新排序参数并简化思考模式

### 维护

- **Docker 改进**
	- Dockerfile 添加 `REGISTRY_MIRROR` 构建参数，支持自定义镜像仓库
	- `.dockerignore` 添加 `references/` 目录忽略，减小镜像体积

## [0.5.4.post1] - 2026-01-13

### 修复

- **版本端点可见性**
	- 使用 `include_in_schema=False` 从 OpenAPI 文档中隐藏版本端点（`/version/` 和 `/version/check`）
	- 版本端点保持完全功能，可通过 HTTP 请求正常访问
	- 防止版本端点在 MCP 模式下被暴露为 LLM 工具

## [0.5.4] - 2026-01-13

### 重构

- **认知工具统一架构**
	- 将 reason 和 think 端点合并为单一的 think 端点，整合结构化推理与探索性思考功能
	- 合并思考模式：分析、假设、规划、验证、修正（结构化）与头脑风暴、心理模拟、换位思考、直觉（探索性）
	- 简化 API 表面，移除独立的 /reason 端点，更新请求模型
	- 统一参数命名：'thought' → 'thought_process'，'thinking_type' → 'thinking_mode'
	- 重构测试套件，覆盖所有思考模式和参数组合
	- 更新文档，反映 "recall + think" 的双工具认知架构

### 新功能

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

### 文档改进

- **网页搜索时间敏感查询指导**
	- 在所有网页搜索类 docstring 中添加重要提示
	- 强调 LLM 无时间感知能力，训练数据可能过时
	- 要求处理"最近新闻"等查询时先使用时间工具获取当前时间
	- 应用于所有搜索提供商类

- **日期时间工具文档增强**
	- 为 now() 和 convert_timezone() 方法添加详细描述
	- 扩展参数文档，包含时区格式示例
	- 路由描述直接引用方法 docstrings，提升一致性

### 维护

- **版本属性修复**
	- 更新 pyproject.toml 使用 __version__ 属性替代 version
	- 在 __init__.py 中添加 __version__ 变量，遵循 Python 版本约定
	- 保留 version 变量以保持向后兼容性

## [0.5.3] - 2025-12-13

### 重构

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

### 修复

- **Docker 构建流程**
	- 修复Dockerfile中包含服务器扩展包(fastapi, uvicorn, fastmcp)的包安装
	- 改进Makefile构建逻辑，提升包安装处理
	- 移除冗余的docker/requirements.txt文件
	- 增强本地wheel、特定版本和从PyPI最新版本的包安装逻辑

- **类型注解与兼容性**
	- 解决pyright兼容性的类型注解和参数命名问题
	- 修复server_core.py和websearch模块中的类型提示
	- 改进测试兼容性和类型安全

### 文档

- **Docker 文档**
	- 添加全面的Docker文档和迁移指南
	- 添加中英文Docker README文件
	- 提供OpenWebUI工具服务器迁移文档

## [0.5.2] - 2025-12-12

### 新功能

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

### 弃用

- **Bing 搜索**：由于机器人检测问题，标记 BingSearch 为已弃用

### 文档改进

- 更新 README 中的徽章样式
- 添加 DeepWiki 徽章到文档
- 更新项目描述和 README 文件
- 将 references 目录添加到 gitignore

## [0.5.1] - 2025-12-05

### 安全与认证

- **MCP 服务器认证** (#15)
	- 为 MCP 服务器添加 Bearer Token 认证支持
	- 实现 `DebugTokenVerifier` 用于 MCP 认证
	- 支持基于 Token 配置的认证和开放模式
	- 添加全面的认证事件日志记录
	- 将 Token 验证移至 FastAPI 全局依赖项
	- 重构认证架构，解耦路由和认证关注点

### 任务管理

- **Todo List 工具增强** (#15)
	- 添加 Todo List 工具，支持灵活的输入格式
	- 支持字典格式和简单字符串格式 `"[id] content (status)"`
	- 实现全面的输入验证和详细的错误消息
	- 增强状态选项，添加 "pending" 状态
	- 支持多种输出格式：'simple'（无输出）、'markdown' 和 'ascii'
	- 添加 Markdown 表格生成 API 端点
	- 改进文档和类型注解

### 服务器

- **架构重构**
	- 创建 `server_core.py` 模块提供基础 FastAPI 应用
	- 从所有路由中移除认证依赖
	- 支持创建认证和非认证服务器变体
	- 改进路由发现日志逻辑
	- 优化服务器架构，提升可维护性

### 日期时间

- **API 增强**
	- 为 `time_now` 端点添加 `TimeNowRequest` 模型
	- 使用结构化请求体替代查询参数
	- 保持与现有时区名称功能的向后兼容性
	- 改进 API 文档结构

### 文档

- **项目文档**
	- 更新项目描述和 README 文件
	- 将 README 引用从 `README.md` 改为 `readme_en.md`
	- 更新 PyPI 和 GitHub 徽章链接
	- 改进文档视觉一致性

## [0.5.0] - 2025-11-11

### 安全与认证

- **多 Bearer Token 认证** (#11)
	- 支持通过环境变量或文件配置多个 Bearer Token
	- 支持 `API_BEARER_TOKEN` 环境变量（逗号分隔）
	- 支持 `API_BEARER_TOKENS_FILE` 文件配置（每行一个 Token）
	- 添加 Token 缓存机制提升效率
	- 增强认证日志和调试功能
	- 新增独立的多 Token 认证测试套件

### 服务器 (#9)

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

### Docker

- **完整的容器化部署方案**
	- 添加 Dockerfile 用于构建容器镜像
	- 提供 `.env.sample` 环境变量参考
	- 添加 `requirements.txt` 依赖安装文件
	- 提供 `compose.yaml` 和 `compose.dev.yaml` 编排配置
	- 添加构建和推送自动化 Makefile
	- 优化 `.dockerignore` 减少镜像大小

### 网络搜索 (#8)

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

### 时区功能增强 (#5)

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

### 文档 (#10)

- **文档结构优化**
	- 重构文档结构，提升可读性
	- 添加多语言文档支持
	- 详细的 Docker 部署指南
	- 网络搜索引擎使用文档
	- API 端点和配置说明

### 测试 (#12)

- **测试覆盖增强**
	- 添加 0.4.16a0 版本测试
	- 多 Token 认证测试套件
	- 时区功能单元测试
	- 网络搜索引擎测试

### 重构

- **think_tool**: 简化 think 方法返回类型
	- 将返回类型从 `Dict[str, str]` 改为 `None`
	- 移除未使用的 typing 导入
	- 移除思考日志返回值，因为它未被使用

### 文档

- **文档托管**: 迁移文档到 ReadTheDocs 托管平台

## [0.4.15] - 2025-08-11

### 新功能

- **DateTime 工具**: 添加用于获取当前时间的 DateTime 实用工具
- **ThinkTool**: 新增推理和头脑风暴工具，为 AI 工具集成提供认知处理空间

### 文档

- 增强工具描述和使用示例
- 更新独立性声明和包上下文
- 改进 README 文档结构

### 维护

- 版本号提升至 0.4.15
- 依赖项更新和优化

## [0.4.14] - 首个正式发布版本

### 初始发布

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

- **新功能** - 新增功能或特性
- **重构** - 代码重构，不影响功能
- **修复** - 错误修复
- **文档** - 文档更新
- **安全** - 安全相关改进
- **服务器** - 服务器功能
- **Docker** - 容器化相关
- **搜索** - 搜索功能相关
- **时区** - 时区功能相关
- **测试** - 测试相关改进
- **维护** - 维护性更新

### 获取更新

要获取最新版本，请使用：

```bash
pip install --upgrade toolregistry-hub
```

### 反馈和建议

如果您发现任何问题或有改进建议，请在我们的 [GitHub 仓库](https://github.com/OakLight/toolregistry-hub) 提交 Issue。
