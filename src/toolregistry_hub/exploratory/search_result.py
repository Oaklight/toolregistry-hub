from dataclasses import dataclass


@dataclass
class SearchResult:
    title: str
    url: str
    content: str
    excerpt: str = None
    score: int = 1.0
