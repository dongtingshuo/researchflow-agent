"""Evidence and uncertainty verifier for generated workflow artifacts."""

from __future__ import annotations

from dataclasses import dataclass, field
import re

from src.code_analyzer.models import CodeAnalysisResult


@dataclass(frozen=True)
class EvidenceItem:
    """One verifier item with an optional source label."""

    content: str
    source: str = ""


@dataclass(frozen=True)
class VerificationIssue:
    """One verification warning or failure."""

    level: str
    message: str


@dataclass(frozen=True)
class VerificationResult:
    """Verifier output for workflow artifacts.

    The verifier is intentionally conservative: it does not certify that the
    generated content is fully correct. It separates observed evidence from
    model inference and highlights content that still needs human review.
    """

    passed: bool
    paper_evidence: list[EvidenceItem] = field(default_factory=list)
    code_evidence: list[EvidenceItem] = field(default_factory=list)
    model_inferences: list[EvidenceItem] = field(default_factory=list)
    missing_evidence: list[EvidenceItem] = field(default_factory=list)
    human_review_needed: list[EvidenceItem] = field(default_factory=list)
    possible_hallucinations: list[EvidenceItem] = field(default_factory=list)
    improvement_suggestions: list[str] = field(default_factory=list)
    issues: list[VerificationIssue] = field(default_factory=list)

    def to_markdown(self) -> str:
        """Render verifier results as Markdown."""
        status = "PASS_WITH_UNCERTAINTY" if self.passed else "NEEDS_REVIEW"
        lines = [
            f"# Verifier Result: {status}",
            "",
            "> 说明：Verifier 只能做证据归因和风险提示，不能保证生成内容 100% 正确。"
            "最终结论、实验指标和复现可行性仍需要人工核对。",
            "",
        ]
        lines.extend(_section("1. 来自论文的内容", self.paper_evidence))
        lines.extend(_section("2. 来自代码仓库的内容", self.code_evidence))
        lines.extend(_section("3. 模型推断的内容", self.model_inferences))
        lines.extend(_section("4. 缺少证据的内容", self.missing_evidence))
        lines.extend(_section("5. 需要人工确认的内容", self.human_review_needed))
        lines.extend(_section("6. 可能存在幻觉的内容", self.possible_hallucinations))
        lines.extend(["## 7. 改进建议"])
        if self.improvement_suggestions:
            lines.extend(f"- {item}" for item in self.improvement_suggestions)
        else:
            lines.append("- 暂无额外建议。")
        if self.issues:
            lines.extend(["", "## 结构检查与提示"])
            lines.extend(f"- **{issue.level}**: {issue.message}" for issue in self.issues)
        return "\n".join(lines)


def verify_workflow_outputs(
    paper_summary: str,
    code_analysis: CodeAnalysisResult | None,
    experiment_plan: str,
    project_report: str,
) -> VerificationResult:
    """Check generated artifacts for evidence grounding and uncertainty.

    This function does not assert factual correctness. It classifies content by
    source, flags weakly supported statements, and lists items that require
    manual confirmation before a project report is treated as final.
    """
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

    paper_evidence = _extract_paper_evidence(paper_summary)
    code_evidence = _extract_code_evidence(code_analysis)
    generated_text = "\n".join([experiment_plan, project_report])
    model_inferences = _extract_model_inferences(generated_text)
    missing_evidence = _extract_missing_evidence(generated_text, paper_evidence, code_evidence)
    human_review_needed = _extract_human_review_items(
        generated_text,
        code_analysis,
        missing_evidence,
    )
    possible_hallucinations = _extract_possible_hallucinations(
        generated_text,
        paper_summary,
        code_analysis,
    )
    improvement_suggestions = _build_improvement_suggestions(
        paper_evidence,
        code_evidence,
        missing_evidence,
        human_review_needed,
        possible_hallucinations,
    )

    blocking = any(issue.level == "ERROR" for issue in issues)
    return VerificationResult(
        passed=not blocking,
        paper_evidence=paper_evidence,
        code_evidence=code_evidence,
        model_inferences=model_inferences,
        missing_evidence=missing_evidence,
        human_review_needed=human_review_needed,
        possible_hallucinations=possible_hallucinations,
        improvement_suggestions=improvement_suggestions,
        issues=issues,
    )


def _extract_paper_evidence(paper_summary: str) -> list[EvidenceItem]:
    items: list[EvidenceItem] = []
    for line in _meaningful_lines(paper_summary):
        if "Page " in line or line.startswith("##") or "论文" in line or "研究" in line:
            items.append(EvidenceItem(content=line, source="paper_summary"))
        if len(items) >= 8:
            break
    if not items and paper_summary.strip():
        items.append(EvidenceItem(content=_shorten(paper_summary), source="paper_summary"))
    return items


def _extract_code_evidence(code_analysis: CodeAnalysisResult | None) -> list[EvidenceItem]:
    if code_analysis is None:
        return []
    items = [
        EvidenceItem(
            content=f"{item.role}: {item.path} ({item.reason})",
            source="code_key_file",
        )
        for item in code_analysis.key_files[:12]
    ]
    for line in _meaningful_lines(code_analysis.summary):
        if line.startswith("##") or "`" in line:
            items.append(EvidenceItem(content=line, source="code_summary"))
        if len(items) >= 14:
            break
    return items


def _extract_model_inferences(generated_text: str) -> list[EvidenceItem]:
    inference_markers = [
        "建议",
        "推荐",
        "优先",
        "可以",
        "应",
        "需要",
        "适合",
        "目标是",
    ]
    items = []
    for line in _meaningful_lines(generated_text):
        if any(marker in line for marker in inference_markers):
            items.append(EvidenceItem(content=line, source="generated_plan_or_report"))
        if len(items) >= 12:
            break
    return items


def _extract_missing_evidence(
    generated_text: str,
    paper_evidence: list[EvidenceItem],
    code_evidence: list[EvidenceItem],
) -> list[EvidenceItem]:
    items = []
    weak_markers = [
        "未识别",
        "未提供",
        "未发现",
        "未自动",
        "TBD",
        "待填写",
        "需要人工",
        "需要从",
        "尚未",
    ]
    for line in _meaningful_lines(generated_text):
        if any(marker in line for marker in weak_markers):
            items.append(EvidenceItem(content=line, source="generated_plan_or_report"))
        if len(items) >= 12:
            break
    if not paper_evidence:
        items.append(EvidenceItem(content="未找到可引用的论文证据片段。", source="paper_summary"))
    if not code_evidence:
        items.append(EvidenceItem(content="未找到可引用的代码仓库证据。", source="code_analysis"))
    return items


def _extract_human_review_items(
    generated_text: str,
    code_analysis: CodeAnalysisResult | None,
    missing_evidence: list[EvidenceItem],
) -> list[EvidenceItem]:
    items = list(missing_evidence[:6])
    review_keywords = [
        "数据集",
        "指标",
        "权重",
        "环境",
        "依赖",
        "命令",
        "训练",
        "测试",
    ]
    for line in _meaningful_lines(generated_text):
        if any(keyword in line for keyword in review_keywords):
            items.append(EvidenceItem(content=line, source="generated_plan_or_report"))
        if len(items) >= 12:
            break
    if code_analysis is not None and not _has_role(code_analysis, "train.py"):
        items.append(EvidenceItem(content="未识别到训练入口，需要人工确认训练命令。", source="code_analysis"))
    if code_analysis is not None and not _has_role(code_analysis, "dataset.py"):
        items.append(EvidenceItem(content="未识别到数据集加载文件，需要人工确认数据格式。", source="code_analysis"))
    return _dedupe_items(items)[:14]


def _extract_possible_hallucinations(
    generated_text: str,
    paper_summary: str,
    code_analysis: CodeAnalysisResult | None,
) -> list[EvidenceItem]:
    items = []
    absolute_markers = [
        "完全",
        "一定",
        "必然",
        "100%",
        "最佳",
        "显著优于",
        "达到",
        "证明",
    ]
    metric_pattern = re.compile(r"\b\d+(?:\.\d+)?\s?(?:%|accuracy|acc|f1|map|bleu)\b", re.IGNORECASE)
    evidence_text = "\n".join([paper_summary, _code_text(code_analysis)])
    for line in _meaningful_lines(generated_text):
        if any(marker in line for marker in absolute_markers):
            items.append(EvidenceItem(content=line, source="absolute_or_overconfident_claim"))
        elif metric_pattern.search(line) and line not in evidence_text:
            items.append(EvidenceItem(content=line, source="metric_without_visible_evidence"))
        if len(items) >= 10:
            break
    if not items:
        items.append(
            EvidenceItem(
                content="未检测到明显绝对化或无证据指标声明，但仍需人工核对关键事实。",
                source="verifier_note",
            )
        )
    return items


def _build_improvement_suggestions(
    paper_evidence: list[EvidenceItem],
    code_evidence: list[EvidenceItem],
    missing_evidence: list[EvidenceItem],
    human_review_needed: list[EvidenceItem],
    possible_hallucinations: list[EvidenceItem],
) -> list[str]:
    suggestions = [
        "为每个实验结论补充论文页码、代码文件路径或运行日志证据。",
        "不要把模板中的 TBD、待填写、未识别内容作为最终结果提交。",
        "对训练命令、数据集路径、指标名称和模型权重来源进行人工确认。",
    ]
    if not paper_evidence:
        suggestions.append("重新解析 PDF 或使用论文问答补充研究问题、方法和实验设置证据。")
    if not code_evidence:
        suggestions.append("重新分析仓库，确认 README、依赖文件、训练入口和推理入口是否存在。")
    if missing_evidence:
        suggestions.append("把缺少证据的句子改写为待确认事项，或补充可追溯来源。")
    if human_review_needed:
        suggestions.append("将需要人工确认的内容整理成复现实验 checklist。")
    if possible_hallucinations:
        suggestions.append("删除或弱化绝对化表述，避免宣称未实际验证的性能和结论。")
    return suggestions


def _section(title: str, items: list[EvidenceItem]) -> list[str]:
    lines = [f"## {title}"]
    if not items:
        lines.append("- 暂无明确条目。")
        lines.append("")
        return lines
    for item in _dedupe_items(items):
        suffix = f" 来源：`{item.source}`" if item.source else ""
        lines.append(f"- {item.content}{suffix}")
    lines.append("")
    return lines


def _meaningful_lines(text: str) -> list[str]:
    lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or set(line) <= {"-", "|", " "}:
            continue
        lines.append(_shorten(line))
    return lines


def _shorten(text: str, limit: int = 220) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3].rstrip() + "..."


def _dedupe_items(items: list[EvidenceItem]) -> list[EvidenceItem]:
    seen = set()
    output = []
    for item in items:
        key = (item.content, item.source)
        if key in seen:
            continue
        seen.add(key)
        output.append(item)
    return output


def _has_role(code_analysis: CodeAnalysisResult, role: str) -> bool:
    return any(item.role == role for item in code_analysis.key_files)


def _code_text(code_analysis: CodeAnalysisResult | None) -> str:
    if code_analysis is None:
        return ""
    key_file_text = "\n".join(item.path for item in code_analysis.key_files)
    return "\n".join([code_analysis.summary, code_analysis.directory_tree, key_file_text])


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
