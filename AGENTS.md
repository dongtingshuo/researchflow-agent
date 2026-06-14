# AGENTS.md

## Project Name

ResearchFlow-Agent

## Project Goal

This repository implements an AI Agent system for research paper reading, code repository analysis, experiment reproduction planning, and report generation.

The project is intended as a complete undergraduate AI project that can be used in a portfolio or graduate school application.

## Main Features

- Paper PDF parsing
- RAG-based paper question answering
- GitHub repository analysis
- Code structure explanation
- Experiment reproduction planning
- Markdown report generation
- Verification of citations, evidence, and uncertainty
- Gradio-based Web UI

## Tech Stack

- Python 3.10+
- Gradio
- PyMuPDF or pdfplumber
- Chroma or FAISS
- sentence-transformers
- OpenAI-compatible LLM API
- GitPython
- SQLite or local JSON storage
- pytest

## Development Rules

1. Keep code modular.
2. Do not put all logic in app.py.
3. Use src/ as the main package directory.
4. Add docstrings for important functions and classes.
5. Read API keys from .env.
6. Never hard-code secrets.
7. Keep the project runnable on macOS without GPU.
8. Write simple tests for core modules.
9. Prefer clear implementation over over-engineering.
10. If a model call fails, return a user-friendly error.

## Commands

Install dependencies:

pip install -r requirements.txt

Run the app:

python app.py

Run tests:

pytest tests

## Directory Guide

- app.py: Gradio entry point
- src/llm: LLM API client and prompts
- src/paper: PDF parsing and paper reading
- src/rag: chunking, embedding, vector store, retrieval, QA
- src/code_analyzer: GitHub and zip code analysis
- src/agent: planner, workflow, verifier
- src/report: experiment plan and report generation
- src/evaluation: evaluation metrics
- src/storage: history and saved sessions
- src/utils: helper functions
- data/uploads: uploaded files
- data/vectorstores: local vector databases
- data/workspaces: cloned repositories
- data/outputs: generated reports

## Expected MVP

The MVP should allow a user to:

1. Upload a PDF paper.
2. Parse and chunk the paper.
3. Ask questions about the paper.
4. Get answers with source page references.
5. Analyze a GitHub repository structure.
6. Generate an experiment reproduction plan.
7. Generate a Markdown report.
