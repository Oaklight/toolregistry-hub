"""ToolRegistry Hub module providing commonly used tools.

This module serves as a central hub for various utility tools including:
- Calculator: Basic arithmetic operations
- FileSystem: File system operations
- FileOps: File manipulation functions
- ThinkTool: write out thoughts for reasoning and brainstorming
- UnitConverter: Unit conversion functions

Example:
    ```python
    from toolregistry.hub import Calculator, FileSystem, FileOps, ThinkTool
    calc = Calculator()
    result = calc.add(1, 2)
    fs = FileSystem()
    exists = fs.exists('/path/to/file')
    ops = FileOps()
    ops.replace_lines('file.txt', 5, 'new content')
    think = ThinkTool.think("Analyzing the problem...")
    ```
"""

from .calculator import BaseCalculator, Calculator
from .datetime_utils import DateTime
from .fetch import Fetch
from .file_ops import FileOps
from .filesystem import FileSystem
from .think_tool import ThinkTool
from .todo_list import TodoList
from .unit_converter import UnitConverter
from .websearch import (
    BraveSearch,
    SearchResult,
    SearXNGSearch,
    SerperSearch,
    TavilySearch,
)
from .websearch_legacy import (
    WebSearchBing,
    WebSearchGeneral,
    WebSearchGoogle,
    WebSearchSearXNG,
)

__all__ = [
    "BaseCalculator",
    "Calculator",
    "DateTime",
    "FileSystem",
    "FileOps",
    "ThinkTool",
    "UnitConverter",
    # WebSearch related tools
    "Fetch",
    # ------- WebSearch tools -------
    "SearchResult",
    "BraveSearch",
    "SearXNGSearch",
    "SerperSearch",
    "TavilySearch",
    # ------- Legacy WebSearch tools -------
    "WebSearchGeneral",
    "WebSearchGoogle",
    "WebSearchBing",
    "WebSearchSearXNG",
    "TodoList",
]

__version__ = "0.6.0"  # version convention
version = __version__  # I made mistake. But here kept for backward compatibility
