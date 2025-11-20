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
    print(f"Line: {result['line']}")
    print(f"Content: {result['content']}")
    print(f"Context: {result['context']}")
```

## 详细 API

### FileOps 类

`FileOps` 是一个提供核心文件操作功能的类，专为 LLM 代理集成设计。

#### 方法

- `replace_by_diff(path: str, diff: str) -> None`: 使用差异字符串替换文件内容
- `search_files(path: str, regex: str, file_pattern: str = "*") -> List[dict]`: 在文件中搜索匹配正则表达式的内容
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

# Write file
FileOps.write_file("new_file.txt", "This is the content of a new file.")

# Append content to file
FileOps.append_file("example.txt", "\nThis is appended content.")

# Read file again to see changes
updated_content = FileOps.read_file("example.txt")
print(f"Updated content:\n{updated_content}")
```

### 搜索文件

```python
from toolregistry_hub import FileOps

# Search for class definitions in Python files
results = FileOps.search_files("src", "class\\s+\\w+\\(.*\\):", "*.py")
print(f"Found {len(results)} matches:")
for result in results:
    print(f"File: {result['file']}")
    print(f"Line: {result['line']}")
    print(f"Content: {result['content']}")
    print(f"Context:\n{result['context']}")
    print("-" * 50)

# Search for specific string
results = FileOps.search_files(".", "TODO", "*")
print(f"Found {len(results)} TODO items:")
for result in results:
    print(f"File: {result['file']}")
    print(f"Line: {result['line']}")
    print(f"Content: {result['content']}")
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
    print(f"Path is invalid: {result['error']}")

# Validate directory path
result = FileOps.validate_path("non_existent_directory/")
if result["valid"]:
    print("Path is valid")
else:
    print(f"Path is invalid: {result['error']}")
