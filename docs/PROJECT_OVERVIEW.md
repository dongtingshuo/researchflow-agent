# ResearchFlow-Agent: A Multi-Tool AI Agent for Paper-Grounded Experiment Reproduction

# ResearchFlow-Agent：面向论文证据的多工具实验复现 Agent

## 中文项目简介

ResearchFlow-Agent 是一个面向科研论文阅读、代码仓库分析、实验复现规划、指标解析和证据核验的 AI Agent 系统。它把论文解析、RAG 问答、代码结构分析、复现命令规划、安全执行、日志解析、结果对比和 Markdown 报告生成组织为一个可复核的本地工作流。

系统的目标不是替代人工科研判断，而是帮助使用者把论文证据、代码证据、运行日志和生成报告连接起来，使每一步都更容易检查和追踪。

## English Overview

ResearchFlow-Agent supports paper-grounded research workflow automation. It connects paper understanding, code analysis, command planning, safe execution, metric parsing, evidence-aware verification, and structured reporting.

The system is designed as an assistive workflow tool. It does not claim to complete arbitrary experiment reproduction automatically. Instead, it makes intermediate evidence, commands, logs, and uncertainty visible for human review.

## Motivation / 动机

Reproducing paper results is difficult because:

论文结果复现通常较难，原因包括：

- Experimental results are scattered across tables, figures, and text.
- 实验结果分散在表格、图和正文中。
- Code repositories often lack clear reproduction instructions.
- 代码仓库经常缺少清晰的复现说明。
- Environment and configuration details may be incomplete.
- 环境和配置细节可能不完整。
- Execution logs and reported metrics are difficult to compare manually.
- 运行日志和论文指标之间的人工对比成本较高。
- Generated reports may contain unsupported claims without evidence tracking.
- 生成报告可能包含缺少证据追踪的结论。

## System Design / 系统设计

ResearchFlow-Agent is organized into modular components:

ResearchFlow-Agent 由以下模块组成：

- **Paper Result Extractor**: extracts experiment-related claims, datasets, metrics, and page evidence from paper chunks.
- **Paper Result Extractor**：从论文 chunk 中抽取实验相关结论、数据集、指标和页码证据。
- **Code Analyzer**: reads repository structure and key files such as README, dependency files, training scripts, model files, dataset files, and configs.
- **Code Analyzer**：读取仓库结构和 README、依赖文件、训练脚本、模型文件、数据集文件、配置文件等关键内容。
- **Command Planner**: generates candidate reproduction commands from detected entry points and config files.
- **Command Planner**：根据入口文件和配置文件生成候选复现命令。
- **Safe Runner**: executes only low-risk commands when requested and records stdout, stderr, return code, duration, and JSON artifacts.
- **Safe Runner**：只在用户请求时执行低风险命令，并记录 stdout、stderr、返回码、耗时和 JSON 文件。
- **Log Parser**: extracts metrics such as accuracy, loss, F1, Dice, IoU, BLEU, and ROUGE from logs.
- **Log Parser**：从日志中抽取 accuracy、loss、F1、Dice、IoU、BLEU、ROUGE 等指标。
- **Result Comparator**: compares paper-reported metrics with reproduced metrics.
- **Result Comparator**：对比论文报告指标和复现日志指标。
- **Verifier**: classifies paper, code, log, inference, and missing evidence.
- **Verifier**：区分论文、代码、日志、推断和缺失证据。
- **Report Builder**: generates a structured Markdown reproduction report.
- **Report Builder**：生成结构化 Markdown 复现实验报告。
- **Gradio UI**: provides interactive tabs for paper QA, code analysis, full workflow, reproduction, and evaluation.
- **Gradio UI**：提供论文问答、代码分析、完整工作流、论文复现和实验评测交互界面。

## Workflow / 工作流

1. Upload or parse a paper.
2. Extract experiment-related claims and metrics.
3. Analyze the associated code repository.
4. Plan candidate reproduction commands.
5. Execute safe commands or run in dry-run mode.
6. Parse logs and extract metrics.
7. Compare reproduced results with paper-reported results.
8. Verify evidence sources.
9. Generate a structured reproduction report.

中文流程：

1. 上传或解析论文。
2. 抽取实验相关结论和指标。
3. 分析关联代码仓库。
4. 规划候选复现命令。
5. 执行 safe 命令或使用 dry-run 模式。
6. 解析日志并抽取指标。
7. 对比复现结果和论文报告结果。
8. 核验证据来源。
9. 生成结构化复现实验报告。

## Technical Highlights / 技术亮点

- Retrieval-Augmented paper understanding
- 基于检索增强的论文理解
- Code-aware reproduction planning
- 代码感知的复现规划
- Dry-run-first safe execution
- dry-run 优先的安全执行机制
- Log-based metric parsing
- 基于日志的指标解析
- Evidence-aware verification
- 证据感知核验
- Structured reproduction report generation
- 结构化复现实验报告生成
- Modular Python architecture
- 模块化 Python 架构
- Testable experiment workflow
- 可测试的实验工作流

## Current Limitations / 当前限制

- PDF table extraction may be imperfect.
- PDF 表格抽取可能不完整。
- Real benchmark reproduction may require manual dataset preparation.
- 真实 benchmark 复现可能需要人工准备数据集。
- Some commands require user confirmation.
- 部分命令需要用户确认。
- Metric extraction relies on recognizable logging patterns.
- 指标抽取依赖可识别的日志格式。
- Environment conflicts are not fully solved automatically.
- 环境冲突尚不能完全自动解决。
- The system does not guarantee full reproduction of arbitrary papers.
- 系统不保证完整复现任意论文。

## Future Work / 后续方向

- Support real benchmark datasets.
- 支持真实 benchmark 数据集。
- Improve table extraction from PDFs.
- 改进 PDF 表格抽取。
- Integrate Docker environment generation.
- 集成 Docker 环境生成。
- Support GitHub Actions based reproduction.
- 支持基于 GitHub Actions 的复现流程。
- Add automatic ablation study planning.
- 增加自动消融实验规划。
- Support richer experiment metadata tracking.
- 支持更丰富的实验元数据追踪。
- Improve command safety classification.
- 改进命令安全分类。

## Engineering Notes / 工程说明

- Default mode is dry-run.
- 默认模式为 dry-run。
- Unsafe commands are filtered.
- unsafe 命令会被过滤。
- Outputs are saved under `data/outputs/`.
- 输出文件保存到 `data/outputs/`。
- Tests are provided for core modules.
- 核心模块提供测试。
- The system is designed to be modular and extensible.
- 系统设计强调模块化和可扩展性。
