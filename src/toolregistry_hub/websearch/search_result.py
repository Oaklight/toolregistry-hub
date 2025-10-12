from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class SearchResult:
    title: str
    url: str
    content: str
    score: float = 1.0

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Support dict-like get method for backward compatibility."""
        return getattr(self, key, default)
