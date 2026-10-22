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
| `exit_code` | `int` | Process exit code |

A timeout does **not** return a dict: `execute()` raises `CommandTimeoutError` (since bash-execute 0.3.2), so MCP reports `isError: true` instead of a result that looks successful. The exception carries `command`, `timeout`, the partial `stdout` / `stderr` written before the kill and `exit_code = -1`; `str(exc)` names the command and the budget.

### Handling Errors

```python
# Non-zero exit code
result = BashTool.execute("ls /nonexistent")
if result["exit_code"] != 0:
    print(f"Error: {result['stderr']}")

# Timeout (raises CommandTimeoutError, importable from toolregistry_hub.bashtool)
try:
    BashTool.execute("sleep 60", timeout=5)
except CommandTimeoutError as exc:
    print(f"{exc.command} timed out after {exc.timeout}s")
    print(exc.stdout, exc.stderr)  # partial output written before the kill

# Dangerous command (raises ValueError)
try:
    BashTool.execute("rm -rf /")
except ValueError as e:
    print(f"Blocked: {e}")
```

## Security

### Built-in Deny List

BashTool includes a deny list that blocks known-dangerous command patterns. It is a safety floor, not a sandbox, and is disabled only when `BASHTOOL_UNSAFE` is set in the environment (which prints a warning on first use).

Commands are split on `;`, `&`, `&&`, `||`, `|` and newlines that appear **outside quotes**, and each segment is checked independently: `echo hi & rm -rf /` is two commands, while `echo 'a; rm -rf / b'` is one. Grouping and compound syntax is unwrapped before a segment is judged — `( … )`, `{ …; }`, `!`, function definitions, case arms and the keywords `then` / `do` / `else` / `elif` / `if` / `while` / `until` — along with wrapper chains (`sudo -u …`, `env -i`, `nice -n`, `timeout 5`, `xargs`, `busybox`), `find -exec` payloads, `sh -c` / `bash -lc` payloads (including clustered flags) and `$(…)` / backtick substitutions.

| Category | Blocked Patterns |
|----------|-----------------|
| Destructive FS | `rm -rf /`, `rm -rf /etc`, `rm -rf $HOME`, `rm -rf /*`, `rm -rf /usr/lib`, `rm -rf //etc`, `mkfs`, `dd if=`, `> /dev/sd*` |
| Privilege escalation | `sudo`, `su -`, `chmod -R 777 /`, `chown -R` |
| Code injection | `eval`, `exec` as the invoked command, `curl\|sh`, `wget\|sh`, `$(rm -rf /)` |
| Fork bomb | `:(){ :\|:& };:` |
| Git destructive | `git push --force`, `git reset --hard`, `git clean -f` |
| System control | `shutdown`, `reboot`, `halt`, `kill -9 1` |

`rm` is judged by **what it deletes**, not by how the path is spelled. Refused: the root; the system directory names themselves; trees that cannot be reinstalled (`/usr/bin`, `/usr/lib*`, `/lib*`, `/boot`, `/dev`, `/proc`, `/sys`, `/var/lib`, `/etc/ssh`, …); `$HOME`, `~` and anything under `/home/` or `/root/`; `.`, `..` and any target made only of parent segments; and wildcard, glob or brace spellings that resolve to those (`/*`, `/et?`, `/{etc,usr}`). Allowed: concrete paths elsewhere, which is ordinary cleanup — `rm -rf /tmp/build`, `/srv/app/cache`, `/var/tmp/cache`, `/etc/nginx/cache`, `/var/log/app/*`, `./build`. Recursive-and-force is required for a refusal, and the flags may be clustered, separated, long-form or an unambiguous GNU prefix (`rm --rec -f`). Text inside single quotes is not a command, so `echo 'rm -rf /'` runs.

### Design Rationale

The deny list is based on a survey of security approaches across 6 AI coding CLI tools (Claude Code, Codex, Aider, Kilo Code, Cline/Roo Code, Pi). It covers the most commonly blocked patterns found across the industry.

**What this tool does NOT provide:**

- OS-level sandboxing (use containers or VM isolation at the deployment level)
- Interactive approval prompts (MCP protocol limitation)
- AST-based shell parsing: `rm`, `eval` and `exec` are judged structurally, the rest by pattern. Targets that only a shell can resolve are out of reach — relative spellings of a protected tree (`rm -rf usr/lib`, since the working directory is unknown) and values that exist only at runtime (`rm -rf "$VAR"`, `for d in /; do rm -rf $d; done`).

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

## API Reference

::: toolregistry_hub.bash_tool.BashTool
