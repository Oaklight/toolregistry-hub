---
title: File System Tools
summary: File system operations for directory management, file operations, and path utilities
description: Comprehensive file system tools for creating, managing, and manipulating directories and files with advanced features like hidden file detection and recursive operations.
keywords: filesystem, file operations, directory management, path utilities, file manipulation
author: Oaklight
---

# File System Tools

The FileSystem tools provide comprehensive file system operations for creating, managing, and manipulating directories and files. These tools are designed for robust file system interactions with advanced features like hidden file detection and recursive operations.

## 🎯 Overview

The FileSystem class provides operations related to file system structure, status, and metadata:

- **Existence Checks**: Verify if files or directories exist
- **Directory Management**: Create, list, and manage directories
- **File Operations**: Create, copy, move, and delete files
- **Path Utilities**: Join paths and get absolute paths
- **Metadata Access**: Get file sizes and modification times
- **Hidden File Support**: Automatic detection of hidden files across platforms

## 🚀 Quick Start

```python
from toolregistry_hub import FileSystem

# Basic operations
FileSystem.create_dir("my_directory")
FileSystem.create_file("my_directory/test.txt")
files = FileSystem.list_dir("my_directory")
print(files)  # ['test.txt']

# Check existence
exists = FileSystem.exists("my_directory/test.txt")
print(f"File exists: {exists}")  # True

# Get file information
size = FileSystem.get_size("my_directory/test.txt")
print(f"File size: {size} bytes")
```

## 📋 API Reference

### Core Methods

#### `exists(path: str) -> bool`

Check if a file or directory exists.

**Parameters:**

- `path` (str): Path to check

**Returns:**

- `bool`: True if path exists, False otherwise

#### `is_file(path: str) -> bool`

Check if a path points to a file.

**Parameters:**

- `path` (str): Path to check

**Returns:**

- `bool`: True if path is a file, False otherwise

#### `is_dir(path: str) -> bool`

Check if a path points to a directory.

**Parameters:**

- `path` (str): Path to check

**Returns:**

- `bool`: True if path is a directory, False otherwise

#### `create_dir(path: str, parents: bool = True, exist_ok: bool = True) -> None`

Create a directory.

**Parameters:**

- `path` (str): Directory path to create
- `parents` (bool): Create parent directories if needed (default: True)
- `exist_ok` (bool): Don't raise error if directory exists (default: True)

#### `create_file(path: str) -> None`

Create an empty file or update timestamp.

**Parameters:**

- `path` (str): File path to create

#### `delete(path: str) -> None`

Delete a file or directory recursively.

**Parameters:**

- `path` (str): Path to delete

#### `list_dir(path: str, depth: int = 1, show_hidden: bool = False) -> List[str]`

List directory contents with configurable depth and hidden file visibility.

**Parameters:**

- `path` (str): Directory path to list
- `depth` (int): Maximum depth to list (default: 1, must be ≥ 1)
- `show_hidden` (bool): Include hidden files/directories (default: False)

**Returns:**

- `List[str]`: List of relative path strings

**Hidden File Detection:**

- **Unix/Linux/macOS**: Files starting with '.'
- **Windows**: Files with hidden attribute set

## 🔧 Advanced Operations

### Directory Management

```python
from toolregistry_hub import FileSystem

# Create nested directories
FileSystem.create_dir("project/src/components", parents=True)

# Create multiple directories
directories = ["build", "dist", "logs"]
for dir_name in directories:
    FileSystem.create_dir(dir_name)

# Check directory structure
if FileSystem.is_dir("project"):
    print("Project directory exists")
```

### File Operations

```python
from toolregistry_hub import FileSystem

# Create files
FileSystem.create_file("config.json")
FileSystem.create_file("README.md")

# Copy files
FileSystem.copy("config.json", "config.backup.json")

# Move/rename files
FileSystem.move("README.md", "docs/README.md")

# Delete files
FileSystem.delete("config.backup.json")
```

### Recursive Directory Listing

```python
from toolregistry_hub import FileSystem

# List immediate contents
files = FileSystem.list_dir("src")
print("Direct files:", files)

# List with depth 3
files = FileSystem.list_dir("src", depth=3)
print(f"Found {len(files)} items")

# Include hidden files
files_with_hidden = FileSystem.list_dir(".", show_hidden=True)
print("Files including hidden:", files_with_hidden)

# List Python files recursively
python_files = [f for f in FileSystem.list_dir("src", depth=5) if f.endswith('.py')]
print(f"Found {len(python_files)} Python files")
```

### Path Utilities

```python
from toolregistry_hub import FileSystem

# Join paths safely
config_path = FileSystem.join_paths("etc", "app", "config.yaml")
print(f"Config path: {config_path}")

# Get absolute paths
abs_src_path = FileSystem.get_absolute_path("src")
print(f"Absolute src path: {abs_src_path}")

# Cross-platform path handling
log_file = FileSystem.join_paths("logs", "app.log")
FileSystem.create_file(log_file)
```

### File Metadata

```python
from toolregistry_hub import FileSystem
import time

# Get file size
size = FileSystem.get_size("large_file.zip")
print(f"File size: {size:,} bytes")

# Get last modified time
mod_time = FileSystem.get_last_modified_time("config.json")
print(f"Last modified: {time.ctime(mod_time)}")

# Check file vs directory
path = "some_path"
if FileSystem.exists(path):
    if FileSystem.is_file(path):
        print(f"{path} is a file, size: {FileSystem.get_size(path)} bytes")
    elif FileSystem.is_dir(path):
        print(f"{path} is a directory")
else:
    print(f"{path} does not exist")
```

## 🛠️ Best Practices

### Error Handling

```python
from toolregistry_hub import FileSystem

def safe_file_operation(file_path):
    """Safely perform file operations with error handling."""
    if not FileSystem.exists(file_path):
        print(f"Warning: {file_path} does not exist")
        return False

    try:
        if FileSystem.is_file(file_path):
            size = FileSystem.get_size(file_path)
            print(f"File {file_path} exists and is {size} bytes")
            return True
        else:
            print(f"{file_path} is not a file")
            return False
    except Exception as e:
        print(f"Error accessing {file_path}: {e}")
        return False
```

### Directory Cleanup

```python
from toolregistry_hub import FileSystem

def cleanup_temp_files():
    """Clean up temporary files and directories."""
    temp_dirs = ["temp", "tmp", ".cache"]

    for temp_dir in temp_dirs:
        if FileSystem.exists(temp_dir):
            print(f"Removing {temp_dir}...")
            FileSystem.delete(temp_dir)
            print(f"{temp_dir} removed successfully")

# Usage
cleanup_temp_files()
```

### Project Structure Creation

```python
from toolregistry_hub import FileSystem

def create_project_structure(base_path):
    """Create a standard project directory structure."""
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
        print(f"Created: {full_path}")

# Usage
create_project_structure("my_project")
```

## 🚨 Important Notes

### Hidden File Handling

- **Cross-platform**: Automatically detects hidden files on different operating systems
- **Unix systems**: Files starting with '.'
- **Windows**: Uses file attributes to detect hidden files
- **Permission errors**: Skipped during listing operations

### Path Safety

- **Relative paths**: Handled correctly with proper joining
- **Absolute paths**: Supported for all operations
- **Invalid paths**: May raise exceptions or return False

### Performance Considerations

- **Deep recursion**: Use appropriate depth limits for large directory structures
- **Large directories**: Consider filtering results for better performance
- **Hidden files**: Enabling `show_hidden=True` may impact performance on large directories

## 🔄 Comparison with FileOps

**FileSystem vs FileOps:**

- **FileSystem**: Directory operations, file existence, metadata, path utilities
- **FileOps**: File content operations, searching, diff-based modifications
- **Use together**: FileSystem for structure, FileOps for content

```python
from toolregistry_hub import FileSystem, FileOps

# Create directory structure
FileSystem.create_dir("project/src")

# Create and manipulate file content
FileOps.write_file("project/src/main.py", "print('Hello World')")
content = FileOps.read_file("project/src/main.py")

# Check file info
if FileSystem.exists("project/src/main.py"):
    size = FileSystem.get_size("project/src/main.py")
    print(f"File size: {size} bytes")
```
