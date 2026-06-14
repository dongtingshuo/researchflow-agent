"""Paper RAG question answering service."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from config import Settings
from src.llm.client import ChatMessage, LLMClientError, OpenAICompatibleClient
from src.paper.models import ParsedPaper, RetrievedChunk
from src.paper.parser import parse_pdf
from src.rag.chunking import chunk_pages
from src.rag.embeddings import EmbeddingModel, create_embedding_model
from src.rag.vectorstore import LocalVectorStore


@dataclass
class PaperIndex:
    """Indexed paper state used by the Gradio app."""

    paper: ParsedPaper
    chunk_count: int
    embedding_model_name: str


@dataclass
class QAResult:
    """Answer plus supporting evidence."""

    answer: str
    citations_markdown: str
    retrieved_chunks: list[RetrievedChunk]


class PaperRAGService:
    """End-to-end MVP service for paper parsing, indexing, retrieval, and QA."""

    def __init__(
        self,
        settings: Settings,
        embedding_model: Optional[EmbeddingModel] = None,
    ) -> None:
        self.settings = settings
        self.embedding_model = embedding_model or create_embedding_model(
            settings.embedding_model,
            settings.allow_hash_embedding_fallback,
        )
        self.vectorstore = LocalVectorStore()
        self.index: Optional[PaperIndex] = None

    def build_from_pdf(self, pdf_path: Union[str, Path]) -> PaperIndex:
        """Parse a PDF, chunk it, embed chunks, and build the local vector store."""
        stored_pdf = self._copy_to_uploads(Path(pdf_path))
        paper = parse_pdf(stored_pdf)
        chunks = chunk_pages(
            paper.pages,
            max_tokens=self.settings.max_chunk_tokens,
            overlap_tokens=self.settings.chunk_overlap_tokens,
        )
        if not chunks:
            raise ValueError("No extractable text was found in this PDF.")

        embeddings = self.embedding_model.embed_texts([chunk.text for chunk in chunks])
        self.vectorstore = LocalVectorStore()
        self.vectorstore.add(chunks, embeddings)
        self.index = PaperIndex(
            paper=paper,
            chunk_count=len(chunks),
            embedding_model_name=self.embedding_model.name,
        )
        index_path = self.settings.vectorstore_dir / f"{stored_pdf.stem}.json"
        self.vectorstore.save(index_path)
        return self.index

    def answer(self, question: str) -> QAResult:
        """Answer a question using retrieved paper chunks."""
        if self.index is None:
            raise ValueError("Please upload and index a PDF before asking questions.")
        if not question.strip():
            raise ValueError("Please enter a question.")

        query_embedding = self.embedding_model.embed_texts([question])[0]
        retrieved = self.vectorstore.similarity_search(
            query_embedding,
            top_k=self.settings.top_k_retrieval,
        )
        citations = format_citations(retrieved)

        if self.settings.llm_enabled:
            answer = self._answer_with_llm(question, retrieved)
        else:
            answer = self._answer_without_llm(question, retrieved)

        return QAResult(
            answer=answer,
            citations_markdown=citations,
            retrieved_chunks=retrieved,
        )

    def _copy_to_uploads(self, pdf_path: Path) -> Path:
        self.settings.upload_dir.mkdir(parents=True, exist_ok=True)
        target = self.settings.upload_dir / pdf_path.name
        if pdf_path.resolve() != target.resolve():
            shutil.copy2(pdf_path, target)
        return target

    def _answer_with_llm(
        self,
        question: str,
        retrieved: list[RetrievedChunk],
    ) -> str:
        context = "\n\n".join(
            f"[Page {', '.join(map(str, item.chunk.page_numbers))}] {item.chunk.text}"
            for item in retrieved
        )
        client = OpenAICompatibleClient(
            api_key=self.settings.openai_api_key,
            base_url=self.settings.openai_base_url,
            model=self.settings.openai_model,
            timeout_seconds=self.settings.request_timeout_seconds,
        )
        messages = [
            ChatMessage(
                role="system",
                content=(
                    "You are ResearchFlow-Agent. Answer only from the provided paper "
                    "context. Cite page numbers in the answer. If the context is "
                    "insufficient, say so clearly."
                ),
            ),
            ChatMessage(
                role="user",
                content=f"Paper context:\n{context}\n\nQuestion: {question}",
            ),
        ]
        try:
            return client.chat(messages)
        except LLMClientError as exc:
            return (
                "The LLM call failed, so I returned the most relevant paper evidence "
                f"instead. Error: {exc}"
            )

    def _answer_without_llm(
        self,
        question: str,
        retrieved: list[RetrievedChunk],
    ) -> str:
        if not retrieved:
            return "No relevant paper context was found."
        page_text = ", ".join(
            sorted(
                {
                    str(page)
                    for item in retrieved[:2]
                    for page in item.chunk.page_numbers
                },
                key=int,
            )
        )
        snippets = "\n\n".join(
            f"- Page {', '.join(map(str, item.chunk.page_numbers))}: "
            f"{trim_snippet(item.chunk.text, 420)}"
            for item in retrieved[:2]
        )
        return (
            "No LLM API key is configured, so this MVP is returning an extractive "
            f"answer from the most relevant paper passages for: {question}\n\n"
            f"Most relevant pages: {page_text}\n\n{snippets}"
        )


def format_citations(retrieved: list[RetrievedChunk]) -> str:
    """Render retrieved chunks as page citations with source snippets."""
    if not retrieved:
        return "No citations found."

    lines = []
    for index, item in enumerate(retrieved, start=1):
        pages = ", ".join(map(str, item.chunk.page_numbers))
        snippet = trim_snippet(item.chunk.text, 700)
        lines.append(
            f"**[{index}] Page {pages} | score {item.score:.3f}**\n\n> {snippet}"
        )
    return "\n\n".join(lines)


def trim_snippet(text: str, max_length: int = 500) -> str:
    """Trim a citation snippet without losing readability."""
    cleaned = " ".join(text.split())
    if len(cleaned) <= max_length:
        return cleaned
    return cleaned[: max_length - 3].rstrip() + "..."
