"""Gradio Web UI for the ResearchFlow-Agent MVP."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional, Tuple

from config import get_settings
from src.agent import generate_experiment_plan, run_full_agent_workflow
from src.code_analyzer import analyze_github_repository, analyze_zip_archive
from src.code_analyzer.models import CodeAnalysisResult
from src.evaluation import generate_evaluation_table, verify_workflow_outputs
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
            f"- Embedding: {index.embedding_model_name}\n"
            f"- Reranker: {index.reranker_model_name}"
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


def run_complete_workflow(
    uploaded_file: Any,
    github_url: str,
    task_goal: str,
) -> Tuple[str, str, str, str, str, Optional[str], Optional[str]]:
    """Run the full Agent workflow from PDF and GitHub URL."""
    try:
        result = run_full_agent_workflow(
            settings=get_settings(),
            pdf_path=_file_path(uploaded_file, "PDF paper"),
            github_url=github_url,
            task_goal=task_goal,
        )
        paper_summary = result.paper_summary or "论文摘要未生成。"
        plan_markdown = (
            result.experiment_plan.markdown
            if result.experiment_plan is not None
            else "实验计划未生成。"
        )
        report_markdown = (
            result.project_report.markdown
            if result.project_report is not None
            else "项目报告未生成。"
        )
        verifier_markdown = (
            result.verification.to_markdown()
            if result.verification is not None
            else "Verifier 未执行。"
        )
        plan_file = (
            str(result.experiment_plan.output_path)
            if result.experiment_plan is not None
            else None
        )
        report_file = (
            str(result.project_report.output_path)
            if result.project_report is not None
            else None
        )
        return (
            result.logs_markdown(),
            paper_summary,
            plan_markdown,
            report_markdown,
            verifier_markdown,
            plan_file,
            report_file,
        )
    except Exception as exc:
        return f"# Workflow Status\n\n- **ERROR**: {exc}", "", "", "", "", None, None


def create_evaluation_sheet(
    question: str,
    reference_answer: str,
    human_notes: str,
    rag_answer_input: str,
    agent_answer_input: str,
    agent_verifier_answer_input: str,
    paper_service: Optional[PaperRAGService],
    code_analysis: Optional[CodeAnalysisResult],
    experiment_plan: str,
) -> Tuple[str, str, Optional[str], Optional[str]]:
    """Generate Markdown and CSV evaluation sheets for three modes."""
    try:
        rag_answer = rag_answer_input
        if not rag_answer.strip() and paper_service is not None and question.strip():
            qa_result = paper_service.answer(question)
            rag_answer = f"{qa_result.answer}\n\n{qa_result.citations_markdown}"

        agent_answer = agent_answer_input or experiment_plan
        if not agent_answer.strip():
            agent_answer = "未提供 Agent 分步骤回答。建议先生成实验计划或运行完整 Agent 工作流。"

        agent_verifier_answer = agent_verifier_answer_input
        if not agent_verifier_answer.strip():
            verification = verify_workflow_outputs(
                paper_summary="",
                code_analysis=code_analysis,
                experiment_plan=agent_answer,
                project_report="",
            )
            agent_verifier_answer = f"{agent_answer}\n\n{verification.to_markdown()}"

        result = generate_evaluation_table(
            settings=get_settings(),
            question=question,
            reference_answer=reference_answer,
            human_notes=human_notes,
            rag_answer=rag_answer,
            agent_answer=agent_answer,
            agent_verifier_answer=agent_verifier_answer,
        )
        status = (
            f"Evaluation saved to `{result.markdown_path}` and `{result.csv_path}`"
        )
        return status, result.markdown, str(result.markdown_path), str(result.csv_path)
    except Exception as exc:
        return f"Evaluation generation failed: {exc}", "", None, None


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

            with gr.Tab("完整 Agent 工作流"):
                workflow_pdf_input = gr.File(label="Upload Paper PDF", file_types=[".pdf"])
                workflow_repo_url = gr.Textbox(
                    label="GitHub Repository URL",
                    placeholder="https://github.com/user/repository",
                )
                workflow_goal = gr.Textbox(
                    label="Task Goal",
                    placeholder="例如：复现论文核心实验，并生成本科 AI 项目展示报告。",
                    lines=4,
                )
                workflow_button = gr.Button("一键运行", variant="primary")

                workflow_logs = gr.Markdown(label="Status Logs")
                workflow_paper_summary = gr.Markdown(label="Paper Structured Summary")
                workflow_plan = gr.Markdown(label="Experiment Plan")
                workflow_report = gr.Markdown(label="Project Report")
                workflow_verifier = gr.Markdown(label="Verifier")

                with gr.Row():
                    workflow_plan_file = gr.File(label="Download Experiment Plan")
                    workflow_report_file = gr.File(label="Download Project Report")

                workflow_button.click(
                    fn=run_complete_workflow,
                    inputs=[workflow_pdf_input, workflow_repo_url, workflow_goal],
                    outputs=[
                        workflow_logs,
                        workflow_paper_summary,
                        workflow_plan,
                        workflow_report,
                        workflow_verifier,
                        workflow_plan_file,
                        workflow_report_file,
                    ],
                )

            with gr.Tab("实验评测"):
                evaluation_question = gr.Textbox(
                    label="Question",
                    placeholder="输入要评测的问题，例如：论文方法的核心创新是什么？",
                    lines=3,
                )
                evaluation_reference = gr.Textbox(
                    label="Reference Answer / Standard Answer",
                    placeholder="填写论文原文依据、教师标准答案或人工参考答案。",
                    lines=5,
                )
                evaluation_notes = gr.Textbox(
                    label="Human Notes",
                    placeholder="填写人工评分备注、评分标准或观察到的问题。",
                    lines=4,
                )
                rag_answer_input = gr.Textbox(
                    label="普通 RAG 回答（可留空，系统会尝试用当前论文索引生成）",
                    lines=5,
                )
                agent_answer_input = gr.Textbox(
                    label="Agent 分步骤回答（可留空，系统会尝试使用当前实验计划）",
                    lines=5,
                )
                agent_verifier_answer_input = gr.Textbox(
                    label="Agent + Verifier 回答（可留空，系统会基于当前内容生成 Verifier 记录）",
                    lines=5,
                )
                evaluation_button = gr.Button("Generate Evaluation Sheet", variant="primary")
                evaluation_status = gr.Markdown(label="Status")
                evaluation_markdown = gr.Markdown(label="Evaluation Markdown")
                with gr.Row():
                    evaluation_markdown_file = gr.File(label="Download Markdown")
                    evaluation_csv_file = gr.File(label="Download CSV")

                evaluation_button.click(
                    fn=create_evaluation_sheet,
                    inputs=[
                        evaluation_question,
                        evaluation_reference,
                        evaluation_notes,
                        rag_answer_input,
                        agent_answer_input,
                        agent_verifier_answer_input,
                        service_state,
                        code_analysis_state,
                        plan_state,
                    ],
                    outputs=[
                        evaluation_status,
                        evaluation_markdown,
                        evaluation_markdown_file,
                        evaluation_csv_file,
                    ],
                )

    return demo


def main() -> None:
    build_app().launch()


if __name__ == "__main__":
    main()
