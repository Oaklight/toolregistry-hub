---
title: 文件系统工具
summary: 文件系统操作，用于目录管理、文件操作和路径工具
description: 全面的文件系统工具，用于创建、管理和操作目录与文件，具备高级功能如隐藏文件检测和递归操作。
keywords: filesystem, file operations, directory management, path utilities, file manipulation
author: Oaklight
---

# 文件系统工具

文件系统工具提供全面的文件系统操作，用于创建、管理和操作目录与文件，具备高级功能如隐藏文件检测和递归操作。

## 🎯 概述

FileSystem 类提供与文件系统结构、状态和元数据相关的操作：

- **存在性检查**：验证文件或目录是否存在
- **目录管理**：创建、列出和管理目录
- **文件操作**：创建、复制、移动和删除文件
- **路径工具**：连接路径和获取绝对路径
- **元数据访问**：获取文件大小和修改时间
- **隐藏文件支持**：跨平台自动检测隐藏文件

## 🚀 快速开始

```python
from toolregistry_hub import FileSystem

# 基本操作
FileSystem.create_dir("my_directory")
FileSystem.create_file("my_directory/test.txt")
files = FileSystem.list_dir("my_directory")
print(files)  # ['test.txt']

# 检查存在性
exists = FileSystem.exists("my_directory/test.txt")
print(f"文件存在: {exists}")  # True

# 获取文件信息
size = FileSystem.get_size("my_directory/test.txt")
print(f"文件大小: {size} 字节")
```

## 📋 API 参考

### 核心方法

#### `exists(path: str) -> bool`

检查文件或目录是否存在。

**参数：**

- `path` (str): 要检查的路径

**返回：**

- `bool`: 路径存在时返回 True，否则返回 False

#### `is_file(path: str) -> bool`

检查路径是否指向文件。

**参数：**

- `path` (str): 要检查的路径

**返回：**

- `bool`: 路径是文件时返回 True，否则返回 False

#### `is_dir(path: str) -> bool`

检查路径是否指向目录。

**参数：**

- `path` (str): 要检查的路径

**返回：**

- `bool`: 路径是目录时返回 True，否则返回 False

#### `create_dir(path: str, parents: bool = True, exist_ok: bool = True) -> None`

创建目录。

**参数：**

- `path` (str): 要创建的目录路径
- `parents` (bool): 如需则创建父目录（默认: True）
- `exist_ok` (bool): 目录存在时不抛出错误（默认: True）

#### `list_dir(path: str, depth: int = 1, show_hidden: bool = False) -> List[str]`

列出目录内容，支持可配置深度和隐藏文件可见性。

**参数：**

- `path` (str): 要列出的目录路径
- `depth` (int): 最大列出深度（默认: 1，必须 ≥ 1）
- `show_hidden` (bool): 包括隐藏文件/目录（默认: False）

**返回：**

- `List[str]`: 相对路径字符串列表

**隐藏文件检测：**

- **Unix/Linux/macOS**: 以 '.' 开头的文件
- **Windows**: 设置了隐藏属性的文件

#### `create_file(path: str) -> None`

创建空文件或更新时间戳。

**参数：**

- `path` (str): 要创建的文件路径

#### `delete(path: str) -> None`

递归删除文件或目录。

**参数：**

- `path` (str): 要删除的路径

#### `copy(src: str, dst: str) -> None`

复制文件或目录。

**参数：**

- `src` (str): 源路径
- `dst` (str): 目标路径

#### `move(src: str, dst: str) -> None`

移动或重命名文件或目录。

**参数：**

- `src` (str): 源路径
- `dst` (str): 目标路径

#### `get_size(path: str) -> int`

获取文件或目录的大小（字节）。

**参数：**

- `path` (str): 路径

**返回：**

- `int`: 大小（字节）

#### `get_last_modified_time(path: str) -> float`

获取文件或目录的最后修改时间。

**参数：**

- `path` (str): 路径

**返回：**

- `float`: Unix 时间戳

#### `join_paths(*paths: str) -> str`

安全连接路径。

**参数：**

- `*paths` (str): 路径段

**返回：**

- `str`: 连接后的路径

#### `get_absolute_path(path: str) -> str`

获取绝对路径。

**参数：**

- `path` (str): 路径

**返回：**

- `str`: 绝对路径

## 🔧 高级操作

### 目录管理

```python
from toolregistry_hub import FileSystem

# 创建嵌套目录
FileSystem.create_dir("project/src/components", parents=True)

# 创建多个目录
directories = ["build", "dist", "logs"]
for dir_name in directories:
    FileSystem.create_dir(dir_name)

# 检查目录结构
if FileSystem.is_dir("project"):
    print("项目目录存在")
```

### 文件操作

```python
from toolregistry_hub import FileSystem

# 创建文件
FileSystem.create_file("config.json")
FileSystem.create_file("README.md")

# 复制文件
FileSystem.copy("config.json", "config.backup.json")

# 移动/重命名文件
FileSystem.move("README.md", "docs/README.md")

# 删除文件
FileSystem.delete("config.backup.json")
```

### 递归目录列出

```python
from toolregistry_hub import FileSystem

# 列出直接内容
files = FileSystem.list_dir("src")
print("直接文件:", files)

# 列出深度为3的内容
files = FileSystem.list_dir("src", depth=3)
print(f"找到 {len(files)} 个项目")

# 包括隐藏文件
files_with_hidden = FileSystem.list_dir(".", show_hidden=True)
print("包括隐藏文件的文件:", files_with_hidden)

# 递归列出 Python 文件
python_files = [f for f in FileSystem.list_dir("src", depth=5) if f.endswith('.py')]
print(f"找到 {len(python_files)} 个 Python 文件")
```

### 路径工具

```python
from toolregistry_hub import FileSystem

# 安全连接路径
config_path = FileSystem.join_paths("etc", "app", "config.yaml")
print(f"配置路径: {config_path}")

# 获取绝对路径
abs_src_path = FileSystem.get_absolute_path("src")
print(f"绝对 src 路径: {abs_src_path}")

# 跨平台路径处理
log_file = FileSystem.join_paths("logs", "app.log")
FileSystem.create_file(log_file)
```

### 文件元数据

```python
from toolregistry_hub import FileSystem
import time

# 获取文件大小
size = FileSystem.get_size("large_file.zip")
print(f"文件大小: {size:,} 字节")

# 获取最后修改时间
mod_time = FileSystem.get_last_modified_time("config.json")
print(f"最后修改时间: {time.ctime(mod_time)}")

# 检查文件与目录
path = "some_path"
if FileSystem.exists(path):
    if FileSystem.is_file(path):
        print(f"{path} 是文件，大小: {FileSystem.get_size(path)} 字节")
    elif FileSystem.is_dir(path):
        print(f"{path} 是目录")
else:
    print(f"{path} 不存在")
```

## 🛠️ 最佳实践

### 错误处理

```python
from toolregistry_hub import FileSystem

def safe_file_operation(file_path):
    """安全执行文件操作，带错误处理。"""
    if not FileSystem.exists(file_path):
        print(f"警告: {file_path} 不存在")
        return False

    try:
        if FileSystem.is_file(file_path):
            size = FileSystem.get_size(file_path)
            print(f"文件 {file_path} 存在，大小为 {size} 字节")
            return True
        else:
            print(f"{file_path} 不是文件")
            return False
    except Exception as e:
        print(f"访问 {file_path} 时出错: {e}")
        return False
```

### 目录清理

```python
from toolregistry_hub import FileSystem

def cleanup_temp_files():
    """清理临时文件和目录。"""
    temp_dirs = ["temp", "tmp", ".cache"]

    for temp_dir in temp_dirs:
        if FileSystem.exists(temp_dir):
            print(f"正在删除 {temp_dir}...")
            FileSystem.delete(temp_dir)
            print(f"{temp_dir} 已成功删除")

# 使用
cleanup_temp_files()
```

### 项目结构创建

```python
from toolregistry_hub import FileSystem

def create_project_structure(base_path):
    """创建标准项目目录结构。"""
    directories = [
        "src",
        "tests",
        "docs",
        "logs",
        "config",
        "build",
        "dist"
    ]

    for directory in directories:
        full_path = FileSystem.join_paths(base_path, directory)
        FileSystem.create_dir(full_path)
        print(f"已创建: {full_path}")

# 使用
create_project_structure("my_project")
```

## 🚨 重要注意事项

### 隐藏文件处理

- **跨平台**：自动检测不同操作系统的隐藏文件
- **Unix 系统**：以 '.' 开头的文件
- **Windows**：使用文件属性检测隐藏文件
- **权限错误**：列出操作中跳过

### 路径安全性

- **相对路径**：正确处理
- **绝对路径**：支持所有操作
- **无效路径**：可能引发异常或返回 False

### 性能考虑

- **深层递归**：对大型目录结构使用适当的深度限制
- **大目录**：考虑过滤结果以提高性能
- **隐藏文件**：启用 `show_hidden=True` 可能影响大目录的性能

## 🔄 与 FileOps 的对比

**FileSystem 与 FileOps 对比：**

- **FileSystem**：目录操作、文件存在性、元数据、路径工具
- **FileOps**：文件内容操作、搜索、基于差异的修改
- **协同使用**：FileSystem 管理结构，FileOps 处理内容

```python
from toolregistry_hub import FileSystem, FileOps

# 创建目录结构
FileSystem.create_dir("project/src")

# 创建和操作文件内容
FileOps.write_file("project/src/main.py", "print('Hello World')")
content = FileOps.read_file("project/src/main.py")

# 检查文件信息
if FileSystem.exists("project/src/main.py"):
    size = FileSystem.get_size("project/src/main.py")
    print(f"文件大小: {size} 字节")
