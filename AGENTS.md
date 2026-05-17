# AGENTS.md — toolregistry-hub

> Context file for AI coding assistants. Symlinked as `CLAUDE.md`.

## What this project is

toolregistry-hub is a **ready-to-use tool collection** for LLM agents,
providing 19+ pre-configured tools (calculator, web search, file ops, code
execution, etc.) exposed via OpenAPI or MCP servers.

| Package | Role | Depends on |
|---------|------|------------|
| `toolregistry` | Core library: `Tool` model, `ToolRegistry`, client integrations | — |
| `toolregistry-server` | Server infrastructure: `RouteTable`, OpenAPI/MCP adapters, auth, CLI | `toolregistry` |
| `toolregistry-hub` (this) | Tool implementations + default server configuration | `toolregistry-server` |

Entry point: `toolregistry-hub` CLI (defined in `pyproject.toml`).

## Architecture

All tools are registered dynamically in `build_registry()` (`server/registry.py`):

1. Load tool config from `tools.jsonc` (if present)
2. Import each tool class via `_DEFAULT_TOOLS` (or config-specified list)
3. Register classes/instances into `ToolRegistry`
4. Auto-disable tools that fail `Configurable._is_configured()` (missing API keys)
5. Apply `tools.jsonc` enable/disable rules (highest priority)
6. Apply metadata (tags, defer flags) from `_TOOL_METADATA`
7. Enable progressive tool discovery if `enable_discovery=True`

Registered tools and namespaces (from `_DEFAULT_TOOLS` in `server/registry.py`):

| Namespace | Class | Tags |
|-----------|-------|------|
| `calculator` | `Calculator` | READ_ONLY |
| `datetime` | `DateTime` | READ_ONLY |
| `think` | `ThinkTool` | READ_ONLY |
| `web/fetch` | `Fetch` | NETWORK, READ_ONLY |
| `file_ops` | `FileOps` | FILE_SYSTEM, DESTRUCTIVE |
| `web/websearch` | `WebSearch` (unified) | NETWORK, READ_ONLY |
| `web/brave_search` | `BraveSearch` | NETWORK, READ_ONLY, deferred |
| `web/tavily_search` | `TavilySearch` | NETWORK, READ_ONLY, deferred |
| `web/searxng_search` | `SearXNGSearch` | NETWORK, READ_ONLY, deferred |
| `web/brightdata_search` | `BrightDataSearch` | NETWORK, READ_ONLY, deferred |
| `web/scrapeless_search` | `ScrapelessSearch` | NETWORK, READ_ONLY, deferred |
| `web/serper_search` | `SerperSearch` | NETWORK, READ_ONLY, deferred |
| `reader` | `FileReader` | FILE_SYSTEM, READ_ONLY, deferred |
| `fs/file_search` | `FileSearch` | FILE_SYSTEM, READ_ONLY, deferred |
| `fs/path_info` | `PathInfo` | FILE_SYSTEM, READ_ONLY, deferred |
| `bash` | `BashTool` | DESTRUCTIVE, PRIVILEGED, deferred |
| `cron` | `CronTool` | PRIVILEGED, deferred |
| `todolist` | `TodoList` | READ_ONLY, deferred |
| `unit_converter` | `UnitConverter` | READ_ONLY, deferred |

"Deferred" tools are hidden from initial schema and discoverable via `discover_tools`.

Configuration priority: `tools.jsonc > Configurable auto-disable > Default (all enabled)`.

## Repository layout

```
src/toolregistry_hub/
├── __init__.py              # Package exports, __version__
├── server/
│   ├── cli.py               # CLI entry point (openapi/mcp subcommands)
│   ├── registry.py          # build_registry() — registration + auto-disable
│   ├── tool_config.py       # JSONC config loading (tools.jsonc)
│   ├── auth.py              # Token auth helpers
│   └── banner.py            # Startup banner art
├── utils/
│   ├── configurable.py      # Configurable protocol (structural subtyping)
│   ├── api_key_parser.py    # API key rotation/parsing
│   └── fn_namespace.py      # Static-method detection helper
├── _vendor/                 # Vendored modules from zerodep (DO NOT EDIT)
├── websearch/               # Search providers (brave, tavily, searxng, etc.)
├── calculator.py, datetime_utils.py, fetch.py, file_ops.py, ...
└── version_check.py         # PyPI update checker

tests/
├── run_tests.py             # Test runner with modular targets
├── test_*.py                # Per-module unit tests
└── websearch/               # Websearch-specific tests

docker/                      # Dockerfile and Docker docs
```

## Setup and commands

```bash
conda activate toolregistry_hub
pip install -e ".[dev,server]"
pre-commit install
```

Pre-commit hooks configured (ruff, ty, complexipy) — run `pre-commit install` after setup.

Key commands:

```bash
# Lint (single source of truth — same as CI)
pre-commit run --all-files

# Test
pytest tests/ -v
# or: cd tests && python run_tests.py --module calculator

# Build & release
make build-package          # python -m build
make push-package           # twine upload dist/*
make build-docker           # Docker image build
```

## Definition of done

1. `pre-commit run --all-files` passes (ruff, ty, complexipy)
2. `pytest tests/ -v` passes
4. New code has tests in `tests/`
5. Google-style docstrings on public APIs; comments in English
6. No manual edits to `_vendor/` — update upstream in zerodep, re-vendor via CLI

## Adding a new tool

1. Create `src/toolregistry_hub/your_tool.py`
   - Static methods for stateless tools, instance methods for stateful ones
   - If API keys needed: implement `Configurable._is_configured()` and set `_required_envs`
2. Add entry to `_DEFAULT_TOOLS` in `server/registry.py`
3. Add metadata to `_TOOL_METADATA` in `server/registry.py` (tags, defer flag)
4. Export from `__init__.py`
5. Write tests in `tests/test_your_tool.py`

## Workflow

- **Branch from master**, open a PR, require CI green before merge.
- **Merge strategy: rebase** — keep commits atomic and well-messaged.
- Branch naming: `feature/...`, `fix/...`, `refactor/...`, `test/...`, `docs/...`
- Never force-push to `master` unless the user explicitly requests it.

## Documentation

User-facing docs live on **orphan branches** (`docs_en`, `docs_zh`), mounted
as git worktrees. Built with zensical.

### When to update docs worktrees

Update `docs_en/` and `docs_zh/` whenever any of the following happens:

- **New public API added or signature changed**: update the relevant API
  reference pages in both languages.
- **Behavior change or bug fix affecting documented functionality**: update
  affected guide/reference pages.
- **Changelog-worthy change merged to main branch**: update
  `docs_en/docs/changelog.md` and `docs_zh/docs/changelog.md` under the
  `[Unreleased]` section. Follow the [Keep a Changelog](https://keepachangelog.com/)
  format. Entries should cover: features, enhancements, bug fixes,
  breaking changes, and infrastructure.
- **Release published**: move `[Unreleased]` entries into a new versioned
  section in both changelogs.

Commits in doc worktrees use `PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit` since
those branches have no `.pre-commit-config.yaml`.

## Escalation

- Upstream incompatibility → check CI, verify `toolregistry` / `toolregistry-server` versions
- `_vendor/` issues → never fix in-place; update in zerodep repo, re-vendor
- Test failure after 3 attempts → stop, report full output
- Never: delete files to fix errors, skip tests, modify `_vendor/` directly

## Files to never edit

- `src/toolregistry_hub/_vendor/**` — vendored from zerodep, managed via `zerodep` CLI
- `docs_en/`, `docs_zh/` — separate git branches, edit inside the worktree only
