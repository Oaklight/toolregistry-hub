# 文件搜索工具

FileSearch 工具提供 Agent 工作流中常用的文件发现和内容搜索功能：基于 glob 的文件查找、正则表达式内容搜索（grep）和目录树显示。

## 类概述

- `FileSearch` - 三个静态方法，覆盖最常见的文件发现操作：
    - `glob()` - 按模式查找文件
    - `grep()` - 使用正则表达式搜索文件内容
    - `tree()` - 显示目录结构

## 使用方法

### Glob - 按模式查找文件

```python
from toolregistry_hub import FileSearch

# 递归查找所有 Python 文件
files = FileSearch.glob("**/*.py", root="/path/to/project")

# 仅在根目录中非递归搜索
files = FileSearch.glob("*.txt", root=".", recursive=False)
```

结果按修改时间排序（最近的在前），最多返回 1000 条。路径相对于 `root`。

### Grep - 搜索文件内容

```python
# 在目录中搜索模式
results = FileSearch.grep("import os", path="/path/to/project")
# [{"file": "main.py", "line_number": 3, "content": "import os"}, ...]

# 使用文件过滤器搜索
results = FileSearch.grep(r"def\s+test_", path=".", file_pattern="*.py")

# 搜索单个文件
results = FileSearch.grep("TODO", path="src/main.py")

# 限制结果数
results = FileSearch.grep(".", path=".", max_results=10)
```

每个结果是包含 `file`（相对路径）、`line_number`（从 1 开始）和 `content`（去除首尾空白的行）的字典。

### Tree - 目录结构

```python
# 基本树形显示
print(FileSearch.tree("/path/to/project"))
# project/
# +-- src/
# |   +-- main.py
# |   +-- utils.py
# +-- tests/
# |   +-- test_main.py
# +-- README.md

# 限制深度并过滤文件
print(FileSearch.tree(".", max_depth=2, file_pattern="*.py"))

# 显示隐藏文件
print(FileSearch.tree(".", show_hidden=True))
```

### 参数

#### `glob()`

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `pattern` | `str` | 必填 | Glob 模式（如 `"**/*.py"`） |
| `root` | `str` | `"."` | 搜索的根目录 |
| `recursive` | `bool` | `True` | `**` 是否匹配子目录 |

#### `grep()`

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `pattern` | `str` | 必填 | 要搜索的正则表达式 |
| `path` | `str` | `"."` | 要搜索的文件或目录 |
| `recursive` | `bool` | `True` | 是否搜索子目录 |
| `file_pattern` | `str \| None` | `None` | 文件过滤 glob（如 `"*.py"`） |
| `max_results` | `int` | `50` | 最大结果数（上限 200） |

#### `tree()`

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `path` | `str` | `"."` | 根目录 |
| `max_depth` | `int` | `3` | 最大显示深度 |
| `show_hidden` | `bool` | `False` | 是否显示隐藏文件/目录 |
| `file_pattern` | `str \| None` | `None` | 文件过滤 glob |

### 安全上限

- Glob：最多 1000 条结果
- Grep：最多 200 条结果
- Tree：最多 2000 个条目

## MCP 服务端点

```
POST /tools/fs/file_search/glob
POST /tools/fs/file_search/grep
POST /tools/fs/file_search/tree
```
