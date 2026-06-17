"""Manual experiment evaluation tables for comparing ResearchFlow modes."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

from config import Settings
from src.utils.files import unique_output_path


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
class BenchmarkCase:
    """One repeatable evaluation case for system validation."""

    case_id: str
    paper: str
    question: str
    reference_answer: str
    expected_pages: str = ""
    expected_terms: list[str] = field(default_factory=list)
    repository_url: str = ""
    evaluation_focus: str = ""


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


DEFAULT_BENCHMARK_CASES = [
    BenchmarkCase(
        case_id="clip-data-scale",
        paper="CLIP: Learning Transferable Visual Models From Natural Language Supervision",
        question="How many image-text pairs were used to train CLIP?",
        reference_answer=(
            "The CLIP paper states that it creates a dataset of 400 million "
            "(image, text) pairs for training."
        ),
        expected_pages="Page 2 in the local CLIP PDF used by the benchmark",
        expected_terms=["400 million", "image", "text", "pairs", "CLIP"],
        repository_url="https://github.com/openai/CLIP",
        evaluation_focus="Quantity answer, page citation, and direct evidence snippet.",
    ),
    BenchmarkCase(
        case_id="react-benchmarks",
        paper="ReAct: Synergizing Reasoning and Acting in Language Models",
        question="Which tasks or benchmarks are used in ReAct?",
        reference_answer=(
            "The ReAct paper evaluates on HotPotQA, Fever, ALFWorld, and WebShop."
        ),
        expected_pages="Pages 1 and 3 in the local ReAct PDF used by the benchmark",
        expected_terms=["HotPotQA", "Fever", "ALFWorld", "WebShop"],
        repository_url="https://github.com/ysymyth/ReAct",
        evaluation_focus="Named benchmark preservation and no unsupported extra tasks.",
    ),
    BenchmarkCase(
        case_id="rag-formulations",
        paper="Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
        question="What are the two RAG formulations?",
        reference_answer=(
            "The two formulations are RAG-Sequence, which uses the same retrieved "
            "document for a generated sequence, and RAG-Token, which can use "
            "different documents per target token."
        ),
        expected_pages="Pages 1 and 3 in the local RAG PDF used by the benchmark",
        expected_terms=["RAG-Sequence", "RAG-Token", "same document", "different document"],
        repository_url="https://github.com/facebookresearch/DPR",
        evaluation_focus="Method-name preservation and formulation distinction.",
    ),
]


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


def generate_benchmark_template(
    settings: Settings,
    cases: list[BenchmarkCase] | None = None,
) -> EvaluationResult:
    """Generate a repeatable benchmark sheet for multiple evaluation questions."""
    active_cases = cases or DEFAULT_BENCHMARK_CASES
    markdown = render_benchmark_markdown(active_cases)
    markdown_path, csv_path = save_benchmark_artifacts(settings.output_dir, markdown, active_cases)
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


def render_benchmark_markdown(cases: list[BenchmarkCase]) -> str:
    """Render a multi-case benchmark protocol for repeatable experiments."""
    lines = [
        "# ResearchFlow-Agent Evaluation Benchmark",
        "",
        "# ResearchFlow-Agent 评测 Benchmark",
        "",
        "## 目的 / Purpose",
        "用固定论文问题比较普通 RAG、Agent 分步骤、Agent + Verifier 三种模式，记录答案、引用页码、证据片段和人工分数。",
        "",
        "Use fixed paper questions to compare ordinary RAG, step-by-step Agent, and Agent + Verifier outputs.",
        "",
        "## 评分规则 / Scoring",
        "- 答案完整性：1-5 分，是否覆盖标准答案关键点。",
        "- 引用正确性：1-5 分，页码和引用片段是否直接支持答案。",
        "- 复现计划可执行性：1-5 分，步骤是否可以实际运行或验证。",
        "- 无依据结论：填写无、少量、较多，并说明原因。",
        "",
        "## Benchmark Cases",
        "",
    ]
    for case in cases:
        lines.extend(
            [
                f"### {case.case_id}",
                "",
                f"- Paper: {case.paper}",
                f"- Question: {case.question}",
                f"- Reference answer: {case.reference_answer}",
                f"- Expected pages: {case.expected_pages or 'To be filled during evaluation'}",
                f"- Expected terms: {', '.join(case.expected_terms) or 'To be filled'}",
                f"- Repository: {case.repository_url or 'Not specified'}",
                f"- Focus: {case.evaluation_focus or 'General answer quality'}",
                "",
                "| Mode | Raw answer | Answer completeness | Citation correctness | Plan executability | Unsupported conclusions | Human notes |",
                "| --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for mode in EVALUATION_MODES:
            lines.append(
                f"| {_escape(mode)} | 待填入原始输出 | 待评分（1-5） | 待评分（1-5） | 待评分（1-5） | 待判断 | 待填写 |"
            )
        lines.append("")
    return "\n".join(lines)


def save_evaluation_artifacts(
    output_dir: Path,
    markdown: str,
    rows: list[EvaluationRow],
) -> tuple[Path, Path]:
    """Save Markdown and CSV evaluation artifacts."""
    markdown_path = unique_output_path(output_dir, "evaluation", ".md")
    csv_path = unique_output_path(output_dir, "evaluation", ".csv")
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


def save_benchmark_artifacts(
    output_dir: Path,
    markdown: str,
    cases: list[BenchmarkCase],
) -> tuple[Path, Path]:
    """Save a multi-case benchmark protocol as Markdown and CSV."""
    markdown_path = unique_output_path(output_dir, "benchmark-evaluation", ".md")
    csv_path = unique_output_path(output_dir, "benchmark-evaluation", ".csv")
    markdown_path.write_text(markdown, encoding="utf-8")

    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "case_id",
                "paper",
                "question",
                "reference_answer",
                "expected_pages",
                "expected_terms",
                "repository_url",
                "evaluation_focus",
                "mode",
                "raw_answer",
                "answer_completeness",
                "citation_correctness",
                "plan_executability",
                "unsupported_conclusions",
                "human_notes",
            ],
        )
        writer.writeheader()
        for case in cases:
            for mode in EVALUATION_MODES:
                writer.writerow(
                    {
                        "case_id": case.case_id,
                        "paper": case.paper,
                        "question": case.question,
                        "reference_answer": case.reference_answer,
                        "expected_pages": case.expected_pages,
                        "expected_terms": "; ".join(case.expected_terms),
                        "repository_url": case.repository_url,
                        "evaluation_focus": case.evaluation_focus,
                        "mode": mode,
                        "raw_answer": "",
                        "answer_completeness": "",
                        "citation_correctness": "",
                        "plan_executability": "",
                        "unsupported_conclusions": "",
                        "human_notes": "",
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
