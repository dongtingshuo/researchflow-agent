import tempfile
import unittest
from pathlib import Path

from config import Settings
from src.agent import generate_experiment_plan
from src.code_analyzer.models import CodeAnalysisResult, KeyFile
from src.report import generate_markdown_report


def _settings(tmpdir: str) -> Settings:
    root = Path(tmpdir)
    return Settings(
        upload_dir=root / "uploads",
        vectorstore_dir=root / "vectorstores",
        workspace_dir=root / "workspaces",
        output_dir=root / "outputs",
    )


def _code_analysis(tmpdir: str) -> CodeAnalysisResult:
    workspace = Path(tmpdir) / "repo"
    workspace.mkdir()
    return CodeAnalysisResult(
        source_type="local",
        source="fixture",
        workspace_path=workspace,
        directory_tree="repo/\n|-- train.py\n|-- inference.py\n`-- requirements.txt",
        key_files=[
            KeyFile("requirements.txt", "requirements.txt", "Dependency file."),
            KeyFile("train.py", "train.py", "Training entry point."),
            KeyFile("inference.py", "inference.py", "Inference entry point."),
            KeyFile("dataset.py", "dataset.py", "Dataset loader."),
            KeyFile("model.py", "model.py", "Model definition."),
        ],
        summary="## 项目用途\n测试项目\n\n## 训练入口\n`train.py`",
    )


class PlannerReportTests(unittest.TestCase):
    def test_generate_experiment_plan_saves_markdown(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = generate_experiment_plan(
                settings=_settings(tmpdir),
                code_analysis=_code_analysis(tmpdir),
                user_notes="Use CPU only.",
            )

            self.assertTrue(result.output_path.exists())
            self.assertIn("## 实验目标", result.markdown)
            self.assertIn("## 实验结果表格模板", result.markdown)
            self.assertIn("train.py", result.markdown)

    def test_generate_markdown_report_saves_required_sections(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            plan = "# 实验复现计划\n\n## 训练步骤\n- python train.py"
            result = generate_markdown_report(
                settings=_settings(tmpdir),
                code_analysis=_code_analysis(tmpdir),
                experiment_plan=plan,
                user_notes="Portfolio report.",
            )

            self.assertTrue(result.output_path.exists())
            self.assertIn("## 项目背景", result.markdown)
            self.assertIn("## 实验步骤", result.markdown)
            self.assertIn("## 总结与展望", result.markdown)
            self.assertIn("python train.py", result.markdown)


if __name__ == "__main__":
    unittest.main()
