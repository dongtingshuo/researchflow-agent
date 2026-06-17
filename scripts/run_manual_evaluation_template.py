"""Generate manual evaluation templates from paper_eval_questions.json.

This script is local-only by design:
- no LLM calls
- no API key required
- no network access required
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import OUTPUT_DIR  # noqa: E402
from src.utils.files import unique_output_path  # noqa: E402


OUTPUT_FIELDS = [
    "paper_id",
    "paper_title",
    "question_id",
    "question_type",
    "question",
    "ordinary_rag_answer",
    "agent_answer",
    "agent_verifier_answer",
    "answer_completeness_score",
    "citation_correctness",
    "unsupported_claim_count",
    "reproduction_plan_executability_score",
    "human_notes",
]

ALLOWED_QUESTION_TYPES = {"method", "dataset", "metric", "result", "limitation"}


@dataclass(frozen=True)
class ManualEvaluationArtifacts:
    """Generated manual evaluation files."""

    markdown_path: Path
    csv_path: Path
    row_count: int


def load_question_set(path: Path) -> list[dict[str, Any]]:
    """Load and validate the paper evaluation question set."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Question set must be a list.")
    for paper in payload:
        _validate_paper_entry(paper)
    return payload


def build_rows(question_set: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Flatten paper questions into manual evaluation table rows."""
    rows: list[dict[str, str]] = []
    for paper in question_set:
        for question in paper["questions"]:
            rows.append(
                {
                    "paper_id": paper["paper_id"],
                    "paper_title": paper["paper_title"],
                    "question_id": question["question_id"],
                    "question_type": question["question_type"],
                    "question": question["question"],
                    "ordinary_rag_answer": "",
                    "agent_answer": "",
                    "agent_verifier_answer": "",
                    "answer_completeness_score": "",
                    "citation_correctness": "",
                    "unsupported_claim_count": "",
                    "reproduction_plan_executability_score": "",
                    "human_notes": question.get("scoring_note", ""),
                }
            )
    return rows


def generate_manual_evaluation_template(
    question_path: Path,
    output_dir: Path,
) -> ManualEvaluationArtifacts:
    """Generate Markdown and CSV manual evaluation templates."""
    question_set = load_question_set(question_path)
    rows = build_rows(question_set)
    markdown = render_markdown(question_set, rows)

    markdown_path = unique_output_path(output_dir, "manual-evaluation-template", ".md")
    csv_path = unique_output_path(output_dir, "manual-evaluation-template", ".csv")
    markdown_path.write_text(markdown, encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return ManualEvaluationArtifacts(
        markdown_path=markdown_path,
        csv_path=csv_path,
        row_count=len(rows),
    )


def render_markdown(
    question_set: list[dict[str, Any]],
    rows: list[dict[str, str]],
) -> str:
    """Render a Markdown manual evaluation sheet."""
    lines = [
        "# ResearchFlow-Agent Manual Evaluation Template",
        "",
        "## Purpose",
        "This template supports human-reviewable evaluation of paper QA, evidence citation, code analysis, experiment planning, and Verifier uncertainty classification.",
        "",
        "## Instructions",
        "- Fill answers for Ordinary RAG, Agent Workflow, and Agent Workflow + Verifier.",
        "- Score Answer Completeness from 1 to 5.",
        "- Set Citation Correctness to 0/1 or a percentage.",
        "- Count unsupported claims manually.",
        "- Score Reproduction Plan Executability from 1 to 5.",
        "- Add Human Review Notes for missing evidence, uncertainty, or reproduction risks.",
        "",
        "## Question Set Summary",
        "",
        "| paper_id | paper_title | paper_area | optional_repo_url | question_count |",
        "| --- | --- | --- | --- | --- |",
    ]
    for paper in question_set:
        lines.append(
            "| "
            f"{_escape(paper['paper_id'])} | "
            f"{_escape(paper['paper_title'])} | "
            f"{_escape(paper['paper_area'])} | "
            f"{_escape(paper.get('optional_repo_url', ''))} | "
            f"{len(paper['questions'])} |"
        )

    lines.extend(
        [
            "",
            "## Evaluation Rows",
            "",
            "| paper_id | paper_title | question_id | question_type | question | ordinary_rag_answer | agent_answer | agent_verifier_answer | answer_completeness_score | citation_correctness | unsupported_claim_count | reproduction_plan_executability_score | human_notes |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            "| "
            + " | ".join(_escape(row[field]) for field in OUTPUT_FIELDS)
            + " |"
        )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--questions",
        type=Path,
        default=PROJECT_ROOT / "examples" / "paper_eval_questions.json",
        help="Path to paper evaluation question JSON.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help="Directory for generated Markdown and CSV files.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the manual evaluation template generator."""
    args = build_parser().parse_args(argv)
    artifacts = generate_manual_evaluation_template(args.questions, args.output_dir)
    print(f"Markdown: {artifacts.markdown_path}")
    print(f"CSV: {artifacts.csv_path}")
    print(f"Rows: {artifacts.row_count}")
    return 0


def _validate_paper_entry(paper: dict[str, Any]) -> None:
    required_paper_fields = {
        "paper_id",
        "paper_title",
        "paper_area",
        "optional_repo_url",
        "questions",
    }
    missing = required_paper_fields - set(paper)
    if missing:
        raise ValueError(f"Paper entry missing fields: {sorted(missing)}")
    questions = paper["questions"]
    if not isinstance(questions, list) or len(questions) != 5:
        raise ValueError(f"Paper {paper['paper_id']} must contain exactly 5 questions.")
    for question in questions:
        _validate_question_entry(question)


def _validate_question_entry(question: dict[str, Any]) -> None:
    required_question_fields = {
        "question_id",
        "question",
        "question_type",
        "expected_evidence_type",
        "scoring_note",
    }
    missing = required_question_fields - set(question)
    if missing:
        raise ValueError(f"Question entry missing fields: {sorted(missing)}")
    if question["question_type"] not in ALLOWED_QUESTION_TYPES:
        raise ValueError(f"Unsupported question_type: {question['question_type']}")


def _escape(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


if __name__ == "__main__":
    raise SystemExit(main())
