# Project Structure

# 项目结构

## `src/paper/`

PDF parsing, page text models, and paper result extraction.

PDF 解析、页码文本建模和论文结果抽取。

## `src/rag/`

Chunking, embeddings, local vector retrieval, reranking, and paper QA.

chunk 切分、embedding、本地向量检索、rerank 和论文问答。

## `src/code_analyzer/`

Repository loading, zip extraction, directory trees, key file detection, and code summaries.

仓库加载、zip 解压、目录树、关键文件识别和代码摘要。

## `src/agent/`

Planner and workflow orchestration for paper analysis, code analysis, report generation, and verification.

用于论文分析、代码分析、报告生成和核验的规划与工作流编排。

## `src/experiment/`

Command planning, dry-run-first execution, log parsing, result comparison, and reproduction reports.

命令规划、dry-run 优先执行、日志解析、结果对比和复现实验报告。

## `src/evaluation/`

Verifier logic, reproduction evidence checks, and manual evaluation sheet generation.

Verifier 逻辑、复现实验证据检查和人工评测表生成。

## `src/report/`

Markdown report generation for experiment planning and project reports.

用于实验规划和项目报告的 Markdown 生成。

## `examples/reproduction_demo/`

Local toy reproduction case with a paper excerpt, a tiny runnable repository, and expected output examples.

本地 toy 复现案例，包含论文片段、极小可运行仓库和预期输出示例。

## `scripts/`

Local command-line utilities for demos and evaluation templates.

本地命令行工具，用于 demo 和评测模板生成。

## `tests/`

Unit and integration tests for core modules and demo workflows.

核心模块和 demo 工作流的单元测试与集成测试。

## `docs/`

Project overview, safety notes, workflow guides, API reference, and troubleshooting.

项目概览、安全说明、工作流指南、API 参考和问题排查文档。

## `data/outputs/`

Generated local artifacts such as reports, evaluation sheets, run records, and demo outputs.

生成的本地文件，如报告、评测表、运行记录和 demo 输出。
