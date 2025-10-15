# 其他工具

除了主要工具外，ToolRegistry Hub还提供了一些其他实用工具，包括思考工具和网页内容获取工具等。

## 思考工具

思考工具提供了用于推理和头脑风暴的简单工具。

### 类概览

- `ThinkTool` - 提供推理和头脑风暴功能的简单工具

### 详细 API

#### ThinkTool 类

`ThinkTool` 是一个提供推理和头脑风暴功能的简单工具。

##### 方法

- `think(thought: str) -> None`: 记录思考内容，不获取新信息或修改仓库

### 使用示例

```python
from toolregistry_hub import ThinkTool

# 记录思考内容
ThinkTool.think("我需要考虑如何优化这个算法。首先，我可以尝试减少循环次数...")
```

## 网页内容获取工具

网页内容获取工具提供了从URL获取网页内容的功能。

### 类概览

- `Fetch` - 提供网页内容获取功能的类

### 详细 API

#### Fetch 类

`Fetch` 是一个提供网页内容获取功能的类。

##### 方法

- `fetch_content(url: str, timeout: float = 10.0, proxy: Optional[str] = None) -> str`: 从URL获取网页内容

### 使用示例

```python
from toolregistry_hub import Fetch

# 获取网页内容
content = Fetch.fetch_content("https://www.example.com")
print(f"网页内容长度: {len(content)} 字符")
print(f"网页内容预览: {content[:200]}...")
```

## 工具辅助函数

ToolRegistry Hub还提供了一些辅助函数，用于支持工具的开发和使用。

### 函数概览

- `_is_all_static_methods(cls: Type) -> bool`: 检查类是否只包含静态方法
- `_determine_namespace(module_name: str, class_name: str) -> str`: 确定类的命名空间
- `get_all_static_methods(cls: Type) -> List[str]`: 获取类的所有静态方法

### 使用示例

```python
from toolregistry_hub.utils import get_all_static_methods
from toolregistry_hub import Calculator

# 获取Calculator类的所有静态方法
methods = get_all_static_methods(Calculator)
print(f"Calculator类的静态方法: {methods}")
```

## 浏览器使用工具

浏览器使用工具提供了与浏览器交互的功能，但目前该模块尚未实现。

## 导航

- [返回首页](index.md)
- [查看导航页面](navigation.md)
- [计算器工具](calculator.md)
- [日期时间工具](datetime.md)
- [文件操作工具](file_ops.md)
- [文件系统工具](filesystem.md)
- [网络搜索工具](websearch/index.md)
- [单位转换工具](unit_converter.md)