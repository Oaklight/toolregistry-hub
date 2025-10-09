from dataclasses import dataclass


@dataclass
class SearchResult:
    title: str
    url: str
    content: str
    score: int = 1.0
