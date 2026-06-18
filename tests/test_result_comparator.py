import unittest

from src.experiment.result_comparator import compare_results


class ResultComparatorTests(unittest.TestCase):
    def test_compare_higher_is_better_metric(self):
        result = compare_results({"accuracy": 87.2}, {"accuracy": 84.9}, tolerance=0.5)

        self.assertEqual(result.status, "partially reproduced")
        self.assertEqual(result.comparisons[0].name, "accuracy")
        self.assertAlmostEqual(result.comparisons[0].gap or 0.0, -2.3)
        self.assertEqual(result.comparisons[0].status, "partially reproduced")

    def test_compare_lower_is_better_metric(self):
        result = compare_results({"loss": 0.5}, {"loss": 0.4}, tolerance=0.05)

        self.assertEqual(result.status, "reproduced")
        self.assertAlmostEqual(result.comparisons[0].gap or 0.0, 0.1)


if __name__ == "__main__":
    unittest.main()
