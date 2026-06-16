import unittest
from unittest.mock import patch

from src.paper.models import RetrievedChunk, TextChunk
from src.rag.reranker import HeuristicReranker, create_reranker


class RerankerTests(unittest.TestCase):
    def test_heuristic_reranker_promotes_formulation_definitions(self):
        candidates = [
            RetrievedChunk(
                chunk=TextChunk("table", "RAG model scores in a result table.", [8]),
                score=0.8,
            ),
            RetrievedChunk(
                chunk=TextChunk(
                    "definition",
                    (
                        "In one approach, RAG-Sequence uses the same document. "
                        "The second approach, RAG-Token, can use a different document."
                    ),
                    [3],
                ),
                score=0.6,
            ),
        ]

        results = HeuristicReranker().rerank(
            "What are the two RAG formulations?",
            candidates,
            top_k=1,
        )

        self.assertEqual(results[0].chunk.chunk_id, "definition")

    def test_heuristic_reranker_promotes_direct_quantity_answer(self):
        candidates = [
            RetrievedChunk(
                chunk=TextChunk(
                    "related",
                    (
                        "Related datasets are smaller than WIT with between 1 and "
                        "10 million training examples. These image-query pairs are "
                        "used as additional training data."
                    ),
                    [26],
                ),
                score=0.86,
            ),
            RetrievedChunk(
                chunk=TextChunk(
                    "direct",
                    (
                        "We create a new dataset of 400 million (image, text) pairs "
                        "and train CLIP with natural language supervision."
                    ),
                    [2],
                ),
                score=0.78,
            ),
        ]

        results = HeuristicReranker().rerank(
            "How many image-text pairs were used to train CLIP?",
            candidates,
            top_k=1,
        )

        self.assertEqual(results[0].chunk.chunk_id, "direct")

    def test_create_reranker_prefers_cached_cross_encoder(self):
        sentinel = HeuristicReranker(name="cached-cross-encoder")
        with patch(
            "src.rag.reranker.CrossEncoderReranker",
            return_value=sentinel,
        ) as mocked_reranker:
            reranker = create_reranker("cross-encoder/test-model", True)

        self.assertIs(reranker, sentinel)
        mocked_reranker.assert_called_once_with(
            "cross-encoder/test-model",
            local_files_only=True,
        )

    def test_create_reranker_falls_back_to_download_then_heuristic(self):
        with patch(
            "src.rag.reranker.CrossEncoderReranker",
            side_effect=[RuntimeError("cache miss"), RuntimeError("download failed")],
        ) as mocked_reranker:
            reranker = create_reranker("cross-encoder/test-model", True)

        self.assertIsInstance(reranker, HeuristicReranker)
        self.assertIn("failed to load cross-encoder/test-model", reranker.name)
        self.assertEqual(mocked_reranker.call_count, 2)


if __name__ == "__main__":
    unittest.main()
