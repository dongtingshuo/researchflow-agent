# Project Summary

## Short Summary

ResearchFlow-Agent 是一个面向科研工作流的 AI Agent 系统，支持论文阅读、代码仓库分析、实验复现规划、技术报告生成和证据核验。

ResearchFlow-Agent is an AI Agent system for research workflows, supporting paper reading, repository analysis, experiment planning, technical report generation, and evidence verification.

## Technical Summary

The system is organized as a modular Python application:

系统采用模块化 Python 架构：

- Paper RAG: parses PDFs, chunks text, embeds paper content, retrieves relevant passages, and answers with page-grounded citations.
- Paper RAG：解析 PDF、切分文本、生成 embedding、检索相关片段，并生成带页码引用的回答。
- Code Analyzer: loads GitHub repositories or zip archives, builds a directory tree, and reads key files.
- Code Analyzer：加载 GitHub 仓库或 zip 代码包，生成目录树并读取关键文件。
- Agent Workflow: coordinates paper parsing, RAG indexing, code analysis, planning, reporting, and verification.
- Agent Workflow：编排论文解析、RAG 建索引、代码分析、计划生成、报告生成和核验。
- Experiment Planner: generates environment, dependency, dataset, training, testing, metric, and risk plans.
- Experiment Planner：生成环境、依赖、数据集、训练、测试、指标和风险计划。
- Report Writer: generates Markdown technical reports from paper, code, and plan context.
- Report Writer：基于论文、代码和计划上下文生成 Markdown 技术报告。
- Verifier: classifies paper evidence, code evidence, model inference, missing evidence, and uncertainty.
- Verifier：分类论文证据、代码证据、模型推断、缺少证据和不确定性。
- Evaluation Template: exports Markdown and CSV evaluation sheets.
- Evaluation Template：导出 Markdown 和 CSV 评测表。
- Gradio UI: provides a local web interface.
- Gradio UI：提供本地 Web 界面。
- CI/tests: GitHub Actions runs `pytest tests` without real API keys.
- CI/tests：GitHub Actions 在不使用真实 API key 的情况下运行 `pytest tests`。

## Research Workflow Summary

ResearchFlow-Agent supports the following workflow:

ResearchFlow-Agent 支持以下科研工作流：

- paper reading
- 论文阅读
- evidence-grounded QA
- 基于证据的问答
- repository analysis
- 代码仓库分析
- experiment planning
- 实验规划
- human-reviewable verification
- 人工可复核的核验流程

## Key Features

- PDF parsing with page preservation.
- 保留页码的 PDF 解析。
- Hybrid retrieval and optional cross-encoder reranking.
- Hybrid retrieval 和可选 cross-encoder reranking。
- Query-focused citation snippets.
- 面向问题的引用片段。
- GitHub URL and zip safety checks.
- GitHub URL 和 zip 安全检查。
- Key-file code analysis.
- 关键文件代码分析。
- Markdown plan and report generation.
- Markdown 计划和报告生成。
- Verifier uncertainty classification.
- Verifier 不确定性分类。
- Markdown/CSV evaluation templates.
- Markdown/CSV 评测模板。

## Current Limitations

- The system does not automatically execute training experiments.
- 系统不会自动执行训练实验。
- Verifier does not guarantee complete factual correctness.
- Verifier 不保证事实完全正确。
- Evaluation still requires human review.
- 评测仍需要人工复核。
- If hashing fallback is used, semantic retrieval quality may decrease.
- 如果使用 hashing fallback，语义检索质量可能下降。
- Chroma / FAISS can be extension directions, but the main implementation currently uses a local JSON vector store.
- Chroma / FAISS 可以作为扩展方向，但当前主实现仍以本地 JSON vector store 为主。
