import tempfile
import unittest
from pathlib import Path

import fitz

from config import Settings
from src.rag.embeddings import HashingEmbeddingModel
from src.rag.qa import PaperRAGService
from src.rag.reranker import HeuristicReranker


class RAGIntegrationTests(unittest.TestCase):
    def test_pdf_to_retrieval_keeps_supporting_page(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            pdf_path = root / "paper.pdf"
            document = fitz.open()
            first = document.new_page()
            first.insert_text((72, 72), "The paper studies image classification.")
            second = document.new_page()
            second.insert_text(
                (72, 72),
                "The experiment uses toy-cifar and reports accuracy 87.2.",
            )
            document.save(pdf_path)
            document.close()

            settings = Settings(
                upload_dir=root / "uploads",
                vectorstore_dir=root / "vectorstores",
                workspace_dir=root / "workspaces",
                output_dir=root / "outputs",
                top_k_retrieval=2,
            )
            service = PaperRAGService(
                settings,
                embedding_model=HashingEmbeddingModel(dimension=128),
                reranker=HeuristicReranker(),
            )
            index = service.build_from_pdf(pdf_path)
            answer = service.answer("Which dataset reports accuracy 87.2?")

        self.assertEqual(index.paper.page_count, 2)
        self.assertTrue(
            any(2 in item.chunk.page_numbers for item in answer.retrieved_chunks)
        )
        self.assertIn("Page 2", answer.citations_markdown)
        self.assertIn("toy-cifar", answer.citations_markdown)


if __name__ == "__main__":
    unittest.main()
