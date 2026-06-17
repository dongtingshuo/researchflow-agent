"""Run the fixed ResearchFlow-Agent evaluation benchmark.

The script is intentionally local-first:
- By default, it disables LLM calls to avoid unexpected API usage.
- It looks for benchmark PDFs under data/test_inputs/.
- Missing PDFs are recorded as skipped cases instead of crashing the run.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import Settings, get_settings  # noqa: E402
from src.rag.qa import PaperRAGService  # noqa: E402
from src.utils.files import unique_output_path  # noqa: E402


DEFAULT_PDF_NAMES = {
    "clip-data-scale": "clip.pdf",
    "react-benchmarks": "react.pdf",
    "rag-formulations": "rag.pdf",
}


@dataclass(frozen=True)
class EvaluationCase:
    """One benchmark case loaded from examples/evaluation_benchmark.json."""

    case_id: str
    paper: str
    question: str
    reference_answer: str
    expected_pages: str = ""
    expected_terms: tuple[str, ...] = ()
    repository_url: str = ""
    evaluation_focus: str = ""


@dataclass(frozen=True)
class EvaluationResult:
    """Serializable result for one benchmark case."""

    case_id: str
    paper: str
    question: str
    status: str
    pdf_path: str
    answer: str
    citations: str
    top_pages: list[int]
    expected_terms: list[str]
    term_hits: dict[str, bool]
    notes: str = ""


def load_cases(path: Path) -> list[EvaluationCase]:
    """Load benchmark cases from JSON."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    cases = []
    for item in payload:
        cases.append(
            EvaluationCase(
                case_id=item["case_id"],
                paper=item["paper"],
                question=item["question"],
                reference_answer=item["reference_answer"],
                expected_pages=item.get("expected_pages", ""),
                expected_terms=tuple(item.get("expected_terms", [])),
                repository_url=item.get("repository_url", ""),
                evaluation_focus=item.get("evaluation_focus", ""),
            )
        )
    return cases


def run_cases(
    cases: list[EvaluationCase],
    settings: Settings,
    pdf_root: Path,
    pdf_overrides: dict[str, Path],
) -> list[EvaluationResult]:
    """Run all benchmark cases and collect results."""
    results = []
    for case in cases:
        pdf_path = pdf_overrides.get(
            case.case_id,
            pdf_root / DEFAULT_PDF_NAMES.get(case.case_id, f"{case.case_id}.pdf"),
        )
        if not pdf_path.exists():
            results.append(
                EvaluationResult(
                    case_id=case.case_id,
                    paper=case.paper,
                    question=case.question,
                    status="skipped",
                    pdf_path=str(pdf_path),
                    answer="PDF not found; provide it with --pdf-root or --pdf case_id=path.",
                    citations="",
                    top_pages=[],
                    expected_terms=list(case.expected_terms),
                    term_hits={term: False for term in case.expected_terms},
                    notes="Missing local PDF.",
                )
            )
            continue

        try:
            service = PaperRAGService(settings)
            service.build_from_pdf(pdf_path)
            qa_result = service.answer(case.question)
            combined = f"{qa_result.answer}\n{qa_result.citations_markdown}"
            results.append(
                EvaluationResult(
                    case_id=case.case_id,
                    paper=case.paper,
                    question=case.question,
                    status="passed",
                    pdf_path=str(pdf_path),
                    answer=qa_result.answer,
                    citations=qa_result.citations_markdown,
                    top_pages=[
                        page
                        for item in qa_result.retrieved_chunks[:4]
                        for page in item.chunk.page_numbers
                    ],
                    expected_terms=list(case.expected_terms),
                    term_hits={
                        term: term.lower() in combined.lower()
                        for term in case.expected_terms
                    },
                )
            )
        except Exception as exc:
            results.append(
                EvaluationResult(
                    case_id=case.case_id,
                    paper=case.paper,
                    question=case.question,
                    status="failed",
                    pdf_path=str(pdf_path),
                    answer="",
                    citations="",
                    top_pages=[],
                    expected_terms=list(case.expected_terms),
                    term_hits={term: False for term in case.expected_terms},
                    notes=f"{type(exc).__name__}: {exc}",
                )
            )
    return results


def save_results(
    results: list[EvaluationResult],
    output_dir: Path,
) -> tuple[Path, Path]:
    """Save benchmark results as JSON and Markdown."""
    json_path = unique_output_path(output_dir, "evaluation-benchmark-results", ".json")
    markdown_path = unique_output_path(output_dir, "evaluation-benchmark-results", ".md")
    json_path.write_text(
        json.dumps([asdict(result) for result in results], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    markdown_path.write_text(render_results_markdown(results), encoding="utf-8")
    return json_path, markdown_path


def render_results_markdown(results: list[EvaluationResult]) -> str:
    """Render benchmark results as a compact Markdown report."""
    lines = [
        "# ResearchFlow-Agent Evaluation Benchmark Results",
        "",
        "# ResearchFlow-Agent 评测 Benchmark 结果",
        "",
        "| Case | Status | Top Pages | Expected Term Hits | Notes |",
        "| --- | --- | --- | --- | --- |",
    ]
    for result in results:
        hit_text = ", ".join(
            f"{term}: {'yes' if hit else 'no'}"
            for term, hit in result.term_hits.items()
        )
        page_text = ", ".join(map(str, result.top_pages)) or "-"
        lines.append(
            "| "
            f"{_escape(result.case_id)} | "
            f"{_escape(result.status)} | "
            f"{_escape(page_text)} | "
            f"{_escape(hit_text or '-')} | "
            f"{_escape(result.notes or '-')} |"
        )

    for result in results:
        lines.extend(
            [
                "",
                f"## {result.case_id}",
                "",
                f"- Paper: {result.paper}",
                f"- PDF: `{result.pdf_path}`",
                f"- Question: {result.question}",
                f"- Status: {result.status}",
                "",
                "### Answer / 回答",
                result.answer.strip() or "No answer.",
                "",
                "### Citations / 引用",
                result.citations.strip() or "No citations.",
            ]
        )
    return "\n".join(lines)


def parse_pdf_overrides(values: list[str]) -> dict[str, Path]:
    """Parse --pdf case_id=path overrides."""
    overrides = {}
    for value in values:
        if "=" not in value:
            raise ValueError("--pdf values must use case_id=path format.")
        case_id, path = value.split("=", 1)
        overrides[case_id.strip()] = Path(path).expanduser()
    return overrides


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--benchmark",
        type=Path,
        default=PROJECT_ROOT / "examples" / "evaluation_benchmark.json",
        help="Path to benchmark JSON.",
    )
    parser.add_argument(
        "--pdf-root",
        type=Path,
        default=PROJECT_ROOT / "data" / "test_inputs",
        help="Directory containing clip.pdf, react.pdf, and rag.pdf.",
    )
    parser.add_argument(
        "--pdf",
        action="append",
        default=[],
        help="Override one case PDF with case_id=path. Can be passed multiple times.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for generated JSON and Markdown results.",
    )
    parser.add_argument(
        "--use-llm",
        action="store_true",
        help="Use the configured OpenAI-compatible LLM. Default disables LLM calls.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the evaluation benchmark CLI."""
    args = build_parser().parse_args(argv)
    settings = get_settings()
    if not args.use_llm:
        settings = replace(settings, openai_api_key="")
    if args.output_dir is not None:
        settings = replace(settings, output_dir=args.output_dir)

    cases = load_cases(args.benchmark)
    results = run_cases(
        cases=cases,
        settings=settings,
        pdf_root=args.pdf_root,
        pdf_overrides=parse_pdf_overrides(args.pdf),
    )
    json_path, markdown_path = save_results(results, settings.output_dir)
    print(f"JSON: {json_path}")
    print(f"Markdown: {markdown_path}")
    return 1 if any(result.status == "failed" for result in results) else 0


def _escape(text: Any) -> str:
    return str(text).replace("|", "\\|").replace("\n", "<br>")


if __name__ == "__main__":
    raise SystemExit(main())
