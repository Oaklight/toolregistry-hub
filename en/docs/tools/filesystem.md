# File System Tools

The file system tools provide various functions for file system operations, including creating, copying, moving, and deleting files and directories.

## Class Overview

The file system tools mainly include the following classes:

- `FileSystem` - Provides operations related to file system structure, status, and metadata

## Usage

### Basic Usage

```python
from toolregistry_hub import FileSystem

# Check if file or directory exists
exists = FileSystem.exists("path/to/file.txt")
print(f"File exists: {exists}")

# List directory contents
files = FileSystem.list_dir("src", depth=2, show_hidden=False)
for file in files:
    print(file)

# Create directory
FileSystem.create_dir("new_directory", parents=True, exist_ok=True)

# Create file
FileSystem.create_file("new_directory/new_file.txt")

# Get file size
size = FileSystem.get_size("path/to/file.txt")
print(f"File size: {size} bytes")
```

## Detailed API

### FileSystem Class

`FileSystem` is a class that provides operations related to file system structure, status, and metadata.

#### Methods

- `exists(path: str) -> bool`: Check if file or directory exists
- `is_file(path: str) -> bool`: Check if path is a file
- `is_dir(path: str) -> bool`: Check if path is a directory
- `_is_hidden(path_obj: Path) -> bool`: Check if path is a hidden file or directory
- `list_dir(path: str, depth: int = 1, show_hidden: bool = False) -> List[str]`: List directory contents
- `create_file(path: str) -> None`: Create empty file
- `copy(src: str, dst: str) -> None`: Copy file or directory
- `move(src: str, dst: str) -> None`: Move file or directory
- `delete(path: str) -> None`: Delete file or directory
- `get_size(path: str) -> int`: Get size of file or directory (bytes)
- `get_last_modified_time(path: str) -> float`: Get last modified time of file or directory
- `join_paths(*paths: str) -> str`: Join paths
- `get_absolute_path(path: str) -> str`: Get absolute path
- `create_dir(path: str, parents: bool = True, exist_ok: bool = True) -> None`: Create directory

## Examples

### File and Directory Checks

```python
from toolregistry_hub import FileSystem

# Check if file or directory exists
exists = FileSystem.exists("example.txt")
print(f"example.txt exists: {exists}")

# Check if it's a file
is_file = FileSystem.is_file("example.txt")
print(f"example.txt is a file: {is_file}")

# Check if it's a directory
is_dir = FileSystem.is_dir("src")
print(f"src is a directory: {is_dir}")
```

### Directory Operations

```python
from toolregistry_hub import FileSystem

# List directory contents
files = FileSystem.list_dir("src", depth=1, show_hidden=False)
print("src directory contents:")
for file in files:
    print(f"- {file}")

# Recursively list directory contents
files = FileSystem.list_dir("src", depth=3, show_hidden=False)
print(f"Found {len(files)} files and directories")

# Create directory
FileSystem.create_dir("temp/nested/dir", parents=True, exist_ok=True)
print("Directory created")
```

### File Operations

```python
from toolregistry_hub import FileSystem

# Create file
FileSystem.create_file("temp/test.txt")
print("File created")

# Copy file
FileSystem.copy("temp/test.txt", "temp/test_copy.txt")
print("File copied")

# Move file
FileSystem.move("temp/test_copy.txt", "temp/nested/test_moved.txt")
print("File moved")

# Get file size
size = FileSystem.get_size("temp/test.txt")
print(f"File size: {size} bytes")

# Get last modified time
mod_time = FileSystem.get_last_modified_time("temp/test.txt")
print(f"Last modified time: {mod_time}")

# Delete file
FileSystem.delete("temp/test.txt")
print("File deleted")
```

### Path Operations

```python
from toolregistry_hub import FileSystem

# Join paths
path = FileSystem.join_paths("src", "toolregistry_hub", "filesystem.py")
print(f"Joined path: {path}")

# Get absolute path
abs_path = FileSystem.get_absolute_path("src")
print(f"Absolute path: {abs_path}")
```

### Cleaning Up Temporary Files and Directories

```python
from toolregistry_hub import FileSystem

# Delete directory and its contents
if FileSystem.exists("temp"):
    FileSystem.delete("temp")
    print("Temporary directory deleted")
```

## Navigation

- [Back to Home](../readme_en.md)
- [View Navigation Page](navigation.md)
- [Calculator Tools](calculator.md)
- [Date Time Tools](datetime.md)
- [File Operations Tools](file_ops.md)
- [Web Search Tools](websearch/index.md)
- [Unit Converter Tools](unit_converter.md)
- [Other Tools](other_tools.md)
