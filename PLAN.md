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

The server’s responsibility is:

- build the registry
- generate tool routes
- implement transport integration (OpenAPI/MCP)

Avoid reintroducing per-tool route files.

---

## 5) Roadmap (Compact)

This roadmap intentionally stays high-level. Detailed checklists belong in Issues/Projects.

### Done

- **Phase 1**: dependency restructuring to avoid circular packaging constraints
- **Phase 2**: tool model/name consistency (`Tool.namespace` + `Tool.method_name`, related naming fixes)
- **Phase 3**: enable/disable with reason tracking (namespace + method)
- **Phase 4**: environment requirements + registry build foundation
- **Phase 5 (core)**: auto-route generation from `ToolRegistry`
- **Phase 6**: MCP server migration/finalization
  - MCP exposure generated directly from `ToolRegistry` (using [`registry_to_mcp_server()`](src/toolregistry_hub/server/mcp_adapter.py:1))
  - enable/disable state reflected dynamically (no drift) — each `list_tools`/`call_tool` queries registry in real-time
  - removed `FastMCP.from_fastapi()` dependency; now uses MCP SDK low-level Server API
- **Phase 8**: cleanup of legacy hand-written routes after migration period
- Startup tool configuration via **`tools.jsonc`**
- Externalize tool registration list to configuration (reduce hard-coded tool lists)
- Adopt nested namespaces (e.g. `web/*`)

### Next

- **Operational observability (lightweight)**
  - expose which tools are enabled/disabled and why (API and/or logs)

- **Websearch API key resilience / failover**
  - investigate invalid/expired/quota-exhausted API key detection and automatic retry with the next available key
  - design shared failover behavior in [`APIKeyParser`](src/toolregistry_hub/utils/api_key_parser.py) and websearch providers
  - address current double key-consumption behavior in providers that call key rotation separately for headers and rate limiting
  - tracking issue: [`#53`](https://github.com/Oaklight/toolregistry-hub/issues/53)

- **OpenAPI change efficiency**
  - evaluate ETag / conditional responses for `openapi.json` so clients can refresh efficiently

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
  - MCP server support (registry-driven): https://github.com/Oaklight/ToolRegistry/issues/68
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

### Shared project board

- GitHub Project (ToolRegistry + toolregistry-hub): https://github.com/users/Oaklight/projects/5
