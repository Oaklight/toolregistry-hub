# 文件操作工具

文件操作工具提供各种文件内容操作功能，包括读取、写入、搜索和替换。

## 类概览

文件操作工具主要包括以下类：

- `FileOps` - 提供核心文件操作功能，专为 LLM 代理集成设计

## 使用方法

### 基本使用

```python
from toolregistry_hub import FileOps

# Read file
content = FileOps.read_file("path/to/file.txt")
print(content)

# Write file
FileOps.write_file("path/to/new_file.txt", "Hello, World!")

# Append content to file
FileOps.append_file("path/to/file.txt", "\nNew line appended.")

# Search files
results = FileOps.search_files("src", "class.*Search", "*.py")
for result in results:
    print(f"File: {result['file']}")
    print(f"Line number: {result['line_num']}")
    print(f"Line: {result['line']}")
    print(f"Context: {result['context']}")
```

## 详细 API

### FileOps 类

`FileOps` 是一个提供核心文件操作功能的类，专为 LLM 代理集成设计。

#### 方法

- `replace_by_diff(path: str, diff: str) -> None`: 使用差异字符串替换文件内容
- `search_files(path: str, regex: str, file_pattern: str = "*") -> List[dict]`: 在文件中搜索匹配正则表达式的内容，返回包含 file, line_num, line, context 键的字典列表
- `replace_by_git(path: str, diff: str) -> None`: 使用 Git 风格的差异替换文件内容
- `read_file(path: str) -> str`: 读取文件内容
- `write_file(path: str, content: str) -> None`: 写入内容到文件
- `append_file(path: str, content: str) -> None`: 追加内容到文件
- `make_diff(ours: str, theirs: str) -> str`: 创建两个字符串之间的差异
- `make_git_conflict(ours: str, theirs: str) -> str`: 创建 Git 风格的冲突标记
- `validate_path(path: str) -> Dict[str, Union[bool, str]]`: 验证路径是否有效

## 示例

### 读写文件

```python
from toolregistry_hub import FileOps

# Read file
content = FileOps.read_file("example.txt")
print(f"Original content:\n{content}")
# 输出: Original content:
# Hello, World!

# Write file
FileOps.write_file("new_file.txt", "This is the content of a new file.")

# Append content to file
FileOps.append_file("example.txt", "\nThis is appended content.")

# Read file again to see changes
updated_content = FileOps.read_file("example.txt")
print(f"Updated content:\n{updated_content}")
# 输出: Updated content:
# Hello, World!
# This is appended content.
```

### 搜索文件

```python
from toolregistry_hub import FileOps

# Search for class definitions in Python files
results = FileOps.search_files("src", r"class\s+\w+", "*.py")
print(f"Found {len(results)} matches:")
for result in results:
    print(f"File: {result['file']}")
    print(f"Line number: {result['line_num']}")
    print(f"Line: {result['line']}")
    print(f"Context: {result['context']}")
    print("-" * 50)
# 输出示例:
# Found 2 matches:
# File: /tmp/test1.py
# Line number: 1
# Line: class MyClass:
# Context: [(2, '    def __init__(self):'), (3, '        pass')]
# --------------------------------------------------

# Search for specific string
results = FileOps.search_files(".", "TODO", "*")
print(f"Found {len(results)} TODO items:")
for result in results:
    print(f"File: {result['file']}")
    print(f"Line number: {result['line_num']}")
    print(f"Line: {result['line']}")
    print("-" * 50)
```

### 使用差异替换文件内容

```python
from toolregistry_hub import FileOps

# Read original file
original_content = FileOps.read_file("example.py")
print(f"Original content:\n{original_content}")

# Create diff
modified_content = original_content.replace("def hello():", "def hello_world():")
diff = FileOps.make_diff(original_content, modified_content)
print(f"Diff:\n{diff}")

# Apply diff
FileOps.replace_by_diff("example.py", diff)

# View updated file
updated_content = FileOps.read_file("example.py")
print(f"Updated content:\n{updated_content}")
```

### 验证路径

```python
from toolregistry_hub import FileOps

# Validate file path
result = FileOps.validate_path("example.txt")
if result["valid"]:
    print("Path is valid")
else:
    print(f"Path is invalid: {result['message']}")
# 输出: Path is valid

# Validate directory path
result = FileOps.validate_path("non_existent_directory/")
if result["valid"]:
    print("Path is valid")
else:
    print(f"Path is invalid: {result['message']}")
# 输出: Path is valid
```
