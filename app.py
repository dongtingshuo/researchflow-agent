"""Gradio Web UI for the ResearchFlow-Agent MVP."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional, Tuple

from config import get_settings
from src.agent import generate_experiment_plan
from src.code_analyzer import analyze_github_repository, analyze_zip_archive
from src.code_analyzer.models import CodeAnalysisResult
from src.report import generate_markdown_report
from src.rag.qa import PaperRAGService


def _file_path(uploaded_file: Any, label: str = "file") -> Path:
    if uploaded_file is None:
        raise ValueError(f"Please upload a {label} first.")
    if isinstance(uploaded_file, (str, Path)):
        return Path(uploaded_file)
    if hasattr(uploaded_file, "name"):
        return Path(uploaded_file.name)
    raise ValueError("Unsupported uploaded file object.")


def index_pdf(uploaded_file: Any) -> Tuple[str, Optional[PaperRAGService]]:
    """Parse and index an uploaded PDF for retrieval."""
    try:
        settings = get_settings()
        service = PaperRAGService(settings)
        index = service.build_from_pdf(_file_path(uploaded_file, "PDF paper"))
        status = (
            f"Indexed `{index.paper.source_path.name}` successfully.\n\n"
            f"- Pages: {index.paper.page_count}\n"
            f"- Chunks: {index.chunk_count}\n"
            f"- Characters: {index.paper.total_characters}\n"
            f"- Embedding: {index.embedding_model_name}"
        )
        return status, service
    except Exception as exc:
        return f"Indexing failed: {exc}", None


def ask_paper(question: str, service: Optional[PaperRAGService]) -> Tuple[str, str]:
    """Answer a question from the indexed paper."""
    if service is None:
        return "Please upload and index a PDF first.", ""
    try:
        result = service.answer(question)
        return result.answer, result.citations_markdown
    except Exception as exc:
        return f"Question answering failed: {exc}", ""


def analyze_repo_url(
    repo_url: str,
) -> Tuple[str, str, str, Optional[CodeAnalysisResult]]:
    """Analyze a GitHub repository URL for the code-analysis tab."""
    try:
        result = analyze_github_repository(repo_url, get_settings())
        return (
            f"Analyzed GitHub repository: `{repo_url}`\n\n"
            f"Workspace: `{result.workspace_path}`",
            f"```text\n{result.directory_tree}\n```",
            f"{result.key_files_markdown()}\n\n{result.summary}",
            result,
        )
    except Exception as exc:
        return f"Repository analysis failed: {exc}", "", "", None


def analyze_zip_upload(
    uploaded_file: Any,
) -> Tuple[str, str, str, Optional[CodeAnalysisResult]]:
    """Analyze an uploaded zip archive for the code-analysis tab."""
    try:
        result = analyze_zip_archive(_file_path(uploaded_file, "zip archive"), get_settings())
        return (
            f"Analyzed uploaded zip archive.\n\nWorkspace: `{result.workspace_path}`",
            f"```text\n{result.directory_tree}\n```",
            f"{result.key_files_markdown()}\n\n{result.summary}",
            result,
        )
    except Exception as exc:
        return f"Zip analysis failed: {exc}", "", "", None


def create_experiment_plan(
    paper_service: Optional[PaperRAGService],
    code_analysis: Optional[CodeAnalysisResult],
    notes: str,
) -> Tuple[str, str, Optional[str], str]:
    """Generate and save an experiment reproduction plan."""
    try:
        result = generate_experiment_plan(
            settings=get_settings(),
            paper_service=paper_service,
            code_analysis=code_analysis,
            user_notes=notes,
        )
        status = f"Experiment plan saved to `{result.output_path}`"
        return status, result.markdown, str(result.output_path), result.markdown
    except Exception as exc:
        return f"Experiment planning failed: {exc}", "", None, ""


def create_project_report(
    paper_service: Optional[PaperRAGService],
    code_analysis: Optional[CodeAnalysisResult],
    experiment_plan: str,
    notes: str,
) -> Tuple[str, str, Optional[str]]:
    """Generate and save a Markdown project report."""
    try:
        result = generate_markdown_report(
            settings=get_settings(),
            paper_service=paper_service,
            code_analysis=code_analysis,
            experiment_plan=experiment_plan,
            user_notes=notes,
        )
        status = f"Project report saved to `{result.output_path}`"
        return status, result.markdown, str(result.output_path)
    except Exception as exc:
        return f"Report generation failed: {exc}", "", None


def build_app():
    """Build the Gradio Blocks UI."""
    try:
        import gradio as gr  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "Gradio is not installed. Install dependencies with "
            "`pip install -r requirements.txt` in a non-base environment."
        ) from exc

    with gr.Blocks(title="ResearchFlow-Agent") as demo:
        gr.Markdown("# ResearchFlow-Agent MVP")
        gr.Markdown(
            "Upload a paper PDF, build a local RAG index, then ask questions with "
            "page-grounded citations."
        )

        with gr.Tabs():
            with gr.Tab("论文问答"):
                service_state = gr.State(value=None)

                with gr.Row():
                    pdf_input = gr.File(label="Upload PDF", file_types=[".pdf"])
                    index_button = gr.Button("Parse and Index", variant="primary")

                index_status = gr.Markdown(label="Index Status")

                question_input = gr.Textbox(
                    label="Question",
                    placeholder="What is the main method proposed in this paper?",
                    lines=3,
                )
                ask_button = gr.Button("Ask Paper", variant="primary")

                answer_output = gr.Markdown(label="Answer")
                citation_output = gr.Markdown(label="Citations and Source Snippets")

                index_button.click(
                    fn=index_pdf,
                    inputs=[pdf_input],
                    outputs=[index_status, service_state],
                )
                ask_button.click(
                    fn=ask_paper,
                    inputs=[question_input, service_state],
                    outputs=[answer_output, citation_output],
                )

            with gr.Tab("代码分析"):
                code_analysis_state = gr.State(value=None)
                repo_url_input = gr.Textbox(
                    label="GitHub Repository URL",
                    placeholder="https://github.com/user/repository",
                )
                analyze_repo_button = gr.Button("Clone and Analyze", variant="primary")

                zip_input = gr.File(label="Upload Code Zip", file_types=[".zip"])
                analyze_zip_button = gr.Button("Analyze Zip")

                code_status = gr.Markdown(label="Status")
                directory_tree_output = gr.Markdown(label="Directory Tree")
                code_summary_output = gr.Markdown(label="Key Files and Summary")

                analyze_repo_button.click(
                    fn=analyze_repo_url,
                    inputs=[repo_url_input],
                    outputs=[
                        code_status,
                        directory_tree_output,
                        code_summary_output,
                        code_analysis_state,
                    ],
                )
                analyze_zip_button.click(
                    fn=analyze_zip_upload,
                    inputs=[zip_input],
                    outputs=[
                        code_status,
                        directory_tree_output,
                        code_summary_output,
                        code_analysis_state,
                    ],
                )

            with gr.Tab("实验计划"):
                plan_state = gr.State(value="")
                planner_notes = gr.Textbox(
                    label="Additional Requirements",
                    placeholder="例如：只使用 CPU、先跑最小 demo、优先生成本科项目展示版本。",
                    lines=4,
                )
                planner_button = gr.Button(
                    "Generate Experiment Plan",
                    variant="primary",
                )
                planner_status = gr.Markdown(label="Status")
                planner_output = gr.Markdown(label="Experiment Plan")
                planner_file = gr.File(label="Download Markdown")

                planner_button.click(
                    fn=create_experiment_plan,
                    inputs=[service_state, code_analysis_state, planner_notes],
                    outputs=[
                        planner_status,
                        planner_output,
                        planner_file,
                        plan_state,
                    ],
                )

            with gr.Tab("项目报告"):
                report_notes = gr.Textbox(
                    label="Additional Report Notes",
                    placeholder="例如：面向保研项目经历，强调系统设计和可扩展性。",
                    lines=4,
                )
                report_button = gr.Button("Generate Markdown Report", variant="primary")
                report_status = gr.Markdown(label="Status")
                report_output = gr.Markdown(label="Markdown Report")
                report_file = gr.File(label="Download Markdown")

                report_button.click(
                    fn=create_project_report,
                    inputs=[
                        service_state,
                        code_analysis_state,
                        plan_state,
                        report_notes,
                    ],
                    outputs=[report_status, report_output, report_file],
                )

    return demo


def main() -> None:
    build_app().launch()


if __name__ == "__main__":
    main()
