import unittest

from src.paper.models import RetrievedChunk, TextChunk
from src.rag.reranker import HeuristicReranker
from src.rag.qa import (
    extract_relevant_excerpt,
    format_citations,
    format_retrieved_context,
    ground_answer_with_evidence,
    trim_snippet,
)


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

        self.assertIn("[S1] Page 2", markdown)
        self.assertIn("chunk `p2-0-8`", markdown)
        self.assertIn("retrieval augmented generation", markdown)

    def test_format_citations_uses_relevant_excerpt_when_query_is_given(self):
        retrieved = [
            RetrievedChunk(
                chunk=TextChunk(
                    chunk_id="p2-0-20",
                    text=(
                        "Related work discusses web image datasets. "
                        "We train CLIP on 400 million image-text pairs. "
                        "The appendix discusses other datasets."
                    ),
                    page_numbers=[2],
                ),
                score=0.91,
            )
        ]

        markdown = format_citations(
            retrieved,
            query="How many image-text pairs were used to train CLIP?",
        )

        self.assertIn("400 million image-text pairs", markdown)
        self.assertIn("[S1] Page 2", markdown)

    def test_format_retrieved_context_contains_source_id_page_and_chunk(self):
        retrieved = [
            RetrievedChunk(
                chunk=TextChunk(
                    chunk_id="p4-0-5",
                    text="Ablation results are reported in the paper.",
                    page_numbers=[4],
                ),
                score=0.81,
            )
        ]

        context = format_retrieved_context(retrieved)

        self.assertIn("[S1] Page 4", context)
        self.assertIn("chunk_id=p4-0-5", context)
        self.assertIn("Ablation results", context)

    def test_format_retrieved_context_includes_relevant_evidence(self):
        retrieved = [
            RetrievedChunk(
                chunk=TextChunk(
                    chunk_id="p1-0-20",
                    text=(
                        "Background discussion. We constructed a new dataset of "
                        "400 million (image, text) pairs. Other unrelated sentence."
                    ),
                    page_numbers=[1],
                ),
                score=0.9,
            )
        ]

        context = format_retrieved_context(
            retrieved,
            query="How many image-text pairs were used?",
        )

        self.assertIn("Evidence excerpt:", context)
        self.assertIn("400 million", context)
        self.assertIn("image, text", context)

    def test_extract_relevant_excerpt_prefers_answer_sentence(self):
        excerpt = extract_relevant_excerpt(
            "A generic sentence. "
            "We compare two RAG formulations: RAG-Sequence and RAG-Token. "
            "Another unrelated sentence.",
            "What are the two RAG formulations?",
        )

        self.assertIn("RAG-Sequence", excerpt)
        self.assertIn("RAG-Token", excerpt)

    def test_ground_answer_rejects_uncited_llm_answer(self):
        retrieved = [
            RetrievedChunk(
                chunk=TextChunk(
                    chunk_id="p3-0-6",
                    text="The method uses a contrastive objective.",
                    page_numbers=[3],
                ),
                score=0.9,
            )
        ]

        answer = ground_answer_with_evidence(
            "The method is definitely state of the art.",
            retrieved,
            "What is the method?",
        )

        self.assertIn("拒绝直接采用", answer)
        self.assertIn("[S1] Page 3", answer)
        self.assertIn("contrastive objective", answer)

    def test_heuristic_reranker_keeps_relevant_candidate_visible(self):
        candidates = [
            RetrievedChunk(TextChunk("generic", "General RAG discussion.", [1]), 0.9),
            RetrievedChunk(
                TextChunk(
                    "answer",
                    "RAG-Sequence and RAG-Token are the two formulations.",
                    [3],
                ),
                0.7,
            ),
        ]

        reranked = HeuristicReranker().rerank(
            "What are the two RAG formulations?",
            candidates,
            top_k=2,
        )

        self.assertEqual(reranked[0].chunk.chunk_id, "answer")

    def test_trim_snippet_limits_length(self):
        snippet = trim_snippet("word " * 100, max_length=30)

        self.assertLessEqual(len(snippet), 30)
        self.assertTrue(snippet.endswith("..."))


if __name__ == "__main__":
    unittest.main()
