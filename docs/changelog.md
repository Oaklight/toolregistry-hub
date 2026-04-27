---
title: Changelog
summary: Version history and change records for the toolregistry-hub project
description: Detailed documentation of all feature updates, fixes, and improvements in toolregistry-hub since version 0.4.14
keywords: changelog, version history, release notes, changes
author: Oaklight
---

# Changelog

This page documents all notable changes to the toolregistry-hub project since the first official release version 0.4.14.

## [Unreleased] - since 0.8.0

### New Features

- **Tool discovery with progressive disclosure**
    - Call `registry.enable_tool_discovery()` to register a `discover_tools` tool for BM25F search across all registered tools
    - Less-used tools (FileReader, FileSearch, PathInfo, BashTool, CronTool, TodoList, UnitConverter) marked as deferred — discoverable via `discover_tools` but excluded from initial schema for smart clients
    - Add `--tool-discovery / --no-tool-discovery` CLI flag (default: enabled)

- **Think-augmented function calling**
    - Inject a `thought` property into tool schemas for chain-of-thought reasoning ([arXiv:2601.18282](https://arxiv.org/abs/2601.18282))
    - Built-in dedup prevents double injection when both server and harness enable it
    - Add `--think-augment / --no-think-augment` CLI flag (default: enabled)

- **ToolTag metadata for all registered tools**
    - Assign `ToolTag` labels (`READ_ONLY`, `DESTRUCTIVE`, `NETWORK`, `FILE_SYSTEM`, `PRIVILEGED`) to every default tool based on its behavior
    - Tags are available via `tool.metadata.tags` for filtering and display

- **Fetch: Jina API key support with multi-key rotation**
    - `Fetch` class now accepts optional `api_keys` parameter for Jina Reader authentication
    - Falls back to `JINA_API_KEY` environment variable (comma-separated for multiple keys)
    - Round-robin key rotation with automatic failure tracking (HTTP 401/403 → 1h cooldown, HTTP 429 → 5min cooldown)

- **Fetch: User-specified extraction engine**
    - Add `engine` parameter to `_extract()`: `"auto"` (default fallback chain), `"markdown"`, `"readability"`, `"soup"`, `"jina"`
    - Direct engine mode skips fallback chain — only the specified engine is tried

- **Fetch: Replace BS4 with readability + soup extraction pipeline** ([#87](https://github.com/Oaklight/toolregistry-hub/pull/87), [#83](https://github.com/Oaklight/toolregistry-hub/issues/83))
    - Replace simplistic BeautifulSoup CSS selector extraction with multi-strategy pipeline: readability (Mozilla Readability.js port, intelligent article scoring) → soup (structural CSS fallback)
    - HTML fetched once and shared across both local strategies; readability preferred unless soup extracts >2x more content
    - Vendor readability and soup modules from [zerodep](https://github.com/Oaklight/zerodep) into `_vendor/` with nested layout

- **WebSearch: Unified entry point with dynamic engine selection**
    - New `WebSearch` class registered at `web/websearch` namespace; the 6 individual provider tools (`web/brave_search`, `web/tavily_search`, etc.) are now deferred and discoverable via `discover_tools`
    - `search(query, engine="auto", fallback=False, ...)` — `engine="auto"` tries configured providers in priority order; specific engines fail loudly when their key is missing, or fall through to auto when `fallback=True`
    - Configurable priority via `WEBSEARCH_PRIORITY` environment variable (comma-separated names); default order is paid-providers-first
    - Per-instance dynamic narrowing of the `engine` `Literal` annotation: at construction time, the JSON schema seen by LLM clients only includes engines whose API keys are actually configured on this server
    - `list_engines()` helper for runtime introspection of available providers

### Code Cleanup

- Remove dead code from `fetch.py`: `_get_lynx_useragent()`, `HEADERS_LYNX`, `_remove_emojis()`, unused `random` import
- Move Lynx-based user-agent generation to `_legacy` for future Chrome CDP reference
- Convert `Fetch` from static utility to instance class for API key state management

### Deprecations

- **FileSystem removed from default server registry**
    - `FileSystem` class is no longer registered in server mode; replaced by PathInfo, FileSearch, and FileReader
    - The class itself is kept for library backward compatibility and still emits `DeprecationWarning`

### Internal Changes

- Consolidate all zerodep vendored modules (structlog, scheduler, readability, soup) into `_vendor/` with nested layout ([#87](https://github.com/Oaklight/toolregistry-hub/pull/87))
- Remove `beautifulsoup4` external dependency; migrate `websearch_legacy` (bing, google) to zerodep soup ([#87](https://github.com/Oaklight/toolregistry-hub/pull/87))
- Exclude `_vendor/` from ruff UP035 lint rule and ty type checking
- Refactor CLI to always build registry with CLI flags instead of only when `--config` is set
- Fix deprecated `with_namespace=` parameter in `register_from_class()` calls (now uses `namespace=`)

### Fixes

- **SearXNG: Support optional X-API-Key header for protected instances** ([#85](https://github.com/Oaklight/toolregistry-hub/pull/85))
    - Add optional `api_key` parameter to `SearXNGSearch`, with fallback to `SEARXNG_API_KEY` environment variable
    - When set, sends `X-API-Key` header with JSON API requests; fully backwards compatible

## [0.8.0] - 2026-04-06

### Breaking Changes

- **FileOps: Replace diff-based editing with exact string replacement** ([#70](https://github.com/Oaklight/toolregistry-hub/pull/70), [#62](https://github.com/Oaklight/toolregistry-hub/issues/62))
    - Removed `replace_by_diff()` and `replace_by_git()` methods
    - Added `edit(file_path, old_string, new_string)` with exact string matching
    - Supports `replace_all` for bulk replacement and `start_line` for disambiguation when multiple matches exist
    - Preserves file encoding (UTF-8/UTF-8-sig/UTF-16) and line endings (CRLF/LF)
    - Returns unified diff of changes

### New Features

- **BashTool: Shell command execution with safety validation** ([#77](https://github.com/Oaklight/toolregistry-hub/pull/77), [#66](https://github.com/Oaklight/toolregistry-hub/issues/66))
    - Execute shell commands via `subprocess.run` with configurable timeout and working directory
    - Built-in deny list blocks dangerous patterns (rm -rf, sudo, fork bombs, pipe-to-shell, git force push, etc.)
    - Deny list based on security survey of 6 AI coding CLI tools
    - Lazy upstream `ToolMetadata` integration for future permission system support
    - stdout/stderr truncation at 64KB to prevent memory exhaustion

- **FileReader: Multi-format file reading** ([#75](https://github.com/Oaklight/toolregistry-hub/pull/75), [#65](https://github.com/Oaklight/toolregistry-hub/issues/65), [#79](https://github.com/Oaklight/toolregistry-hub/pull/79))
    - `read()` — text files with line numbers and pagination (10MB cap, 2000 lines default)
    - `read_notebook()` — Jupyter notebooks with cell types and outputs (stdlib only)
    - `read_pdf()` — PDF text extraction via pypdf or pdfplumber (optional dependency)
    - `read_image()` — image files as multimodal content blocks (`[TextBlock, ImageBlock]`) with adaptive downsampling via Pillow ([#79](https://github.com/Oaklight/toolregistry-hub/pull/79), [#74](https://github.com/Oaklight/toolregistry-hub/issues/74))
    - Supports `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp` formats
    - Auto-downsamples images exceeding the base64 size budget (default 5 MB) with format-specific quality floors
    - Add `reader_image = ["Pillow>=10.0.0"]` optional dependency group

- **FileSearch: File discovery tools** ([#72](https://github.com/Oaklight/toolregistry-hub/pull/72))
    - `glob()` — find files by pattern, sorted by modification time (1000 results cap)
    - `grep()` — regex content search with file filtering (200 results cap)
    - `tree()` — directory tree display with depth control (2000 entries cap)

- **PathInfo: Unified metadata query** ([#71](https://github.com/Oaklight/toolregistry-hub/pull/71))
    - Single `info()` call returns existence, type, size, modification time, and permissions
    - Replaces five separate `FileSystem` methods
    - Recursive size calculation for directories

- **CronTool: Scheduled prompt execution** ([#69](https://github.com/Oaklight/toolregistry-hub/issues/69), [4864ca7](https://github.com/Oaklight/toolregistry-hub/commit/4864ca7))
    - Cron expression scheduling with standard 5-field format
    - Recurring and one-shot modes with `on_trigger` callback for agent runtime integration
    - 7-day TTL auto-expiry for recurring jobs
    - Optional durable persistence via JSON file
    - Vendored zerodep/scheduler (v0.3.0) as internal dependency

- **API key failover with retry on auth/rate-limit errors** ([#53](https://github.com/Oaklight/toolregistry-hub/issues/53), [29bdd13](https://github.com/Oaklight/toolregistry-hub/commit/29bdd13))
    - Thread-safe failed key tracking in `APIKeyParser` with TTL-based auto-recovery (1h for 401/403, 5min for 429)
    - Fix double key consumption bug: replace `_headers` property with `_build_headers(api_key)` method
    - Retry loop in all API-key-based websearch providers (Brave, Tavily, Serper, Scrapeless, BrightData) that automatically tries the next valid key on 401/403/429 errors

### Deprecations

- **FileSystem class deprecated** ([#76](https://github.com/Oaklight/toolregistry-hub/pull/76))
    - Replaced by PathInfo (metadata), FileSearch (discovery), and FileReader (reading)
    - All methods emit `DeprecationWarning` with migration guidance
    - Will be removed in a future major release

- **FileOps legacy methods deprecated** ([#76](https://github.com/Oaklight/toolregistry-hub/pull/76))
    - `read_file()` → use `FileReader.read()`
    - `write_file()` → use `FileOps.edit()` for modifications

### Internal

- **Replace loguru with vendored zerodep/structlog** ([#80](https://github.com/Oaklight/toolregistry-hub/pull/80), [7e17fb4](https://github.com/Oaklight/toolregistry-hub/commit/7e17fb4))
    - Remove `loguru` external dependency, replaced with vendored zero-dependency structlog module
    - All logging now uses `get_logger()` from internal `_structlog` module

### Fixes

- **ty type-check error in tool_config.py** ([5890365](https://github.com/Oaklight/toolregistry-hub/commit/5890365))
    - Fixed dict type narrowing issue between ty 0.0.23 and 0.0.27

### Build

- Bump `toolregistry-server` minimum to `>=0.1.2` for MCP parameter validation fix

### CI

- Enhanced upstream compatibility tests to cover `toolregistry-server`
- Support multiple upstream packages in compat check ([d8d25e4](https://github.com/Oaklight/toolregistry-hub/commit/d8d25e4))
- Add version validation and issues permission to upstream-compat workflow ([f590cc0](https://github.com/Oaklight/toolregistry-hub/commit/f590cc0))

## [0.7.0] - 2026-03-18

### Breaking Changes

- **Server Code Migrated to `toolregistry-server`** ([#56](https://github.com/Oaklight/toolregistry-hub/issues/56), [#57](https://github.com/Oaklight/toolregistry-hub/pull/57))
    - Server-related functionality (OpenAPI adapter, MCP adapter, CLI server commands) has been moved to the standalone `toolregistry-server` package
    - Users who relied on server features should install `toolregistry-server` separately

- **Minimum Python Version Upgraded to 3.10** ([#54](https://github.com/Oaklight/toolregistry-hub/issues/54))
    - Python 3.8 and 3.9 no longer supported
    - Aligns with Python 3.9 EOL and MCP SDK requirements

- **`is_configured` Renamed to `_is_configured`** ([#58](https://github.com/Oaklight/toolregistry-hub/pull/58))
    - The method is now private and no longer exposed as a tool endpoint

### New Features

- **Admin Panel Support** ([a88ab25](https://github.com/Oaklight/toolregistry-hub/commit/a88ab25))
    - Add `--admin-port` flag to enable admin panel for server management
    - Requires `toolregistry-server>=0.1.1`

- **Serper Search Provider** ([2305551](https://github.com/Oaklight/toolregistry-hub/commit/2305551))
    - Add Serper (serper.dev) search provider for Google search results
    - 2,500 free queries per month
    - Supports country, language, and location targeting

- **`.env` File Loading Support** ([#59](https://github.com/Oaklight/toolregistry-hub/pull/59))
    - Support for loading environment variables from `.env` files
    - Added `--env-file` and `--no-env` CLI options

### Improvements

- **Dependency Updates**
    - Bump `toolregistry` minimum to `>=0.6.0`
    - Bump `toolregistry-server` minimum to `>=0.1.1`

- **CI/CD**
    - Add ruff/ty CI workflow for lint and type checking ([e5b2f06](https://github.com/Oaklight/toolregistry-hub/commit/e5b2f06))
    - Add upstream compatibility test workflow ([79585d2](https://github.com/Oaklight/toolregistry-hub/commit/79585d2))
    - Add lint and lint-fix targets to root Makefile

### Refactoring

- **Modernize Type Annotations to Python 3.10+**
    - Replaced legacy typing imports with modern Python 3.10+ syntax

- **MCP Server FastMCP Rewrite**
    - Refactored MCP server implementation using FastMCP (official MCP SDK high-level API)
    - Fixed streamable-http transport timing issues
    - Fixed ASGI duplicate response errors

### Documentation

- **Brave Search Pricing Update**
    - Document Brave Search API free plan removal (Feb 2026)
    - Update to credit-based pricing: $5/1k requests with $5 free monthly credits (~1,000 queries)

- **Web Search Docs Refresh**
    - Add Serper search documentation (EN/ZH)
    - Update free tier summary tables
    - Remove outdated "(Recommended)" labels

## [0.6.0] - 2026-03-10

### New Features

- **Startup Tool Configuration via JSONC** ([#37](https://github.com/Oaklight/toolregistry-hub/issues/37), [#38](https://github.com/Oaklight/toolregistry-hub/pull/38))
    - Add JSONC (JSON with Comments) configuration file support for declarative tool loading at server startup
    - New `tool_config.py` module with JSONC parser and tool configuration loader
    - Add `--tools-config` CLI option to specify configuration file path
    - Provide `tools.jsonc.example` as a documented example configuration
    - Graceful fallback: loads all tools if no config file is specified

- **Auto-Route Generation from ToolRegistry** ([#31](https://github.com/Oaklight/toolregistry-hub/issues/31), [#36](https://github.com/Oaklight/toolregistry-hub/pull/36))
    - Add `autoroute.py` module for automatic FastAPI route generation from registered tools in ToolRegistry
    - Introspect tools registered in ToolRegistry and automatically generate endpoint handlers
    - Eliminate the need for hand-written route boilerplate
    - Integrate auto-route into server startup with fallback to manual routes
    - Add comprehensive tests for autoroute functionality

- **Tool Environment Requirements and Central Registry** ([#30](https://github.com/Oaklight/toolregistry-hub/issues/30), [#35](https://github.com/Oaklight/toolregistry-hub/pull/35))
    - Add `@requires_env` decorator to declare required environment variables on tool classes
    - Add `Configurable` protocol with `is_configured()` for instance-state readiness checks (structural subtyping)
    - Add `build_registry()` / `get_registry()` central registry that auto-disables unconfigured tools
    - Defer `APIKeyParser` and `SearXNGSearch` validation to call time, allowing graceful initialization without env vars

- **Nested Namespaces for WebSearch Tools** ([#39](https://github.com/Oaklight/toolregistry-hub/issues/39), [#40](https://github.com/Oaklight/toolregistry-hub/pull/40))
    - Support nested namespaces like `web/brave_search`, producing URLs like `/tools/web/brave_search/search`
    - Hide internal methods (`is_configured`) from API endpoints via `_HIDDEN_METHODS`

### Bug Fixes

- **Jina Reader Multi-Engine Retry** ([#43](https://github.com/Oaklight/toolregistry-hub/pull/43))
    - Separate httpx transport timeout from Jina `X-Timeout` (add 10s buffer) to prevent race conditions
    - Add `X-Wait-For-Selector` header with common content selectors for dynamic content
    - Add multi-engine retry: try `browser` first, fall back to `cf-browser-rendering` engine for JS-heavy websites
    - Extract `_jina_reader_request()` as low-level single-request function

- **Dockerfile Missing Server Dependencies**
    - Local wheel install path now uses `[server]` extra instead of hardcoded dependency list
    - Ensures all dependencies are managed by `pyproject.toml`, preventing `ModuleNotFoundError` in Docker containers

### Refactoring

- **Remove Legacy Hand-Written Route Files** ([#39](https://github.com/Oaklight/toolregistry-hub/issues/39), [#40](https://github.com/Oaklight/toolregistry-hub/pull/40))
    - Remove `calculator.py`, `datetime_tools.py`, `fetch.py`, `think.py`, `todo_list.py`, `unit_converter.py`, and `routes/websearch/` directory
    - Replace with auto-generated routes from ToolRegistry
    - Simplify `routes/__init__.py` to export only `version_router`
    - `server_core.py` uses auto-generated routes alongside `version_router`

- **Remove BingSearch** ([#34](https://github.com/Oaklight/toolregistry-hub/pull/34))
    - Remove deprecated `BingSearch` class, server route, and related tests
    - Rewrite and modernize websearch test suite for remaining engines

- **Restructure Server Optional Dependencies** ([#29](https://github.com/Oaklight/toolregistry-hub/issues/29), [#33](https://github.com/Oaklight/toolregistry-hub/pull/33))
    - Update `server_openapi` and `server_mcp` extras to require `toolregistry>=0.5.0`
    - Refactor `server` extra to use self-referencing composition

- Replace pyright with ty for type checking
- `APIKeyParser.__init__` no longer raises on missing keys; defers validation to call time

## [0.5.6] - 2026-03-05

### New Features

- **Web Fetch Improvements**
	- Add Cloudflare content negotiation strategy for markdown extraction, increasing default timeout
	- Add strategy tracking logs to `_extract()` for better observability and debugging
	- Improve Jina Reader fallback: fix headers (remove placeholder selectors, add `X-Engine: browser`, `X-Timeout`), use POST with JSON body and structured JSON response parsing
	- Add `_is_content_sufficient()` to evaluate BeautifulSoup content quality (minimum length threshold + SPA shell indicator detection)
	- Improve `_extract()` fallback logic: low-quality BS4 content triggers Jina Reader; if Jina also fails, fall back to BS4 result
	- Enhance logging with strategy reasons and content quality metrics
	- Add comprehensive unit tests (43 test cases)

## [0.5.5] - 2026-01-31

### Refactoring

- **Think Tool Enhancement**
	- Unify reason and think endpoints into single think endpoint
	- Reorder parameters and simplify thinking modes

### Maintenance

- **Docker Improvements**
	- Add `REGISTRY_MIRROR` build argument to Dockerfile for custom registry support
	- Add `references/` directory to `.dockerignore` to reduce image size

## [0.5.4.post1] - 2026-01-13

### Bug Fixes

- **Version Endpoint Visibility**
	- Hide version endpoints (`/version/` and `/version/check`) from OpenAPI documentation using `include_in_schema=False`
	- Version endpoints remain fully functional and accessible via HTTP requests
	- Prevents version endpoints from being exposed as LLM tools in MCP mode

## [0.5.4] - 2026-01-13

### Refactoring

- **Unified Cognitive Tools Architecture**
	- Consolidate reason and think endpoints into single think endpoint, combining structured reasoning and exploratory thinking
	- Merge thinking modes: analysis, hypothesis, planning, verification, correction (structured) with brainstorming, mental_simulation, perspective_taking, intuition (exploratory)
	- Simplify API surface by removing separate /reason endpoint and updating request models
	- Unify parameter naming: 'thought' → 'thought_process', 'thinking_type' → 'thinking_mode'
	- Refactor test suite with comprehensive coverage of all thinking modes and parameter combinations
	- Update documentation to reflect "recall + think" dual-tool cognitive architecture

### New Features

- **PyPI Version Check & Update Notifications**
	- Add comprehensive PyPI version checking system, inspired by argo-proxy implementation
	- New `version_check.py` module with async PyPI API calls and intelligent version comparison
	- Implement pre-release version support (alpha, beta, rc) and event loop safety handling
	- Add `/version/` and `/version/check` API endpoints returning version info and update status
	- CLI adds `--version` parameter to display current version and check for updates
	- Enhanced startup banner with automatic version info and update notifications
	- Use standard library for version comparison without additional dependencies
	- Include complete synchronous test suite (10 tests)

- **ASCII Art Banner**
	- Add new banner.py module with ASCII art banner
	- Implement centered alignment and consistent border styling (80-char width)
	- Display banner on CLI startup with show_banner=False parameter to disable

### Documentation

- **Time-Sensitive Query Guidance for Web Search**
	- Add IMPORTANT note in all websearch class docstrings
	- Emphasize LLMs have no inherent sense of time and training data may be outdated
	- Require checking current time with datetime tools for queries like "recent news"
	- Applied to all search provider classes

- **DateTime Tools Documentation Enhancement**
	- Add detailed descriptions for now() and convert_timezone() methods
	- Expand parameter documentation with timezone format examples
	- Route descriptions directly reference method docstrings for better consistency

### Maintenance

- **Version Attribute Fix**
	- Update pyproject.toml to use __version__ attribute instead of version
	- Add __version__ variable in __init__.py following Python version convention
	- Maintain backward compatibility by keeping version variable

## [0.5.3] - 2025-12-13

### Refactoring

- **Multi-API Key Management System**
	- Consolidate scattered API key implementations into centralized APIKeyParser utility
	- Replace individual API key management across websearch engines with unified system
	- Implement consistent API key rotation and error handling across all search providers
	- Refactor all websearch engines (Brave, Brightdata, Scrapeless, Tavily) to use centralized API key management
	- Improve search engine reliability and performance
	- Add rate limiting support to API key parser

- **Utils Module Structure**
	- Migrate utils module to package structure for better organization
	- Add fn_namespace.py module for function namespace utilities
	- Improve module imports and dependencies
	- Simplify version extraction from pyproject.toml
	- Update build configuration for better reproducibility

- **Version Management System**
	- Configure pyproject.toml to use dynamic version loading from toolregistry_hub.version
	- Remove hardcoded version from pyproject.toml, use setuptools dynamic version attribute
	- Centralize version management with single source of truth in `__init__.py`
	- Improve build process with setuptools dynamic version support

### Bug Fixes

- **Docker Build Process**
	- Fix Dockerfile package installation with server extras (fastapi, uvicorn, fastmcp)
	- Improve Makefile build logic for better package installation handling
	- Remove redundant docker/requirements.txt file
	- Enhance package installation logic for local wheel, specific version, and latest from PyPI

- **Type Annotations & Compatibility**
	- Resolve type annotation and parameter naming issues for pyright compatibility
	- Fix type hints in server_core.py and websearch modules
	- Improve test compatibility and type safety

### Documentation

- **Docker Documentation**
	- Add comprehensive Docker documentation and migration guide
	- Add Docker README files in both English and Chinese
	- Provide OpenWebUI tool server migration documentation

## [0.5.2] - 2025-12-12

### New Features

- **Unit Converter API Routes**
	- Add unit converter API routes
	- Refactor unit converter with base class and utility methods
	- Update unit converter tests

- **Web Search Enhancements**
	- Add Scrapeless DeepSERP API (Google SERP) integration
	- Add Bright Data search (Google SERP) integration
	- Implement universal Google search results parser
	- Add Bright Data engines test for Bing and Yandex
	- Add environment variable support for Bing search proxy

### Deprecations

- **Bing Search**: Mark BingSearch as deprecated due to bot detection issues

### Documentation

- Update badge styles in README
- Add DeepWiki badge to documentation
- Update project description and README file
- Add references directory to gitignore

## [0.5.1] - 2025-12-05

### Security & Authentication

- **MCP Server Authentication** (#15)
	- Add Bearer Token authentication support for MCP server
	- Implement `DebugTokenVerifier` for MCP authentication
	- Support authenticated and open modes based on token configuration
	- Add comprehensive authentication event logging
	- Move token verification to FastAPI global dependencies
	- Refactor authentication architecture, decoupling routes and authentication concerns

### Task Management

- **Todo List Tool Enhancements** (#15)
	- Add Todo List tool with flexible input format support
	- Support both dictionary format and simple string format `"[id] content (status)"`
	- Implement comprehensive input validation with detailed error messages
	- Enhance status options with "pending" status
	- Support multiple output formats: 'simple' (no output), 'markdown', and 'ascii'
	- Add Markdown table generation API endpoint
	- Improve documentation and type annotations

### Server

- **Architecture Refactoring**
	- Create `server_core.py` module providing base FastAPI application
	- Remove authentication dependencies from all routes
	- Enable creation of both authenticated and non-authenticated server variants
	- Improve router discovery logging logic
	- Optimize server architecture for better maintainability

### Date and Time

- **API Enhancements**
	- Add `TimeNowRequest` model for `time_now` endpoint
	- Use structured request body instead of query parameters
	- Maintain backward compatibility with existing timezone name functionality
	- Improve API documentation structure

### Documentation

- **Project Documentation**
	- Update project description and README files
	- Change README reference from `README.md` to `readme_en.md`
	- Update PyPI and GitHub badge links
	- Improve documentation visual consistency

## [0.5.0] - 2025-11-11

### Security & Authentication

- **Multi Bearer Token Authentication** (#11)
	- Support multiple Bearer tokens via environment variables or file configuration
	- Support `API_BEARER_TOKEN` environment variable (comma-separated)
	- Support `API_BEARER_TOKENS_FILE` file configuration (one token per line)
	- Add token caching mechanism for improved efficiency
	- Enhanced authentication logging and debugging features
	- New standalone multi-token authentication test suite

### Server (#9)

- **REST API Server**
	- New `toolregistry-server` CLI command-line tool
	- Support for OpenAPI and MCP server modes
	- Individual REST API endpoints for each tool:
		- Calculator API (`/calculator`)
		- DateTime API (`/datetime`)
		- Web Fetch API (`/fetch`)
		- Think Tool API (`/think`)
		- Web Search API (`/websearch`)
	- Automatic router discovery and registration mechanism
	- Recursive router discovery for nested modules

### Docker

- **Complete Containerized Deployment Solution**
	- Add Dockerfile for building container images
	- Provide `.env.sample` environment variable reference
	- Add `requirements.txt` for dependency installation
	- Provide `compose.yaml` and `compose.dev.yaml` orchestration configs
	- Add automated build and push Makefile
	- Optimize `.dockerignore` to reduce image size

### Web Search (#8)

- **New Search Engine Support**

	- Add Brave Search API integration
	- Add Tavily Search API integration
	- Add SearXNG search engine support
	- Refactor Bing search with modern implementation

- **Unified Search Architecture**

	- Introduce `BaseSearch` abstract base class
	- Standardize search API method signatures
	- Use `SearchResult` dataclass for type safety
	- Unified header generation and content fetching logic

- **Advanced Search Features**

	- Multi API key support (Brave and Tavily)
	- Pagination support for up to 180 results
	- Flexible search parameters and filtering options
	- Improved result parsing and error handling

- **User Agent Optimization**

	- Replace `fake-useragent` with `ua-generator`
	- Dynamic user agent generation for better anti-bot evasion
	- Enhanced browser fingerprinting realism

- **Module Restructuring**
	- Move modern search engines to `websearch/` directory
	- Move legacy search implementations to `websearch_legacy/` directory
	- Clean up outdated Google search modules

### Timezone Enhancements (#5)

- **Timezone Support**

	- `DateTime.now()` supports timezone parameter specification
	- New `convert_timezone()` timezone conversion functionality
	- Support IANA timezone names (e.g., "Asia/Shanghai")
	- Support UTC/GMT offset formats (e.g., "UTC+5:30", "GMT-3")
	- Handle fractional hour offsets (e.g., Nepal UTC+5:45)

- **Python Compatibility**
	- Support Python 3.8 via `backports.zoneinfo`
	- Unified timezone parsing logic
	- Improved error handling and exception messages

### Documentation (#10)

- **Documentation Structure Optimization**
	- Refactor documentation structure for improved readability
	- Add multi-language documentation support
	- Detailed Docker deployment guides
	- Web search engine usage documentation
	- API endpoint and configuration instructions

### Testing (#12)

- **Enhanced Test Coverage**
	- Add 0.4.16a0 version testing
	- Multi-token authentication test suite
	- Timezone functionality unit tests
	- Web search engine testing

### Refactoring

- **think_tool**: Simplify think method return type
	- Change return type from `Dict[str, str]` to `None`
	- Remove unused typing import for Dict
	- Remove thought logging return value since it's not used

### Documentation

- **Documentation hosting**: Migrate documentation to ReadTheDocs hosting

## [0.4.15] - 2025-08-11

### New Features

- **DateTime Tool**: Add DateTime utility for current time retrieval
- **ThinkTool**: Add reasoning and brainstorming tool providing cognitive processing space for AI tool integration

### Documentation

- Enhance tool descriptions and usage examples
- Update independence notice and package context
- Improve README documentation structure

### Maintenance

- Bump version to 0.4.15
- Update and optimize dependencies

## [0.4.14] - First Official Release

### Initial Release

- Basic tool collection
- Core functionality implementation
- Basic documentation structure
- Test framework establishment

---

## Version Notes

### Semantic Versioning

This project follows [Semantic Versioning](https://semver.org/) specification:

- **Major version**: Incompatible API changes
- **Minor version**: Backward-compatible functionality additions
- **Patch version**: Backward-compatible bug fixes

### Change Type Legend

- **New Features** - New functionality or features
- **Refactoring** - Code refactoring without functional changes
- **Bug Fixes** - Error corrections
- **Documentation** - Documentation updates
- **Security** - Security-related improvements
- **Server** - Server functionality
- **Docker** - Containerization related
- **Search** - Search functionality related
- **Timezone** - Timezone functionality related
- **Testing** - Testing-related improvements
- **Maintenance** - Maintenance updates

### Getting Updates

To get the latest version, use:

```bash
pip install --upgrade toolregistry-hub
```

### Feedback and Suggestions

If you find any issues or have improvement suggestions, please submit an Issue in our [GitHub repository](https://github.com/OakLight/toolregistry-hub).
