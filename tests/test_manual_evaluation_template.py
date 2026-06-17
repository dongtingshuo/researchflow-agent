import csv
import json
import os
import tempfile
import unittest
from pathlib import Path

from scripts.run_manual_evaluation_template import (
    ALLOWED_QUESTION_TYPES,
    OUTPUT_FIELDS,
    build_rows,
    generate_manual_evaluation_template,
    load_question_set,
)


class ManualEvaluationTemplateTests(unittest.TestCase):
    def test_paper_eval_questions_schema(self):
        path = Path("examples/paper_eval_questions.json")
        payload = load_question_set(path)

        self.assertEqual(len(payload), 5)
        for paper in payload:
            self.assertIn("paper_id", paper)
            self.assertIn("paper_title", paper)
            self.assertIn("paper_area", paper)
            self.assertIn("optional_repo_url", paper)
            self.assertIn("questions", paper)
            self.assertEqual(len(paper["questions"]), 5)

            question_types = {question["question_type"] for question in paper["questions"]}
            self.assertEqual(question_types, ALLOWED_QUESTION_TYPES)
            for question in paper["questions"]:
                self.assertIn("question_id", question)
                self.assertIn("question", question)
                self.assertIn("question_type", question)
                self.assertIn("expected_evidence_type", question)
                self.assertIn("scoring_note", question)
                self.assertIn(question["question_type"], ALLOWED_QUESTION_TYPES)

    def test_question_json_is_valid(self):
        path = Path("examples/paper_eval_questions.json")
        parsed = json.loads(path.read_text(encoding="utf-8"))

        self.assertIsInstance(parsed, list)

    def test_build_rows_has_required_output_fields(self):
        payload = load_question_set(Path("examples/paper_eval_questions.json"))
        rows = build_rows(payload)

        self.assertEqual(len(rows), 25)
        for row in rows:
            self.assertEqual(set(row), set(OUTPUT_FIELDS))

    def test_generate_manual_evaluation_template_is_local_only(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            previous_key = os.environ.pop("OPENAI_API_KEY", None)
            try:
                artifacts = generate_manual_evaluation_template(
                    question_path=Path("examples/paper_eval_questions.json"),
                    output_dir=Path(tmpdir),
                )
            finally:
                if previous_key is not None:
                    os.environ["OPENAI_API_KEY"] = previous_key

            self.assertTrue(artifacts.markdown_path.exists())
            self.assertTrue(artifacts.csv_path.exists())
            self.assertEqual(artifacts.row_count, 25)
            markdown = artifacts.markdown_path.read_text(encoding="utf-8")
            self.assertIn("ResearchFlow-Agent Manual Evaluation Template", markdown)
            with artifacts.csv_path.open("r", encoding="utf-8") as file:
                rows = list(csv.DictReader(file))

        self.assertEqual(len(rows), 25)
        self.assertEqual(set(rows[0]), set(OUTPUT_FIELDS))


if __name__ == "__main__":
    unittest.main()
