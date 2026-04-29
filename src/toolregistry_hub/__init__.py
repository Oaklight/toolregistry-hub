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

from .bash_tool import BashTool
from .calculator import BaseCalculator, Calculator
from .cron_tool import CronTool
from .datetime_utils import DateTime
from .fetch import Fetch
from .file_ops import FileOps
from .file_reader import FileReader
from .file_search import FileSearch
from .filesystem import FileSystem
from .path_info import PathInfo
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

__all__ = [
    "BashTool",
    "BaseCalculator",
    "Calculator",
    "DateTime",
    "FileSystem",
    "FileOps",
    "FileReader",
    "FileSearch",
    "PathInfo",
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
    "TodoList",
    "CronTool",
]

__version__ = "0.8.0"  # version convention
version = __version__  # I made mistake. But here kept for backward compatibility
