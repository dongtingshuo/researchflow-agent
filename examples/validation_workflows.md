# ResearchFlow-Agent Validation Workflows

# ResearchFlow-Agent 验证流程

This file records repeatable validation workflows for the ResearchFlow-Agent system.

本文档记录 ResearchFlow-Agent 系统的可重复验证流程。

## Workflow 1: Paper RAG QA / 论文 RAG 问答

- Paper: CLIP, ReAct, or RAG PDF
- 论文：CLIP、ReAct 或 RAG PDF
- Operation:
- 操作：
  1. Open the `论文问答` tab.
     打开 `论文问答` Tab。
  2. Upload the paper PDF.
     上传论文 PDF。
  3. Click `Parse and Index`.
     点击 `Parse and Index`。
  4. Ask one benchmark question from `examples/evaluation_benchmark.json`.
     使用 `examples/evaluation_benchmark.json` 中的一个 benchmark 问题进行提问。
- Expected output:
- 预期输出：
  - Answer uses retrieved paper context.
    回答基于检索到的论文上下文。
  - Citations contain page numbers.
    引用包含页码。
  - Source snippets include direct evidence.
    原文片段包含直接证据。

## Workflow 2: Code Analyzer / 代码分析

- Repository examples:
- 仓库示例：
  - `https://github.com/openai/CLIP`
  - `https://github.com/karpathy/nanoGPT`
  - `https://github.com/ysymyth/ReAct`
- Operation:
- 操作：
  1. Open the `代码分析` tab.
     打开 `代码分析` Tab。
  2. Paste a public HTTPS GitHub repository URL.
     输入公开 HTTPS GitHub 仓库 URL。
  3. Click `Clone and Analyze`.
     点击 `Clone and Analyze`。
- Expected output:
- 预期输出：
  - Directory tree.
    目录树。
  - README and dependency files detected.
    识别 README 和依赖文件。
  - Training, inference, model, dataset, and config files identified when present.
    在存在时识别训练、推理、模型、数据集和配置文件。
  - Summary explains project purpose, core files, model location, entry points, data format, and run steps.
    总结说明项目用途、核心文件、模型位置、入口脚本、数据格式和运行步骤。

## Workflow 3: Full Agent Workflow / 完整 Agent 工作流

- Inputs:
- 输入：
  - Paper PDF: CLIP / ReAct / RAG
    论文 PDF：CLIP / ReAct / RAG
  - Repository URL: a matching public HTTPS GitHub repository
    仓库 URL：匹配论文任务的公开 HTTPS GitHub 仓库
  - Task goal: `复现论文核心实验，并生成技术报告。`
    Task goal: `Reproduce the core experiment and generate a technical report.`
- Expected output:
- 预期输出：
  - Status logs for each step.
    每一步的状态日志。
  - Structured paper summary.
    结构化论文摘要。
  - Code analysis.
    代码分析。
  - Experiment reproduction plan.
    实验复现计划。
  - Markdown technical report.
    Markdown 技术报告。
  - Verifier result separating paper evidence, code evidence, model inference, missing evidence, human-review items, and possible hallucinations.
    Verifier 输出，用于区分论文证据、代码证据、模型推断、缺少证据、人工确认项和潜在幻觉。

## Workflow 4: Evaluation / 实验评测

- Operation:
- 操作：
  1. Open the `实验评测` tab.
     打开 `实验评测` Tab。
  2. Click `Generate Evaluation Benchmark`.
     点击 `Generate Evaluation Benchmark`。
  3. Fill the CSV or Markdown table after running each mode.
     运行各模式后填写 CSV 或 Markdown 表格。
- Expected output:
- 预期输出：
  - `data/outputs/benchmark-evaluation-*.md`
  - `data/outputs/benchmark-evaluation-*.csv`

## Notes / 说明

- Keep uploaded PDFs and generated vector stores out of Git.
- 不要将上传 PDF 和生成的向量库提交到 Git。
- Rotate API keys if they were exposed during local testing.
- 如果 API key 在本地测试中暴露，应及时轮换。
- Record both successful answers and uncertain verifier outputs; uncertainty is an important part of evidence-aware systems.
- 同时记录成功回答和 Verifier 的不确定性输出；不确定性是证据感知系统的重要组成部分。
