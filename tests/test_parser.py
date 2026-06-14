import tempfile
import unittest
from pathlib import Path

from src.paper.parser import PDFParseError, parse_pdf


class ParserTests(unittest.TestCase):
    def test_parse_pdf_rejects_missing_file(self):
        with self.assertRaises(PDFParseError):
            parse_pdf("missing.pdf")

    def test_parse_pdf_rejects_non_pdf_suffix(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "paper.txt"
            path.write_text("not a pdf", encoding="utf-8")

            with self.assertRaises(PDFParseError):
                parse_pdf(path)


if __name__ == "__main__":
    unittest.main()
