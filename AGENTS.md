# AGENTS.md

## Project Name

ResearchFlow-Agent

## Project Goal

This repository implements an AI Agent system for research paper reading, code repository analysis, experiment reproduction planning, and report generation.

本仓库实现一个用于科研论文阅读、代码仓库分析、实验复现规划和报告生成的 AI Agent 系统。

The project is maintained as a professional research workflow system with modular components, reproducible outputs, and evidence-aware verification.

本项目定位为专业科研工作流系统，强调模块化组件、可复现输出和证据感知核验。

## Main Features

- Paper PDF parsing
- 论文 PDF 解析
- RAG-based paper question answering
- 基于 RAG 的论文问答
- GitHub repository analysis
- GitHub 仓库分析
- Code structure explanation
- 代码结构解释
- Experiment reproduction planning
- 实验复现计划生成
- Markdown report generation
- Markdown 报告生成
- Verification of citations, evidence, and uncertainty
- 引用、证据和不确定性核验
- Gradio-based Web UI
- 基于 Gradio 的 Web UI

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
   保持代码模块化。
2. Do not put all logic in app.py.
   不要把全部逻辑放在 app.py。
3. Use src/ as the main package directory.
   使用 src/ 作为主要包目录。
4. Add docstrings for important functions and classes.
   为重要函数和类添加 docstring。
5. Read API keys from .env.
   从 .env 读取 API key。
6. Never hard-code secrets.
   不要硬编码密钥。
7. Keep the project runnable on macOS without GPU.
   保持项目可在无 GPU 的 macOS 上运行。
8. Write simple tests for core modules.
   为核心模块编写简单测试。
9. Prefer clear implementation over over-engineering.
   优先清晰实现，避免过度工程化。
10. If a model call fails, return a user-friendly error.
    如果模型调用失败，返回用户友好的错误信息。

## Commands

Install dependencies:

pip install -r requirements.txt

Run the app:

python app.py

Run tests:

pytest tests

## Directory Guide

- app.py: Gradio entry point
- app.py：Gradio 入口
- src/llm: LLM API client and prompts
- src/llm：LLM API 客户端和 prompt
- src/paper: PDF parsing and paper reading
- src/paper：PDF 解析和论文读取
- src/rag: chunking, embedding, vector store, retrieval, QA
- src/rag：chunk、embedding、向量库、检索和问答
- src/code_analyzer: GitHub and zip code analysis
- src/code_analyzer：GitHub 和 zip 代码分析
- src/agent: planner, workflow, verifier
- src/agent：planner、workflow、verifier
- src/report: experiment plan and report generation
- src/report：实验计划和报告生成
- src/evaluation: evaluation metrics
- src/evaluation：评测指标和评测表
- src/storage: history and saved sessions
- src/storage：历史记录和会话保存
- src/utils: helper functions
- src/utils：辅助函数
- data/uploads: uploaded files
- data/uploads：上传文件
- data/vectorstores: local vector databases
- data/vectorstores：本地向量数据库
- data/workspaces: cloned repositories
- data/workspaces：克隆的代码仓库
- data/outputs: generated reports
- data/outputs：生成的报告和评测文件

## Expected MVP

The MVP should allow a user to:

MVP 应支持用户完成：

1. Upload a PDF paper.
2. Parse and chunk the paper.
3. Ask questions about the paper.
4. Get answers with source page references.
5. Analyze a GitHub repository structure.
6. Generate an experiment reproduction plan.
7. Generate a Markdown report.
