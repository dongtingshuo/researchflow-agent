"""Lightweight verifier for generated plans and reports."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.code_analyzer.models import CodeAnalysisResult


@dataclass(frozen=True)
class VerificationIssue:
    """One verification warning or failure."""

    level: str
    message: str


@dataclass(frozen=True)
class VerificationResult:
    """Verifier output for workflow artifacts."""

    passed: bool
    issues: list[VerificationIssue] = field(default_factory=list)

    def to_markdown(self) -> str:
        """Render verifier results as Markdown."""
        status = "PASS" if self.passed else "WARN"
        lines = [f"# Verifier Result: {status}", ""]
        if not self.issues:
            lines.append("- 未发现明显结构问题。")
            return "\n".join(lines)
        for issue in self.issues:
            lines.append(f"- **{issue.level}**: {issue.message}")
        return "\n".join(lines)


def verify_workflow_outputs(
    paper_summary: str,
    code_analysis: CodeAnalysisResult | None,
    experiment_plan: str,
    project_report: str,
) -> VerificationResult:
    """Check whether generated artifacts contain required evidence and sections."""
    issues: list[VerificationIssue] = []

    if not paper_summary.strip():
        issues.append(VerificationIssue("WARN", "论文结构化摘要为空。"))
    if code_analysis is None:
        issues.append(VerificationIssue("WARN", "缺少代码分析结果。"))
    elif not code_analysis.key_files:
        issues.append(VerificationIssue("WARN", "代码分析未识别到关键文件。"))

    for section in _PLAN_SECTIONS:
        if f"## {section}" not in experiment_plan:
            issues.append(VerificationIssue("WARN", f"实验计划缺少章节：{section}。"))

    for section in _REPORT_SECTIONS:
        if f"## {section}" not in project_report:
            issues.append(VerificationIssue("WARN", f"项目报告缺少章节：{section}。"))

    if "TBD" in project_report or "待填写" in project_report:
        issues.append(
            VerificationIssue(
                "INFO",
                "项目报告仍包含待填写结果，适合真实实验完成后继续补充。",
            )
        )

    blocking = any(issue.level == "ERROR" for issue in issues)
    return VerificationResult(passed=not blocking, issues=issues)


_PLAN_SECTIONS = [
    "实验目标",
    "环境配置",
    "依赖安装",
    "数据集准备",
    "训练步骤",
    "测试步骤",
    "指标记录方式",
    "实验结果表格模板",
    "可能遇到的问题",
    "降低复现难度的简化方案",
]

_REPORT_SECTIONS = [
    "项目背景",
    "相关工作",
    "方法原理",
    "系统设计",
    "实验环境",
    "实验步骤",
    "实验结果记录表",
    "结果分析",
    "总结与展望",
]
