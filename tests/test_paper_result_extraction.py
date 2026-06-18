import unittest

from src.paper.models import TextChunk
from src.paper.results import extract_paper_results


class PaperResultExtractionTests(unittest.TestCase):
    def test_extract_metric_dataset_and_page_evidence(self):
        chunks = [
            TextChunk(
                chunk_id="p3-0-30",
                text=(
                    "Table 2 reports experiment results on VQA v2.0. "
                    "The model achieves accuracy: 67.2 and F1: 66.0 compared with baselines."
                ),
                page_numbers=[3],
            )
        ]

        result = extract_paper_results(chunks)

        self.assertEqual(result.status, "ok")
        self.assertIn(3, result.evidence_pages)
        self.assertTrue(any(metric.name == "accuracy" for metric in result.metrics))
        self.assertTrue(any("VQA" in dataset for dataset in result.datasets))


if __name__ == "__main__":
    unittest.main()
