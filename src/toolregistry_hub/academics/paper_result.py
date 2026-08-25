from dataclasses import dataclass
from typing import Any


@dataclass
class PaperResult:
    """Structured result from an academic paper search."""

    title: str
    authors: list[str]
    abstract: str
    url: str
    year: int | None = None
    venue: str | None = None
    doi: str | None = None
    pdf_url: str | None = None
    cited_by_count: int | None = None
    source: str = ""
    score: float = 1.0

    def get(self, key: str, default: Any | None = None) -> Any:
        """Support dict-like get method for backward compatibility."""
        return getattr(self, key, default)
