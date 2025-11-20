---
title: 工具辅助函数
summary: 用于工具开发和使用的实用函数
description: 支持 ToolRegistry Hub 中工具开发和使用的辅助函数，包括类检查和方法发现实用程序。
keywords: 辅助, 函数, 实用程序, 静态方法, 类检查, 开发
author: ToolRegistry Hub 团队
---

# 工具辅助函数

ToolRegistry Hub 提供了一些辅助函数，用于支持工具的开发和使用。

## 概览

这些实用函数旨在帮助开发者：

- 检查类结构
- 发现静态方法
- 确定适当的命名空间
- 验证工具实现

## 函数参考

### `_is_all_static_methods(cls: Type) -> bool`

检查类是否只包含静态方法。

**参数：**
- `cls` (Type): 要检查的类

**返回值：**
- `bool`: 如果类只包含静态方法则返回 True，否则返回 False

**示例：**
```python
from toolregistry_hub.utils import _is_all_static_methods
from toolregistry_hub import Calculator

# 检查 Calculator 是否只有静态方法
is_static_only = _is_all_static_methods(Calculator)
print(f"Calculator 只有静态方法: {is_static_only}")
```

### `_determine_namespace(module_name: str, class_name: str) -> str`

根据模块和类名确定类的命名空间。

**参数：**
- `module_name` (str): 模块名称
- `class_name` (str): 类名称

**返回值：**
- `str`: 确定的命名空间字符串

**示例：**
```python
from toolregistry_hub.utils import _determine_namespace

# 为类确定命名空间
namespace = _determine_namespace("toolregistry_hub.calculator", "Calculator")
print(f"命名空间: {namespace}")
```

### `get_all_static_methods(cls: Type) -> List[str]`

获取类的所有静态方法。

**参数：**
- `cls` (Type): 要检查的类

**返回值：**
- `List[str]`: 静态方法名称列表

**示例：**
```python
from toolregistry_hub.utils import get_all_static_methods
from toolregistry_hub import Calculator

# 获取 Calculator 类的所有静态方法
methods = get_all_static_methods(Calculator)
print(f"Calculator 类的静态方法: {methods}")
```

## 开发用例

### 工具开发

```python
from toolregistry_hub.utils import get_all_static_methods, _is_all_static_methods

class MyCustomTool:
    @staticmethod
    def process_data(data):
        return data.upper()
    
    @staticmethod
    def validate_input(input_data):
        return isinstance(input_data, str)

# 验证工具结构
is_valid_tool = _is_all_static_methods(MyCustomTool)
print(f"MyCustomTool 是有效的静态工具: {is_valid_tool}")

# 获取可用方法
methods = get_all_static_methods(MyCustomTool)
print(f"可用方法: {methods}")
```

### 动态工具发现

```python
from toolregistry_hub.utils import get_all_static_methods
from toolregistry_hub import Calculator, DateTime, FileOps

def discover_tool_capabilities():
    tools = {
        'Calculator': Calculator,
        'DateTime': DateTime,
        'FileOps': FileOps
    }
    
    capabilities = {}
    for tool_name, tool_class in tools.items():
        methods = get_all_static_methods(tool_class)
        capabilities[tool_name] = methods
    
    return capabilities

# 发现所有工具功能
all_capabilities = discover_tool_capabilities()
for tool, methods in all_capabilities.items():
    print(f"{tool}: {len(methods)} 个方法")
    for method in methods[:3]:  # 显示前3个方法
        print(f"  - {method}")
    if len(methods) > 3:
        print(f"  ... 还有 {len(methods) - 3} 个")
```

### 工具验证

```python
from toolregistry_hub.utils import _is_all_static_methods, get_all_static_methods

def validate_tool_class(cls):
    """验证类是否遵循工具约定。"""
    validation_results = {
        'class_name': cls.__name__,
        'is_static_only': _is_all_static_methods(cls),
        'method_count': len(get_all_static_methods(cls)),
        'methods': get_all_static_methods(cls)
    }
    
    # 检查是否是有效工具
    validation_results['is_valid_tool'] = (
        validation_results['is_static_only'] and 
        validation_results['method_count'] > 0
    )
    
    return validation_results

# 使用示例
from toolregistry_hub import Calculator

validation = validate_tool_class(Calculator)
print(f"{validation['class_name']} 的工具验证:")
print(f"  有效工具: {validation['is_valid_tool']}")
print(f"  仅静态方法: {validation['is_static_only']}")
print(f"  方法数量: {validation['method_count']}")
```

## 贡献指南

在为 ToolRegistry Hub 开发新工具时，使用这些辅助函数确保您的工具遵循项目约定：

### 工具结构要求

1. **仅静态方法**：所有工具方法都应该是静态的
2. **清晰命名**：使用描述性的方法名称
3. **适当文档**：为所有方法包含文档字符串
4. **类型提示**：使用适当的类型注解

### 示例工具模板

```python
from typing import Any, List, Optional
from toolregistry_hub.utils import _is_all_static_methods, get_all_static_methods

class MyNewTool:
    """ToolRegistry Hub 的新工具。"""
    
    @staticmethod
    def my_method(param: str) -> str:
        """
        描述此方法的功能。
        
        Args:
            param: 参数描述
            
        Returns:
            返回值描述
        """
        return f"已处理: {param}"
    
    @staticmethod
    def another_method(data: List[Any]) -> int:
        """
        另一个方法示例。
        
        Args:
            data: 要处理的数据列表
            
        Returns:
            已处理项目的数量
        """
        return len(data)

# 在提交前验证您的工具
if __name__ == "__main__":
    # 检查工具是否遵循约定
    is_valid = _is_all_static_methods(MyNewTool)
    methods = get_all_static_methods(MyNewTool)
    
    print(f"工具有效: {is_valid}")
    print(f"可用方法: {methods}")
```

### 测试您的工具

```python
import unittest
from toolregistry_hub.utils import _is_all_static_methods, get_all_static_methods

class TestMyNewTool(unittest.TestCase):
    def test_tool_structure(self):
        from my_module import MyNewTool
        
        # 测试工具是否遵循约定
        self.assertTrue(_is_all_static_methods(MyNewTool))
        
        # 测试是否有方法
        methods = get_all_static_methods(MyNewTool)
        self.assertGreater(len(methods), 0)
        
        # 测试特定方法是否存在
        self.assertIn('my_method', methods)
        self.assertIn('another_method', methods)
    
    def test_method_functionality(self):
        from my_module import MyNewTool
        
        # 测试方法功能
        result = MyNewTool.my_method("test")
        self.assertEqual(result, "已处理: test")
        
        count = MyNewTool.another_method([1, 2, 3])
        self.assertEqual(count, 3)

if __name__ == '__main__':
    unittest.main()
```

## 贡献者最佳实践

1. **使用辅助函数**：始终使用这些实用程序验证您的工具
2. **遵循约定**：确保您的工具仅使用静态方法
3. **编写测试**：为您的工具包含全面的测试
4. **记录一切**：提供清晰的文档字符串和示例
5. **提交前验证**：在提交拉取请求前运行验证检查
