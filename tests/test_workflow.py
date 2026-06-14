import tempfile
import unittest
from pathlib import Path

from config import Settings
from src.agent.planner import ExperimentPlanResult
from src.agent.workflow import AgentWorkflow
from src.code_analyzer.models import CodeAnalysisResult, KeyFile
from src.paper.models import PageText, ParsedPaper
from src.report.writer import ReportWriterResult


class FakePaperService:
    def __init__(self, settings):
        self.settings = settings
        self.index = None

    def build_from_pdf(self, pdf_path):
        paper = ParsedPaper(
            source_path=Path(pdf_path),
            pages=[
                PageText(
                    page_number=1,
                    text="This paper proposes a compact neural network experiment.",
                )
            ],
        )
        self.index = FakePaperIndex(paper=paper)
        return self.index


class FakePaperIndex:
    def __init__(self, paper):
        self.paper = paper
        self.chunk_count = 1
        self.embedding_model_name = "fake"


def _settings(tmpdir):
    root = Path(tmpdir)
    return Settings(
        upload_dir=root / "uploads",
        vectorstore_dir=root / "vectorstores",
        workspace_dir=root / "workspaces",
        output_dir=root / "outputs",
    )


def _code_analysis(tmpdir):
    workspace = Path(tmpdir) / "repo"
    workspace.mkdir(exist_ok=True)
    return CodeAnalysisResult(
        source_type="github",
        source="https://github.com/example/repo",
        workspace_path=workspace,
        directory_tree="repo/\n|-- train.py\n`-- README.md",
        key_files=[
            KeyFile("README", "README.md", "Project guide."),
            KeyFile("train.py", "train.py", "Training entry point."),
        ],
        summary="## 项目用途\n测试仓库",
    )


def _plan_generator(settings, paper_service, code_analysis, user_notes):
    path = settings.output_dir / "plan.md"
    markdown = "\n".join(
        [
            "# 实验复现计划",
            "## 实验目标",
            "## 环境配置",
            "## 依赖安装",
            "## 数据集准备",
            "## 训练步骤",
            "## 测试步骤",
            "## 指标记录方式",
            "## 实验结果表格模板",
            "## 可能遇到的问题",
            "## 降低复现难度的简化方案",
        ]
    )
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown, encoding="utf-8")
    return ExperimentPlanResult(markdown=markdown, output_path=path)


def _report_generator(settings, paper_service, code_analysis, experiment_plan, user_notes):
    path = settings.output_dir / "report.md"
    markdown = "\n".join(
        [
            "# 项目报告",
            "## 项目背景",
            "## 相关工作",
            "## 方法原理",
            "## 系统设计",
            "## 实验环境",
            "## 实验步骤",
            "## 实验结果记录表",
            "## 结果分析",
            "## 总结与展望",
        ]
    )
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown, encoding="utf-8")
    return ReportWriterResult(markdown=markdown, output_path=path)


class WorkflowTests(unittest.TestCase):
    def test_workflow_success_returns_all_outputs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workflow = AgentWorkflow(
                settings=_settings(tmpdir),
                paper_service_factory=FakePaperService,
                code_analyzer=lambda url, settings: _code_analysis(tmpdir),
                plan_generator=_plan_generator,
                report_generator=_report_generator,
            )

            result = workflow.run("paper.pdf", "https://github.com/example/repo", "复现实验")

        self.assertTrue(result.success)
        self.assertIn("执行 Verifier 检查", result.completed_steps)
        self.assertIsNotNone(result.experiment_plan)
        self.assertIsNotNone(result.project_report)
        self.assertIsNotNone(result.verification)

    def test_workflow_failure_returns_completed_steps_and_error(self):
        def broken_code_analyzer(url, settings):
            raise RuntimeError("clone failed")

        with tempfile.TemporaryDirectory() as tmpdir:
            workflow = AgentWorkflow(
                settings=_settings(tmpdir),
                paper_service_factory=FakePaperService,
                code_analyzer=broken_code_analyzer,
                plan_generator=_plan_generator,
                report_generator=_report_generator,
            )

            result = workflow.run("paper.pdf", "https://github.com/example/repo", "复现实验")

        self.assertFalse(result.success)
        self.assertIn("解析论文", result.completed_steps)
        self.assertIn("构建论文 RAG 知识库", result.completed_steps)
        self.assertIn("生成论文结构化摘要", result.completed_steps)
        self.assertIn("clone failed", result.error)
        self.assertIn("工作流中断", result.logs_markdown())


if __name__ == "__main__":
    unittest.main()
