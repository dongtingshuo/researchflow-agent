# ResearchFlow-Agent

面向大学生科研训练场景的多工具调用 AI Agent 系统。项目目标是帮助用户围绕一篇科研论文和对应代码仓库，完成论文阅读、RAG 问答、代码结构分析、实验复现计划生成、实验报告生成，以及引用与事实检查。

> 当前阶段：MVP 已实现论文 PDF RAG 问答、代码仓库分析、实验复现计划生成、Markdown 项目报告生成和完整 Agent 工作流。已提供证据与不确定性 Verifier。

## 1. Project Overview

ResearchFlow-Agent is not a general chatbot. It is designed as a research-assistant workflow system for students who need to understand papers, inspect codebases, and plan reproducible experiments.

Planned full workflow:

1. Upload a research paper PDF.
2. Provide a GitHub repository URL or upload a code archive.
3. Extract and chunk paper content.
4. Build a local vector index for retrieval-augmented question answering.
5. Analyze repository structure, dependencies, scripts, and experiment entry points.
6. Generate a step-by-step reproduction plan.
7. Produce an experiment report.
8. Check claims, citations, and facts against the paper context.

## 2. Target Features

Implemented in the MVP:

- Gradio Web UI.
- PDF upload.
- PDF text parsing with page numbers.
- Text chunking.
- Embedding generation.
- Local vector retrieval.
- Paper question answering.
- Answer evidence with source page numbers and snippets.
- GitHub repository cloning into `data/workspaces/`.
- Uploaded zip code archive extraction and analysis.
- Directory tree generation.
- Key file detection for README, dependency files, training/inference scripts, model/data/config files.
- LLM-based or local fallback code structure summary.
- Experiment reproduction plan generation.
- Markdown project report generation.
- Saving generated plans and reports to `data/outputs/`.
- One-click Agent workflow: paper parsing, RAG indexing, paper summary, code analysis, experiment planning, report writing, and verification.
- Verifier for evidence attribution, uncertainty, missing evidence, human-review items, and possible hallucinations.
- Manual experiment evaluation for comparing ordinary RAG, step-by-step Agent, and Agent + Verifier outputs.
- Markdown and CSV evaluation sheets saved to `data/outputs/`.
- Basic tests for paper RAG, code analysis, experiment planning, report writing, and workflow modules.

Planned after the MVP:

- Local history storage with SQLite or JSON.
- Stronger citation-level and fact-checking verifier.

## 3. Tech Stack

- Python 3.10+
- Gradio
- PyMuPDF / pdfplumber
- ChromaDB or FAISS
- sentence-transformers
- OpenAI-compatible API client
- GitPython / subprocess
- SQLite / local JSON
- pytest

## 4. Quick Start

Create or activate a non-base Python environment first. Python 3.10+ is recommended.

```bash
conda create -n researchflow python=3.11
conda activate researchflow
pip install -r requirements.txt
cp .env.example .env
python app.py
```

Open the local Gradio URL.

Paper QA workflow:

1. Open the **论文问答** tab.
2. Upload a PDF.
3. Click **Parse and Index**.
4. Ask a question and inspect page-grounded citations.

Code analysis workflow:

1. Open the **代码分析** tab.
2. Paste a GitHub repository URL and click **Clone and Analyze**, or upload a `.zip` archive and click **Analyze Zip**.
3. Review the generated directory tree, key files, and code structure summary.

Experiment planning workflow:

1. Complete paper indexing and code analysis when possible.
2. Open the **实验计划** tab.
3. Add optional constraints such as CPU-only, small dataset, or portfolio style.
4. Click **Generate Experiment Plan**.
5. Download the saved Markdown file from `data/outputs/`.

Report writing workflow:

1. Generate an experiment plan first when possible.
2. Open the **项目报告** tab.
3. Add optional report notes.
4. Click **Generate Markdown Report**.
5. Download the saved Markdown report from `data/outputs/`.

Complete Agent workflow:

1. Open the **完整 Agent 工作流** tab.
2. Upload a paper PDF.
3. Paste a GitHub repository URL.
4. Enter the task goal, such as "复现论文核心实验，并生成本科 AI 项目展示报告".
5. Click **一键运行**.
6. Review status logs, paper summary, experiment plan, project report, and verifier output.

Experiment evaluation workflow:

1. Open the **实验评测** tab.
2. Enter a question, standard answer or reference answer, and optional human notes.
3. Optionally paste outputs from three modes:
   - 普通 RAG 回答
   - Agent 分步骤回答
   - Agent + Verifier 回答
4. If the ordinary RAG answer is left blank, the app will try to use the current paper index to answer the question.
5. If the Agent answer is left blank, the app will try to use the current experiment plan.
6. Click **Generate Evaluation Sheet**.
7. Download the Markdown and CSV evaluation files from `data/outputs/`.

Evaluation metrics:

1. 答案完整性
2. 引用正确性
3. 复现计划可执行性
4. 是否存在无依据结论
5. 人工评分备注

The evaluation sheet is intentionally designed for manual scoring. It records comparable outputs and scoring fields, but it does not pretend that automatic scoring can fully replace human review.

Verifier output:

1. 来自论文的内容
2. 来自代码仓库的内容
3. 模型推断的内容
4. 缺少证据的内容
5. 需要人工确认的内容
6. 可能存在幻觉的内容
7. 改进建议

The verifier is intentionally conservative. It does not claim the generated plan or report is 100% correct; it separates visible evidence from model inference and highlights what still needs manual checking.

To run tests:

```bash
pytest tests
```

## 5. Configuration

Edit `.env` after copying `.env.example`.

Important settings:

- `OPENAI_API_KEY`: enables LLM-generated answers when configured.
- `OPENAI_BASE_URL`: any OpenAI-compatible API endpoint.
- `OPENAI_MODEL`: chat model name.
- `EMBEDDING_MODEL`: default sentence-transformers model.
- `ALLOW_HASH_EMBEDDING_FALLBACK`: when true, the app falls back to a deterministic local hashing embedding if sentence-transformers cannot load.
- `MAX_PAPER_CHUNK_TOKENS`: chunk size.
- `CHUNK_OVERLAP_TOKENS`: overlap between adjacent chunks.
- `TOP_K_RETRIEVAL`: number of retrieved chunks shown as evidence.

If no LLM API key is configured, the paper QA app still works in offline mode and returns extractive answers from retrieved paper snippets. The code analyzer, experiment planner, report writer, and full workflow also work offline with deterministic structure-based templates where possible.

## 6. Project Structure

```text
researchflow-agent/
  README.md
  AGENTS.md
  requirements.txt
  .env.example
  app.py
  config.py
  data/
    uploads/
    vectorstores/
    workspaces/
    outputs/
  src/
    llm/
    paper/
    rag/
    code_analyzer/
    agent/
    report/
    evaluation/
    storage/
    utils/
  tests/
  examples/
```

Directory responsibilities:

- `data/uploads/`: uploaded PDFs and code archives.
- `data/vectorstores/`: local vector database files.
- `data/workspaces/`: cloned or extracted code repositories.
- `data/outputs/`: generated plans, answers, and reports.
- `src/llm/`: OpenAI-compatible LLM client and prompt helpers.
- `src/paper/`: PDF parsing, section extraction, and metadata handling.
- `src/rag/`: document chunking, embeddings, vector store, and retrieval.
- `src/code_analyzer/`: GitHub cloning, zip extraction, file tree scanning, key file detection, and codebase summarization.
- `src/agent/`: experiment reproduction planning and complete multi-step workflow orchestration.
- `src/report/`: Markdown project report generation.
- `src/evaluation/`: experiment evaluation tables, evidence and uncertainty verification, citation checking, fact checking, and quality scoring.
- `src/storage/`: local history persistence with SQLite or JSON.
- `src/utils/`: shared utilities such as logging, file handling, and path validation.
- `tests/`: basic unit and integration tests.
- `examples/`: sample inputs, workflows, and generated outputs.

## 7. Development Roadmap

### Phase 1: Project Initialization

- Create project structure.
- Add dependency list.
- Add environment variable template.
- Write README and AGENTS development guide.
- Define module responsibilities and implementation plan.

### Phase 2: Paper RAG MVP

- Implement PDF upload handling. Done.
- Extract full text from PDFs with page numbers. Done.
- Split text into chunks. Done.
- Generate embeddings. Done.
- Store and retrieve chunks from a local vector store. Done.
- Build Gradio paper question-answering UI. Done.
- Show page citations and source snippets. Done.
- Add basic tests. Done.

### Phase 3: LLM Client Improvements

- Implement OpenAI-compatible API wrapper.
- Support configurable base URL, API key, and model name.
- Add retry and richer error handling.
- Add prompt templates for paper reading and experiment planning.

### Phase 4: Code Repository Analysis

- Support GitHub repository URL input. Done.
- Clone repositories into `data/workspaces/`. Done.
- Analyze file tree, dependencies, scripts, and likely experiment entry points. Done.
- Add support for uploaded `.zip` code archives. Done.
- Summarize code structure with an LLM or local fallback. Done.

### Phase 5: Agent Workflow

- Design the tool-calling workflow:
  - paper parser
  - retriever
  - repository analyzer
  - reproduction planner
  - report writer
  - citation checker
- Implement experiment reproduction planner. Done.
- Save generated plans to `data/outputs/`. Done.
- Implement complete one-click workflow. Done.
- Return per-step status logs and partial results on failure. Done.
- Implement a structured task state object for broader workflows. Done.
- Add history persistence.

### Phase 6: Report and Evaluation

- Generate Markdown experiment reports. Done.
- Include environment setup, dataset requirements, commands, risks, and expected outputs. Done.
- Implement evidence and uncertainty verifier. Done.
- Implement manual experiment evaluation tables for three answer modes. Done.
- Improve citation grounding and fact-check result summaries.

### Phase 7: Tests, Examples, and Polish

- Add unit tests for each module.
- Add a small demo workflow under `examples/`.
- Improve README with screenshots and usage instructions.
- Prepare the project as a complete undergraduate AI project showcase.

## 8. Current Status

This repository currently provides a runnable paper-RAG, code-analysis, experiment-planning, Markdown-report, evidence verifier, experiment evaluation, and complete Agent workflow MVP. The next recommended task is to add persistent session history and stronger citation-level verification.
