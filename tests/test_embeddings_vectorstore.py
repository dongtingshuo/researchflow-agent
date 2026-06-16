import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.paper.models import TextChunk
from src.rag.embeddings import HashingEmbeddingModel, create_embedding_model
from src.rag.vectorstore import LocalVectorStore


class EmbeddingVectorStoreTests(unittest.TestCase):
    def test_hash_embedding_is_deterministic(self):
        model = HashingEmbeddingModel(dimension=32)

        first = model.embed_texts(["retrieval augmented generation"])[0]
        second = model.embed_texts(["retrieval augmented generation"])[0]

        self.assertEqual(first, second)

    def test_create_embedding_model_prefers_cached_sentence_transformer(self):
        sentinel = HashingEmbeddingModel(name="cached-sentence-transformer")
        with patch(
            "src.rag.embeddings.SentenceTransformerEmbeddingModel",
            return_value=sentinel,
        ) as mocked_embedding:
            model = create_embedding_model("sentence-transformers/test-model")

        self.assertIs(model, sentinel)
        mocked_embedding.assert_called_once_with(
            "sentence-transformers/test-model",
            local_files_only=True,
        )

    def test_create_embedding_model_uses_hash_fallback_after_load_failures(self):
        with patch(
            "src.rag.embeddings.SentenceTransformerEmbeddingModel",
            side_effect=[RuntimeError("cache miss"), RuntimeError("download failed")],
        ) as mocked_embedding:
            model = create_embedding_model("sentence-transformers/test-model")

        self.assertIsInstance(model, HashingEmbeddingModel)
        self.assertIn("failed to load sentence-transformers/test-model", model.name)
        self.assertEqual(mocked_embedding.call_count, 2)

    def test_vectorstore_returns_relevant_chunk_and_persists(self):
        model = HashingEmbeddingModel(dimension=64)
        chunks = [
            TextChunk("c1", "transformer attention mechanism", [1]),
            TextChunk("c2", "convolution image filters", [2]),
        ]
        embeddings = model.embed_texts([chunk.text for chunk in chunks])
        store = LocalVectorStore()
        store.add(chunks, embeddings)

        query = model.embed_texts(["attention transformer"])[0]
        results = store.similarity_search(query, top_k=1)

        self.assertEqual(results[0].chunk.chunk_id, "c1")

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "store.json"
            store.save(path)
            loaded = LocalVectorStore.load(path)
            loaded_results = loaded.similarity_search(query, top_k=1)

        self.assertEqual(loaded_results[0].chunk.chunk_id, "c1")

    def test_hybrid_search_uses_keyword_overlap(self):
        model = HashingEmbeddingModel(dimension=64)
        chunks = [
            TextChunk("generic", "vision language model benchmark", [1]),
            TextChunk("specific", "trained on 400 million image text pairs", [2]),
        ]
        embeddings = model.embed_texts([chunk.text for chunk in chunks])
        store = LocalVectorStore()
        store.add(chunks, embeddings)

        query = "How many image-text pairs were used?"
        query_embedding = model.embed_texts([query])[0]
        results = store.hybrid_search(query, query_embedding, top_k=1)

        self.assertEqual(results[0].chunk.chunk_id, "specific")

    def test_hybrid_search_promotes_quantity_answer_patterns(self):
        chunks = [
            TextChunk(
                "background",
                "Related datasets contain between 1 and 10 million training examples.",
                [1],
            ),
            TextChunk(
                "answer",
                "We constructed a new dataset of 400 million (image, text) pairs.",
                [2],
            ),
        ]
        store = LocalVectorStore()
        store.add(chunks, [[0.0, 0.0], [0.0, 0.0]])

        results = store.hybrid_search(
            "How many image-text pairs were used to train CLIP?",
            [0.0, 0.0],
            top_k=1,
        )

        self.assertEqual(results[0].chunk.chunk_id, "answer")


if __name__ == "__main__":
    unittest.main()
