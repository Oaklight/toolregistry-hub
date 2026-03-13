---
title: Changelog
summary: Version history and change records for the toolregistry-hub project
description: Detailed documentation of all feature updates, fixes, and improvements in toolregistry-hub since version 0.4.14
keywords: changelog, version history, release notes, changes
author: Oaklight
---

# Changelog

This page documents all notable changes to the toolregistry-hub project since the first official release version 0.4.14.

## [Unreleased]

### New Features

- Added Serper search provider integration

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
