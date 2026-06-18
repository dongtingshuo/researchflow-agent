"""Metric extraction from training and evaluation logs."""

from __future__ import annotations

from dataclasses import dataclass, field
import re


METRIC_ALIASES = {
    "accuracy": "accuracy",
    "acc": "accuracy",
    "top1": "top1",
    "top5": "top5",
    "precision": "precision",
    "recall": "recall",
    "f1": "f1",
    "f1_score": "f1",
    "dice": "dice",
    "iou": "iou",
    "miou": "miou",
    "bleu": "bleu",
    "rouge": "rouge",
    "loss": "loss",
    "val_loss": "val_loss",
}

METRIC_PATTERN = re.compile(
    r"(?P<name>val_loss|accuracy|acc|top1|top5|precision|recall|f1_score|f1|dice|miou|iou|bleu|rouge|loss)"
    r"\s*(?:[:=]|\s)\s*"
    r"(?P<value>-?\d+(?:\.\d+)?)\s*(?P<percent>%?)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class RawMetricMatch:
    """One raw metric match found in a log."""

    name: str
    normalized_name: str
    value: float
    raw_text: str
    line_number: int


@dataclass(frozen=True)
class LogParseResult:
    """Parsed metrics and raw evidence from a log."""

    metrics: dict[str, float] = field(default_factory=dict)
    raw_matches: list[RawMetricMatch] = field(default_factory=list)
    summary: str = ""

    def to_markdown(self) -> str:
        """Render metrics as Markdown."""
        lines = ["# Log Metric Summary", ""]
        if not self.metrics:
            lines.append("- No supported metrics were found in the log.")
        else:
            lines.extend(f"- `{name}`: {value}" for name, value in self.metrics.items())
        if self.raw_matches:
            lines.extend(["", "## Raw Matches"])
            lines.extend(
                f"- Line {item.line_number}: `{item.raw_text}` -> `{item.normalized_name}` = {item.value}"
                for item in self.raw_matches[:20]
            )
        if self.summary:
            lines.extend(["", "## Summary", self.summary])
        return "\n".join(lines)


def parse_experiment_log(log_text: str) -> LogParseResult:
    """Extract common metrics from plain-text logs."""
    metrics: dict[str, float] = {}
    raw_matches: list[RawMetricMatch] = []
    for line_number, line in enumerate(log_text.splitlines(), start=1):
        for match in METRIC_PATTERN.finditer(line):
            raw_name = match.group("name")
            normalized = normalize_metric_name(raw_name)
            value = float(match.group("value"))
            metrics[normalized] = value
            raw_matches.append(
                RawMetricMatch(
                    name=raw_name,
                    normalized_name=normalized,
                    value=value,
                    raw_text=match.group(0),
                    line_number=line_number,
                )
            )
    summary = _build_summary(metrics)
    return LogParseResult(metrics=metrics, raw_matches=raw_matches, summary=summary)


def normalize_metric_name(name: str) -> str:
    """Normalize metric aliases to stable lowercase names."""
    lowered = name.strip().lower().replace("-", "_")
    return METRIC_ALIASES.get(lowered, lowered)


def _build_summary(metrics: dict[str, float]) -> str:
    if not metrics:
        return "No metrics were extracted. Manual log review is required."
    names = ", ".join(sorted(metrics))
    return f"Extracted {len(metrics)} metric(s): {names}."
