# File Operations Tools

The file operations tools provide various functions for file content operations, including reading, writing, searching, and replacing.

## Class Overview

The file operations tools mainly include the following classes:

- `FileOps` - Provides core file operation functions, designed for LLM agent integration

## Usage

### Basic Usage

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

## Detailed API

### FileOps Class

`FileOps` is a class that provides core file operation functions, designed for LLM agent integration.

#### Methods

- `replace_by_diff(path: str, diff: str) -> None`: Replace file content using diff string
- `search_files(path: str, regex: str, file_pattern: str = "*") -> List[dict]`: Search for content matching regex in files, returns list of dicts with file, line_num, line, context keys
- `replace_by_git(path: str, diff: str) -> None`: Replace file content using Git-style diff
- `read_file(path: str) -> str`: Read file content
- `write_file(path: str, content: str) -> None`: Write content to file
- `append_file(path: str, content: str) -> None`: Append content to file
- `make_diff(ours: str, theirs: str) -> str`: Create diff between two strings
- `make_git_conflict(ours: str, theirs: str) -> str`: Create Git-style conflict markers
- `validate_path(path: str) -> Dict[str, Union[bool, str]]`: Validate if path is valid

## Examples

### Reading and Writing Files

```python
from toolregistry_hub import FileOps

# Read file
content = FileOps.read_file("example.txt")
print(f"Original content:\n{content}")
# Output: Original content:
# Hello, World!

# Write file
FileOps.write_file("new_file.txt", "This is the content of a new file.")

# Append content to file
FileOps.append_file("example.txt", "\nThis is appended content.")

# Read file again to see changes
updated_content = FileOps.read_file("example.txt")
print(f"Updated content:\n{updated_content}")
# Output: Updated content:
# Hello, World!
# This is appended content.
```

### Searching Files

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
# Output example:
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

### Using Diff to Replace File Content

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

### Validating Paths

```python
from toolregistry_hub import FileOps

# Validate file path
result = FileOps.validate_path("example.txt")
if result["valid"]:
    print("Path is valid")
else:
    print(f"Path is invalid: {result['message']}")
# Output: Path is valid

# Validate directory path
result = FileOps.validate_path("non_existent_directory/")
if result["valid"]:
    print("Path is valid")
else:
    print(f"Path is invalid: {result['message']}")
# Output: Path is valid
```
