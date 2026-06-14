"""PDF parsing utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Union

from src.paper.models import PageText, ParsedPaper


class PDFParseError(RuntimeError):
    """Raised when a PDF cannot be parsed."""


def parse_pdf(pdf_path: Union[str, Path]) -> ParsedPaper:
    """Extract text from a PDF while preserving 1-based page numbers."""
    path = Path(pdf_path)
    if not path.exists():
        raise PDFParseError(f"PDF file does not exist: {path}")
    if path.suffix.lower() != ".pdf":
        raise PDFParseError(f"Expected a .pdf file, got: {path.name}")

    try:
        return _parse_with_pymupdf(path)
    except ImportError:
        return _parse_with_pdfplumber(path)
    except Exception as exc:
        raise PDFParseError(f"Failed to parse PDF '{path.name}': {exc}") from exc


def _parse_with_pymupdf(path: Path) -> ParsedPaper:
    try:
        import fitz  # type: ignore
    except ImportError as exc:
        raise ImportError("PyMuPDF is not installed") from exc

    pages: list[PageText] = []
    with fitz.open(path) as document:
        for index, page in enumerate(document, start=1):
            text = page.get_text("text") or ""
            pages.append(PageText(page_number=index, text=_clean_text(text)))
    return ParsedPaper(source_path=path, pages=pages)


def _parse_with_pdfplumber(path: Path) -> ParsedPaper:
    try:
        import pdfplumber  # type: ignore
    except ImportError as exc:
        raise PDFParseError(
            "PDF parsing requires PyMuPDF or pdfplumber. Install dependencies with "
            "`pip install -r requirements.txt`."
        ) from exc

    pages: list[PageText] = []
    with pdfplumber.open(path) as document:
        for index, page in enumerate(document.pages, start=1):
            text = page.extract_text() or ""
            pages.append(PageText(page_number=index, text=_clean_text(text)))
    return ParsedPaper(source_path=path, pages=pages)


def _clean_text(text: str) -> str:
    lines = [line.strip() for line in text.replace("\r", "\n").split("\n")]
    return "\n".join(line for line in lines if line)
