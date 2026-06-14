"""Shared data models for paper parsing and retrieval."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class PageText:
    """Text extracted from one PDF page."""

    page_number: int
    text: str


@dataclass(frozen=True)
class ParsedPaper:
    """Parsed representation of a paper PDF."""

    source_path: Path
    pages: list[PageText]

    @property
    def page_count(self) -> int:
        return len(self.pages)

    @property
    def total_characters(self) -> int:
        return sum(len(page.text) for page in self.pages)


@dataclass(frozen=True)
class TextChunk:
    """A retrieval chunk with page provenance."""

    chunk_id: str
    text: str
    page_numbers: list[int]
    start_token: int = 0
    end_token: int = 0
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class RetrievedChunk:
    """A chunk returned by vector search."""

    chunk: TextChunk
    score: float
