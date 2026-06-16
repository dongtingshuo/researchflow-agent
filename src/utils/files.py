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
