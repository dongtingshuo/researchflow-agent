from pathlib import Path
import tempfile
import unittest

from src.code_analyzer.models import CodeAnalysisResult
from src.experiment.command_planner import plan_reproduction_commands
from src.experiment.log_parser import parse_experiment_log
from src.experiment.report_builder import build_reproduction_report
from src.experiment.result_comparator import compare_results


class ReproductionReportTests(unittest.TestCase):
    def test_report_builder_generates_markdown_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "repo"
            root.mkdir()
            (root / "train.py").write_text("print('train')", encoding="utf-8")
            (root / "requirements.txt").write_text("pytest\n", encoding="utf-8")

            analysis = CodeAnalysisResult(
                source_type="local",
                source=str(root),
                workspace_path=root,
                directory_tree="repo/",
            )
            command_plan = plan_reproduction_commands(analysis)
            log_summary = parse_experiment_log("accuracy: 84.9\nloss: 0.35")
            comparison = compare_results({"accuracy": 87.2}, log_summary.metrics)
            report = build_reproduction_report(
                paper_info="Paper reports accuracy 87.2 on Page 3.",
                code_analysis=analysis,
                command_plan=command_plan,
                run_results=[],
                log_summary=log_summary,
                comparison=comparison,
                verifier_markdown="# Verifier\nneeds review",
                output_dir=tmpdir,
                user_notes="Use a small validation split.",
            )

            self.assertTrue(report.output_path.exists())
            self.assertIn("## 候选复现命令", report.markdown)
            self.assertIn("## 与论文结果对比", report.markdown)
            self.assertIn("accuracy", report.markdown)


if __name__ == "__main__":
    unittest.main()
