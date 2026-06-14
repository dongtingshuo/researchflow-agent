import tempfile
import unittest
from pathlib import Path

from src.paper.models import TextChunk
from src.rag.embeddings import HashingEmbeddingModel
from src.rag.vectorstore import LocalVectorStore


class EmbeddingVectorStoreTests(unittest.TestCase):
    def test_hash_embedding_is_deterministic(self):
        model = HashingEmbeddingModel(dimension=32)

        first = model.embed_texts(["retrieval augmented generation"])[0]
        second = model.embed_texts(["retrieval augmented generation"])[0]

        self.assertEqual(first, second)

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


if __name__ == "__main__":
    unittest.main()
