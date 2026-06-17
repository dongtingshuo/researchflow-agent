import tempfile
import unittest
from pathlib import Path

from config import Settings
from scripts.run_demo_benchmark import (
    DemoCase,
    load_cases,
    run_cases,
    save_results,
)


class DemoBenchmarkScriptTests(unittest.TestCase):
    def test_load_cases_from_examples_file(self):
        cases = load_cases(Path("examples/evaluation_benchmark.json"))

        self.assertEqual(len(cases), 3)
        self.assertEqual(cases[0].case_id, "clip-data-scale")
        self.assertIn("400 million", cases[0].reference_answer)

    def test_run_cases_skips_missing_pdfs_and_saves_results(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            cases = [
                DemoCase(
                    case_id="clip-data-scale",
                    paper="CLIP",
                    question="How many image-text pairs?",
                    reference_answer="400 million",
                    expected_terms=("400 million", "CLIP"),
                )
            ]
            results = run_cases(
                cases=cases,
                settings=Settings(output_dir=tmp / "outputs"),
                pdf_root=tmp / "missing-pdfs",
                pdf_overrides={},
            )
            json_path, markdown_path = save_results(results, tmp / "outputs")

            self.assertEqual(results[0].status, "skipped")
            self.assertTrue(json_path.exists())
            self.assertTrue(markdown_path.exists())
            self.assertIn("clip-data-scale", markdown_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
