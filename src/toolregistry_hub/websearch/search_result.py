from dataclasses import dataclass
from typing import Any


@dataclass
class SearchResult:
    title: str
    url: str
    content: str
    score: float = 1.0

    def get(self, key: str, default: Any | None = None) -> Any:
        """Support dict-like get method for backward compatibility."""
        return getattr(self, key, default)
