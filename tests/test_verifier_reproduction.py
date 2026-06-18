from pathlib import Path
import tempfile
import unittest

from src.code_analyzer.models import CodeAnalysisResult
from src.evaluation.verifier import verify_reproduction_artifacts
from src.experiment.command_planner import plan_reproduction_commands
from src.experiment.log_parser import parse_experiment_log
from src.experiment.result_comparator import compare_results
from src.paper.results import PaperMetric, PaperResultSummary


class ReproductionVerifierTests(unittest.TestCase):
    def test_verifier_marks_missing_evidence_without_logs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "train.py").write_text("print('train')", encoding="utf-8")
            analysis = CodeAnalysisResult(
                source_type="local",
                source=str(root),
                workspace_path=root,
                directory_tree="repo/",
            )
            command_plan = plan_reproduction_commands(analysis)
            paper_results = PaperResultSummary(
                metrics=[
                    PaperMetric(
                        name="accuracy",
                        value=87.2,
                        evidence="Accuracy is 87.2.",
                        page=3,
                    )
                ],
                evidence_pages=[3],
                status="ok",
            )
            log_summary = parse_experiment_log("")
            comparison = compare_results(paper_results.metrics_dict(), log_summary.metrics)

            result = verify_reproduction_artifacts(
                paper_results=paper_results,
                code_analysis=analysis,
                command_plan=command_plan,
                run_results=[],
                log_summary=log_summary,
                comparison=comparison,
            )

            self.assertFalse(result.passed)
            self.assertTrue(any(item.source_type == "missing" for item in result.checks))
            self.assertIn("missing", result.to_markdown())


if __name__ == "__main__":
    unittest.main()
