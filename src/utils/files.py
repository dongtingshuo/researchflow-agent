"""File naming helpers."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from uuid import uuid4


def unique_output_path(output_dir: Path, prefix: str, suffix: str) -> Path:
    """Return a collision-resistant output path under output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)
    clean_suffix = suffix if suffix.startswith(".") else f".{suffix}"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    return output_dir / f"{prefix}-{timestamp}-{uuid4().hex[:8]}{clean_suffix}"


def portable_display_path(path: str | Path, base_dir: str | Path | None = None) -> str:
    """Return a report-friendly path without exposing a local home directory."""
    resolved = Path(path).resolve()
    base = Path(base_dir).resolve() if base_dir is not None else Path.cwd().resolve()
    try:
        return resolved.relative_to(base).as_posix()
    except ValueError:
        return f"<external>/{resolved.name}"
