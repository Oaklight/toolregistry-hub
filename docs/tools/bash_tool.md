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
| `exit_code` | `int` | 进程退出码 |

超时**不会**返回字典：`execute()` 会抛出 `CommandTimeoutError`（自 bash-execute 0.3.2 起），因此 MCP 会返回 `isError: true`，而不是一个看起来成功的结果。该异常携带 `command`、`timeout`、被终止前写入的部分 `stdout` / `stderr` 以及 `exit_code = -1`；`str(exc)` 会说明命令与超时预算。

### 错误处理

```python
# 非零退出码
result = BashTool.execute("ls /nonexistent")
if result["exit_code"] != 0:
    print(f"Error: {result['stderr']}")

# 超时（抛出 CommandTimeoutError，可从 toolregistry_hub.bashtool 导入）
try:
    BashTool.execute("sleep 60", timeout=5)
except CommandTimeoutError as exc:
    print(f"{exc.command} 在 {exc.timeout} 秒后超时")
    print(exc.stdout, exc.stderr)  # 被终止前写入的部分输出

# 危险命令（抛出 ValueError）
try:
    BashTool.execute("rm -rf /")
except ValueError as e:
    print(f"已阻止: {e}")
```

## 安全机制

### 内置拒绝列表

BashTool 包含拒绝列表，阻止已知的危险命令模式。它是安全底线而非沙箱，只有设置环境变量 `BASHTOOL_UNSAFE` 时才会关闭（首次使用时打印警告）。

命令会在**引号之外**的 `;`、`&`、`&&`、`||`、`|` 与换行处切分，每段独立检查：`echo hi & rm -rf /` 是两条命令，而 `echo 'a; rm -rf / b'` 是一条。判断某段之前会先剥离分组与复合语法——`( … )`、`{ …; }`、`!`、函数定义、case 分支以及 `then` / `do` / `else` / `elif` / `if` / `while` / `until` 等关键字——以及包装命令链（`sudo -u …`、`env -i`、`nice -n`、`timeout 5`、`xargs`、`busybox`）、`find -exec` 负载、`sh -c` / `bash -lc` 负载（含合并短选项）和 `$(…)` / 反引号命令替换。

| 类别 | 阻止的模式 |
|----------|-----------------|
| 破坏性文件操作 | `rm -rf /`、`rm -rf /etc`、`rm -rf $HOME`、`rm -rf /*`、`rm -rf /usr/lib`、`rm -rf //etc`、`mkfs`、`dd if=`、`> /dev/sd*` |
| 权限提升 | `sudo`、`su -`、`chmod -R 777 /`、`chown -R` |
| 代码注入 | 作为被调用命令的 `eval`、`exec`，`curl\|sh`、`wget\|sh`、`$(rm -rf /)` |
| Fork 炸弹 | `:(){ :\|:& };:` |
| Git 破坏性操作 | `git push --force`、`git reset --hard`、`git clean -f` |
| 系统控制 | `shutdown`、`reboot`、`halt`、`kill -9 1` |

`rm` 依据**删除的是什么**判断，而不是路径的写法。阻止：根目录；系统目录名本身；无法通过重装恢复的目录（`/usr/bin`、`/usr/lib*`、`/lib*`、`/boot`、`/dev`、`/proc`、`/sys`、`/var/lib`、`/etc/ssh` 等）；`$HOME`、`~` 以及 `/home/`、`/root/` 下的任意路径；`.`、`..` 以及完全由上级目录段组成的目标；以及解析为上述位置的通配符、glob 或花括号写法（`/*`、`/et?`、`/{etc,usr}`）。允许：其他位置的具体路径，即常规清理——`rm -rf /tmp/build`、`/srv/app/cache`、`/var/tmp/cache`、`/etc/nginx/cache`、`/var/log/app/*`、`./build`。只有在递归与强制标志同时存在时才会阻止，标志可以合并、分开、使用长格式或 GNU 无歧义前缀（`rm --rec -f`）。单引号内的文本不是命令，因此 `echo 'rm -rf /'` 可以正常执行。

### 设计依据

拒绝列表基于对 6 个 AI 编程 CLI 工具（Claude Code、Codex、Aider、Kilo Code、Cline/Roo Code、Pi）安全方案的调研，涵盖了业界最常见的阻止模式。

**本工具不提供：**

- 操作系统级沙箱（请在部署层使用容器或虚拟机隔离）
- 交互式审批提示（MCP 协议限制）
- 基于 AST 的 Shell 解析：`rm`、`eval`、`exec` 按结构判断，其余按模式匹配。只能由 Shell 解析的目标无法覆盖——受保护目录的相对写法（`rm -rf usr/lib`，因为不知道工作目录）以及仅在运行时存在的值（`rm -rf "$VAR"`、`for d in /; do rm -rf $d; done`）。

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
