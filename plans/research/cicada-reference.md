# Cicada Code Execution Model - Reference Analysis

## 1. Architecture Overview

Cicada is a coding agent designed for CAD/3D modeling (specifically build123d). Its execution
model follows a **generate-validate-execute-feedback** loop where an LLM generates Python code,
the code is statically checked, executed in a subprocess, and execution results feed back into
the next generation iteration.

### Core Components

```
CodeExecutionLoop (orchestrator)
├── Describer          - Refines design goals using VLM
├── Coder              - Manages code generation + execution cycle
│   ├── CodeGenerator  - LLM-based code generation/fixing (extends MultiModalModel)
│   ├── CodeExecutor   - Subprocess-based Python execution with sandboxing
│   └── CodeCache      - SQLite-based session/iteration persistence
├── VisualFeedback     - Evaluates rendered output against design goals
└── FeedbackJudge      - Scores whether design goal is achieved
```

### Key Files

| File | Role |
|------|------|
| `src/cicada/coding/code_executor.py` | Core execution engine |
| `src/cicada/coding/coder.py` | Generate-validate-execute loop coordinator |
| `src/cicada/coding/code_generator.py` | LLM code generation with tool-assisted fixing |
| `src/cicada/coding/code_cache.py` | SQLite persistence for sessions/iterations/errors |
| `src/cicada/workflow/codecad_agent.py` | Top-level orchestrator with design feedback loop |
| `src/cicada/core/model.py` | LLM base class with ToolRegistry integration |
| `src/cicada/tools/code_dochelper.py` | Runtime introspection tool for API docs |

## 2. Key Implementation Patterns

### 2.1 Subprocess-Based Code Execution (`CodeExecutor`)

The central execution mechanism uses `subprocess.run` to execute generated Python code in an
isolated temporary directory:

```python
temp_dir = tempfile.mkdtemp()
script_path = os.path.join(temp_dir, "script.py")
# write code to file
completed_process = run(
    ["python", script_path],
    cwd=temp_dir,
    capture_output=True,
    text=True,
    timeout=timeout,
)
# ... cleanup with shutil.rmtree(temp_dir)
```

**Key characteristics:**
- **Temp directory isolation**: Each execution runs in a fresh `tempfile.mkdtemp()` directory,
  preventing file collisions and providing a clean workspace.
- **Subprocess isolation**: Code runs in a separate Python process via `subprocess.run`, not
  via `exec()` or `eval()`. This provides process-level isolation.
- **Timeout enforcement**: Uses `subprocess.run(timeout=...)` (default 10 seconds). Catches
  `TimeoutExpired` and returns a clean error.
- **Output capture**: Uses `capture_output=True, text=True` to capture both stdout and stderr
  as strings.
- **File artifact collection**: After successful execution, walks the temp directory to collect
  all generated files (read as binary), returning them in an `output_files` dict keyed by
  relative path.
- **Guaranteed cleanup**: `shutil.rmtree(temp_dir)` in a `finally` block ensures the temp
  directory is always removed.
- **Return convention**: Returns `tuple[bool, dict]` where bool indicates success and dict
  contains either `{"output": ..., "files": ...}` or `{"error": ...}`.

### 2.2 Pre-Execution Validation

Before executing code, `CodeExecutor` performs three static checks:

1. **Syntax check** (`check_syntax`): Uses `compile(code, "<string>", "exec")` to detect
   syntax errors without executing the code.
2. **Grammar check** (`check_grammar`): Uses `ast.parse(code)` for AST-level validation.
3. **Import check** (`check_imports`): Parses import statements and uses
   `importlib.util.find_spec(module)` to verify all imported modules are available before
   execution.

The `validate_code` method chains all three checks, short-circuiting on the first failure.

### 2.3 Iterative Code Generation Loop (`Coder.generate_executable_code`)

The Coder class implements an iterative loop (max 10 iterations by default):

```
for each iteration:
    1. Generate or fix code (via LLM)
    2. Validate code (syntax, grammar, imports)
    3. If invalid -> feed errors back, continue
    4. Execute code (subprocess, test_run=True)
    5. If not runnable -> feed errors back, continue
    6. Return valid executable code
```

**Escalation pattern**: After 2/3 of iterations are exhausted, the system escalates to a
"code master" model (a potentially more capable LLM) for code generation/fixing.

### 2.4 Execute-and-Save Pattern (`CodeExecutor.execute_and_save`)

A convenience method that:
1. Executes code via `execute_code`
2. Filters output files by extension (optional)
3. Saves artifacts to a specified output directory
4. Writes stdout to `output.log`

### 2.5 ToolRegistry Integration

Cicada uses `toolregistry.ToolRegistry` for LLM tool calling:

- `CodeGenerator` registers a `doc_helper` function as a tool, allowing the LLM to query
  Python module/class/function documentation at runtime during code fixing.
- `MultiModalModel.query()` accepts an optional `tools: ToolRegistry` parameter. When tools
  are provided, the model processes tool calls via `tools.execute_tool_calls()` and
  `tools.recover_tool_call_assistant_message()`, then re-queries the model with tool results.
- This creates a tool-augmented code fixing workflow where the LLM can introspect API docs
  to understand how to fix errors.

### 2.6 Session Persistence (`CodeCache`)

SQLite-based persistence with three tables:
- **session**: Design goal, coding plan, parent session linkage
- **iteration**: Generated code, feedback, is_correct/is_runnable flags
- **error**: Error type (syntax/runtime), message, line number

This enables tracking the full history of code generation attempts across sessions.

### 2.7 Outer Design Feedback Loop (`CodeExecutionLoop`)

The top-level orchestrator adds a visual feedback loop on top of code generation:

```
for each design iteration:
    1. Generate executable code (inner loop via Coder)
    2. Render to 3D output (STL/STEP)
    3. Take snapshots of rendered mesh
    4. Get visual feedback (VLM compares snapshots to design goal)
    5. Judge if design goal achieved (score threshold)
    6. If achieved -> done; otherwise feed visual feedback back
```

## 3. What Can Be Reused or Adapted for toolregistry-hub

### 3.1 Directly Reusable Patterns

1. **Subprocess execution with temp directory isolation**: The `CodeExecutor.execute_code`
   pattern is clean and directly applicable. The combination of `tempfile.mkdtemp()` +
   `subprocess.run` + `capture_output` + `timeout` + `finally: shutil.rmtree` is a solid
   foundation for any sandboxed code execution tool.

2. **Pre-execution validation**: The `validate_code` chain (syntax -> grammar -> imports) is
   lightweight and can catch common errors before wasting execution resources. This is
   especially useful if toolregistry-hub wants to expose a "code execution" tool.

3. **Return convention**: The `tuple[bool, dict]` pattern with structured error/output dicts
   is clean for tool return values.

### 3.2 Patterns to Adapt

1. **File artifact collection**: Cicada collects all files generated during execution. For
   toolregistry-hub, this could be adapted to return specific artifact types (e.g., images,
   data files) depending on the tool's purpose.

2. **Timeout configuration**: The 10-second default is appropriate for CAD scripts but may
   need adjustment for other workloads. Consider making timeout configurable per-tool or
   per-invocation.

3. **Iterative execution with feedback**: The generate-validate-execute loop could be
   adapted as a higher-level "agentic code execution" tool where:
   - A user provides a task description
   - The tool generates code, validates, and executes it
   - Errors are fed back for automatic retry

### 3.3 Gaps / Improvements Needed

1. **No resource limits beyond timeout**: Cicada does not restrict memory, CPU, disk, or
   network access. For a general-purpose tool hub, consider adding:
   - Memory limits (e.g., `resource.setrlimit` or cgroups)
   - Network isolation (e.g., `--network=none` in Docker)
   - Disk write limits
   - Process count limits

2. **No Docker/container sandboxing**: Execution happens directly on the host via
   `subprocess.run`. For production use in toolregistry-hub, wrapping execution in a Docker
   container would provide stronger isolation.

3. **No allowlist/denylist for imports**: The import check only verifies availability, not
   safety. Dangerous modules (`os`, `subprocess`, `shutil`, `socket`) are not blocked.

4. **Single Python interpreter**: Cicada uses whatever `python` is on PATH. For
   toolregistry-hub, consider allowing configurable interpreters or virtual environments.

5. **No concurrent execution management**: There is no queue, rate limiting, or concurrency
   control. If exposed as a shared tool, this would need to be added.

### 3.4 Summary

Cicada's execution model is straightforward and pragmatic: write code to a temp file, run it
as a subprocess with a timeout, capture output and artifacts, clean up. The pre-execution
validation (syntax/grammar/imports) is a nice lightweight safety net. The model is suitable
as a starting point for a "code execution" tool in toolregistry-hub, but would need hardening
(resource limits, import restrictions, container isolation) before being exposed to untrusted
input.
