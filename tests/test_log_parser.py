import unittest

from src.experiment.log_parser import parse_experiment_log


class LogParserTests(unittest.TestCase):
    def test_parse_common_metrics_from_text_log(self):
        log_text = """
        epoch=1 loss: 0.35 accuracy: 0.85
        validation dice=0.91 iou=0.78
        """

        result = parse_experiment_log(log_text)

        self.assertAlmostEqual(result.metrics["loss"], 0.35)
        self.assertAlmostEqual(result.metrics["accuracy"], 0.85)
        self.assertAlmostEqual(result.metrics["dice"], 0.91)
        self.assertAlmostEqual(result.metrics["iou"], 0.78)
        self.assertGreaterEqual(len(result.raw_matches), 4)


if __name__ == "__main__":
    unittest.main()
