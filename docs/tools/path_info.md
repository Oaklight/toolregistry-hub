# Path Info Tool

The PathInfo tool provides a single-call interface to retrieve file and directory metadata.

## Class Overview

- `PathInfo` - Unified metadata query returning existence, type, size, modification time, and permissions in a single call.

## Usage

### Basic Usage

```python
from toolregistry_hub import PathInfo

# Query a file
info = PathInfo.info("/path/to/file.py")
print(info)
# {
#     "exists": True,
#     "type": "file",
#     "size": 1234,
#     "last_modified": "2026-03-18T12:00:00+00:00",
#     "permissions": "rw-r--r--"
# }

# Query a directory (size is recursive)
info = PathInfo.info("/path/to/dir")
print(info["size"])  # Total size of all files in the directory

# Non-existent path
info = PathInfo.info("/does/not/exist")
print(info)  # {"exists": False}
```

### Return Value

`info()` returns a dict with the following keys when the path exists:

| Key | Type | Description |
|-----|------|-------------|
| `exists` | `bool` | Always `True` for existing paths |
| `type` | `str` | `"file"`, `"directory"`, `"symlink"`, or `"other"` |
| `size` | `int` | Size in bytes. For directories, total size of all contents (recursive) |
| `last_modified` | `str` | ISO 8601 timestamp in UTC |
| `permissions` | `str` | Unix-style permission string (e.g. `"rwxr-xr-x"`) |

When the path does not exist, only `{"exists": False}` is returned.

## Design Rationale

PathInfo consolidates five separate metadata queries (`exists`, `is_file`, `is_dir`, `get_size`, `get_last_modified_time`) into a single call. This reduces the number of tool invocations needed in agent workflows, as LLMs typically need multiple metadata fields at once.

## MCP Server Endpoint

```
POST /tools/fs/path_info/info
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `path` | `string` | Yes | Absolute or relative path to query |

## API Reference

::: toolregistry_hub.path_info.PathInfo
