# Executor & Sandbox Architecture Design

**Date:** 2026-03-26
**Status:** Draft
**Scope:** toolregistry (core executor refactor) + toolregistry-sandbox (new package) + toolregistry-hub (bash tool)

---

## 1. Problem Statement

The toolregistry executor currently hardcodes two execution backends (ThreadPool, ProcessPool).
Planned features — **remote dispatch** and **sandboxed execution** — cannot be added without
a pluggable backend abstraction.

Meanwhile, toolregistry-hub needs a bash/command execution tool that runs code in isolated
environments. This overlaps with the executor's remote dispatch in the "sandboxed remote worker"
scenario.

### Two Orthogonal Dimensions

```
              ┌──────────────────────────────────────────────┐
              │      "WHERE to run" (Executor concern)       │
              │                                              │
              │  ThreadPool ── ProcessPool ── Remote Worker  │
              └───────────────────┬──────────────────────────┘
                                  │
                                  ×  ← convergence point
                                  │
              ┌───────────────────┴──────────────────────────┐
              │      "HOW SAFELY to run" (Sandbox concern)   │
              │                                              │
              │  None ── OS-native ── Docker ── microVM      │
              └──────────────────────────────────────────────┘
```

- **Executor** dispatches Python callables (cloudpickle-serialized) to backends.
- **Sandbox** runs arbitrary commands/scripts in isolated environments.
- **Overlap**: when a remote worker IS a sandbox (e.g., run a cloudpickled function in Docker).

---

## 2. Current State

### Executor (`toolregistry/executor.py`)

```python
# Hardcoded pools, no abstraction
self._process_pool = ProcessPoolExecutor()
self._thread_pool = ThreadPoolExecutor()
self._execution_mode: Literal["process", "thread"] = "process"
```

- cloudpickle >= 3.0.0 for cross-process serialization
- Async functions auto-wrapped to sync via `make_sync_wrapper`
- Fallback: process pool failure → retry with thread pool
- No pluggable backend interface

### Cicada (`~/projects/cicada`)

- `subprocess.run(["python", script_path], cwd=temp_dir, capture_output=True, timeout=10)`
- Pre-execution validation: `compile()` → `ast.parse()` → `importlib.util.find_spec()`
- Artifact collection from temp directory
- No resource limits, no container isolation, no import restrictions

---

## 3. Proposed Architecture

### 3.1 ExecutionBackend Protocol (toolregistry core)

```python
from __future__ import annotations
from typing import Protocol, Any, Callable
from concurrent.futures import Future


class ExecutionBackend(Protocol):
    """Pluggable backend for dispatching Python callables."""

    def submit(
        self, fn: Callable[..., Any], /, *args: Any, **kwargs: Any
    ) -> Future[Any]:
        """Submit a callable for execution. Returns a Future."""
        ...

    def shutdown(self, wait: bool = True) -> None:
        """Shut down the backend, release resources."""
        ...

    @property
    def requires_serialization(self) -> bool:
        """Whether callables must be serializable (cloudpickle).

        True for ProcessPool, Remote, Sandboxed backends.
        False for ThreadPool (shared memory).
        """
        ...
```

**Built-in backends** (in toolregistry core):

| Backend | Serialization | Transport | Isolation |
|---------|--------------|-----------|-----------|
| `ThreadPoolBackend` | None | In-process | None |
| `ProcessPoolBackend` | cloudpickle | OS fork | Process-level |

**Extension backends** (separate packages):

| Backend | Serialization | Transport | Isolation |
|---------|--------------|-----------|-----------|
| `RemoteBackend` | cloudpickle | Network (HTTP/gRPC/WS) | Network boundary |
| `SandboxedBackend` | cloudpickle | Container/VM API | Container/VM |

### 3.2 SandboxRuntime Protocol (toolregistry-sandbox)

```python
from __future__ import annotations
from typing import Protocol
from dataclasses import dataclass


@dataclass
class CommandResult:
    """Result of a command execution in a sandbox."""
    stdout: str
    stderr: str
    exit_code: int


class SandboxRuntime(Protocol):
    """Protocol for isolated code execution environments."""

    def execute_command(
        self, command: str, *, timeout: float | None = None
    ) -> CommandResult:
        """Execute a shell command in the sandbox."""
        ...

    async def aexecute_command(
        self, command: str, *, timeout: float | None = None
    ) -> CommandResult:
        """Async variant of execute_command."""
        ...

    def read_file(self, path: str) -> str:
        """Read a file from the sandbox filesystem."""
        ...

    def write_file(self, path: str, content: str) -> None:
        """Write a file to the sandbox filesystem."""
        ...

    def cleanup(self) -> None:
        """Destroy the sandbox and release all resources."""
        ...
```

### 3.3 Runtime Implementations

```
SandboxRuntime (protocol)
│
├── SubprocessRuntime        # Baseline, all platforms, no isolation
│   └── subprocess.run + tempdir + timeout
│
├── NativeRuntime            # OS-native security, zero extra deps
│   ├── Linux: Landlock LSM (kernel 5.13+)
│   └── macOS: Seatbelt (sandbox-exec)
│
├── DockerRuntime            # Container isolation, needs Docker
│   └── docker run --rm --network=none --memory --cpus
│
├── E2BRuntime               # Firecracker microVM, cloud
│   └── e2b SDK
│
└── BoxLiteRuntime           # KVM microVM, local embedded
    └── boxlite SDK
```

**Cross-platform support matrix:**

| Runtime | Linux | macOS | Windows | Extra Deps |
|---------|-------|-------|---------|------------|
| SubprocessRuntime | ✓ | ✓ | ✓ | None |
| NativeRuntime | ✓ (5.13+) | ✓ | ✗ | None |
| DockerRuntime | ✓ | ✓ | ✓ | Docker |
| E2BRuntime | ✓ | ✓ | ✓ | E2B account |
| BoxLiteRuntime | ✓ (KVM) | ✗ | ✗ | boxlite |

### 3.4 Auto-Detection (Layered Fallback)

```python
def auto_detect_runtime(**kwargs) -> SandboxRuntime:
    """Detect the best available isolation level, falling back gracefully.

    Detection order (highest isolation first):
      Level 3: BoxLite/E2B (microVM) — requires KVM or cloud API
      Level 2: Docker (container)    — requires Docker daemon
      Level 1: Native (OS security)  — requires Landlock/Seatbelt
      Level 0: Subprocess (baseline) — always available
    """
    ...
```

### 3.5 SandboxedBackend (Bridge)

Bridges `ExecutionBackend` (executor) and `SandboxRuntime` (sandbox), allowing the
executor to transparently dispatch tool functions into a sandboxed environment:

```python
class SandboxedBackend:
    """ExecutionBackend that runs Python callables inside a sandbox.

    Flow:
      1. cloudpickle.dumps(fn, args, kwargs) → payload
      2. runtime.write_file("/tmp/_payload.pkl", payload)
      3. runtime.execute_command("python /tmp/_runner.py")
         (_runner.py loads payload, executes, writes result)
      4. runtime.read_file("/tmp/_result.pkl") → result
      5. cloudpickle.loads(result)
    """

    def __init__(self, runtime: SandboxRuntime) -> None:
        self._runtime = runtime

    def submit(self, fn, /, *args, **kwargs):
        ...

    @property
    def requires_serialization(self) -> bool:
        return True
```

---

## 4. Package Structure

### 4.1 toolregistry (core) — Executor refactor

```
src/toolregistry/
  executor.py                 # Refactored: delegates to ExecutionBackend
  backends/
    __init__.py
    protocol.py               # ExecutionBackend protocol
    thread_pool.py            # ThreadPoolBackend
    process_pool.py           # ProcessPoolBackend (cloudpickle)
```

### 4.2 toolregistry-sandbox (new package)

```
src/toolregistry_sandbox/
  __init__.py                 # Exports: SandboxRuntime, CommandResult, auto_detect_runtime
  runtime.py                  # SandboxRuntime protocol, CommandResult dataclass
  auto_detect.py              # Layered auto-detection
  validation.py               # Pre-execution checks (syntax, grammar, imports) from Cicada
  backends/
    __init__.py
    subprocess_rt.py          # SubprocessRuntime
    native_rt.py              # NativeRuntime (Landlock/Seatbelt)
    docker_rt.py              # DockerRuntime
    e2b_rt.py                 # E2BRuntime
    boxlite_rt.py             # BoxLiteRuntime
  executor_bridge.py          # SandboxedBackend(ExecutionBackend)
```

**pyproject.toml dependencies:**

```toml
[project]
dependencies = [
    "cloudpickle>=3.0.0",
]

[project.optional-dependencies]
docker = ["docker>=7.0.0"]
e2b = ["e2b>=1.0.0"]
boxlite = ["boxlite>=0.1.0"]
executor = ["toolregistry>=0.7.0"]    # for SandboxedBackend bridge
all = ["toolregistry-sandbox[docker,e2b,boxlite,executor]"]
dev = ["pytest>=7.0.0", "pytest-asyncio>=0.21.0"]
```

### 4.3 toolregistry-hub — Bash tool

```
src/toolregistry_hub/
  bash_tool.py                # BashTool class using SandboxRuntime
```

```python
class BashTool:
    """Shell command execution tool for AI agents.

    Provides sandboxed bash execution with configurable isolation level.
    Auto-detects the best available runtime if not specified.
    """

    def __init__(self, runtime: SandboxRuntime | None = None):
        self._runtime = runtime or auto_detect_runtime()

    def execute(self, command: str, *, timeout: float = 30.0) -> str:
        """Execute a shell command and return the output."""
        result = self._runtime.execute_command(command, timeout=timeout)
        if result.exit_code != 0:
            return f"Error (exit {result.exit_code}):\n{result.stderr}"
        return result.stdout

    def read_file(self, path: str) -> str:
        """Read a file from the sandbox."""
        return self._runtime.read_file(path)

    def write_file(self, path: str, content: str) -> None:
        """Write a file to the sandbox."""
        self._runtime.write_file(path, content)

    def _is_configured(self) -> bool:
        return self._runtime is not None
```

---

## 5. Dependency Graph

```
toolregistry (core)
  ├── defines: ExecutionBackend protocol
  ├── built-in: ThreadPoolBackend, ProcessPoolBackend
  └── deps: cloudpickle, pydantic, loguru

toolregistry-server
  └── depends on: toolregistry

toolregistry-sandbox (new)
  ├── defines: SandboxRuntime protocol, CommandResult
  ├── built-in: SubprocessRuntime, NativeRuntime
  ├── optional[docker]: DockerRuntime
  ├── optional[e2b]: E2BRuntime
  ├── optional[boxlite]: BoxLiteRuntime
  ├── optional[executor]: SandboxedBackend (bridge)
  └── depends on: cloudpickle
  └── optional dep: toolregistry (for ExecutionBackend protocol only)

toolregistry-hub
  ├── uses: toolregistry-sandbox (for BashTool)
  └── depends on: toolregistry-server, toolregistry-sandbox

cicada (external consumer)
  └── depends on: toolregistry-sandbox (replace current CodeExecutor)
```

---

## 6. Migration Strategy

### Phase 1: Executor Refactor (toolregistry core)

**Goal:** Extract ExecutionBackend protocol, wrap existing pools as backends.

1. Create `backends/protocol.py` with `ExecutionBackend` protocol
2. Implement `ThreadPoolBackend` and `ProcessPoolBackend`
3. Refactor `Executor` to hold an `ExecutionBackend` instance
4. Keep `set_execution_mode()` working (backward compat — switches backend internally)
5. Add `set_backend(backend: ExecutionBackend)` for custom backends
6. Tests: verify all existing tests pass unchanged

**Backward compatibility guarantee:**

```python
# Old API still works
registry.set_execution_mode("thread")
registry.execute_tool_calls(tool_calls)

# New API available
from toolregistry.backends import ProcessPoolBackend
registry.set_backend(ProcessPoolBackend(max_workers=4))
```

### Phase 2: toolregistry-sandbox MVP

**Goal:** SandboxRuntime protocol + SubprocessRuntime + NativeRuntime.

1. Create new repo `toolregistry-sandbox`
2. Implement `SandboxRuntime` protocol and `CommandResult`
3. Implement `SubprocessRuntime` (subprocess.run + tempdir + timeout)
4. Implement `NativeRuntime` (Landlock on Linux, Seatbelt on macOS)
5. Implement `auto_detect_runtime()`
6. Port `validation.py` from Cicada (syntax/grammar/import checks)
7. Tests on Linux and macOS

### Phase 3: Docker Backend

**Goal:** Container-based isolation.

1. Implement `DockerRuntime` using Docker SDK for Python
2. Support: `--network=none`, `--memory`, `--cpus`, `--read-only`, volume mounts
3. Image management: default image, custom Dockerfile support
4. Integration tests with Docker

### Phase 4: BashTool in toolregistry-hub

**Goal:** Expose sandbox as an MCP tool.

1. Implement `BashTool` class in toolregistry-hub
2. Register in `_DEFAULT_TOOLS` with namespace `bash` or `shell`
3. Wire up auto-detection of best available runtime
4. Integration tests

### Phase 5: Advanced Backends & Remote Dispatch

**Goal:** Cloud sandboxes + remote execution.

1. `E2BRuntime` and `BoxLiteRuntime` implementations
2. `RemoteBackend` for executor (cloudpickle over HTTP)
3. `SandboxedBackend` bridge (executor → sandbox)
4. Cicada migration to toolregistry-sandbox

---

## 7. Design Considerations

### Security

- **Default-deny networking**: DockerRuntime uses `--network=none` by default
- **Filesystem isolation**: sandbox has its own filesystem; host FS not accessible
- **Resource limits**: all backends enforce memory, CPU, wall-clock timeout
- **No privilege escalation**: containers run as non-root
- **Import restrictions**: optional allowlist/denylist for Python imports (in validation.py)

### Reliability

- **Cleanup guarantee**: context manager / `__del__` / atexit ensures sandbox destruction
- **Timeout enforcement**: all `execute_command` calls have wall-clock timeout
- **Output truncation**: cap stdout/stderr to prevent memory exhaustion (default 64KB)
- **Graceful degradation**: auto-detect falls back to lower isolation without error

### Observability

- **Structured logging** via loguru for all command executions
- **Execution metadata**: command, duration, exit_code, isolation_level
- **Integrates with toolregistry's existing execution logging**

### Async Support

- Every sync method has an async counterpart (`execute_command` / `aexecute_command`)
- `SubprocessRuntime` uses `asyncio.create_subprocess_exec` for async
- `DockerRuntime` async via `aiodocker` (optional)

### Backward Compatibility

- `set_execution_mode("thread" | "process")` continues to work
- `execute_tool_calls()` API unchanged
- New `set_backend()` is additive, not replacing

---

## 8. Comparison with Vercel bash-tool

| Aspect | Vercel bash-tool | Our Design |
|--------|-----------------|------------|
| Sandbox interface | `Sandbox` (3 methods) | `SandboxRuntime` (5 methods, + async) |
| Default sandbox | `just-bash` (virtual TS bash) | `SubprocessRuntime` (real subprocess) |
| VM sandbox | `@vercel/sandbox` (cloud) | E2B / BoxLite / Docker |
| Tool dispatch | N/A (tools always in sandbox) | `ExecutionBackend` protocol |
| Serialization | N/A | cloudpickle (for SandboxedBackend) |
| Tool discovery | Probes `/usr/bin` for CLI tools | Not in scope (separate concern) |
| Skill system | SKILL.md + scripts | Not in scope (separate concern) |
| Language | TypeScript | Python |
| Cross-platform | Node.js (via just-bash) | Linux/macOS/Windows (layered) |

**Key differentiator:** Our design bridges the executor (tool function dispatch) and sandbox
(command isolation) via `SandboxedBackend`, which Vercel's bash-tool doesn't address — their
tools always run inside the sandbox with no concept of dispatching registered Python callables.

---

## 9. Open Questions

1. **Naming**: `toolregistry-sandbox` vs `toolregistry-runtime` vs `pysandbox`?
2. **NativeRuntime scope**: Should Landlock/Seatbelt support be in the MVP or deferred?
3. **Remote dispatch transport**: HTTP vs gRPC vs WebSocket for RemoteBackend?
4. **Sandbox lifecycle**: Per-command ephemeral vs long-lived session with state?
5. **GPU passthrough**: Needed for ML workloads? Only Docker and cloud backends support it.
6. **Windows isolation**: Worth implementing (e.g., Windows Job Objects)? Or subprocess-only?
