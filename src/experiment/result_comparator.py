"""Compare paper-reported metrics with reproduced log metrics."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.experiment.log_parser import normalize_metric_name


LOWER_IS_BETTER = {"loss", "val_loss"}


@dataclass(frozen=True)
class MetricComparison:
    """One paper-vs-reproduced metric comparison."""

    name: str
    paper_value: float
    reproduced_value: float | None
    gap: float | None
    status: str
    reason: str
    evidence: str = ""


@dataclass(frozen=True)
class ResultComparison:
    """Collection of metric comparisons."""

    comparisons: list[MetricComparison] = field(default_factory=list)
    status: str = "missing"
    notes: list[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        """Render comparison as Markdown."""
        lines = ["# Paper Result vs Reproduced Result", "", f"- Overall status: `{self.status}`", ""]
        if not self.comparisons:
            lines.append("- No comparable metrics were found.")
        else:
            lines.extend(
                [
                    "| Metric | Paper | Reproduced | Gap | Status |",
                    "| --- | ---: | ---: | ---: | --- |",
                ]
            )
            for item in self.comparisons:
                reproduced = "" if item.reproduced_value is None else f"{item.reproduced_value:g}"
                gap = "" if item.gap is None else f"{item.gap:g}"
                lines.append(
                    f"| {item.name} | {item.paper_value:g} | {reproduced} | {gap} | {item.status} |"
                )
        if self.notes:
            lines.extend(["", "## Notes"])
            lines.extend(f"- {note}" for note in self.notes)
        return "\n".join(lines)


def compare_results(
    paper_metrics: dict[str, float],
    reproduced_metrics: dict[str, float],
    tolerance: float = 0.5,
) -> ResultComparison:
    """Compare normalized metric dictionaries."""
    comparisons: list[MetricComparison] = []
    notes: list[str] = []
    normalized_reproduced = {
        normalize_metric_name(name): value for name, value in reproduced_metrics.items()
    }

    for raw_name, paper_value in paper_metrics.items():
        name = normalize_metric_name(raw_name)
        reproduced_value = normalized_reproduced.get(name)
        if reproduced_value is None:
            comparisons.append(
                MetricComparison(
                    name=name,
                    paper_value=paper_value,
                    reproduced_value=None,
                    gap=None,
                    status="missing",
                    reason="No reproduced metric with the same normalized name was found.",
                )
            )
            continue

        gap = _metric_gap(name, paper_value, reproduced_value)
        status = _status_for_gap(name, gap, tolerance)
        reason = _reason_for_status(name, gap, tolerance, status)
        comparisons.append(
            MetricComparison(
                name=name,
                paper_value=paper_value,
                reproduced_value=reproduced_value,
                gap=round(gap, 6),
                status=status,
                reason=reason,
            )
        )

    if not paper_metrics:
        notes.append("No paper metrics were available for comparison.")
    if not reproduced_metrics:
        notes.append("No reproduced metrics were parsed from logs.")
    overall = _overall_status(comparisons)
    return ResultComparison(comparisons=comparisons, status=overall, notes=notes)


def _metric_gap(name: str, paper_value: float, reproduced_value: float) -> float:
    if name in LOWER_IS_BETTER:
        return paper_value - reproduced_value
    return reproduced_value - paper_value


def _status_for_gap(name: str, gap: float, tolerance: float) -> str:
    if gap >= -tolerance:
        return "reproduced"
    if gap >= -max(5.0, tolerance * 5):
        return "partially reproduced"
    return "not reproduced"


def _reason_for_status(name: str, gap: float, tolerance: float, status: str) -> str:
    direction = "lower is better" if name in LOWER_IS_BETTER else "higher is better"
    return (
        f"{status}; gap={gap:g}, tolerance={tolerance:g}, metric direction: {direction}."
    )


def _overall_status(comparisons: list[MetricComparison]) -> str:
    if not comparisons:
        return "missing"
    statuses = {item.status for item in comparisons}
    if statuses == {"reproduced"}:
        return "reproduced"
    if "reproduced" in statuses or "partially reproduced" in statuses:
        return "partially reproduced"
    if "missing" in statuses and len(statuses) == 1:
        return "missing"
    return "not reproduced"
