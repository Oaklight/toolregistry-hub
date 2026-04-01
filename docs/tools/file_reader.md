# 文件读取工具

FileReader 工具提供多格式文件读取功能，支持行号显示、分页和安全上限。支持纯文本文件、Jupyter Notebook 和 PDF。

## 类概述

- `FileReader` - 三种读取方法，对应不同文件格式：
    - `read()` - 文本文件，带行号和分页
    - `read_notebook()` - Jupyter Notebook（`.ipynb`）
    - `read_pdf()` - PDF 文件（需要可选依赖）

## 使用方法

### 读取文本文件

```python
from toolregistry_hub import FileReader

# 读取文件，显示行号
content = FileReader.read("/path/to/file.py")
print(content)
# [/path/to/file.py] lines 1-50 of 200 (use offset=51 to read more)
# 1 | import os
# 2 | import sys
# 3 |
# 4 | def main():
# ...

# 分页读取
content = FileReader.read("/path/to/file.py", offset=50, limit=25)
```

### 读取 Jupyter Notebook

```python
# 读取 notebook 单元格，显示类型标记和输出
content = FileReader.read_notebook("analysis.ipynb")
# [Notebook: analysis.ipynb]
#
# --- Cell 1 [markdown] ---
# # Data Analysis
#
# --- Cell 2 [code] ---
# ```python
# import pandas as pd
# df = pd.read_csv("data.csv")
# ```
# Output:
# ...
```

无需外部依赖 -- 使用标准库 `json`。

### 读取 PDF

```python
# 读取所有页面（上限 20 页）
content = FileReader.read_pdf("document.pdf")

# 读取指定页面范围
content = FileReader.read_pdf("document.pdf", pages="5-10")

# 读取单页
content = FileReader.read_pdf("document.pdf", pages="3")
```

需要安装 `pypdf` 或 `pdfplumber`：

```bash
pip install toolregistry-hub[reader]
```

如果两者都已安装，优先使用 `pdfplumber` 以获得更好的文本质量。

### 参数

#### `read()`

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `path` | `str` | 必填 | 文本文件路径 |
| `offset` | `int` | `1` | 起始行号（从 1 开始） |
| `limit` | `int \| None` | `None` | 最大读取行数（默认 2000） |

#### `read_notebook()`

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `path` | `str` | 必填 | `.ipynb` 文件路径 |

#### `read_pdf()`

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `path` | `str` | 必填 | PDF 文件路径 |
| `pages` | `str \| None` | `None` | 页面范围（如 `"1-5"`、`"3"`） |

### 安全上限

- 文本文件：最大 10 MB
- 文本行数：每次读取默认 2000 行
- PDF 页数：每次调用最多 20 页
- Notebook 输出：每个单元格输出最大 10 KB

## MCP 服务端点

```
POST /tools/reader/read
POST /tools/reader/read_pdf
POST /tools/reader/read_notebook
```

## API 参考

::: toolregistry_hub.file_reader.FileReader
