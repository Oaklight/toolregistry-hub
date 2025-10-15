# 文件系统工具

文件系统工具提供了对文件系统的各种操作功能，包括文件和目录的创建、复制、移动、删除等。

## 类概览

文件系统工具主要包含以下类：

- `FileSystem` - 提供与文件系统结构、状态和元数据相关的操作

## 使用方法

### 基本使用

```python
from toolregistry_hub import FileSystem

# 检查文件或目录是否存在
exists = FileSystem.exists("path/to/file.txt")
print(f"文件存在: {exists}")

# 列出目录内容
files = FileSystem.list_dir("src", depth=2, show_hidden=False)
for file in files:
    print(file)

# 创建目录
FileSystem.create_dir("new_directory", parents=True, exist_ok=True)

# 创建文件
FileSystem.create_file("new_directory/new_file.txt")

# 获取文件大小
size = FileSystem.get_size("path/to/file.txt")
print(f"文件大小: {size} 字节")
```

## 详细 API

### FileSystem 类

`FileSystem` 是一个提供与文件系统结构、状态和元数据相关操作的类。

#### 方法

- `exists(path: str) -> bool`: 检查文件或目录是否存在
- `is_file(path: str) -> bool`: 检查路径是否为文件
- `is_dir(path: str) -> bool`: 检查路径是否为目录
- `_is_hidden(path_obj: Path) -> bool`: 检查路径是否为隐藏文件或目录
- `list_dir(path: str, depth: int = 1, show_hidden: bool = False) -> List[str]`: 列出目录内容
- `create_file(path: str) -> None`: 创建空文件
- `copy(src: str, dst: str) -> None`: 复制文件或目录
- `move(src: str, dst: str) -> None`: 移动文件或目录
- `delete(path: str) -> None`: 删除文件或目录
- `get_size(path: str) -> int`: 获取文件或目录的大小（字节）
- `get_last_modified_time(path: str) -> float`: 获取文件或目录的最后修改时间
- `join_paths(*paths: str) -> str`: 连接路径
- `get_absolute_path(path: str) -> str`: 获取绝对路径
- `create_dir(path: str, parents: bool = True, exist_ok: bool = True) -> None`: 创建目录

## 示例

### 文件和目录检查

```python
from toolregistry_hub import FileSystem

# 检查文件或目录是否存在
exists = FileSystem.exists("example.txt")
print(f"example.txt 存在: {exists}")

# 检查是否为文件
is_file = FileSystem.is_file("example.txt")
print(f"example.txt 是文件: {is_file}")

# 检查是否为目录
is_dir = FileSystem.is_dir("src")
print(f"src 是目录: {is_dir}")
```

### 目录操作

```python
from toolregistry_hub import FileSystem

# 列出目录内容
files = FileSystem.list_dir("src", depth=1, show_hidden=False)
print("src 目录内容:")
for file in files:
    print(f"- {file}")

# 递归列出目录内容
files = FileSystem.list_dir("src", depth=3, show_hidden=False)
print(f"找到 {len(files)} 个文件和目录")

# 创建目录
FileSystem.create_dir("temp/nested/dir", parents=True, exist_ok=True)
print("目录已创建")
```

### 文件操作

```python
from toolregistry_hub import FileSystem

# 创建文件
FileSystem.create_file("temp/test.txt")
print("文件已创建")

# 复制文件
FileSystem.copy("temp/test.txt", "temp/test_copy.txt")
print("文件已复制")

# 移动文件
FileSystem.move("temp/test_copy.txt", "temp/nested/test_moved.txt")
print("文件已移动")

# 获取文件大小
size = FileSystem.get_size("temp/test.txt")
print(f"文件大小: {size} 字节")

# 获取最后修改时间
mod_time = FileSystem.get_last_modified_time("temp/test.txt")
print(f"最后修改时间: {mod_time}")

# 删除文件
FileSystem.delete("temp/test.txt")
print("文件已删除")
```

### 路径操作

```python
from toolregistry_hub import FileSystem

# 连接路径
path = FileSystem.join_paths("src", "toolregistry_hub", "filesystem.py")
print(f"连接路径: {path}")

# 获取绝对路径
abs_path = FileSystem.get_absolute_path("src")
print(f"绝对路径: {abs_path}")
```

### 清理临时文件和目录

```python
from toolregistry_hub import FileSystem

# 删除目录及其内容
if FileSystem.exists("temp"):
    FileSystem.delete("temp")
    print("临时目录已删除")
```

## 导航

- [返回首页](index.md)
- [查看导航页面](navigation.md)
- [计算器工具](calculator.md)
- [日期时间工具](datetime.md)
- [文件操作工具](file_ops.md)
- [网络搜索工具](websearch/index.md)
- [单位转换工具](unit_converter.md)
- [其他工具](other_tools.md)