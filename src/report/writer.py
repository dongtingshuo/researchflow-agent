"""Markdown report writer for ResearchFlow-Agent."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from config import Settings
from src.agent.planner import _code_context, _paper_context
from src.code_analyzer.models import CodeAnalysisResult
from src.llm.client import ChatMessage, LLMClientError, OpenAICompatibleClient
from src.rag.qa import PaperRAGService
from src.utils.files import unique_output_path


REPORT_SECTIONS = [
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


@dataclass(frozen=True)
class ReportWriterResult:
    """Generated Markdown report and saved file location."""

    markdown: str
    output_path: Path


def generate_markdown_report(
    settings: Settings,
    paper_service: Optional[PaperRAGService] = None,
    code_analysis: Optional[CodeAnalysisResult] = None,
    experiment_plan: str = "",
    user_notes: str = "",
) -> ReportWriterResult:
    """Generate and save a Markdown project report."""
    paper_context = _paper_context(paper_service)
    code_context = _code_context(code_analysis)

    markdown = _generate_with_llm(
        settings=settings,
        paper_context=paper_context,
        code_context=code_context,
        experiment_plan=experiment_plan,
        user_notes=user_notes,
    )
    if markdown is None:
        markdown = _local_report(
            paper_context=paper_context,
            code_context=code_context,
            experiment_plan=experiment_plan,
            user_notes=user_notes,
        )

    output_path = _save_markdown(settings.output_dir, "project-report", markdown)
    return ReportWriterResult(markdown=markdown, output_path=output_path)


def _generate_with_llm(
    settings: Settings,
    paper_context: str,
    code_context: str,
    experiment_plan: str,
    user_notes: str,
) -> Optional[str]:
    if not settings.llm_enabled:
        return None

    sections = "\n".join(f"{index}. {section}" for index, section in enumerate(REPORT_SECTIONS, 1))
    prompt = (
        "请生成一份专业的 Markdown 技术报告。"
        "报告必须使用中文，结构必须包含以下章节：\n"
        f"{sections}\n\n"
        f"论文上下文：\n{paper_context}\n\n"
        f"代码分析上下文：\n{code_context}\n\n"
        f"实验复现计划：\n{experiment_plan or '未生成实验计划'}\n\n"
        f"用户补充要求：\n{user_notes or '无'}\n\n"
        "要求内容专业、清晰、可复核；缺少真实结果时保留可填写模板，不要编造实验数值。"
    )
    client = OpenAICompatibleClient(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        model=settings.openai_model,
        timeout_seconds=settings.request_timeout_seconds,
    )
    try:
        return client.chat(
            [
                ChatMessage(
                    role="system",
                    content=(
                        "You are ResearchFlow-Agent. Write polished Markdown research "
                        "project reports without fabricating results."
                    ),
                ),
                ChatMessage(role="user", content=prompt),
            ]
        )
    except LLMClientError as exc:
        return _llm_failure_report(exc)


def _local_report(
    paper_context: str,
    code_context: str,
    experiment_plan: str,
    user_notes: str,
) -> str:
    lines = [
        "# ResearchFlow-Agent 项目报告",
        "",
        "## 项目背景",
        "本项目面向大学生科研训练场景，目标是将论文阅读、代码理解和实验复现流程整合为一个可交互的 AI Agent 系统。",
        "",
        "## 相关工作",
        "相关方向包括科研论文解析、检索增强生成（RAG）、代码仓库静态分析、实验复现流程管理和 Markdown 自动报告生成。",
        "",
        "## 方法原理",
        "系统先解析论文 PDF 并保留页码，再将正文切分为 chunk，通过 embedding 和本地向量检索支持论文问答；代码部分通过目录树和关键文件识别提取复现实验线索。",
        "",
        "## 系统设计",
        "系统由 Gradio Web UI、论文解析模块、RAG 检索模块、代码分析模块、实验计划模块和报告生成模块组成。各模块通过结构化结果传递信息，便于后续扩展。",
        "",
        "### 论文上下文",
        paper_context,
        "",
        "### 代码上下文",
        code_context,
        "",
        "## 实验环境",
        "- 操作系统：macOS 或其他 Python 3.10+ 环境",
        "- Python：建议 3.10 或 3.11",
        "- Web UI：Gradio",
        "- PDF 解析：PyMuPDF / pdfplumber",
        "- Embedding：sentence-transformers，支持本地哈希 fallback",
        "- LLM：OpenAI-compatible API，可选",
        "",
        "## 实验步骤",
        experiment_plan or "尚未生成实验复现计划。建议先完成论文问答和代码分析，再生成实验计划。",
        "",
        "## 实验结果记录表",
        "",
        "| 实验编号 | 日期 | 数据集 | 方法/配置 | 指标 | 结果 | 备注 |",
        "| --- | --- | --- | --- | --- | --- | --- |",
        "| exp-001 | YYYY-MM-DD | TBD | TBD | TBD | TBD | 待填写 |",
        "",
        "## 结果分析",
        "当前报告保留结果分析模板。完成实验后，应比较论文指标、复现指标和简化实验指标，并分析差异来源。",
        "",
        "## 总结与展望",
        "本项目完成了从论文解析、RAG 问答、代码结构分析到实验计划和报告生成的基础闭环。后续可以加入自动运行实验、日志解析、指标可视化和更严格的事实核查。",
    ]
    if user_notes.strip():
        lines.extend(["", "## 补充说明", user_notes.strip()])
    return "\n".join(lines)


def _save_markdown(output_dir: Path, prefix: str, markdown: str) -> Path:
    path = unique_output_path(output_dir, prefix, ".md")
    path.write_text(markdown, encoding="utf-8")
    return path


def _llm_failure_report(exc: LLMClientError) -> str:
    return (
        "# ResearchFlow-Agent 项目报告\n\n"
        f"> LLM 调用失败：{exc}\n\n"
        "请检查 `.env` 中的 API key、base URL 和模型名称后重试。"
    )
