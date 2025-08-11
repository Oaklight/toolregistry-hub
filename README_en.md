# ToolRegistry Hub

A comprehensive collection of tools designed for LLM function calling, extracted from the main ToolRegistry package to provide focused utility modules.

## Version Information

This package was separated from `toolregistry`, with an initial version of `0.4.14` to maintain version continuity with the original `toolregistry` package.

## Overview

ToolRegistry Hub provides a robust set of utility tools specifically designed for LLM agents and function calling scenarios:

- **Calculator**: Advanced mathematical operations and expression evaluation with support for complex functions
- **FileSystem**: Comprehensive file and directory operations with enhanced error handling
- **FileOps**: Atomic file operations with diff/patch support for safe file manipulations
- **UnitConverter**: Extensive unit conversion utilities covering various measurement systems
- **WebSearch**: Multi-engine web search capabilities with content fetching and filtering options

## Features

### Calculator

- Evaluate mathematical expressions with standard and custom functions
- Support for trigonometric, logarithmic, and statistical operations
- Error handling for invalid expressions

### FileSystem

- Create, read, update, and delete files and directories
- Path manipulation and validation
- Recursive directory operations

### FileOps

- Atomic file operations to prevent data corruption
- Diff and patch functionality for file comparisons and updates
- Safe file writing with backup options

### UnitConverter

- Convert between various units of measurement (length, weight, volume, temperature, etc.)
- Support for custom unit definitions
- Batch conversion capabilities

### WebSearch

- Multiple search engine support (Google, Bing, SearXNG)
- Content fetching and extraction from web pages
- Result filtering and ranking options

## Installation

```bash
pip install toolregistry-hub
```

## Quick Start

```python
from toolregistry_hub import Calculator, FileSystem, WebSearchGoogle

# Mathematical calculations
calc = Calculator()
result = calc.evaluate("sqrt(16) + pow(2, 3)")
print(f"Calculation result: {result}")

# File operations
fs = FileSystem()
fs.create_dir("my_project")
fs.create_file("my_project/config.txt", content="Configuration data")

# Web search
search = WebSearchGoogle()
results = search.search("Python programming", number_results=3)
for result in results:
    print(f"Title: {result['title']}")
    print(f"URL: {result['url']}")
    print(f"Content: {result['content'][:100]}...")
```

## Integration with ToolRegistry

This package is designed to work seamlessly with the main ToolRegistry package:

```bash
# Install ToolRegistry with hub tools
pip install toolregistry[hub]
```

## API Documentation

For detailed API documentation and advanced usage examples, visit: <https://toolregistry.readthedocs.io/>

## Contributing

We welcome contributions! Please see our contributing guidelines for more information on how to get involved.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes and version history.
