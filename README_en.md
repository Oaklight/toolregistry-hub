# ToolRegistry Hub

[中文](README_zh.md) | [English](README_en.md)

> **⚠️ Important Notice**: This is a **standalone package** that can be used independently. This package was separated from `toolregistry` at version `0.4.14` and shares version format for historical continuity only. `toolregistry-hub` has **no dependencies** on `toolregistry` and is completely independent and self-sufficient. It can be used on its own or as a submodule for the main `toolregistry` package.

A comprehensive collection of tools designed for LLM function calling, extracted from the main ToolRegistry package to provide focused utility modules.

## Overview

ToolRegistry Hub provides a robust set of utility tools specifically designed for LLM agents and function calling scenarios:

- **Calculator**: Advanced mathematical operations and expression evaluation with support for complex functions
- **DateTime**: Simple current date and time utilities in ISO format
- **FileSystem**: Comprehensive file and directory operations with enhanced error handling
- **FileOps**: Atomic file operations with diff/patch support for safe file manipulations
- **ThinkTool**: Simple reasoning and brainstorming tool for structured thought processes
- **UnitConverter**: Extensive unit conversion utilities covering various measurement systems
- **WebSearch**: Multi-engine web search capabilities with content fetching and filtering options

## Features

### Calculator

- Evaluate mathematical expressions with standard and custom functions
- Support for basic arithmetic, power/roots, logarithmic/exponential functions
- Statistical operations (min, max, sum, average, median, mode, standard deviation)
- Combinatorics functions (factorial, gcd, lcm)
- Distance calculations and financial computations
- Expression evaluation with safe function execution

### DateTime

- Get current UTC time in ISO 8601 format
- Simple and focused datetime functionality for LLM tools
- Static methods for easy integration

### FileSystem

- Create, read, update, and delete files and directories
- Path manipulation and validation
- Directory listing with depth control and hidden file filtering
- File metadata operations (size, modification time)
- Cross-platform compatibility

### FileOps

- Atomic file operations to prevent data corruption
- Unified diff and git-style conflict resolution
- File search with regex patterns and context
- Safe file writing with temporary file handling
- Path validation utilities

### ThinkTool

- Simple thought logging for reasoning and brainstorming
- Designed for Claude's thinking processes
- Stateless operation without external changes

### UnitConverter

- Convert between various units of measurement:
  - Temperature (Celsius, Fahrenheit, Kelvin)
  - Length (meters, feet, centimeters, inches)
  - Weight (kilograms, pounds)
  - Time (seconds, minutes)
  - Area, speed, data storage, pressure, power, energy
  - Electrical, magnetic, radiation, and light intensity units
- Comprehensive coverage of measurement systems

### WebSearch

- Multiple search engine support (Google, Bing, SearXNG)
- Content fetching and extraction from web pages
- Result filtering and ranking options
- Unified interface across different search providers

## Installation

```bash
pip install toolregistry-hub
```

## Quick Start

```python
from toolregistry_hub import Calculator, DateTime, FileSystem, ThinkTool, UnitConverter, WebSearchGoogle

# Mathematical calculations
calc = Calculator()
result = calc.evaluate("sqrt(16) + pow(2, 3)")
print(f"Calculation result: {result}")

# Get current time
current_time = DateTime.now()
print(f"Current time: {current_time}")

# File operations
fs = FileSystem()
fs.create_dir("my_project")
fs.create_file("my_project/config.txt")

# Unit conversions
converter = UnitConverter()
fahrenheit = converter.celsius_to_fahrenheit(25)
print(f"25°C = {fahrenheit}°F")

# Structured thinking
thought = ThinkTool.think("Analyzing the best approach for this problem...")
print(f"Thought process: {thought}")

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
