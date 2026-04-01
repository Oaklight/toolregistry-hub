# File Search Tools

The FileSearch tools provide file discovery and content search capabilities commonly needed in agent workflows: glob-based file finding, regex content search (grep), and directory tree display.

## Class Overview

- `FileSearch` - Three static methods covering the most common file-discovery operations:
    - `glob()` - Find files by pattern
    - `grep()` - Search file contents with regex
    - `tree()` - Display directory structure

## Usage

### Glob - Find Files by Pattern

```python
from toolregistry_hub import FileSearch

# Find all Python files recursively
files = FileSearch.glob("**/*.py", root="/path/to/project")

# Non-recursive search in root only
files = FileSearch.glob("*.txt", root=".", recursive=False)
```

Results are sorted by modification time (most recent first), capped at 1000 results. Paths are relative to `root`.

### Grep - Search File Contents

```python
# Search for pattern in directory
results = FileSearch.grep("import os", path="/path/to/project")
# [{"file": "main.py", "line_number": 3, "content": "import os"}, ...]

# Search with file filter
results = FileSearch.grep(r"def\s+test_", path=".", file_pattern="*.py")

# Single file search
results = FileSearch.grep("TODO", path="src/main.py")

# Limit results
results = FileSearch.grep(".", path=".", max_results=10)
```

Each result is a dict with `file` (relative path), `line_number` (1-based), and `content` (stripped line).

### Tree - Directory Structure

```python
# Basic tree
print(FileSearch.tree("/path/to/project"))
# project/
# +-- src/
# |   +-- main.py
# |   +-- utils.py
# +-- tests/
# |   +-- test_main.py
# +-- README.md

# Limit depth and filter files
print(FileSearch.tree(".", max_depth=2, file_pattern="*.py"))

# Show hidden files
print(FileSearch.tree(".", show_hidden=True))
```

### Parameters

#### `glob()`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `pattern` | `str` | required | Glob pattern (e.g. `"**/*.py"`) |
| `root` | `str` | `"."` | Root directory to search from |
| `recursive` | `bool` | `True` | Whether `**` matches subdirectories |

#### `grep()`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `pattern` | `str` | required | Regex pattern to search for |
| `path` | `str` | `"."` | File or directory to search in |
| `recursive` | `bool` | `True` | Search subdirectories |
| `file_pattern` | `str \| None` | `None` | Glob to filter files (e.g. `"*.py"`) |
| `max_results` | `int` | `50` | Maximum results (capped at 200) |

#### `tree()`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | `str` | `"."` | Root directory |
| `max_depth` | `int` | `3` | Maximum depth to display |
| `show_hidden` | `bool` | `False` | Show hidden files/directories |
| `file_pattern` | `str \| None` | `None` | Glob to filter displayed files |

### Safety Caps

- Glob: 1000 results max
- Grep: 200 results max
- Tree: 2000 entries max

## MCP Server Endpoints

```
POST /tools/fs/file_search/glob
POST /tools/fs/file_search/grep
POST /tools/fs/file_search/tree
```
