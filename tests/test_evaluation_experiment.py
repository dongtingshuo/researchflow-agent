import csv
import tempfile
import unittest
from pathlib import Path

from config import Settings
from src.evaluation import (
    DEFAULT_BENCHMARK_CASES,
    EVALUATION_METRICS,
    EVALUATION_MODES,
    generate_benchmark_template,
    generate_evaluation_table,
)


class ExperimentEvaluationTests(unittest.TestCase):
    def test_generate_evaluation_table_saves_markdown_and_csv(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            settings = Settings(output_dir=Path(tmpdir) / "outputs")
            result = generate_evaluation_table(
                settings=settings,
                question="论文方法的核心创新是什么？",
                reference_answer="标准答案：需要说明方法、证据和局限性。",
                human_notes="人工备注：检查引用页码。",
                rag_answer="RAG answer with page citation.",
                agent_answer="Agent plan answer.",
                agent_verifier_answer="Agent answer plus verifier uncertainty.",
            )

            self.assertTrue(result.markdown_path.exists())
            self.assertTrue(result.csv_path.exists())
            markdown = result.markdown

            for mode in EVALUATION_MODES:
                self.assertIn(mode, markdown)
            for metric in EVALUATION_METRICS:
                self.assertIn(metric, markdown)

            with result.csv_path.open("r", encoding="utf-8") as file:
                rows = list(csv.DictReader(file))

        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["mode"], "普通 RAG 回答")
        self.assertIn("citation_correctness", rows[0])

    def test_evaluation_outputs_do_not_collide(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            settings = Settings(output_dir=Path(tmpdir) / "outputs")
            first = generate_evaluation_table(settings=settings, question="Q1")
            second = generate_evaluation_table(settings=settings, question="Q2")

        self.assertNotEqual(first.markdown_path, second.markdown_path)
        self.assertNotEqual(first.csv_path, second.csv_path)

    def test_generate_benchmark_template_saves_multi_case_protocol(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            settings = Settings(output_dir=Path(tmpdir) / "outputs")
            result = generate_benchmark_template(settings=settings)

            self.assertTrue(result.markdown_path.exists())
            self.assertTrue(result.csv_path.exists())
            self.assertIn("ResearchFlow-Agent Demo Benchmark", result.markdown)
            self.assertIn("clip-data-scale", result.markdown)
            self.assertIn("react-benchmarks", result.markdown)
            self.assertIn("rag-formulations", result.markdown)

            with result.csv_path.open("r", encoding="utf-8") as file:
                rows = list(csv.DictReader(file))

        self.assertEqual(len(rows), len(DEFAULT_BENCHMARK_CASES) * len(EVALUATION_MODES))
        self.assertEqual(rows[0]["case_id"], "clip-data-scale")
        self.assertIn("reference_answer", rows[0])
        self.assertIn("expected_pages", rows[0])


if __name__ == "__main__":
    unittest.main()
