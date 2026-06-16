"""Data models for code repository analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class KeyFile:
    """A file recognized as important for understanding or running a project."""

    role: str
    path: str
    reason: str
    content_excerpt: str = ""
    size_bytes: int = 0
    line_count: int = 0

    @property
    def has_content(self) -> bool:
        """Return whether this key file was successfully read."""
        return bool(self.content_excerpt.strip())


@dataclass(frozen=True)
class CodeAnalysisResult:
    """Structured output from the code analyzer."""

    source_type: str
    source: str
    workspace_path: Path
    directory_tree: str
    key_files: list[KeyFile] = field(default_factory=list)
    summary: str = ""

    def key_files_markdown(self) -> str:
        """Render key files as Markdown for the UI."""
        if not self.key_files:
            return "No key files were recognized."
        lines = [
            "| Role | Path | Reason | Content read |",
            "| --- | --- | --- | --- |",
        ]
        for item in self.key_files:
            status = f"yes, {item.line_count} lines" if item.has_content else "no"
            lines.append(f"| {item.role} | `{item.path}` | {item.reason} | {status} |")
        return "\n".join(lines)
