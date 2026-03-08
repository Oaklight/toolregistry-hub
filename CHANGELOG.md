# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added

- **Startup tool configuration via JSONC file** — declaratively control which tools are loaded at startup with `tools.jsonc`, supporting allowlist/denylist modes and hierarchical namespace matching ([#37](../../issues/37), [#38](../../pull/38))
- **Auto-route generation from ToolRegistry** — automatically generate FastAPI endpoints from registered tools, eliminating hand-written route boilerplate ([#31](../../issues/31), [#36](../../pull/36))
- **`requires_env` decorator & Configurable protocol** — tools self-declare required environment variables; unconfigured tools are auto-disabled at startup ([#30](../../issues/30), [#35](../../pull/35))
- **Central tool registry** (`build_registry()` / `get_registry()`) with auto-disable for unconfigured tools ([#30](../../issues/30), [#35](../../pull/35))
- **Nested namespaces for websearch tools** — e.g. `web/brave_search`, producing URLs like `/tools/web/brave_search/search` ([#39](../../issues/39), [#40](../../pull/40))
- **Hidden internal methods** — `is_configured` excluded from API endpoints via `_HIDDEN_METHODS` ([#39](../../issues/39), [#40](../../pull/40))
- `--tools-config` CLI option for specifying tool configuration file path ([#37](../../issues/37), [#38](../../pull/38))

### Removed

- **Legacy hand-written route files** — `calculator.py`, `datetime_tools.py`, `fetch.py`, `think.py`, `todo_list.py`, `unit_converter.py`, and `routes/websearch/` directory, replaced by auto-generated routes ([#39](../../issues/39), [#40](../../pull/40))
- **BingSearch** — removed deprecated implementation due to frequent bot detection issues ([#34](../../pull/34))

### Changed

- **Server optional dependencies restructured** — `server_openapi` and `server_mcp` now include `toolregistry>=0.4.14`; `server` extra uses self-referencing composition ([#29](../../issues/29), [#33](../../pull/33))
- `routes/__init__.py` simplified to export only `version_router` ([#40](../../pull/40))
- `server_core.py` no longer registers legacy routers; uses auto-generated routes alongside `version_router` ([#40](../../pull/40))
- `APIKeyParser.__init__` no longer raises on missing keys; defers validation to call time ([#35](../../pull/35))

## [0.5.6] - 2026-03-05

### Added

- **Jina Reader fallback improvements** — fix configuration, add `X-Engine: browser` for JS rendering, switch to POST with JSON body ([#28](../../pull/28))
- **Content quality evaluation** — `_is_content_sufficient()` with minimum length threshold and SPA shell indicator detection ([#28](../../pull/28))
- **Cloudflare content negotiation strategy** and increased default fetch timeout ([70391e4](../../commit/70391e4))
- **Strategy tracking logs** — `logger.info` records which extraction strategy succeeded (`markdown_negotiation`, `beautifulsoup`, or `jina_reader`) ([#27](../../pull/27))

### Changed

- Improved fallback logic: BS4 content is quality-checked before accepting; low-quality triggers Jina Reader fallback ([#28](../../pull/28))

## [0.5.5] - 2026-01-31

### Changed

- **Think tool refactored** — unified recall into think, reordered params, simplified modes ([028a64c](../../commit/028a64c))
- Docker configuration updated with Brightdata and Scrapeless API key env vars ([fd32071](../../commit/fd32071))
- `.dockerignore` updated to exclude references directory ([b264f97](../../commit/b264f97))

### Fixed

- Makefile version extraction from `__init__.py` ([b00f38d](../../commit/b00f38d))

## [0.5.4] - 2026-01-14

### Added

- **Version check** feature ([#26](../../pull/26))
- **ASCII art banner** with version info at server startup ([#25](../../pull/25))
- **Think patterns** — structured thinking tool enhancements ([#23](../../pull/23))

### Changed

- Unified thinking tools into single think endpoint ([c6259c6](../../commit/c6259c6))
- Enhanced DateTime documentation ([#24](../../pull/24))
- Enhanced websearch docstrings for time-sensitive query handling ([a59e8d2](../../commit/a59e8d2))

### Fixed

- Version attribute reference in setuptools configuration ([3b5caa7](../../commit/3b5caa7))

[Unreleased]: ../../compare/v0.5.6...HEAD
[0.5.6]: ../../compare/v0.5.5...v0.5.6
[0.5.5]: ../../compare/v0.5.4...v0.5.5
[0.5.4]: ../../compare/v0.5.3...v0.5.4
