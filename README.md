# ToolRegistry Hub

A collection of commonly used tools for LLM function calling, extracted from the main ToolRegistry package.

## Overview

ToolRegistry Hub provides a comprehensive set of utility tools designed for LLM agents and function calling scenarios:

- **Calculator**: Advanced mathematical operations and expression evaluation
- **FileSystem**: File and directory operations
- **FileOps**: Atomic file operations with diff/patch support
- **UnitConverter**: Comprehensive unit conversion utilities
- **WebSearch**: Web search and content fetching capabilities

## Installation

```bash
pip install toolregistry.hub
```

## Quick Start

```python
from toolregistry.hub import Calculator, FileSystem, WebSearchGoogle

# Mathematical calculations
calc = Calculator()
result = calc.evaluate("sqrt(16) + pow(2, 3)")

# File operations
fs = FileSystem()
fs.create_dir("my_project")
fs.create_file("my_project/config.txt")

# Web search
search = WebSearchGoogle()
results = search.search("Python programming", number_results=3)
```

## Integration with ToolRegistry

This package is designed to work seamlessly with the main ToolRegistry package:

```bash
# Install ToolRegistry with hub tools
pip install toolregistry[hub]
```

## Documentation

For detailed documentation, visit: https://toolregistry.lab.oaklight.cn

## License

MIT License
