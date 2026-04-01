# Bash Tool

The Bash Tool provides shell command execution with built-in safety validation. It is designed for AI agent workflows that need to run shell commands programmatically.

## Class Overview

- `BashTool` - Executes shell commands via `subprocess.run` with a built-in deny list that blocks known-dangerous patterns before execution.

## Usage

### Basic Usage

```python
from toolregistry_hub import BashTool

# Execute a simple command
result = BashTool.execute("echo hello world")
print(result["stdout"])   # "hello world\n"
print(result["exit_code"])  # 0

# Execute with a working directory
result = BashTool.execute("ls -la", cwd="/tmp")

# Execute with a custom timeout (seconds)
result = BashTool.execute("long_running_script.sh", timeout=300)
```

### Return Value

`execute()` returns a dict with the following keys:

| Key | Type | Description |
|-----|------|-------------|
| `stdout` | `str` | Captured standard output (truncated at 64 KB) |
| `stderr` | `str` | Captured standard error (truncated at 64 KB) |
| `exit_code` | `int` | Process exit code, or `-1` on timeout |
| `timed_out` | `bool` | Whether the process was killed due to timeout |

### Handling Errors

```python
# Non-zero exit code
result = BashTool.execute("ls /nonexistent")
if result["exit_code"] != 0:
    print(f"Error: {result['stderr']}")

# Timeout
result = BashTool.execute("sleep 60", timeout=5)
if result["timed_out"]:
    print("Command timed out")

# Dangerous command (raises ValueError)
try:
    BashTool.execute("rm -rf /")
except ValueError as e:
    print(f"Blocked: {e}")
```

## Security

### Built-in Deny List

BashTool includes a hardcoded deny list that blocks known-dangerous command patterns. This deny list **cannot be disabled** and serves as a safety floor.

Commands are segmented by shell operators (`&&`, `||`, `;`) and each segment is checked independently against the deny list.

| Category | Blocked Patterns |
|----------|-----------------|
| Destructive FS | `rm -rf /`, `rm -rf ~`, `rm -rf *`, `mkfs`, `dd if=`, `> /dev/sd*` |
| Privilege escalation | `sudo`, `su -`, `chmod -R 777 /`, `chown -R` |
| Code injection | `eval`, `exec`, `curl\|sh`, `wget\|sh` |
| Fork bomb | `:(){ :\|:& };:` |
| Git destructive | `git push --force`, `git reset --hard`, `git clean -f` |
| System control | `shutdown`, `reboot`, `halt`, `kill -9 1` |

### Design Rationale

The deny list is based on a survey of security approaches across 6 AI coding CLI tools (Claude Code, Codex, Aider, Kilo Code, Cline/Roo Code, Pi). It covers the most commonly blocked patterns found across the industry.

**What this tool does NOT provide:**

- OS-level sandboxing (use containers or VM isolation at the deployment level)
- Interactive approval prompts (MCP protocol limitation)
- AST-based shell parsing (regex-based for v1)

## MCP Server Endpoint

When running via the MCP server, this tool is exposed as:

```
POST /tools/bash/execute
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `command` | `string` | Yes | - | Shell command to execute |
| `timeout` | `integer` | No | `120` | Max seconds before kill |
| `cwd` | `string` | No | `null` | Working directory |
