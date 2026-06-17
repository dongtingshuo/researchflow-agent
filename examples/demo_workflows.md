# ResearchFlow-Agent Demo Workflows

This file records repeatable demo workflows for portfolio and course-project presentations.

## Demo 1: Paper RAG QA

- Paper: CLIP, ReAct, or RAG PDF
- Operation:
  1. Open the `论文问答` tab.
  2. Upload the paper PDF.
  3. Click `Parse and Index`.
  4. Ask one benchmark question from `examples/evaluation_benchmark.json`.
- Expected output:
  - Answer uses retrieved paper context.
  - Citations contain page numbers.
  - Source snippets include direct evidence.

## Demo 2: Code Analyzer

- Repository examples:
  - `https://github.com/openai/CLIP`
  - `https://github.com/karpathy/nanoGPT`
  - `https://github.com/ysymyth/ReAct`
- Operation:
  1. Open the `代码分析` tab.
  2. Paste a public HTTPS GitHub repository URL.
  3. Click `Clone and Analyze`.
- Expected output:
  - Directory tree.
  - README and dependency files detected.
  - Training, inference, model, dataset, and config files identified when present.
  - Summary explains project purpose, core files, model location, entry points, data format, and run steps.

## Demo 3: Full Agent Workflow

- Inputs:
  - Paper PDF: CLIP / ReAct / RAG
  - Repository URL: a matching public HTTPS GitHub repository
  - Task goal: `复现论文核心实验，并生成本科 AI 项目展示报告。`
- Expected output:
  - Status logs for each step.
  - Structured paper summary.
  - Code analysis.
  - Experiment reproduction plan.
  - Markdown project report.
  - Verifier result separating paper evidence, code evidence, model inference, missing evidence, human-review items, and possible hallucinations.

## Demo 4: Evaluation

- Operation:
  1. Open the `实验评测` tab.
  2. Click `Generate Demo Benchmark`.
  3. Fill the CSV or Markdown table after running each mode.
- Expected output:
  - `data/outputs/benchmark-evaluation-*.md`
  - `data/outputs/benchmark-evaluation-*.csv`

## Notes

- Keep uploaded PDFs and generated vector stores out of Git.
- Rotate API keys before public demos.
- Record both successful answers and uncertain verifier outputs; uncertainty makes the project more credible, not weaker.
