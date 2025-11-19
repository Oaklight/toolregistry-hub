---
title: Tool Helper Functions
summary: Utility functions for tool development and usage
description: Helper functions that support the development and use of tools in ToolRegistry Hub, including class inspection and method discovery utilities.
keywords: helper, functions, utilities, static methods, class inspection, development
author: ToolRegistry Hub Team
---

# Tool Helper Functions

ToolRegistry Hub provides helper functions to support the development and use of tools.

## Overview

These utility functions are designed to help developers:

- Inspect class structures
- Discover static methods
- Determine proper namespaces
- Validate tool implementations

## Function Reference

### `_is_all_static_methods(cls: Type) -> bool`

Check if a class contains only static methods.

**Parameters:**
- `cls` (Type): The class to inspect

**Returns:**
- `bool`: True if the class contains only static methods, False otherwise

**Example:**
```python
from toolregistry_hub.utils import _is_all_static_methods
from toolregistry_hub import Calculator

# Check if Calculator has only static methods
is_static_only = _is_all_static_methods(Calculator)
print(f"Calculator has only static methods: {is_static_only}")
```

### `_determine_namespace(module_name: str, class_name: str) -> str`

Determine the namespace of a class based on module and class names.

**Parameters:**
- `module_name` (str): The name of the module
- `class_name` (str): The name of the class

**Returns:**
- `str`: The determined namespace string

**Example:**
```python
from toolregistry_hub.utils import _determine_namespace

# Determine namespace for a class
namespace = _determine_namespace("toolregistry_hub.calculator", "Calculator")
print(f"Namespace: {namespace}")
```

### `get_all_static_methods(cls: Type) -> List[str]`

Get all static methods of a class.

**Parameters:**
- `cls` (Type): The class to inspect

**Returns:**
- `List[str]`: A list of static method names

**Example:**
```python
from toolregistry_hub.utils import get_all_static_methods
from toolregistry_hub import Calculator

# Get all static methods of the Calculator class
methods = get_all_static_methods(Calculator)
print(f"Static methods of Calculator class: {methods}")
```

## Development Use Cases

### Tool Development

```python
from toolregistry_hub.utils import get_all_static_methods, _is_all_static_methods

class MyCustomTool:
    @staticmethod
    def process_data(data):
        return data.upper()
    
    @staticmethod
    def validate_input(input_data):
        return isinstance(input_data, str)

# Validate tool structure
is_valid_tool = _is_all_static_methods(MyCustomTool)
print(f"MyCustomTool is a valid static tool: {is_valid_tool}")

# Get available methods
methods = get_all_static_methods(MyCustomTool)
print(f"Available methods: {methods}")
```

### Dynamic Tool Discovery

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

# Discover all tool capabilities
all_capabilities = discover_tool_capabilities()
for tool, methods in all_capabilities.items():
    print(f"{tool}: {len(methods)} methods")
    for method in methods[:3]:  # Show first 3 methods
        print(f"  - {method}")
    if len(methods) > 3:
        print(f"  ... and {len(methods) - 3} more")
```

### Tool Validation

```python
from toolregistry_hub.utils import _is_all_static_methods, get_all_static_methods

def validate_tool_class(cls):
    """Validate that a class follows tool conventions."""
    validation_results = {
        'class_name': cls.__name__,
        'is_static_only': _is_all_static_methods(cls),
        'method_count': len(get_all_static_methods(cls)),
        'methods': get_all_static_methods(cls)
    }
    
    # Check if it's a valid tool
    validation_results['is_valid_tool'] = (
        validation_results['is_static_only'] and 
        validation_results['method_count'] > 0
    )
    
    return validation_results

# Example usage
from toolregistry_hub import Calculator

validation = validate_tool_class(Calculator)
print(f"Tool validation for {validation['class_name']}:")
print(f"  Valid tool: {validation['is_valid_tool']}")
print(f"  Static methods only: {validation['is_static_only']}")
print(f"  Method count: {validation['method_count']}")
```

## Contributing Guidelines

When developing new tools for ToolRegistry Hub, use these helper functions to ensure your tools follow the project conventions:

### Tool Structure Requirements

1. **Static Methods Only**: All tool methods should be static
2. **Clear Naming**: Use descriptive method names
3. **Proper Documentation**: Include docstrings for all methods
4. **Type Hints**: Use proper type annotations

### Example Tool Template

```python
from typing import Any, List, Optional
from toolregistry_hub.utils import _is_all_static_methods, get_all_static_methods

class MyNewTool:
    """A new tool for ToolRegistry Hub."""
    
    @staticmethod
    def my_method(param: str) -> str:
        """
        Description of what this method does.
        
        Args:
            param: Description of the parameter
            
        Returns:
            Description of the return value
        """
        return f"Processed: {param}"
    
    @staticmethod
    def another_method(data: List[Any]) -> int:
        """
        Another method example.
        
        Args:
            data: List of data to process
            
        Returns:
            Count of processed items
        """
        return len(data)

# Validate your tool before submitting
if __name__ == "__main__":
    # Check if tool follows conventions
    is_valid = _is_all_static_methods(MyNewTool)
    methods = get_all_static_methods(MyNewTool)
    
    print(f"Tool is valid: {is_valid}")
    print(f"Available methods: {methods}")
```

### Testing Your Tools

```python
import unittest
from toolregistry_hub.utils import _is_all_static_methods, get_all_static_methods

class TestMyNewTool(unittest.TestCase):
    def test_tool_structure(self):
        from my_module import MyNewTool
        
        # Test that tool follows conventions
        self.assertTrue(_is_all_static_methods(MyNewTool))
        
        # Test that it has methods
        methods = get_all_static_methods(MyNewTool)
        self.assertGreater(len(methods), 0)
        
        # Test specific methods exist
        self.assertIn('my_method', methods)
        self.assertIn('another_method', methods)
    
    def test_method_functionality(self):
        from my_module import MyNewTool
        
        # Test method functionality
        result = MyNewTool.my_method("test")
        self.assertEqual(result, "Processed: test")
        
        count = MyNewTool.another_method([1, 2, 3])
        self.assertEqual(count, 3)

if __name__ == '__main__':
    unittest.main()
```

## Best Practices for Contributors

1. **Use Helper Functions**: Always validate your tools using these utilities
2. **Follow Conventions**: Ensure your tools use only static methods
3. **Write Tests**: Include comprehensive tests for your tools
4. **Document Everything**: Provide clear docstrings and examples
5. **Validate Before PR**: Run validation checks before submitting pull requests

## Navigation

- [Back to Home](../index.md)
- [Contributing Guide](contributing.md)
- [Development Setup](dev_setup.md)
- [API Reference](../api_reference.md)