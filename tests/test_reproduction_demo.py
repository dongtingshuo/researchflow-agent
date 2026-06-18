from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_DIR = PROJECT_ROOT / "examples" / "reproduction_demo"
SCRIPT = PROJECT_ROOT / "scripts" / "run_reproduction_demo.py"


class ReproductionDemoTests(unittest.TestCase):
    def test_demo_files_exist(self):
        self.assertTrue((DEMO_DIR / "sample_paper_excerpt.md").exists())
        self.assertTrue((DEMO_DIR / "toy_repo" / "train.py").exists())
        self.assertTrue((DEMO_DIR / "toy_repo" / "evaluate.py").exists())
        self.assertTrue((DEMO_DIR / "toy_repo" / "configs" / "default.yaml").exists())
        self.assertTrue((DEMO_DIR / "toy_repo" / "requirements.txt").exists())
        self.assertTrue((DEMO_DIR / "expected_outputs" / "reproduction_report.md").exists())
        self.assertTrue((DEMO_DIR / "expected_outputs" / "parsed_metrics.json").exists())
        self.assertTrue((DEMO_DIR / "expected_outputs" / "comparison_result.json").exists())

    def test_demo_dry_run_does_not_execute_evaluate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "demo"
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), "--output-dir", str(output_dir)],
                cwd=PROJECT_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            run_result = _load_json(output_dir / "run_result.json")
            self.assertTrue(output_dir.exists())
            self.assertTrue((output_dir / "reproduction_report.md").exists())
            self.assertFalse(run_result["run_results"][0]["executed"])
            self.assertTrue(run_result["run_results"][0]["dry_run"])

    def test_demo_run_safe_generates_metrics_comparison_and_verifier(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "demo"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--run-safe",
                    "--timeout",
                    "30",
                    "--output-dir",
                    str(output_dir),
                ],
                cwd=PROJECT_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("Report:", completed.stdout)

            parsed_metrics = _load_json(output_dir / "parsed_metrics.json")
            comparison = _load_json(output_dir / "comparison_result.json")
            verifier = _load_json(output_dir / "verifier_result.json")
            run_result = _load_json(output_dir / "run_result.json")

            self.assertTrue((output_dir / "reproduction_report.md").exists())
            self.assertEqual(parsed_metrics["metrics"]["accuracy"], 84.9)
            self.assertIn("status", comparison)
            self.assertTrue(any("gap" in item for item in comparison["comparisons"]))
            self.assertEqual(comparison["status"], "partially reproduced")
            self.assertIn("checks", verifier)
            self.assertGreater(len(verifier["checks"]), 0)
            self.assertTrue(run_result["run_results"][0]["executed"])
            self.assertIn("evaluate.py --dry-run", run_result["run_results"][0]["command"])


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
