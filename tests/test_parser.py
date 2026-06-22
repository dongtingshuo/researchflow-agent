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

    def test_parse_pdf_preserves_real_page_numbers(self):
        import fitz

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "two-pages.pdf"
            document = fitz.open()
            first = document.new_page()
            first.insert_text((72, 72), "First page method description.")
            second = document.new_page()
            second.insert_text((72, 72), "Second page reports accuracy 87.2.")
            document.save(path)
            document.close()

            paper = parse_pdf(path)

        self.assertEqual(paper.page_count, 2)
        self.assertEqual(paper.pages[0].page_number, 1)
        self.assertEqual(paper.pages[1].page_number, 2)
        self.assertIn("accuracy 87.2", paper.pages[1].text)


if __name__ == "__main__":
    unittest.main()
