"""Run the local toy reproduction demo.

The demo is local-only:
- no network access
- no LLM calls
- no large datasets
- dry-run by default
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import OUTPUT_DIR  # noqa: E402
from src.code_analyzer.analyzer import analyze_codebase  # noqa: E402
from src.evaluation.verifier import verify_reproduction_artifacts  # noqa: E402
from src.experiment.command_planner import CommandCandidate, plan_reproduction_commands  # noqa: E402
from src.experiment.log_parser import LogParseResult, parse_experiment_log  # noqa: E402
from src.experiment.report_builder import build_reproduction_report  # noqa: E402
from src.experiment.result_comparator import ResultComparison, compare_results  # noqa: E402
from src.experiment.runner import CommandRunResult, run_command_candidate  # noqa: E402
from src.paper.models import TextChunk  # noqa: E402
from src.paper.results import PaperResultSummary, extract_paper_results  # noqa: E402


DEMO_DIR = PROJECT_ROOT / "examples" / "reproduction_demo"
DEFAULT_OUTPUT_DIR = OUTPUT_DIR / "reproduction_demo"


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-safe",
        action="store_true",
        help="Execute safe demo commands. Default mode is dry-run only.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Timeout in seconds for each safe command.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for generated demo artifacts.",
    )
    return parser


def run_demo(
    run_safe: bool = False,
    timeout_seconds: int = 30,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Path]:
    """Run the toy reproduction demo and return output paths."""
    output_dir.mkdir(parents=True, exist_ok=True)
    paper_excerpt = DEMO_DIR / "sample_paper_excerpt.md"
    toy_repo = DEMO_DIR / "toy_repo"

    paper_results = _extract_demo_paper_results(paper_excerpt)
    code_analysis = analyze_codebase(
        toy_repo,
        source_type="local",
        source="examples/reproduction_demo/toy_repo",
        settings=_offline_settings(output_dir),
    )
    command_plan = plan_reproduction_commands(code_analysis)
    selected_commands = _select_demo_commands(command_plan.commands)
    run_results = [
        run_command_candidate(
            command,
            cwd=toy_repo,
            output_dir=output_dir,
            timeout_seconds=timeout_seconds,
            dry_run=not run_safe,
        )
        for command in selected_commands
    ]
    log_summary = parse_experiment_log("\n".join(item.combined_log() for item in run_results))
    comparison = compare_results(paper_results.metrics_dict(), log_summary.metrics)
    verification = verify_reproduction_artifacts(
        paper_results=paper_results,
        code_analysis=code_analysis,
        command_plan=command_plan,
        run_results=run_results,
        log_summary=log_summary,
        comparison=comparison,
    )
    report = build_reproduction_report(
        paper_info=paper_results.to_markdown(),
        code_analysis=code_analysis,
        command_plan=command_plan,
        run_results=run_results,
        log_summary=log_summary,
        comparison=comparison,
        verifier_markdown=verification.to_markdown(),
        output_dir=output_dir,
        user_notes="Toy demo. No external data, model download, or API call is required.",
    )

    paths = {
        "parsed_paper_results": output_dir / "parsed_paper_results.json",
        "planned_commands": output_dir / "planned_commands.json",
        "run_result": output_dir / "run_result.json",
        "parsed_metrics": output_dir / "parsed_metrics.json",
        "comparison_result": output_dir / "comparison_result.json",
        "verifier_result": output_dir / "verifier_result.json",
        "reproduction_report": report.output_path,
    }
    _write_json(paths["parsed_paper_results"], _paper_results_payload(paper_results))
    _write_json(paths["planned_commands"], _command_plan_payload(command_plan.commands))
    _write_json(paths["run_result"], _run_results_payload(run_results))
    _write_json(paths["parsed_metrics"], _log_summary_payload(log_summary))
    _write_json(paths["comparison_result"], _comparison_payload(comparison))
    _write_json(paths["verifier_result"], _verification_payload(verification))
    return paths


def main(argv: list[str] | None = None) -> int:
    """Run the demo from the command line."""
    args = build_parser().parse_args(argv)
    paths = run_demo(
        run_safe=args.run_safe,
        timeout_seconds=args.timeout,
        output_dir=args.output_dir,
    )
    print(f"Report: {paths['reproduction_report']}")
    print(f"Output directory: {args.output_dir}")
    return 0


def _extract_demo_paper_results(path: Path) -> PaperResultSummary:
    text = path.read_text(encoding="utf-8")
    chunk = TextChunk(
        chunk_id="toy-paper-excerpt",
        text=text,
        page_numbers=[1],
    )
    return extract_paper_results([chunk])


def _select_demo_commands(commands: list[CommandCandidate]) -> list[CommandCandidate]:
    selected = [
        command
        for command in commands
        if command.risk_level == "safe"
        and command.entry_file.endswith("evaluate.py")
        and "--dry-run" in command.command
    ]
    return selected or [
        command
        for command in commands
        if command.risk_level == "safe" and command.entry_file.endswith("evaluate.py")
    ][:1]


def _offline_settings(output_dir: Path):
    from config import Settings

    return Settings(
        openai_api_key="",
        enable_cross_encoder_reranker=False,
        output_dir=output_dir,
        workspace_dir=output_dir / "workspaces",
        upload_dir=output_dir / "uploads",
        vectorstore_dir=output_dir / "vectorstores",
    )


def _paper_results_payload(result: PaperResultSummary) -> dict[str, Any]:
    return {
        "task": result.task,
        "datasets": result.datasets,
        "metrics": [asdict(item) for item in result.metrics],
        "evidence_pages": result.evidence_pages,
        "status": result.status,
        "notes": result.notes,
    }


def _command_plan_payload(commands: list[CommandCandidate]) -> dict[str, Any]:
    return {"commands": [asdict(item) for item in commands]}


def _run_results_payload(results: list[CommandRunResult]) -> dict[str, Any]:
    payload = []
    for item in results:
        data = asdict(item)
        data["output_path"] = str(item.output_path)
        payload.append(data)
    return {"run_results": payload}


def _log_summary_payload(result: LogParseResult) -> dict[str, Any]:
    return {
        "metrics": result.metrics,
        "raw_matches": [asdict(item) for item in result.raw_matches],
        "summary": result.summary,
    }


def _comparison_payload(result: ResultComparison) -> dict[str, Any]:
    return {
        "status": result.status,
        "comparisons": [asdict(item) for item in result.comparisons],
        "notes": result.notes,
    }


def _verification_payload(result) -> dict[str, Any]:
    return {
        "passed": result.passed,
        "checks": [asdict(item) for item in result.checks],
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
