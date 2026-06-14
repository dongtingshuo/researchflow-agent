"""Dependency-light local vector store for MVP retrieval."""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Union

from src.paper.models import RetrievedChunk, TextChunk


@dataclass
class VectorRecord:
    """One vector store record."""

    chunk: TextChunk
    embedding: list[float]


class LocalVectorStore:
    """A tiny cosine-similarity vector store persisted as JSON."""

    def __init__(self) -> None:
        self._records: list[VectorRecord] = []

    @property
    def size(self) -> int:
        return len(self._records)

    def add(self, chunks: list[TextChunk], embeddings: list[list[float]]) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings must have the same length")
        for chunk, embedding in zip(chunks, embeddings):
            self._records.append(VectorRecord(chunk=chunk, embedding=embedding))

    def similarity_search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> list[RetrievedChunk]:
        if top_k <= 0:
            return []

        ranked = [
            RetrievedChunk(
                chunk=record.chunk,
                score=_cosine_similarity(query_embedding, record.embedding),
            )
            for record in self._records
        ]
        ranked.sort(key=lambda item: item.score, reverse=True)
        return ranked[:top_k]

    def save(self, path: Union[str, Path]) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = [
            {"chunk": asdict(record.chunk), "embedding": record.embedding}
            for record in self._records
        ]
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Union[str, Path]) -> "LocalVectorStore":
        source = Path(path)
        store = cls()
        payload = json.loads(source.read_text(encoding="utf-8"))
        for item in payload:
            store._records.append(
                VectorRecord(
                    chunk=TextChunk(**item["chunk"]),
                    embedding=[float(value) for value in item["embedding"]],
                )
            )
        return store


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)
