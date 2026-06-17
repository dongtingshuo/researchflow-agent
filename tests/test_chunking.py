import unittest

from src.paper.models import PageText
from src.rag.chunking import chunk_pages, tokenize


class ChunkingTests(unittest.TestCase):
    def test_tokenize_handles_english_and_chinese(self):
        tokens = tokenize("RAG helps 论文阅读.")

        self.assertIn("RAG", tokens)
        self.assertIn("论文", "".join(tokens))

    def test_chunk_pages_preserves_page_numbers(self):
        pages = [
            PageText(
                page_number=3,
                text="alpha beta gamma delta epsilon zeta eta theta iota kappa",
            )
        ]

        chunks = chunk_pages(pages, max_tokens=4, overlap_tokens=1)

        self.assertGreater(len(chunks), 1)
        self.assertEqual(chunks[0].page_numbers, [3])
        self.assertEqual(chunks[0].start_token, 0)
        self.assertEqual(chunks[1].start_token, 3)


if __name__ == "__main__":
    unittest.main()
