"""Application configuration for ResearchFlow-Agent."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Optional, Union


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
VECTORSTORE_DIR = DATA_DIR / "vectorstores"
WORKSPACE_DIR = DATA_DIR / "workspaces"
OUTPUT_DIR = DATA_DIR / "outputs"


def _load_env_file(path: Path) -> None:
    """Load simple KEY=VALUE pairs from a local .env file if it exists."""
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _resolve_path(value: Union[str, Path]) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def _env_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return int(raw_value)
    except ValueError:
        return default


def _env_bool(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    """Runtime settings loaded from environment variables."""

    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    allow_hash_embedding_fallback: bool = True
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    enable_cross_encoder_reranker: bool = True
    upload_dir: Path = UPLOAD_DIR
    vectorstore_dir: Path = VECTORSTORE_DIR
    workspace_dir: Path = WORKSPACE_DIR
    output_dir: Path = OUTPUT_DIR
    request_timeout_seconds: int = 60
    max_chunk_tokens: int = 220
    chunk_overlap_tokens: int = 40
    top_k_retrieval: int = 8
    reranker_candidate_multiplier: int = 4

    @property
    def llm_enabled(self) -> bool:
        return bool(self.openai_api_key and self.openai_api_key != "your_api_key_here")

    def data_directories(self) -> Iterable[Path]:
        return (
            self.upload_dir,
            self.vectorstore_dir,
            self.workspace_dir,
            self.output_dir,
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return application settings, loading .env once per process."""
    _load_env_file(PROJECT_ROOT / ".env")

    settings = Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        embedding_model=os.getenv(
            "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
        ),
        allow_hash_embedding_fallback=_env_bool("ALLOW_HASH_EMBEDDING_FALLBACK", True),
        reranker_model=os.getenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2"),
        enable_cross_encoder_reranker=_env_bool("ENABLE_CROSS_ENCODER_RERANKER", True),
        upload_dir=_resolve_path(os.getenv("UPLOAD_DIR", "data/uploads")),
        vectorstore_dir=_resolve_path(
            os.getenv("VECTORSTORE_DIR", "data/vectorstores")
        ),
        workspace_dir=_resolve_path(os.getenv("WORKSPACE_DIR", "data/workspaces")),
        output_dir=_resolve_path(os.getenv("OUTPUT_DIR", "data/outputs")),
        request_timeout_seconds=_env_int("REQUEST_TIMEOUT_SECONDS", 60),
        max_chunk_tokens=_env_int("MAX_PAPER_CHUNK_TOKENS", 220),
        chunk_overlap_tokens=_env_int("CHUNK_OVERLAP_TOKENS", 40),
        top_k_retrieval=_env_int("TOP_K_RETRIEVAL", 8),
        reranker_candidate_multiplier=_env_int("RERANKER_CANDIDATE_MULTIPLIER", 4),
    )
    ensure_directories(settings)
    return settings


def ensure_directories(settings: Optional[Settings] = None) -> None:
    """Create local data directories required by the app."""
    active_settings = settings or Settings()
    for directory in active_settings.data_directories():
        directory.mkdir(parents=True, exist_ok=True)
