import unittest

from src.paper.models import RetrievedChunk, TextChunk
from src.rag.qa import format_citations, trim_snippet


class QAFormattingTests(unittest.TestCase):
    def test_format_citations_includes_page_and_snippet(self):
        retrieved = [
            RetrievedChunk(
                chunk=TextChunk(
                    chunk_id="p2-0-8",
                    text="This method uses retrieval augmented generation.",
                    page_numbers=[2],
                ),
                score=0.75,
            )
        ]

        markdown = format_citations(retrieved)

        self.assertIn("Page 2", markdown)
        self.assertIn("retrieval augmented generation", markdown)

    def test_trim_snippet_limits_length(self):
        snippet = trim_snippet("word " * 100, max_length=30)

        self.assertLessEqual(len(snippet), 30)
        self.assertTrue(snippet.endswith("..."))


if __name__ == "__main__":
    unittest.main()
