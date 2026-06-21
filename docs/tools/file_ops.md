# 文件操作工具

文件操作工具提供安全、原子的文件读/编辑/写接口，通过基于摘要（digest）的版本证明防止覆盖竞争和符号链接注入攻击。

> **注意：** `FileOps` 是向后兼容的入口。推荐用于读取和搜索的类分别是 `FileReader` 和 `FileSearch`。`FileOps` 现在只暴露一套精简的 Claude Code 风格 API — `read` / `edit` / `write` — 并仅保留这三个方法所需的辅助函数。

## 类概览

- `FileOps` — 提供带安全语义的读/编辑/写文件操作，专为 LLM 代理集成设计

## 安全语义

- **`edit` 和 `write` 拒绝符号链接路径**（包括 `.tmp` 中间路径），防止符号链接注入攻击。
- **允许通过符号链接读取文件。** `read` 返回 `is_symlink=True` 和解析后的 `real_path`；若原始路径是符号链接，调用方应将 `real_path` 传给 `edit` / `write`。
- **对已有文件执行 `edit` 和 `write` 必须提供 digest。** digest 是文件原始字节的 SHA-256 值，由 `read` 返回。若文件在 `read` 和 `edit`/`write` 之间被修改，digest 不匹配则操作被拒绝，防止静默覆盖并发写入。
- **新建文件的 `write` 不需要 digest**（文件不存在时 `digest=None` 合法）。
- **`write(mode="append")` 保留原始文件的编码和 BOM。** 操作会先解码现有文件内容，以字符串形式拼接后按原编码重新编码，再原子写入。

## API 参考

### `FileOps.read(path)`

读取文件内容，并返回用于安全编辑/写入的元数据。

**参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| `path` | `str` | 要读取的文件路径，允许符号链接。 |

**返回值** `dict[str, str | bool]`

| 键 | 类型 | 描述 |
|----|------|------|
| `content` | `str` | 解码后的文件内容 |
| `digest` | `str` | 文件原始字节的 SHA-256 十六进制摘要 |
| `is_symlink` | `bool` | `path` 是否为符号链接 |
| `real_path` | `str` | 解析后的绝对路径 |

**异常** 文件不存在时抛出 `FileNotFoundError`。

---

### `FileOps.edit(path, old_string, new_string, digest, replace_all=False, start_line=None)`

在文件中精确替换字符串。需要传入 `read(path)` 返回的 digest。

**参数**

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `path` | `str` | — | 目标文件的绝对路径，不能是符号链接。 |
| `old_string` | `str` | — | 要查找的精确文本，不能为空。 |
| `new_string` | `str` | — | 替换文本（必须与 `old_string` 不同）。 |
| `digest` | `str` | — | `read(path)` 返回的 SHA-256 摘要。 |
| `replace_all` | `bool` | `False` | 替换所有匹配项而非仅第一个。 |
| `start_line` | `int \| None` | `None` | 存在多个匹配时用于消歧的 1-based 行号提示。 |

**返回值** `dict[str, str]`

| 键 | 类型 | 描述 |
|----|------|------|
| `diff` | `str` | 变更的 unified diff |
| `digest` | `str` | 修改后文件的 SHA-256 摘要（可直接用于后续编辑） |

**异常**

- `ValueError` — `old_string` 为空、与 `new_string` 相同、未找到、无 `replace_all`/`start_line` 时存在歧义、digest 缺失或过期、路径为符号链接。
- `FileNotFoundError` — 文件不存在。

**链式编辑：** 返回的 `digest` 可直接传给下一次 `edit` 调用，实现一次读取、多次编辑，无需在每次编辑之间重新读取：

```python
result = FileOps.edit(path, "foo", "bar", digest=digest)
result = FileOps.edit(path, "baz", "qux", digest=result["digest"])
```

---

### `FileOps.write(path, content, digest=None, mode="overwrite")`

原子写入或追加内容到文件。

**参数**

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `path` | `str` | — | 目标文件路径，不能是符号链接。 |
| `content` | `str` | — | 要写入或追加的内容。 |
| `digest` | `str \| None` | `None` | 文件已存在时必填。 |
| `mode` | `"overwrite" \| "append"` | `"overwrite"` | 写入模式。 |

**返回值** `dict[str, str]`

| 键 | 类型 | 描述 |
|----|------|------|
| `digest` | `str` | 写入后文件的 SHA-256 摘要 |

**异常**

- `ValueError` — `mode` 无效、digest 必填但缺失/过期、路径为符号链接。

**说明**

- 对已有文件使用 `mode="append"` 时，会先按原始编码（含 BOM）解码文件，以字符串形式追加 `content`，然后重新编码写入。能正确保留 UTF-16 及带 BOM 的 UTF-8 文件。
- 对不存在的文件使用 `mode="append"` 时，以纯 UTF-8（无 BOM）写入 `content`。

---

## 使用示例

### 读取 → 编辑 → 写入工作流

```python
from toolregistry_hub import FileOps

# 1. 读取文件，获取内容和 digest
result = FileOps.read("config.py")
print(result["content"])
# is_symlink=False, real_path="/abs/path/config.py"

# 2. 使用 digest 进行编辑
edit_result = FileOps.edit(
    "config.py",
    old_string='DEBUG = False',
    new_string='DEBUG = True',
    digest=result["digest"],
)
print(edit_result["diff"])

# 3. 使用更新后的 digest 链式编辑
FileOps.edit(
    "config.py",
    old_string="LOG_LEVEL = 'info'",
    new_string="LOG_LEVEL = 'debug'",
    digest=edit_result["digest"],
)
```

### 创建新文件

```python
# 新文件不需要 digest
result = FileOps.write("notes.txt", "Hello, World!")
print(result["digest"])
```

### 覆盖已有文件

```python
r = FileOps.read("notes.txt")
FileOps.write("notes.txt", "更新后的内容。", digest=r["digest"])
```

### 追加内容到已有文件

```python
r = FileOps.read("log.txt")
FileOps.write("log.txt", "\n新条目。", digest=r["digest"], mode="append")
```

### 符号链接处理

```python
r = FileOps.read("link.txt")        # 允许；r["is_symlink"] == True
# 将 real_path 传给 edit/write，避免符号链接被拒绝
FileOps.write(r["real_path"], "安全写入", digest=r["digest"])
```

### 替换所有匹配项

```python
r = FileOps.read("todos.md")
FileOps.edit("todos.md", "TODO", "DONE", digest=r["digest"], replace_all=True)
```

### 使用 start_line 消歧

```python
r = FileOps.read("script.py")
# 存在两处匹配，选择最接近第 42 行的那处
FileOps.edit("script.py", "return result", "return value",
             digest=r["digest"], start_line=42)
```
