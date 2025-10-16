# Other Tools

In addition to the main tools, ToolRegistry Hub also provides some other utility tools, including thinking tools and web content fetching tools.

## Thinking Tool

The thinking tool provides simple tools for reasoning and brainstorming.

### Class Overview

- `ThinkTool` - A simple tool that provides reasoning and brainstorming functionality

### Detailed API

#### ThinkTool Class

`ThinkTool` is a simple tool that provides reasoning and brainstorming functionality.

##### Methods

- `think(thought: str) -> None`: Record thinking content without obtaining new information or modifying the repository

### Usage Example

```python
from toolregistry_hub import ThinkTool

# Record thinking content
ThinkTool.think("I need to consider how to optimize this algorithm. First, I can try to reduce the number of loops...")
```

## Web Content Fetching Tool

The web content fetching tool provides functionality to fetch web page content from URLs.

### Class Overview

- `Fetch` - A class that provides web content fetching functionality

### Detailed API

#### Fetch Class

`Fetch` is a class that provides web content fetching functionality.

##### Methods

- `fetch_content(url: str, timeout: float = 10.0, proxy: Optional[str] = None) -> str`: Fetch web page content from URL

### Usage Example

```python
from toolregistry_hub import Fetch

# Fetch web page content
content = Fetch.fetch_content("https://www.example.com")
print(f"Web page content length: {len(content)} characters")
print(f"Web page content preview: {content[:200]}...")
```

## Tool Helper Functions

ToolRegistry Hub also provides some helper functions to support the development and use of tools.

### Function Overview

- `_is_all_static_methods(cls: Type) -> bool`: Check if a class contains only static methods
- `_determine_namespace(module_name: str, class_name: str) -> str`: Determine the namespace of a class
- `get_all_static_methods(cls: Type) -> List[str]`: Get all static methods of a class

### Usage Example

```python
from toolregistry_hub.utils import get_all_static_methods
from toolregistry_hub import Calculator

# Get all static methods of the Calculator class
methods = get_all_static_methods(Calculator)
print(f"Static methods of Calculator class: {methods}")
```

## Browser Usage Tool

The browser usage tool provides functionality for interacting with browsers, but this module is not yet implemented.

## Navigation

- [Back to Home](../readme_en.md)
- [View Navigation Page](navigation.md)
- [Calculator Tools](calculator.md)
- [Date Time Tools](datetime.md)
- [File Operations Tools](file_ops.md)
- [File System Tools](filesystem.md)
- [Web Search Tools](websearch/index.md)
- [Unit Converter Tools](unit_converter.md)
