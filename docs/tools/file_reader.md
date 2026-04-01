# File Reader Tools

The FileReader tool provides multi-format file reading with line numbers, pagination, and safety caps. It supports plain text files, Jupyter notebooks, and PDFs.

## Class Overview

- `FileReader` - Four reading methods for different file formats:
    - `read()` - Text files with line numbers and pagination
    - `read_notebook()` - Jupyter notebooks (`.ipynb`)
    - `read_pdf()` - PDF files (requires optional dependency)
    - `read_image()` - Image files with multimodal content blocks (requires optional dependency)

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

### Reading Images

```python
# Read an image — returns multimodal content blocks
blocks = FileReader.read_image("screenshot.png")
# [
#   {"type": "text", "text": "[Image: screenshot.png (image/png, 45321 bytes)]"},
#   {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "iVBOR..."}}
# ]

# With custom max size (default 5 MB base64)
blocks = FileReader.read_image("large_photo.jpg", max_size=1_000_000)
```

Supported formats: `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`.

If the base64-encoded image exceeds `max_size`, Pillow is used for adaptive quality downsampling. Requires `Pillow`:

```bash
pip install toolregistry-hub[reader_image]
```

If Pillow is not installed, the original image is returned with a warning logged.

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

#### `read_image()`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | `str` | required | Path to image file |
| `max_size` | `int` | `5242880` | Max base64-encoded size in bytes (5 MB) |

### Safety Caps

- Text files: 10 MB max file size
- Text lines: 2000 lines default per read
- PDF pages: 20 pages max per call
- Notebook outputs: 10 KB per cell output
- Images: 5 MB max base64-encoded size (auto-downsampled if exceeded)

## MCP Server Endpoints

```
POST /tools/reader/read
POST /tools/reader/read_pdf
POST /tools/reader/read_notebook
POST /tools/reader/read_image
```

## API Reference

::: toolregistry_hub.file_reader.FileReader
