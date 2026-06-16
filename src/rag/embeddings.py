"""Embedding model adapters."""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from typing import Protocol


WORD_PATTERN = re.compile(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]")


class EmbeddingModel(Protocol):
    """Protocol implemented by embedding backends."""

    name: str

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per input text."""


@dataclass
class HashingEmbeddingModel:
    """Small deterministic embedding fallback for offline tests and demos."""

    dimension: int = 384
    name: str = "hashing-fallback"
    fallback_reason: str = ""

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        tokens = WORD_PATTERN.findall(text.lower())
        if not tokens:
            return vector

        for token in tokens:
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            bucket = int.from_bytes(digest[:4], "big") % self.dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[bucket] += sign

        return _normalize(vector)


class SentenceTransformerEmbeddingModel:
    """sentence-transformers embedding adapter."""

    def __init__(self, model_name: str, local_files_only: bool = False) -> None:
        from sentence_transformers import SentenceTransformer  # type: ignore

        self.name = model_name
        self._model = SentenceTransformer(model_name, local_files_only=local_files_only)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        vectors = self._model.encode(texts, normalize_embeddings=True)
        return [list(map(float, vector)) for vector in vectors]


def create_embedding_model(
    model_name: str,
    allow_hash_fallback: bool = True,
) -> EmbeddingModel:
    """Create the configured embedding model with an optional offline fallback."""
    try:
        return SentenceTransformerEmbeddingModel(model_name, local_files_only=True)
    except Exception as cache_exc:
        try:
            return SentenceTransformerEmbeddingModel(model_name, local_files_only=False)
        except Exception as exc:
            if allow_hash_fallback:
                reason = f"{type(cache_exc).__name__}/{type(exc).__name__}"
                return HashingEmbeddingModel(
                    name=f"hashing-fallback; failed to load {model_name}: {reason}",
                    fallback_reason=str(exc),
                )
        raise


def _normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]
