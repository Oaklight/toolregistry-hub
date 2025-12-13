"""ToolRegistry Hub module providing commonly used tools.

This module serves as a central hub for various utility tools including:
- Calculator: Basic arithmetic operations
- FileSystem: File system operations
- FileOps: File manipulation functions
- ThinkTool: write out thoughts for reasoning and brainstorming
- UnitConverter: Unit conversion functions

Example:
    >>> from toolregistry.hub import Calculator, FileSystem, FileOps, ThinkTool
    >>> calc = Calculator()
    >>> result = calc.add(1, 2)
    >>> fs = FileSystem()
    >>> exists = fs.exists('/path/to/file')
    >>> ops = FileOps()
    >>> ops.replace_lines('file.txt', 5, 'new content')
    >>> think = ThinkTool.think("Analyzing the problem...")
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
    BingSearch,  # Deprecated: use alternatives instead
    BraveSearch,
    SearchResult,
    SearXNGSearch,
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
    "BingSearch",  # Deprecated: frequent bot detection issues
    "SearchResult",
    "BraveSearch",
    "SearXNGSearch",
    "TavilySearch",
    # ------- Legacy WebSearch tools -------
    "WebSearchGeneral",
    "WebSearchGoogle",
    "WebSearchBing",
    "WebSearchSearXNG",
    "TodoList",
]

version = "0.5.3"  # standalone version
