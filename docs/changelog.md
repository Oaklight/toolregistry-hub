---
title: Changelog
summary: Version history and change records for the toolregistry-hub project
description: Detailed documentation of all feature updates, fixes, and improvements in toolregistry-hub since version 0.4.14
keywords: changelog, version history, release notes, changes
author: Oaklight
---

# Changelog

This page documents all notable changes to the toolregistry-hub project since the first official release version 0.4.14.

## [0.5.2] - 2025-12-12

### ✨ New Features

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

### ⚠️ Deprecations

- **Bing Search**: Mark BingSearch as deprecated due to bot detection issues

### 📝 Documentation Improvements

- Update badge styles in README
- Add DeepWiki badge to documentation
- Update project description and README file
- Add references directory to gitignore

## [0.5.1] - 2025-12-05

### 🔐 Security & Authentication

- **MCP Server Authentication** (#15)
	- Add Bearer Token authentication support for MCP server
	- Implement `DebugTokenVerifier` for MCP authentication
	- Support authenticated and open modes based on token configuration
	- Add comprehensive authentication event logging
	- Move token verification to FastAPI global dependencies
	- Refactor authentication architecture, decoupling routes and authentication concerns

### 📋 Task Management Enhancements

- **Todo List Tool Enhancements** (#15)
	- Add Todo List tool with flexible input format support
	- Support both dictionary format and simple string format `"[id] content (status)"`
	- Implement comprehensive input validation with detailed error messages
	- Enhance status options with "pending" status
	- Support multiple output formats: 'simple' (no output), 'markdown', and 'ascii'
	- Add Markdown table generation API endpoint
	- Improve documentation and type annotations

### 🌐 Server Features

- **Architecture Refactoring**
	- Create `server_core.py` module providing base FastAPI application
	- Remove authentication dependencies from all routes
	- Enable creation of both authenticated and non-authenticated server variants
	- Improve router discovery logging logic
	- Optimize server architecture for better maintainability

### 🕐 Date and Time Features

- **API Enhancements**
	- Add `TimeNowRequest` model for `time_now` endpoint
	- Use structured request body instead of query parameters
	- Maintain backward compatibility with existing timezone name functionality
	- Improve API documentation structure

### 📝 Documentation Improvements

- **Project Documentation**
	- Update project description and README files
	- Change README reference from `README.md` to `readme_en.md`
	- Update PyPI and GitHub badge links
	- Improve documentation visual consistency

## [0.5.0] - 2025-11-11

### 🔐 Security & Authentication

- **Multi Bearer Token Authentication** (#11)
	- Support multiple Bearer tokens via environment variables or file configuration
	- Support `API_BEARER_TOKEN` environment variable (comma-separated)
	- Support `API_BEARER_TOKENS_FILE` file configuration (one token per line)
	- Add token caching mechanism for improved efficiency
	- Enhanced authentication logging and debugging features
	- New standalone multi-token authentication test suite

### 🌐 Server Features (#9)

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

### 🐳 Docker Support

- **Complete Containerized Deployment Solution**
	- Add Dockerfile for building container images
	- Provide `.env.sample` environment variable reference
	- Add `requirements.txt` for dependency installation
	- Provide `compose.yaml` and `compose.dev.yaml` orchestration configs
	- Add automated build and push Makefile
	- Optimize `.dockerignore` to reduce image size

### 🔍 Modern Web Search (#8)

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

### 🕐 Timezone Enhancements (#5)

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

### 📚 Documentation Refactoring (#10)

- **Documentation Structure Optimization**
	- Refactor documentation structure for improved readability
	- Add multi-language documentation support
	- Detailed Docker deployment guides
	- Web search engine usage documentation
	- API endpoint and configuration instructions

### 🧪 Testing Improvements (#12)

- **Enhanced Test Coverage**
	- Add 0.4.16a0 version testing
	- Multi-token authentication test suite
	- Timezone functionality unit tests
	- Web search engine testing

### 🔄 Refactoring

- **think_tool**: Simplify think method return type
	- Change return type from `Dict[str, str]` to `None`
	- Remove unused typing import for Dict
	- Remove thought logging return value since it's not used

### 📚 Documentation

- **Documentation hosting**: Migrate documentation to ReadTheDocs hosting

## [0.4.15] - 2025-08-11

### ✨ New Features

- **DateTime Tool**: Add DateTime utility for current time retrieval
- **ThinkTool**: Add reasoning and brainstorming tool providing cognitive processing space for AI tool integration

### 📝 Documentation Improvements

- Enhance tool descriptions and usage examples
- Update independence notice and package context
- Improve README documentation structure

### 🔧 Maintenance

- Bump version to 0.4.15
- Update and optimize dependencies

## [0.4.14] - First Official Release

### 🎉 Initial Release

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

- 🎉 **New Features** - New functionality or features
- 🔄 **Refactoring** - Code refactoring without functional changes
- 🐛 **Bug Fixes** - Error corrections
- 📚 **Documentation** - Documentation updates
- 🔐 **Security** - Security-related improvements
- 🌐 **Server** - Server functionality
- 🐳 **Docker** - Containerization related
- 🔍 **Search** - Search functionality related
- 🕐 **Timezone** - Timezone functionality related
- 🧪 **Testing** - Testing-related improvements
- 🔧 **Maintenance** - Maintenance updates

### Getting Updates

To get the latest version, use:

```bash
pip install --upgrade toolregistry-hub
```

### Feedback and Suggestions

If you find any issues or have improvement suggestions, please submit an Issue in our [GitHub repository](https://github.com/OakLight/toolregistry-hub).
