"""Paper experiment-result extraction helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
import re

from src.paper.models import PageText, RetrievedChunk, TextChunk


RESULT_KEYWORDS = {
    "table",
    "result",
    "accuracy",
    "performance",
    "evaluation",
    "experiment",
    "baseline",
    "ablation",
    "comparison",
    "实验",
    "结果",
    "评估",
    "对比",
    "消融",
}

METRIC_NAMES = {
    "accuracy",
    "acc",
    "precision",
    "recall",
    "f1",
    "bleu",
    "rouge",
    "dice",
    "iou",
    "miou",
    "loss",
}

DATASET_PATTERN = re.compile(
    r"\b(?:ImageNet|COCO|CIFAR-10|CIFAR-100|MNIST|VQA\s*v?2(?:\.0)?|"
    r"SQuAD|HotpotQA|FEVER|ALFWorld|WebShop|ADE20K|Cityscapes|Pascal VOC|"
    r"MS COCO|LAION-[A-Za-z0-9-]+|toy-cifar)\b",
    re.IGNORECASE,
)
METRIC_BEFORE_VALUE = re.compile(
    r"\b(?P<name>accuracy|acc|precision|recall|f1|bleu|rouge|dice|miou|iou|loss)"
    r"\b(?P<context>[^\d\n]{0,80}?)"
    r"(?P<value>\d+(?:\.\d+)?)\s*(?P<percent>%?)",
    re.IGNORECASE,
)
VALUE_BEFORE_METRIC = re.compile(
    r"(?P<value>\d+(?:\.\d+)?)\s*(?P<percent>%?)\s*"
    r"\b(?P<name>accuracy|acc|precision|recall|f1|bleu|rouge|dice|miou|iou|loss)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class PaperMetric:
    """One metric extracted from paper text."""

    name: str
    value: float
    dataset: str = ""
    evidence: str = ""
    page: int | None = None
    confidence: str = "medium"


@dataclass(frozen=True)
class PaperResultSummary:
    """Structured summary of paper-reported experiment results."""

    task: str = "uncertain"
    datasets: list[str] = field(default_factory=list)
    metrics: list[PaperMetric] = field(default_factory=list)
    evidence_pages: list[int] = field(default_factory=list)
    status: str = "uncertain"
    notes: list[str] = field(default_factory=list)

    def metrics_dict(self) -> dict[str, float]:
        """Return the first value for each metric name."""
        output: dict[str, float] = {}
        for item in self.metrics:
            output.setdefault(item.name, item.value)
        return output

    def to_markdown(self) -> str:
        """Render extracted paper results as Markdown."""
        lines = [
            "# Paper Result Extraction",
            "",
            f"- Status: `{self.status}`",
            f"- Task: {self.task}",
            f"- Evidence pages: {', '.join(map(str, self.evidence_pages)) or 'none'}",
            "",
            "## Datasets",
        ]
        if self.datasets:
            lines.extend(f"- {item}" for item in self.datasets)
        else:
            lines.append("- missing evidence")
        lines.extend(["", "## Metrics"])
        if self.metrics:
            lines.extend(
                f"- `{item.name}` = {item.value:g}"
                f"{f' on {item.dataset}' if item.dataset else ''}"
                f"{f' (Page {item.page})' if item.page else ''}: {item.evidence}"
                for item in self.metrics
            )
        else:
            lines.append("- missing evidence: no supported metric pattern was extracted.")
        if self.notes:
            lines.extend(["", "## Notes"])
            lines.extend(f"- {note}" for note in self.notes)
        return "\n".join(lines)


def extract_paper_results(
    paper_chunks: list[TextChunk] | list[RetrievedChunk] | list[PageText],
) -> PaperResultSummary:
    """Extract paper experiment results from chunks or pages."""
    evidence_blocks = [_to_evidence_block(item) for item in paper_chunks]
    result_blocks = [
        item for item in evidence_blocks if _contains_result_keyword(item["text"])
    ]
    if not result_blocks:
        return PaperResultSummary(
            status="missing evidence",
            notes=[
                "No result-related chunk matched table/result/evaluation keywords.",
                "requires manual check",
            ],
        )

    datasets = _extract_datasets(result_blocks)
    metrics = _extract_metrics(result_blocks, datasets)
    pages = sorted({page for item in result_blocks for page in item["pages"]})
    notes: list[str] = []
    status = "ok"
    if not metrics:
        status = "uncertain"
        notes.append("missing evidence: result-related text was found, but no supported metric value was extracted.")
    if not datasets:
        notes.append("uncertain: no known dataset name was extracted from the result evidence.")
    notes.append("requires manual check: extracted metrics should be verified against the original PDF tables.")

    return PaperResultSummary(
        task=_infer_task(result_blocks),
        datasets=datasets,
        metrics=metrics,
        evidence_pages=pages,
        status=status,
        notes=notes,
    )


def _to_evidence_block(item: TextChunk | RetrievedChunk | PageText) -> dict[str, object]:
    if isinstance(item, RetrievedChunk):
        chunk = item.chunk
        return {"text": chunk.text, "pages": list(chunk.page_numbers)}
    if isinstance(item, TextChunk):
        return {"text": item.text, "pages": list(item.page_numbers)}
    return {"text": item.text, "pages": [item.page_number]}


def _contains_result_keyword(text: object) -> bool:
    lowered = str(text).lower()
    return any(keyword.lower() in lowered for keyword in RESULT_KEYWORDS)


def _extract_datasets(blocks: list[dict[str, object]]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for block in blocks:
        for match in DATASET_PATTERN.finditer(str(block["text"])):
            name = " ".join(match.group(0).split())
            key = name.lower()
            if key in seen:
                continue
            seen.add(key)
            output.append(name)
    return output[:12]


def _extract_metrics(
    blocks: list[dict[str, object]],
    datasets: list[str],
) -> list[PaperMetric]:
    metrics: list[PaperMetric] = []
    seen: set[tuple[str, float, int | None]] = set()
    patterns = [METRIC_BEFORE_VALUE, VALUE_BEFORE_METRIC]
    for block in blocks:
        text = str(block["text"])
        pages = block["pages"] if isinstance(block["pages"], list) else []
        page = int(pages[0]) if pages else None
        for sentence in _split_sentences(text):
            for pattern in patterns:
                for match in pattern.finditer(sentence):
                    name = _normalize_metric_name(match.group("name"))
                    context = match.groupdict().get("context", "")
                    if context and _context_has_other_metric(context, name):
                        continue
                    value = float(match.group("value"))
                    key = (name, value, page)
                    if key in seen:
                        continue
                    seen.add(key)
                    metrics.append(
                        PaperMetric(
                            name=name,
                            value=value,
                            dataset=_dataset_for_sentence(sentence, datasets),
                            evidence=_shorten(sentence),
                            page=page,
                            confidence="medium" if page is not None else "low",
                        )
                    )
                    if len(metrics) >= 20:
                        return metrics
    return metrics


def _infer_task(blocks: list[dict[str, object]]) -> str:
    text = " ".join(str(item["text"]) for item in blocks).lower()
    if "visual question answering" in text or "vqa" in text:
        return "visual question answering"
    if "segmentation" in text or "miou" in text or "dice" in text:
        return "segmentation"
    if "classification" in text or "imagenet" in text or "accuracy" in text:
        return "classification"
    if "retrieval" in text or "bleu" in text or "rouge" in text:
        return "language or retrieval evaluation"
    return "uncertain"


def _dataset_for_sentence(sentence: str, datasets: list[str]) -> str:
    lowered = sentence.lower()
    for dataset in datasets:
        if dataset.lower() in lowered:
            return dataset
    return datasets[0] if len(datasets) == 1 else ""


def _normalize_metric_name(name: str) -> str:
    lowered = name.lower()
    if lowered == "acc":
        return "accuracy"
    return lowered


def _context_has_other_metric(context: str, name: str) -> bool:
    lowered = context.lower()
    for metric_name in METRIC_NAMES:
        normalized = _normalize_metric_name(metric_name)
        if normalized == name:
            continue
        if re.search(rf"\b{re.escape(metric_name)}\b", lowered):
            return True
    return False


def _split_sentences(text: str) -> list[str]:
    normalized = " ".join(text.split())
    return [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?。！？])\s+", normalized)
        if sentence.strip()
    ]


def _shorten(text: str, limit: int = 280) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3].rstrip() + "..."
