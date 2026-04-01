# 路径信息工具

PathInfo 工具提供单次调用获取文件和目录元数据的接口，替代旧版 FileSystem 类中的多个独立查询方法。

## 类概述

- `PathInfo` - 统一的元数据查询，单次调用返回存在性、类型、大小、修改时间和权限信息。

## 使用方法

### 基本用法

```python
from toolregistry_hub import PathInfo

# 查询文件
info = PathInfo.info("/path/to/file.py")
print(info)
# {
#     "exists": True,
#     "type": "file",
#     "size": 1234,
#     "last_modified": "2026-03-18T12:00:00+00:00",
#     "permissions": "rw-r--r--"
# }

# 查询目录（大小为递归计算）
info = PathInfo.info("/path/to/dir")
print(info["size"])  # 目录下所有文件的总大小

# 不存在的路径
info = PathInfo.info("/does/not/exist")
print(info)  # {"exists": False}
```

### 返回值

当路径存在时，`info()` 返回包含以下键的字典：

| 键 | 类型 | 描述 |
|-----|------|-------------|
| `exists` | `bool` | 路径存在时始终为 `True` |
| `type` | `str` | `"file"`、`"directory"`、`"symlink"` 或 `"other"` |
| `size` | `int` | 大小（字节）。目录为所有内容的递归总大小 |
| `last_modified` | `str` | UTC 时区的 ISO 8601 时间戳 |
| `permissions` | `str` | Unix 风格权限字符串（如 `"rwxr-xr-x"`） |

路径不存在时，仅返回 `{"exists": False}`。

## 设计理念

PathInfo 用单次调用替代了旧版 `FileSystem` 类的五个独立方法（`exists`、`is_file`、`is_dir`、`get_size`、`get_last_modified_time`）。这减少了 Agent 工作流中所需的工具调用次数，因为 LLM 通常需要同时获取多个元数据字段。

## MCP 服务端点

```
POST /tools/fs/path_info/info
```

**参数：**

| 参数 | 类型 | 必填 | 描述 |
|-----------|------|----------|-------------|
| `path` | `string` | 是 | 要查询的绝对或相对路径 |

## API 参考

::: toolregistry_hub.path_info.PathInfo
