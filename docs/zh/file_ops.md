# 文件操作工具

文件操作工具提供了对文件内容的各种操作功能，包括读取、写入、搜索和替换等。

## 类概览

文件操作工具主要包含以下类：

- `FileOps` - 提供核心文件操作功能，专为 LLM 代理集成设计

## 使用方法

### 基本使用

```python
from toolregistry_hub import FileOps

# 读取文件
content = FileOps.read_file("path/to/file.txt")
print(content)

# 写入文件
FileOps.write_file("path/to/new_file.txt", "Hello, World!")

# 追加内容到文件
FileOps.append_file("path/to/file.txt", "\nNew line appended.")

# 搜索文件
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

# 读取文件
content = FileOps.read_file("example.txt")
print(f"原始内容:\n{content}")

# 写入文件
FileOps.write_file("new_file.txt", "这是一个新文件的内容。")

# 追加内容到文件
FileOps.append_file("example.txt", "\n这是追加的内容。")

# 再次读取文件查看变化
updated_content = FileOps.read_file("example.txt")
print(f"更新后的内容:\n{updated_content}")
```

### 搜索文件

```python
from toolregistry_hub import FileOps

# 搜索Python文件中的类定义
results = FileOps.search_files("src", "class\\s+\\w+\\(.*\\):", "*.py")
print(f"找到 {len(results)} 个匹配项:")
for result in results:
    print(f"文件: {result['file']}")
    print(f"行号: {result['line']}")
    print(f"内容: {result['content']}")
    print(f"上下文:\n{result['context']}")
    print("-" * 50)

# 搜索特定字符串
results = FileOps.search_files(".", "TODO", "*")
print(f"找到 {len(results)} 个TODO项:")
for result in results:
    print(f"文件: {result['file']}")
    print(f"行号: {result['line']}")
    print(f"内容: {result['content']}")
    print("-" * 50)
```

### 使用差异替换文件内容

```python
from toolregistry_hub import FileOps

# 读取原始文件
original_content = FileOps.read_file("example.py")
print(f"原始内容:\n{original_content}")

# 创建差异
modified_content = original_content.replace("def hello():", "def hello_world():")
diff = FileOps.make_diff(original_content, modified_content)
print(f"差异:\n{diff}")

# 应用差异
FileOps.replace_by_diff("example.py", diff)

# 查看更新后的文件
updated_content = FileOps.read_file("example.py")
print(f"更新后的内容:\n{updated_content}")
```

### 验证路径

```python
from toolregistry_hub import FileOps

# 验证文件路径
result = FileOps.validate_path("example.txt")
if result["valid"]:
    print("路径有效")
else:
    print(f"路径无效: {result['error']}")

# 验证目录路径
result = FileOps.validate_path("non_existent_directory/")
if result["valid"]:
    print("路径有效")
else:
    print(f"路径无效: {result['error']}")
```

## 导航

- [返回首页](index.md)
- [查看导航页面](navigation.md)
- [计算器工具](calculator.md)
- [日期时间工具](datetime.md)
- [文件系统工具](filesystem.md)
- [网络搜索工具](websearch/index.md)
- [单位转换工具](unit_converter.md)
- [其他工具](other_tools.md)
