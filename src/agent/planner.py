"""Experiment reproduction planner."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from config import Settings
from src.code_analyzer.models import CodeAnalysisResult
from src.llm.client import ChatMessage, LLMClientError, OpenAICompatibleClient
from src.rag.qa import PaperRAGService, trim_snippet
from src.utils.files import unique_output_path


PLAN_SECTIONS = [
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


@dataclass(frozen=True)
class ExperimentPlanResult:
    """Generated experiment plan and saved file location."""

    markdown: str
    output_path: Path


def generate_experiment_plan(
    settings: Settings,
    paper_service: Optional[PaperRAGService] = None,
    code_analysis: Optional[CodeAnalysisResult] = None,
    user_notes: str = "",
) -> ExperimentPlanResult:
    """Generate and save a Markdown experiment reproduction plan."""
    paper_context = _paper_context(paper_service)
    code_context = _code_context(code_analysis)

    markdown = _generate_with_llm(
        settings=settings,
        paper_context=paper_context,
        code_context=code_context,
        user_notes=user_notes,
    )
    if markdown is None:
        markdown = _local_plan(paper_context, code_analysis, user_notes)

    output_path = _save_markdown(
        settings.output_dir,
        "experiment-plan",
        markdown,
    )
    return ExperimentPlanResult(markdown=markdown, output_path=output_path)


def _generate_with_llm(
    settings: Settings,
    paper_context: str,
    code_context: str,
    user_notes: str,
) -> Optional[str]:
    if not settings.llm_enabled:
        return None

    sections = "\n".join(f"{index}. {section}" for index, section in enumerate(PLAN_SECTIONS, 1))
    prompt = (
        "请基于论文解析结果和代码分析结果，生成一份"
        "可执行的实验复现计划。要求使用中文 Markdown，结构必须包含以下章节：\n"
        f"{sections}\n\n"
        f"论文上下文：\n{paper_context}\n\n"
        f"代码分析上下文：\n{code_context}\n\n"
        f"用户补充要求：\n{user_notes or '无'}\n\n"
        "要求具体、谨慎、可操作；如果某项信息缺失，请明确写出需要人工确认。"
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
                        "You are ResearchFlow-Agent. Generate practical experiment "
                        "reproduction plans for AI papers and code repositories."
                    ),
                ),
                ChatMessage(role="user", content=prompt),
            ]
        )
    except LLMClientError as exc:
        return _llm_failure_note(exc)


def _local_plan(
    paper_context: str,
    code_analysis: Optional[CodeAnalysisResult],
    user_notes: str,
) -> str:
    code_files = _key_file_paths(code_analysis)
    dependency_files = _files_by_role(
        code_analysis,
        {"requirements.txt", "pyproject.toml", "environment.yml"},
    )
    train_files = _files_by_role(code_analysis, {"train.py"})
    test_files = _files_by_role(code_analysis, {"test.py"})
    inference_files = _files_by_role(
        code_analysis,
        {"inference.py", "demo.py", "main.py", "notebook"},
    )
    dataset_files = _files_by_role(code_analysis, {"dataset.py"})
    config_files = _files_by_role(code_analysis, {"config"})

    lines = ["# 实验复现计划", ""]
    lines.extend(
        [
            "## 实验目标",
            "- 复现论文中的核心方法，并在本地代码仓库中跑通最小训练或推理流程。",
            "- 对齐论文描述、代码入口、依赖环境、数据集准备方式和评价指标。",
            f"- 论文上下文摘要：{paper_context}",
            "",
            "## 环境配置",
            "- 推荐使用 macOS 可运行的 CPU 环境作为默认复现环境。",
            "- Python 版本优先选择项目声明版本；如果未声明，建议从 Python 3.10 或 3.11 开始。",
            f"- 配置文件线索：{_paths_or_unknown(config_files)}",
            "",
            "## 依赖安装",
            f"- 依赖文件：{_paths_or_unknown(dependency_files)}",
            "- 建议先创建独立 conda 环境，再安装依赖，避免污染 base 环境。",
            "- 如果依赖安装失败，优先固定 Python 版本并逐项安装关键包。",
            "",
            "## 数据集准备",
            f"- 数据集相关文件：{_paths_or_unknown(dataset_files)}",
            "- 根据 README、dataset 文件和配置文件确认数据目录结构。",
            "- 先准备一个小样本数据集，用于验证 dataloader、预处理和 batch 输出是否正常。",
            "",
            "## 训练步骤",
            f"- 训练入口：{_paths_or_unknown(train_files)}",
            "- 先运行帮助命令或阅读参数解析逻辑，确认必要参数。",
            "- 使用小 epoch、小 batch size、少量数据做 smoke test，再扩大实验规模。",
            "",
            "## 测试步骤",
            f"- 测试入口：{_paths_or_unknown(test_files)}",
            f"- 推理、demo 或 notebook 入口：{_paths_or_unknown(inference_files)}",
            "- 先验证模型权重加载、单样本推理和输出格式，再运行完整测试集。",
            "",
            "## 指标记录方式",
            "- 记录每次实验的 commit、环境、数据版本、命令、随机种子和主要指标。",
            "- 如果论文给出 Accuracy、F1、BLEU、mAP、Loss 等指标，优先复用论文指标。",
            "- 保存日志、配置文件、输出结果和异常信息到 `data/outputs/`。",
            "",
            "## 实验结果表格模板",
            "",
            "| Run ID | 日期 | 数据集 | 配置/命令 | 指标1 | 指标2 | 备注 |",
            "| --- | --- | --- | --- | --- | --- | --- |",
            "| run-001 | YYYY-MM-DD | sample/full | python train.py ... | TBD | TBD | smoke test |",
            "",
            "## 可能遇到的问题",
            "- 依赖版本与当前 Python 版本不兼容。",
            "- 数据集路径、权重路径或配置文件缺失。",
            "- GPU 相关代码在 CPU-only 环境下报错。",
            "- README 与实际代码入口不一致。",
            f"- 当前识别到的关键文件：{_paths_or_unknown(code_files)}",
            "",
            "## 降低复现难度的简化方案",
            "- 先只跑推理或 demo，确认模型和输入输出格式。",
            "- 使用小数据集、小 batch size、少 epoch 完成端到端 smoke test。",
            "- 如果训练成本太高，优先复现数据预处理、模型 forward、指标计算和单样本推理。",
            "- 将完整复现拆成环境安装、数据准备、入口脚本运行、指标对齐四个阶段。",
        ]
    )
    if user_notes.strip():
        lines.extend(["", "## 用户补充要求", user_notes.strip()])
    return "\n".join(lines)


def _paper_context(paper_service: Optional[PaperRAGService]) -> str:
    if paper_service is None or paper_service.index is None:
        return "未提供论文解析结果。"

    paper = paper_service.index.paper
    snippets = []
    for page in paper.pages[:3]:
        if page.text.strip():
            snippets.append(f"Page {page.page_number}: {trim_snippet(page.text, 500)}")
    snippet_text = "\n".join(snippets) if snippets else "未提取到可用正文片段。"
    return (
        f"论文文件：{paper.source_path.name}\n"
        f"页数：{paper.page_count}\n"
        f"字符数：{paper.total_characters}\n"
        f"片段：\n{snippet_text}"
    )


def _code_context(code_analysis: Optional[CodeAnalysisResult]) -> str:
    if code_analysis is None:
        return "未提供代码分析结果。"
    return (
        f"来源：{code_analysis.source_type} - {code_analysis.source}\n"
        f"工作目录：{code_analysis.workspace_path}\n"
        f"关键文件：\n{code_analysis.key_files_markdown()}\n\n"
        f"代码总结：\n{code_analysis.summary}\n\n"
        f"目录树：\n{code_analysis.directory_tree}"
    )


def _key_file_paths(code_analysis: Optional[CodeAnalysisResult]) -> list[str]:
    if code_analysis is None:
        return []
    return [item.path for item in code_analysis.key_files]


def _files_by_role(
    code_analysis: Optional[CodeAnalysisResult],
    roles: set[str],
) -> list[str]:
    if code_analysis is None:
        return []
    return [item.path for item in code_analysis.key_files if item.role in roles]


def _paths_or_unknown(paths: list[str]) -> str:
    if not paths:
        return "未识别，需要人工确认"
    return ", ".join(f"`{path}`" for path in paths)


def _save_markdown(output_dir: Path, prefix: str, markdown: str) -> Path:
    path = unique_output_path(output_dir, prefix, ".md")
    path.write_text(markdown, encoding="utf-8")
    return path


def _llm_failure_note(exc: LLMClientError) -> str:
    return (
        "# 实验复现计划\n\n"
        f"> LLM 调用失败：{exc}\n\n"
        "请检查 `.env` 中的 API key、base URL 和模型名称后重试。"
    )
