"""Text chunking for paper RAG."""

from __future__ import annotations

import re

from src.paper.models import PageText, TextChunk


TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]|[^\s]")


def tokenize(text: str) -> list[str]:
    """Tokenize mixed English/Chinese text with a small dependency-free tokenizer."""
    return TOKEN_PATTERN.findall(text)


def chunk_pages(
    pages: list[PageText],
    max_tokens: int = 220,
    overlap_tokens: int = 40,
) -> list[TextChunk]:
    """Split page text into overlapping chunks while retaining page numbers."""
    if max_tokens <= 0:
        raise ValueError("max_tokens must be positive")
    if overlap_tokens < 0:
        raise ValueError("overlap_tokens cannot be negative")
    if overlap_tokens >= max_tokens:
        raise ValueError("overlap_tokens must be smaller than max_tokens")

    chunks: list[TextChunk] = []
    for page in pages:
        tokens = tokenize(page.text)
        if not tokens:
            continue

        start = 0
        while start < len(tokens):
            end = min(start + max_tokens, len(tokens))
            chunk_tokens = tokens[start:end]
            text = _join_tokens(chunk_tokens)
            chunk_id = f"p{page.page_number}-{start}-{end}"
            chunks.append(
                TextChunk(
                    chunk_id=chunk_id,
                    text=text,
                    page_numbers=[page.page_number],
                    start_token=start,
                    end_token=end,
                )
            )
            if end == len(tokens):
                break
            start = end - overlap_tokens

    return chunks


def _join_tokens(tokens: list[str]) -> str:
    text = " ".join(tokens)
    text = re.sub(r"\s+([.,;:!?%)\]\}])", r"\1", text)
    text = re.sub(r"([(\[\{])\s+", r"\1", text)
    text = re.sub(r"(?<=\w)\s*-\s*(?=\w)", "-", text)
    text = re.sub(r"(?<=\d)\.\s+(?=\d)", ".", text)
    return text.strip()
