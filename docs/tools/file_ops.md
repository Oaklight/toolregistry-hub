# File Operations Tools

The file operations tools provide safe, atomic file read/edit/write with a digest-based version proof to prevent lost-update races and symlink injection.

> **Note:** `FileOps` is the legacy compatibility surface. The preferred classes for reading and searching are `FileReader` and `FileSearch`. `FileOps` now exposes a minimal Claude Code-style API — `read` / `edit` / `write` — and retains only the helpers still needed by those three methods.

## Class Overview

- `FileOps` — Core file operations with read/edit/write safety semantics, designed for LLM agent integration

## Safety Semantics

- **`edit` and `write` reject symlink paths** (including `.tmp` intermediate paths) to prevent symlink-injection attacks.
- **Reading a symlink is allowed.** `read` returns `is_symlink=True` and the resolved `real_path`; callers should pass `real_path` to `edit` / `write` when the original path is a symlink.
- **Existing-file `edit` and `write` require a digest.** The digest is the SHA-256 of the file's raw bytes, returned by `read`. If the file changes between `read` and `edit`/`write`, the digest will not match and the operation is rejected, preventing silent overwrite of concurrent changes.
- **New-file `write` does not require a digest** (`digest=None` is accepted when the file does not yet exist).
- **`write(mode="append")` preserves the original file's encoding and BOM.** Content is decoded from the existing file, concatenated as a string, then re-encoded before writing atomically.

## API Reference

### `FileOps.read(path)`

Read text file content and return metadata for safe edits/writes.

**Arguments**

| Parameter | Type | Description |
|-----------|------|-------------|
| `path` | `str` | File path to read. Symlinks are followed. |

**Returns** `dict[str, str | bool]`

| Key | Type | Description |
|-----|------|-------------|
| `content` | `str` | Decoded file content |
| `digest` | `str` | SHA-256 hex digest of raw file bytes |
| `is_symlink` | `bool` | Whether `path` is a symlink |
| `real_path` | `str` | Absolute resolved path |

**Raises** `FileNotFoundError` if the path does not exist.

---

### `FileOps.edit(path, old_string, new_string, digest, replace_all=False, start_line=None)`

Replace an exact string in a file. Requires a digest from `read(path)`.

**Arguments**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | `str` | — | Absolute path to the file. Must not be a symlink. |
| `old_string` | `str` | — | Exact text to find. Must not be empty. |
| `new_string` | `str` | — | Replacement text (must differ from `old_string`). |
| `digest` | `str` | — | SHA-256 digest returned by `read(path)`. |
| `replace_all` | `bool` | `False` | Replace all occurrences instead of just the first. |
| `start_line` | `int \| None` | `None` | 1-based line hint for disambiguation when multiple matches exist. |

**Returns** `dict[str, str]`

| Key | Type | Description |
|-----|------|-------------|
| `diff` | `str` | Unified diff of the change |
| `digest` | `str` | SHA-256 digest of the updated file (use for subsequent edits) |

**Raises**

- `ValueError` — if `old_string` is empty, identical to `new_string`, not found, ambiguous without `replace_all`/`start_line`, digest is missing or stale, or path is a symlink.
- `FileNotFoundError` — if the file does not exist.

**Chaining edits:** the returned `digest` can be passed directly to the next `edit` call, enabling a read-once / edit-many workflow without re-reading between edits:

```python
result = FileOps.edit(path, "foo", "bar", digest=digest)
result = FileOps.edit(path, "baz", "qux", digest=result["digest"])
```

---

### `FileOps.write(path, content, digest=None, mode="overwrite")`

Write or append content to a file atomically.

**Arguments**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | `str` | — | Destination file path. Must not be a symlink. |
| `content` | `str` | — | Content to write or append. |
| `digest` | `str \| None` | `None` | Required when the file already exists. |
| `mode` | `"overwrite" \| "append"` | `"overwrite"` | Write mode. |

**Returns** `dict[str, str]`

| Key | Type | Description |
|-----|------|-------------|
| `digest` | `str` | SHA-256 digest of the written file |

**Raises**

- `ValueError` — if `mode` is invalid, digest is required but missing/stale, or path is a symlink.

**Notes**

- `mode="append"` on an existing file decodes the file using its original encoding (including BOM), appends `content` as a string, and re-encodes before writing. This preserves UTF-16 and BOM-prefixed UTF-8 files correctly.
- `mode="append"` on a non-existent file writes `content` as plain UTF-8 (no BOM).

---

## Usage Examples

### Read → Edit → Write workflow

```python
from toolregistry_hub import FileOps

# 1. Read the file — get content and digest
result = FileOps.read("config.py")
print(result["content"])
# is_symlink=False, real_path="/abs/path/config.py"

# 2. Edit using the returned digest
edit_result = FileOps.edit(
    "config.py",
    old_string='DEBUG = False',
    new_string='DEBUG = True',
    digest=result["digest"],
)
print(edit_result["diff"])

# 3. Chain a second edit using the updated digest
FileOps.edit(
    "config.py",
    old_string="LOG_LEVEL = 'info'",
    new_string="LOG_LEVEL = 'debug'",
    digest=edit_result["digest"],
)
```

### Create a new file

```python
# New files do not require a digest
result = FileOps.write("notes.txt", "Hello, World!")
print(result["digest"])
```

### Overwrite an existing file

```python
r = FileOps.read("notes.txt")
FileOps.write("notes.txt", "Updated content.", digest=r["digest"])
```

### Append to an existing file

```python
r = FileOps.read("log.txt")
FileOps.write("log.txt", "\nNew entry.", digest=r["digest"], mode="append")
```

### Symlink handling

```python
r = FileOps.read("link.txt")        # allowed; r["is_symlink"] == True
# Pass the real path to edit/write to avoid symlink rejection
FileOps.write(r["real_path"], "safe write", digest=r["digest"])
```

### Replace all occurrences

```python
r = FileOps.read("todos.md")
FileOps.edit("todos.md", "TODO", "DONE", digest=r["digest"], replace_all=True)
```

### Disambiguate with start_line

```python
r = FileOps.read("script.py")
# Two matches exist; select the one closest to line 42
FileOps.edit("script.py", "return result", "return value",
             digest=r["digest"], start_line=42)
```
