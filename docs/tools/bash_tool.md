# Bash 工具

Bash 工具提供带有内置安全验证的 Shell 命令执行功能，专为需要以编程方式运行 Shell 命令的 AI Agent 工作流设计。

## 类概述

- `BashTool` - 通过 `subprocess.run` 执行 Shell 命令，内置拒绝列表在执行前阻止已知的危险模式。

## 使用方法

### 基本用法

```python
from toolregistry_hub import BashTool

# 执行简单命令
result = BashTool.execute("echo hello world")
print(result["stdout"])   # "hello world\n"
print(result["exit_code"])  # 0

# 指定工作目录
result = BashTool.execute("ls -la", cwd="/tmp")

# 自定义超时时间（秒）
result = BashTool.execute("long_running_script.sh", timeout=300)
```

### 返回值

`execute()` 返回包含以下键的字典：

| 键 | 类型 | 描述 |
|-----|------|-------------|
| `stdout` | `str` | 捕获的标准输出（截断上限 64 KB） |
| `stderr` | `str` | 捕获的标准错误（截断上限 64 KB） |
| `exit_code` | `int` | 进程退出码，超时时为 `-1` |
| `timed_out` | `bool` | 进程是否因超时被终止 |

### 错误处理

```python
# 非零退出码
result = BashTool.execute("ls /nonexistent")
if result["exit_code"] != 0:
    print(f"Error: {result['stderr']}")

# 超时
result = BashTool.execute("sleep 60", timeout=5)
if result["timed_out"]:
    print("命令超时")

# 危险命令（抛出 ValueError）
try:
    BashTool.execute("rm -rf /")
except ValueError as e:
    print(f"已阻止: {e}")
```

## 安全机制

### 内置拒绝列表

BashTool 包含硬编码的拒绝列表，阻止已知的危险命令模式。该拒绝列表**不可禁用**，作为安全底线。

命令按 Shell 操作符（`&&`、`||`、`;`）分段，每段独立检查。

| 类别 | 阻止的模式 |
|----------|-----------------|
| 破坏性文件操作 | `rm -rf /`、`rm -rf ~`、`rm -rf *`、`mkfs`、`dd if=`、`> /dev/sd*` |
| 权限提升 | `sudo`、`su -`、`chmod -R 777 /`、`chown -R` |
| 代码注入 | `eval`、`exec`、`curl\|sh`、`wget\|sh` |
| Fork 炸弹 | `:(){ :\|:& };:` |
| Git 破坏性操作 | `git push --force`、`git reset --hard`、`git clean -f` |
| 系统控制 | `shutdown`、`reboot`、`halt`、`kill -9 1` |

### 设计依据

拒绝列表基于对 6 个 AI 编程 CLI 工具（Claude Code、Codex、Aider、Kilo Code、Cline/Roo Code、Pi）安全方案的调研，涵盖了业界最常见的阻止模式。

**本工具不提供：**

- 操作系统级沙箱（请在部署层使用容器或虚拟机隔离）
- 交互式审批提示（MCP 协议限制）
- 基于 AST 的 Shell 解析（v1 使用正则匹配）

## MCP 服务端点

通过 MCP 服务运行时，此工具暴露为：

```
POST /tools/bash/execute
```

**参数：**

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|-----------|------|----------|---------|-------------|
| `command` | `string` | 是 | - | 要执行的 Shell 命令 |
| `timeout` | `integer` | 否 | `120` | 超时秒数 |
| `cwd` | `string` | 否 | `null` | 工作目录 |

## API 参考

::: toolregistry_hub.bash_tool.BashTool
