# AGENTS.md — AI Agent Guide for toolregistry-hub

## Project Overview

**toolregistry-hub** is a ready-to-use tool collection for LLM agents, providing 19 pre-configured tools (calculator, web search, file ops, code execution, etc.) exposed via OpenAPI or MCP servers.

It is part of a three-package ecosystem:

| Package | Role | Depends on |
|---------|------|------------|
| `toolregistry` | Core library: `Tool` model, `ToolRegistry`, client integrations | — |
| `toolregistry-server` | Server infrastructure: `RouteTable`, OpenAPI/MCP adapters, auth, CLI | `toolregistry` |
| `toolregistry-hub` | Tool implementations + default server configuration | `toolregistry-server` (transitively provides `toolregistry`) |

Entry point: `toolregistry-hub` CLI (defined in `pyproject.toml` `[project.scripts]`).

## Directory Structure

```
src/toolregistry_hub/
├── __init__.py              # Package exports, __version__
├── server/
│   ├── cli.py               # CLI entry point (argparse, openapi/mcp subcommands)
│   ├── registry.py          # build_registry() — tool registration + auto-disable
│   ├── tool_config.py       # JSONC config loading (tools.jsonc)
│   ├── auth.py              # Token auth helpers
│   ├── banner.py            # Startup banner art
│   └── routes/              # Non-tool routes (e.g. /version)
├── utils/
│   ├── configurable.py      # Configurable protocol (structural subtyping)
│   ├── api_key_parser.py    # API key rotation/parsing
│   └── fn_namespace.py      # Static-method detection helper
├── _vendor/                 # Vendored modules from zerodep (see below)
├── websearch/               # Search providers (brave, tavily, searxng, brightdata, scrapeless, serper)
├── calculator.py            # Math operations
├── datetime_utils.py        # Time/timezone utilities
├── fetch.py                 # URL content fetching
├── file_ops.py              # File manipulation (replace lines, etc.)
├── file_reader.py           # PDF/text/image file reading
├── file_search.py           # Glob/grep file search
├── filesystem.py            # File system operations (exists, read, write)
├── path_info.py             # Path metadata
├── bash_tool.py             # Shell command execution
├── cron_tool.py             # Cron scheduling
├── think_tool.py            # Chain-of-thought reasoning
├── todo_list.py             # Task/todo management
├── unit_converter.py        # Unit conversions
└── version_check.py         # PyPI update checker

tests/
├── run_tests.py             # Test runner with modular targets
├── Makefile                 # Test/lint/format targets
├── test_*.py                # Per-module unit tests
└── websearch/               # Websearch-specific tests

docker/                      # Dockerfile and Docker docs
```

## Architecture

### Registry-Driven Design

All tools are registered dynamically in `build_registry()` (`server/registry.py`). The function:

1. Loads tool config from `tools.jsonc` (if present)
2. Imports each tool class via `_DEFAULT_TOOLS` list (or config-specified list)
3. Registers classes/instances into `ToolRegistry`
4. Auto-disables tools that fail `Configurable._is_configured()` (e.g. missing API keys)
5. Applies `tools.jsonc` enable/disable rules (highest priority)
6. Applies metadata (tags, defer flags) from `_TOOL_METADATA`
7. Enables progressive tool discovery if `enable_discovery=True`

### Registered Tools

Default tools and their namespaces (from `_DEFAULT_TOOLS` in `server/registry.py`):

| Namespace | Class | Tags |
|-----------|-------|------|
| `bash` | `BashTool` | DESTRUCTIVE, PRIVILEGED, deferred |
| `cron` | `CronTool` | PRIVILEGED, deferred |
| `calculator` | `Calculator` | READ_ONLY |
| `datetime` | `DateTime` | READ_ONLY |
| `web/fetch` | `Fetch` | NETWORK, READ_ONLY |
| `file_ops` | `FileOps` | FILE_SYSTEM, DESTRUCTIVE |
| `reader` | `FileReader` | FILE_SYSTEM, READ_ONLY, deferred |
| `fs/file_search` | `FileSearch` | FILE_SYSTEM, READ_ONLY, deferred |
| `fs/path_info` | `PathInfo` | FILE_SYSTEM, READ_ONLY, deferred |
| `think` | `ThinkTool` | READ_ONLY |
| `todolist` | `TodoList` | READ_ONLY, deferred |
| `unit_converter` | `UnitConverter` | READ_ONLY, deferred |
| `web/websearch` | `WebSearch` (unified) | NETWORK, READ_ONLY |
| `web/brave_search` | `BraveSearch` | NETWORK, READ_ONLY, deferred |
| `web/tavily_search` | `TavilySearch` | NETWORK, READ_ONLY, deferred |
| `web/searxng_search` | `SearXNGSearch` | NETWORK, READ_ONLY, deferred |
| `web/brightdata_search` | `BrightDataSearch` | NETWORK, READ_ONLY, deferred |
| `web/scrapeless_search` | `ScrapelessSearch` | NETWORK, READ_ONLY, deferred |
| `web/serper_search` | `SerperSearch` | NETWORK, READ_ONLY, deferred |

"Deferred" tools are hidden from initial schema and discoverable via `discover_tools` (progressive disclosure).

### Auto-Disable

Tools implementing the `Configurable` protocol (a `_is_configured() -> bool` method) are checked at startup. If `_is_configured()` returns `False`, all tools in that namespace are disabled with a reason (e.g. `"Missing env: BRAVE_API_KEY"`). This prevents the server from crashing due to missing credentials.

### Configuration Priority

```
tools.jsonc config  >  Configurable auto-disable  >  Default (all enabled)
```

`tools.jsonc` supports two modes:
- `denylist` (default): disable listed namespaces
- `allowlist`: enable only listed namespaces

Namespace matching is hierarchical: `"web"` matches `"web/brave_search"`, `"web/fetch"`, etc.

## Server Modes

### OpenAPI

```bash
toolregistry-hub openapi [--host 0.0.0.0] [--port 8000] [--config tools.jsonc] [--tokens tokens.txt]
```

Routes are auto-generated from the registry. Includes a `/version` endpoint.

### MCP (Model Context Protocol)

```bash
toolregistry-hub mcp [--transport stdio|sse|streamable-http] [--host 127.0.0.1] [--port 8000]
```

### Common Flags

- `--config PATH` — JSONC tool configuration file
- `--env PATH` — custom `.env` file path
- `--no-env` — skip loading `.env`
- `--admin-port PORT` — enable admin panel
- `--tool-discovery / --no-tool-discovery` — toggle progressive disclosure
- `--think-augment / --no-think-augment` — toggle think-augmented function calling
- `--no-banner` — suppress startup banner

## Development

### Environment

```bash
# Conda environment
conda activate toolregistry_hub

# Install for development
pip install -e ".[dev,server]"
```

### Code Quality

```bash
# Lint (ruff rules: E, F, UP; ignores UP007, E501)
ruff check src/
ruff check --fix src/       # auto-fix

# Format
ruff format src/

# Type check (ty, Python 3.10 target; vendor dir excluded)
ty check src/

# Cognitive complexity analysis (complexipy)
complexipy src/ -e "_vendor"
```

### Testing

```bash
# All tests
make test                   # or: cd tests && python run_tests.py

# Specific module
cd tests && python run_tests.py --module calculator

# Unit / integration / fast
cd tests && python run_tests.py --unit
cd tests && python run_tests.py --integration
cd tests && python run_tests.py --fast
```

### Build & Release

```bash
make build-package          # python -m build
make push-package           # twine upload dist/*
make build-docker           # Docker image build
make build-docker V=0.8.0 PYPI_MIRROR=https://pypi.tuna.tsinghua.edu.cn/simple
```

## Adding a New Tool

1. Create `src/toolregistry_hub/your_tool.py` — implement the tool class
   - Use static methods for stateless tools, instance methods for stateful/configurable ones
   - If the tool needs API keys: implement `Configurable._is_configured()` and set `_required_envs`
2. Add entry to `_DEFAULT_TOOLS` in `server/registry.py` with `class` and `namespace`
3. Add metadata to `_TOOL_METADATA` in `server/registry.py` (tags, defer flag)
4. Export from `__init__.py` (add to imports and `__all__`)
5. Write tests in `tests/test_your_tool.py`
6. Run `ruff check --fix src/ && ruff format src/ && ty check src/ && complexipy src/ -e "_vendor"`

## CI Pipeline

GitHub Actions (`.github/workflows/ci.yml`) runs on push/PR to `master`:

1. **Lint**: `ruff check` + `ruff format --check`
2. **Type check**: `ty check src/`
3. **Test**: `pytest tests/ -v`

Python version: 3.10. Install: `pip install -e ".[dev,server_core]"`.

## Key Conventions

- **Python ≥ 3.10** required
- **Zero runtime dependencies** — the base package has `dependencies = []` in `pyproject.toml`; all deps are in optional extras
- **Vendored modules** in `_vendor/` — sourced from [zerodep](https://github.com/Oaklight/zerodep), managed via `zerodep` CLI (see below)
- **Google-style docstrings** throughout
- **snake_case** for functions/variables, **PascalCase** for classes
- Comments and docstrings in **English**
- Hierarchical namespaces use `/` separator (e.g. `web/brave_search`, `fs/file_search`)

## Vendored Modules (`_vendor/`)

All vendored modules come from [zerodep](https://github.com/Oaklight/zerodep) — a zero-dependency Python module collection by the same author. They are managed via the `zerodep` CLI tool.

### Modules

| Module | Version | Purpose |
|--------|---------|---------|
| `httpclient` | 0.3.1 | Sync+async HTTP client (replaces httpx) |
| `structlog` | 0.3.0 | Structured logging (replaces loguru) |
| `useragent` | 0.1.0 | User-Agent string generator |
| `validate` | 0.4.3 | Runtime type validator with JSON Schema |
| `scheduler` | 0.3.1 | In-process cron task scheduler |
| `soup/` | 0.6.0 | HTML parser (replaces beautifulsoup4) |
| `readability/` | 0.1.0 | HTML content extractor (depends on `soup`) |
| `sparse_search/` | 0.4.0 | BM25/TF-IDF full-text search engine for search result reranking |

### Management

Each module file embeds a `# /// zerodep` metadata block with version, deps, and tier info. To add or update a vendored module:

```bash
zerodep add <module>             # add/update a flat module
zerodep add --nested <module>    # add with nested package layout
```

### Rules

- **Never edit vendored files manually** — update upstream in zerodep, then re-vendor via CLI
- `_vendor/` is excluded from `ty` type checking, `complexipy` analysis, and from ruff `UP035` rule (see `pyproject.toml`)
- Vendored modules must remain stdlib-only (no third-party imports)
