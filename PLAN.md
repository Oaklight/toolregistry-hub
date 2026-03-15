# Hub ↔ ToolRegistry Integration: Architecture & Roadmap

This document is the **architecture/specification/roadmap** for making `toolregistry-hub`'s server surfaces registry-driven.

It is **not** a day-to-day task board.

Execution tracking should live in:

- **GitHub Issues**: actionable work items
- **GitHub Projects**: status/ownership/iteration flow
- **Milestones**: phases / release goals

---

## 1) Background

`toolregistry-hub` was split out from `toolregistry` as a collection of tool implementations plus a server surface.

Historically, the hub server used hand-written FastAPI routes and per-route Request/Response models to wrap tool logic. This does not scale: adding tools requires boilerplate and makes runtime tool availability harder to manage.

---

## 2) Goals

- **Registry-driven server**: the server layer is generated from `ToolRegistry` tool schemas.
- **Single source of truth**: OpenAPI and MCP surfaces should be derived from the same in-memory registry.
- **Runtime availability control**: enable/disable at namespace + method level, with a reason.
- **Environment-aware tools**: missing credentials/dependencies should not crash the server; tools should be gracefully unavailable.
- **Low boilerplate**: new tools should not require writing FastAPI endpoints and Pydantic models by hand.
- **Future-ready**: provide foundations for admin/observability surfaces (optional).

---

## 3) Target Architecture (High Level)

### 3.1 ToolRegistry is the source of truth

All tool exposure (OpenAPI routes and MCP tool listings) should come from a single `ToolRegistry` instance constructed at startup.

### 3.2 Registry build pipeline

At startup, the server builds a registry (conceptually `build_registry()`):

1. Register tool implementations into `ToolRegistry`
2. Apply tool environment requirements / configurability rules
3. Apply startup-time enable/disable policy from configuration (see `tools.jsonc`)

### 3.3 Route generation from tool metadata

FastAPI tool routes are generated from tool metadata and schemas in the registry.

Paths are derived from:

- `Tool.namespace`
- `Tool.method_name`

Never derive paths by splitting the serialized tool `name` string.

### 3.4 Startup configuration: `tools.jsonc`

Startup-time configuration controls which tool namespaces/tools are enabled or disabled, and can also carry tool configuration payload when supported.

This complements:

- tool-side environment checks
- runtime enable/disable controls

### 3.5 Namespace conventions (including nested namespaces)

Namespaces may be hierarchical (e.g. `web/*`) to provide meaningful grouping.

The server should preserve namespace hierarchy consistently across:

- OpenAPI routing
- MCP tool names/listing
- enable/disable semantics

### 3.6 Non-tool routes remain explicit

Not every API endpoint is a “tool”. Server metadata routes may remain hand-written and separate from the tool routing system (e.g. a version endpoint).

---

## 4) Key Design Decisions

### 4.1 Avoid tool-name normalization ambiguity

Historically, tool names combined namespace and method with a separator while other code paths normalize names (e.g. `-` → `_`). This can lose the namespace/method boundary.

Decision: tools carry explicit fields:

- `Tool.namespace`
- `Tool.method_name`

### 4.2 Enable/disable operates on raw identifiers

Enable/disable state should match registry keys and namespace strings directly. Avoid mixing normalized names with raw names.

Decision: enable/disable APIs accept raw tool identifiers (full tool name or namespace) and store an optional reason.

### 4.3 Environment requirements must not crash startup

Tools that require API keys or external services must be able to exist without blocking server startup.

Decision: treat missing requirements as “tool unavailable” rather than “server error”; expose the reason via enable/disable/status mechanisms.

### 4.4 Server boilerplate should be integration glue only

The server's responsibility is:

- build the registry
- generate tool routes
- implement transport integration (OpenAPI/MCP)

Avoid reintroducing per-tool route files.

### 4.5 Central Router Table as bridge between ToolRegistry and protocol adapters

The `RouteTable` class serves as a central abstraction layer:

- **Single source of truth**: converts `ToolRegistry` tools into `RouteEntry` objects with routing metadata
- **Observer pattern**: supports listeners for state change notifications (enable/disable/refresh)
- **ETag support**: provides version tracking for cache validation
- **Protocol agnostic**: both OpenAPI and MCP adapters consume the same `RouteTable`

This design allows protocol adapters to remain thin and focused on transport-specific concerns.

### 4.6 Package responsibility separation

The tooling ecosystem is organized into three packages with clear responsibilities:

| Package | Responsibility | Dependencies |
|---------|---------------|--------------|
| `toolregistry` | Core library: Tool model, ToolRegistry, client integrations | None |
| `toolregistry-server` | Server library: RouteTable, protocol adapters (OpenAPI/MCP), auth, CLI | `toolregistry` |
| `toolregistry-hub` | Tool collection: built-in tools, default server configuration | `toolregistry`, `toolregistry-server` |

This separation enables:

- Independent versioning and release cycles
- Cleaner dependency graphs
- Reuse of server infrastructure for custom tool collections

---

## 5) Roadmap (Compact)

This roadmap intentionally stays high-level. Detailed checklists belong in Issues/Projects.

### Done

- **Phase 1**: dependency restructuring to avoid circular packaging constraints
- **Phase 2**: tool model/name consistency (`Tool.namespace` + `Tool.method_name`, related naming fixes)
- **Phase 3**: enable/disable with reason tracking (namespace + method)
- **Phase 4**: environment requirements + registry build foundation
- **Phase 5 (core)**: auto-route generation from `ToolRegistry`
- **Phase 6 (callback mechanism)**: `on_change()` / `remove_on_change()` callback mechanism in `toolregistry` core
  - Implemented `ChangeEvent`, `ChangeEventType`, `ChangeCallback` types
  - Added callback registration/removal APIs to `ToolRegistry`
  - Callbacks triggered on tool register/unregister/enable/disable events
  - 26 unit tests covering all callback scenarios
  - Bilingual documentation updated
  - Related issue: [toolregistry#68](https://github.com/Oaklight/ToolRegistry/issues/68)
- **Phase 6 (MCP adapter)**: MCP server migration/finalization
  - MCP exposure generated directly from `ToolRegistry` (using [`registry_to_mcp_server()`](src/toolregistry_hub/server/mcp_adapter.py:1))
  - enable/disable state reflected dynamically (no drift) — each `list_tools`/`call_tool` queries registry in real-time
  - removed `FastMCP.from_fastapi()` dependency; now uses MCP SDK low-level Server API
- **Phase 8**: cleanup of legacy hand-written routes after migration period
- Startup tool configuration via **`tools.jsonc`**
- Externalize tool registration list to configuration (reduce hard-coded tool lists)
- Adopt nested namespaces (e.g. `web/*`)

### Next

- **Phase 6 续 (Central Router Table + toolregistry-server)**
  - Create `toolregistry-server` as independent package/repository
  - Implement central `RouteTable` class as bridge between `ToolRegistry` and protocol adapters
  - Migrate server code from `toolregistry-hub` to `toolregistry-server`:
    - `autoroute.py` → `openapi/adapter.py`
    - `mcp_adapter.py` → `mcp/adapter.py`
    - `auth.py` → `auth/bearer.py`
    - CLI code → `cli/main.py`
  - Update `toolregistry-hub` to depend on `toolregistry-server`
  - Implement ETag support for OpenAPI schema caching
  - Design document: [`plans/phase6-router-table-design.md`](plans/phase6-router-table-design.md:1)

- **Operational observability (lightweight)**
  - expose which tools are enabled/disabled and why (API and/or logs)

- **Websearch API key resilience / failover**
  - investigate invalid/expired/quota-exhausted API key detection and automatic retry with the next available key
  - design shared failover behavior in [`APIKeyParser`](src/toolregistry_hub/utils/api_key_parser.py:1) and websearch providers
  - address current double key-consumption behavior in providers that call key rotation separately for headers and rate limiting
  - tracking issue: [`#53`](https://github.com/Oaklight/toolregistry-hub/issues/53)

- **OpenAPI change efficiency**
  - evaluate ETag / conditional responses for `openapi.json` so clients can refresh efficiently
  - (partially addressed by Phase 6 续 RouteTable ETag support)

### Later / Optional

- **Phase 7**: admin panel (deferred)
  - UI layer over enable/disable + tool status inspection

- **Progressive disclosure** for MCP clients (agent attention management)
- **Remote tool source refresh** (tool source/spec refresh strategy)
- Expand schema support/robustness for more complex tool schemas

---

## 6) Risks & Open Questions

- **MCP transport & auth**: how should auth be configured and where should it live?
- **Schema-to-model limits**: which subset of JSON Schema is supported for request models; what fallbacks exist?
- **Client refresh strategy**: how should clients detect tool availability/spec changes efficiently?
- **Responsibility split**: what belongs in upstream `toolregistry` vs hub-specific integration?

---

## 7) References (Issues / PRs)

These links are an index; details live in the referenced Issues/PRs.

### ToolRegistry (upstream)

- Issues (historical):
  - https://github.com/Oaklight/ToolRegistry/issues/50
  - https://github.com/Oaklight/ToolRegistry/issues/51
  - https://github.com/Oaklight/ToolRegistry/issues/52
  - https://github.com/Oaklight/ToolRegistry/issues/53
  - https://github.com/Oaklight/ToolRegistry/issues/54
- PRs (merged):
  - https://github.com/Oaklight/ToolRegistry/pull/57
  - https://github.com/Oaklight/ToolRegistry/pull/58
- MCP client decoupling:
  - https://github.com/Oaklight/ToolRegistry/issues/64
  - https://github.com/Oaklight/ToolRegistry/issues/65
- New roadmap items created from this plan:
  - Callback mechanism (`on_change()` / `remove_on_change()`): https://github.com/Oaklight/ToolRegistry/issues/68 ✅
  - OpenAPI ETag support: https://github.com/Oaklight/ToolRegistry/issues/69
  - Observability API (enabled/disabled + reasons): https://github.com/Oaklight/ToolRegistry/issues/70

### toolregistry-hub

- Dependency/server extras: https://github.com/Oaklight/toolregistry-hub/issues/29
- Env requirements / registry build: https://github.com/Oaklight/toolregistry-hub/issues/30
- Auto-route generation: https://github.com/Oaklight/toolregistry-hub/issues/31
- Cleanup/migration: https://github.com/Oaklight/toolregistry-hub/issues/32
- Startup tool config (`tools.jsonc`):
  - https://github.com/Oaklight/toolregistry-hub/issues/37
  - https://github.com/Oaklight/toolregistry-hub/issues/38
- Externalize tool list:
  - https://github.com/Oaklight/toolregistry-hub/issues/41
  - https://github.com/Oaklight/toolregistry-hub/issues/42
- API key failover / invalid-key skip:
  - https://github.com/Oaklight/toolregistry-hub/issues/53
- MCP server migration (Phase 6):
  - https://github.com/Oaklight/toolregistry-hub/issues/47
- MCP SDK adapter implementation (completed):
  - https://github.com/Oaklight/toolregistry-hub/issues/55
- Server code migration to toolregistry-server:
  - https://github.com/Oaklight/toolregistry-hub/issues/56

### toolregistry-server (new repository)

Repository: https://github.com/Oaklight/toolregistry-server (to be created)

Planned issues:

- `#1` Initialize repository structure
- `#2` Implement RouteTable
- `#3` Migrate OpenAPI adapter
- `#4` Migrate MCP adapter
- `#5` Implement ETag support
- `#6` CLI implementation

Design documents:

- Central Router Table design: [`plans/phase6-router-table-design.md`](plans/phase6-router-table-design.md:1)
- Server template: [`plans/toolregistry-server-template/`](plans/toolregistry-server-template/:1)

### Shared project board

- GitHub Project (ToolRegistry + toolregistry-hub): https://github.com/users/Oaklight/projects/5
