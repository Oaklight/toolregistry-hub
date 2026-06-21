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

| Namespace | Class | Tags | Visibility |
|-----------|-------|------|------------|
| `datetime` | `DateTime` | READ_ONLY | **LIVE** (now only; convert_timezone deferred) |
| `think` | `ThinkTool` | READ_ONLY | **LIVE** |
| `web/fetch` | `Fetch` | NETWORK, READ_ONLY | **LIVE** (fetch_content only) |
| `web/websearch` | `WebSearch` (unified) | NETWORK, READ_ONLY | **LIVE** (search only; list_engines deferred) |
| `file_ops` | `FileOps` | FILE_SYSTEM, DESTRUCTIVE | **LIVE** (local profile only; disabled in remote) |
| `calculator` | `Calculator` | READ_ONLY | deferred |
| `weather` | `Weather` | NETWORK, READ_ONLY | deferred |
| `reader` | `FileReader` | FILE_SYSTEM, READ_ONLY | deferred |
| `fs/file_search` | `FileSearch` | FILE_SYSTEM, READ_ONLY | deferred |
| `fs/path_info` | `PathInfo` | FILE_SYSTEM, READ_ONLY | deferred |
| `bash` | `BashTool` | DESTRUCTIVE, PRIVILEGED | deferred |
| `cron` | `CronTool` | PRIVILEGED | deferred |
| `todolist` | `TodoList` | READ_ONLY | deferred |
| `unit_converter` | `UnitConverter` | READ_ONLY | deferred |

"Deferred" tools are hidden from initial schema and discoverable via `discover_tools`.
Individual search providers (brave, tavily, etc.) are internal engines of the
unified `WebSearch` — they are **not** registered as separate tools.

Remote profile LIVE tools: `datetime-now`, `discover_tools`, `think-think`,
`web/fetch-fetch_content`, `web/websearch-search` (5 tools).

Configuration priority: `tools.jsonc > Configurable auto-disable > Default (all enabled)`.
`tools.jsonc` is optional; the default tool list from code is the primary config.

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
make deploy-dev SSH_TARGET=cloud.usa1   # Build + deploy dev-test
```

## Release process

### PyPI release (via GitHub Actions)

1. Bump `__version__` in `src/toolregistry_hub/__init__.py`
2. Commit: `git commit -m "release: v0.X.Y"`
3. Push to master: `git push origin master`
4. Go to GitHub Actions → "Release" workflow → Run workflow
5. Input the version (e.g. `0.9.0`) — must match `__init__.py`
6. Workflow will: verify version → create git tag → build wheel → publish to PyPI → create GitHub Release

### Docker image

After PyPI release:

```bash
make build-docker V=0.X.Y
make push-docker V=0.X.Y
```

### Deploy to VPS

```bash
# Dev stack (dev-test image from local build)
make deploy-dev SSH_TARGET=cloud.usa1

# Prod stack (uses IMAGE_TAG from .env, restart containers)
ssh cloud.usa1 "cd /dockervol/dockge/stacks/toolregistry-server && docker compose up -d --force-recreate --no-deps openapi mcp-streamable-http mcp-sse"
```

### Release checklist

1. All PRs merged, CI green on master
2. `pre-commit run --all-files` passes locally
3. `pytest tests/ -v` passes
4. Bump version in `__init__.py`, commit, push
5. Trigger GitHub Actions release workflow
6. Build + push Docker image
7. Deploy to prod VPS
8. Notify docs team to move `[Unreleased]` changelog entries to versioned section

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
- **No AI co-author tags in commits.** Do not add `Co-authored-by` lines for AI
  tools in git commit messages. Disclose AI usage in PR descriptions instead.

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

### Cross-language consistency (enforced)

**Both language versions must be updated in the same task/agent run.** Never
update only one language and leave the other for later. The workflow is:

1. Make changes to `docs_en/` first (English is the source of truth).
2. In the same task, apply equivalent changes to `docs_zh/` before committing.
3. Commit and push both worktrees before the task is considered done.

Splitting the two languages across separate agents or separate sessions is not
allowed — it leads to drift and missed pages.

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
