# File Reader Tools

The FileReader tool provides multi-format file reading with line numbers, pagination, and safety caps. It supports plain text files, Jupyter notebooks, and PDFs.

## Class Overview

- `FileReader` - Three reading methods for different file formats:
    - `read()` - Text files with line numbers and pagination
    - `read_notebook()` - Jupyter notebooks (`.ipynb`)
    - `read_pdf()` - PDF files (requires optional dependency)

## Usage

### Reading Text Files

```python
from toolregistry_hub import FileReader

# Read a file with line numbers
content = FileReader.read("/path/to/file.py")
print(content)
# [/path/to/file.py] lines 1-50 of 200 (use offset=51 to read more)
# 1 | import os
# 2 | import sys
# 3 |
# 4 | def main():
# ...

# Read with pagination
content = FileReader.read("/path/to/file.py", offset=50, limit=25)
```

### Reading Jupyter Notebooks

```python
# Read notebook cells with type markers and outputs
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

No external dependencies needed -- uses stdlib `json`.

### Reading PDFs

```python
# Read all pages (up to 20 page cap)
content = FileReader.read_pdf("document.pdf")

# Read specific page range
content = FileReader.read_pdf("document.pdf", pages="5-10")

# Read a single page
content = FileReader.read_pdf("document.pdf", pages="3")
```

Requires `pypdf` or `pdfplumber`:

```bash
pip install toolregistry-hub[reader]
```

If both are installed, `pdfplumber` is preferred for better text quality.

### Parameters

#### `read()`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | `str` | required | Path to text file |
| `offset` | `int` | `1` | Starting line number (1-indexed) |
| `limit` | `int \| None` | `None` | Max lines to read (default 2000) |

#### `read_notebook()`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | `str` | required | Path to `.ipynb` file |

#### `read_pdf()`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | `str` | required | Path to PDF file |
| `pages` | `str \| None` | `None` | Page range (e.g. `"1-5"`, `"3"`) |

### Safety Caps

- Text files: 10 MB max file size
- Text lines: 2000 lines default per read
- PDF pages: 20 pages max per call
- Notebook outputs: 10 KB per cell output

## MCP Server Endpoints

```
POST /tools/reader/read
POST /tools/reader/read_pdf
POST /tools/reader/read_notebook
```

## API Reference

::: toolregistry_hub.file_reader.FileReader
