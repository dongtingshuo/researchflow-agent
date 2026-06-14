"""Manual experiment evaluation tables for comparing ResearchFlow modes."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from config import Settings


EVALUATION_MODES = [
    "普通 RAG 回答",
    "Agent 分步骤回答",
    "Agent + Verifier 回答",
]

EVALUATION_METRICS = [
    "答案完整性",
    "引用正确性",
    "复现计划可执行性",
    "是否存在无依据结论",
    "人工评分备注",
]


@dataclass(frozen=True)
class EvaluationRow:
    """One row in the manual evaluation table."""

    mode: str
    answer: str
    answer_completeness: str = "待人工评分（1-5）"
    citation_correctness: str = "待人工评分（1-5）"
    plan_executability: str = "待人工评分（1-5）"
    unsupported_conclusions: str = "待人工判断（无/少量/较多）"
    human_notes: str = ""


@dataclass(frozen=True)
class EvaluationResult:
    """Generated evaluation artifacts."""

    markdown: str
    markdown_path: Path
    csv_path: Path


def generate_evaluation_table(
    settings: Settings,
    question: str,
    reference_answer: str = "",
    human_notes: str = "",
    rag_answer: str = "",
    agent_answer: str = "",
    agent_verifier_answer: str = "",
) -> EvaluationResult:
    """Generate Markdown and CSV manual evaluation tables for three modes."""
    rows = [
        EvaluationRow(
            mode="普通 RAG 回答",
            answer=rag_answer or "未提供。可先在论文问答 Tab 生成普通 RAG 回答。",
            human_notes=human_notes,
        ),
        EvaluationRow(
            mode="Agent 分步骤回答",
            answer=agent_answer or "未提供。可先生成实验计划或运行完整 Agent 工作流。",
            human_notes=human_notes,
        ),
        EvaluationRow(
            mode="Agent + Verifier 回答",
            answer=agent_verifier_answer or "未提供。可先运行完整 Agent 工作流并复制 Verifier 输出。",
            human_notes=human_notes,
        ),
    ]
    markdown = render_evaluation_markdown(
        question=question,
        reference_answer=reference_answer,
        rows=rows,
        human_notes=human_notes,
    )
    markdown_path, csv_path = save_evaluation_artifacts(settings.output_dir, markdown, rows)
    return EvaluationResult(markdown=markdown, markdown_path=markdown_path, csv_path=csv_path)


def render_evaluation_markdown(
    question: str,
    reference_answer: str,
    rows: list[EvaluationRow],
    human_notes: str = "",
) -> str:
    """Render a reproducible Markdown evaluation sheet."""
    lines = [
        "# ResearchFlow-Agent 实验评测表",
        "",
        "## 评测目标",
        "比较三种回答模式在科研论文阅读与实验复现任务中的表现。",
        "",
        "## 评测问题",
        question.strip() or "未填写",
        "",
        "## 标准答案或参考依据",
        reference_answer.strip() or "未填写。可填写论文原文、人工标准答案或教师备注。",
        "",
        "## 评分说明",
        "- 答案完整性：1 表示严重缺失，5 表示覆盖关键点。",
        "- 引用正确性：1 表示引用缺失或错误，5 表示页码/证据准确。",
        "- 复现计划可执行性：1 表示不可执行，5 表示步骤清楚且可直接尝试。",
        "- 是否存在无依据结论：填写无、少量、较多，并在备注中说明。",
        "- 人工评分备注：记录人工判断理由，不要求自动评分完全替代人工判断。",
        "",
        "## 三种模式对比表",
        "",
        "| 模式 | 答案摘要 | 答案完整性 | 引用正确性 | 复现计划可执行性 | 是否存在无依据结论 | 人工评分备注 |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            f"{_escape(row.mode)} | "
            f"{_escape(_shorten(row.answer, 180))} | "
            f"{_escape(row.answer_completeness)} | "
            f"{_escape(row.citation_correctness)} | "
            f"{_escape(row.plan_executability)} | "
            f"{_escape(row.unsupported_conclusions)} | "
            f"{_escape(row.human_notes or '待填写')} |"
        )

    lines.extend(
        [
            "",
            "## 原始回答记录",
        ]
    )
    for row in rows:
        lines.extend(["", f"### {row.mode}", row.answer.strip() or "未提供"])

    lines.extend(
        [
            "",
            "## 人工备注",
            human_notes.strip() or "未填写",
            "",
            "## 建议实验写法",
            "- 至少选择 3-5 个代表性问题重复评测。",
            "- 对每个问题保留三种模式的原始输出，避免只记录主观分数。",
            "- 评分时优先检查引用页码、代码文件路径、训练命令和 Verifier 风险提示。",
            "- 报告中说明评测表为人工辅助评分，不声称自动评测绝对客观。",
        ]
    )
    return "\n".join(lines)


def save_evaluation_artifacts(
    output_dir: Path,
    markdown: str,
    rows: list[EvaluationRow],
) -> tuple[Path, Path]:
    """Save Markdown and CSV evaluation artifacts."""
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    markdown_path = output_dir / f"evaluation-{timestamp}.md"
    csv_path = output_dir / f"evaluation-{timestamp}.csv"
    markdown_path.write_text(markdown, encoding="utf-8")

    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "mode",
                "answer",
                "answer_completeness",
                "citation_correctness",
                "plan_executability",
                "unsupported_conclusions",
                "human_notes",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "mode": row.mode,
                    "answer": row.answer,
                    "answer_completeness": row.answer_completeness,
                    "citation_correctness": row.citation_correctness,
                    "plan_executability": row.plan_executability,
                    "unsupported_conclusions": row.unsupported_conclusions,
                    "human_notes": row.human_notes,
                }
            )
    return markdown_path, csv_path


def _shorten(text: str, limit: int) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3].rstrip() + "..."


def _escape(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", "<br>")
