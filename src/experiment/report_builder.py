"""Markdown reproduction report builder."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from config import OUTPUT_DIR
from src.code_analyzer.models import CodeAnalysisResult
from src.experiment.command_planner import CommandPlan
from src.experiment.log_parser import LogParseResult
from src.experiment.result_comparator import ResultComparison
from src.experiment.runner import CommandRunResult


@dataclass(frozen=True)
class ReproductionReport:
    """Generated reproduction report."""

    markdown: str
    output_path: Path


def build_reproduction_report(
    paper_info: str,
    code_analysis: CodeAnalysisResult | None,
    command_plan: CommandPlan | None,
    run_results: list[CommandRunResult],
    log_summary: LogParseResult | None,
    comparison: ResultComparison | None,
    verifier_markdown: str,
    output_dir: str | Path | None = None,
    user_notes: str = "",
) -> ReproductionReport:
    """Build and save a Markdown reproduction report."""
    target_dir = Path(output_dir) if output_dir is not None else OUTPUT_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    output_path = target_dir / "reproduction_report.md"
    markdown = "\n".join(
        [
            "# Reproduction Experiment Report",
            "",
            "## 论文信息",
            paper_info.strip() or "未提供论文信息。",
            "",
            "## 代码仓库信息",
            _code_info(code_analysis),
            "",
            "## 环境配置",
            _environment_section(command_plan),
            "",
            "## 候选复现命令",
            command_plan.to_markdown() if command_plan is not None else "未生成候选命令。",
            "",
            "## 实际执行命令",
            _run_results_section(run_results),
            "",
            "## 运行日志摘要",
            log_summary.to_markdown() if log_summary is not None else "未解析运行日志。",
            "",
            "## 指标提取结果",
            _metrics_section(log_summary),
            "",
            "## 与论文结果对比",
            comparison.to_markdown() if comparison is not None else "未执行指标对比。",
            "",
            "## 失败原因分析",
            _failure_analysis(run_results, comparison),
            "",
            "## Verifier 证据标注",
            verifier_markdown.strip() or "Verifier 未返回结果。",
            "",
            "## 后续改进建议",
            _suggestions(command_plan, log_summary, comparison),
            "",
            "## 用户补充说明",
            user_notes.strip() or "无。",
            "",
            f"_Generated at {datetime.now().isoformat(timespec='seconds')}._",
        ]
    )
    output_path.write_text(markdown, encoding="utf-8")
    return ReproductionReport(markdown=markdown, output_path=output_path)


def _code_info(code_analysis: CodeAnalysisResult | None) -> str:
    if code_analysis is None:
        return "未提供代码仓库分析结果。"
    return "\n".join(
        [
            f"- Source type: `{code_analysis.source_type}`",
            f"- Source: `{code_analysis.source}`",
            f"- Workspace: `{code_analysis.workspace_path}`",
            f"- Key files: {len(code_analysis.key_files)}",
        ]
    )


def _environment_section(command_plan: CommandPlan | None) -> str:
    if command_plan is None:
        return "未识别环境配置。"
    env_files = [
        item.path
        for item in command_plan.config_files
        if item.kind in {"pip_requirements", "conda_environment", "python_project"}
    ]
    if not env_files:
        return "未识别 requirements.txt、pyproject.toml 或 environment.yml。"
    return "\n".join(f"- `{path}`" for path in env_files)


def _run_results_section(run_results: list[CommandRunResult]) -> str:
    if not run_results:
        return "没有实际执行命令；当前可能处于 dry-run 模式。"
    lines = [
        "| Command | Executed | Risk | Return Code | Duration | Output JSON |",
        "| --- | --- | --- | ---: | ---: | --- |",
    ]
    for item in run_results:
        returncode = "" if item.returncode is None else str(item.returncode)
        lines.append(
            f"| `{item.command}` | {item.executed} | `{item.risk_level}` | "
            f"{returncode} | {item.duration_seconds:g}s | `{item.output_path}` |"
        )
    return "\n".join(lines)


def _metrics_section(log_summary: LogParseResult | None) -> str:
    if log_summary is None or not log_summary.metrics:
        return "未从日志中提取到指标。"
    return "\n".join(f"- `{name}`: {value}" for name, value in log_summary.metrics.items())


def _failure_analysis(
    run_results: list[CommandRunResult],
    comparison: ResultComparison | None,
) -> str:
    reasons: list[str] = []
    if not run_results:
        reasons.append("未执行真实命令，无法判断训练或评估是否成功。")
    for result in run_results:
        if result.error:
            reasons.append(f"`{result.command}`: {result.error}")
        elif result.returncode not in {0, None}:
            reasons.append(f"`{result.command}` returned non-zero code {result.returncode}.")
    if comparison is not None:
        for item in comparison.comparisons:
            if item.status != "reproduced":
                reasons.append(f"`{item.name}`: {item.reason}")
    if not reasons:
        reasons.append("未发现明确失败原因；仍需人工核对日志和指标。")
    return "\n".join(f"- {reason}" for reason in reasons)


def _suggestions(
    command_plan: CommandPlan | None,
    log_summary: LogParseResult | None,
    comparison: ResultComparison | None,
) -> str:
    suggestions = [
        "在执行训练前确认数据集路径、checkpoint 路径、硬件资源和预计运行时间。",
        "优先执行低成本的 help、demo 或小样本评估命令，再扩展到完整训练。",
    ]
    if command_plan is None or not command_plan.commands:
        suggestions.append("补充 README 或脚本入口信息，以便生成更准确的复现命令。")
    if log_summary is None or not log_summary.metrics:
        suggestions.append("保存训练或评估日志，并确认日志中包含标准指标名称。")
    if comparison is None or comparison.status != "reproduced":
        suggestions.append("对论文表格、日志指标和数据集划分进行人工逐项核对。")
    return "\n".join(f"- {item}" for item in suggestions)
