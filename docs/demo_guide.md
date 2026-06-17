# Demo Guide

本文档是一份 3 分钟录屏讲解脚本，用于专业说明 ResearchFlow-Agent 的主要工作流。它不是结论保证文档，也不声称系统可以替代人工科研判断。

## 1. Project Overview

ResearchFlow-Agent 是一个面向科研工作流的 AI Agent 系统，支持论文阅读、代码仓库分析、实验复现规划、技术报告生成和证据核验。

建议讲解要点：

- 系统输入包括论文 PDF、GitHub 仓库 URL 或 zip 代码包。
- 系统输出包括论文问答、代码结构分析、实验计划、技术报告、Verifier 结果和评测表。
- 所有关键输出都应由用户人工复核，尤其是页码、实验指标、训练命令和复现结论。

## 2. Paper QA Demo

操作：

1. 打开 `论文问答` Tab。
2. 上传论文 PDF。
3. 点击 `Parse and Index`。
4. 输入一个方法、数据集、指标、结果或局限性问题。
5. 查看回答、页码引用和原文片段。

讲解重点：

- 回答来自检索到的论文片段。
- 引用页码和原文片段用于人工核对。
- 如果 LLM 输出缺少可核验来源，系统会回退到抽取式证据。

## 3. Repository Analysis Demo

操作：

1. 打开 `代码分析` Tab。
2. 输入公开 HTTPS GitHub 仓库 URL，或上传 zip 代码包。
3. 查看目录树、关键文件和代码总结。

讲解重点：

- Code Analyzer 会识别 README、依赖文件、训练入口、推理入口、模型定义、数据集文件和配置文件。
- 分析结果用于支持实验复现计划，但不等于代码已经成功运行。
- GitHub URL 和 zip 解压都有基础安全检查。

## 4. Experiment Planning Demo

操作：

1. 完成论文索引和代码分析。
2. 打开 `实验计划` Tab。
3. 输入约束，例如 CPU-only、最小可验证流程或指定数据路径。
4. 生成实验复现计划。

讲解重点：

- 实验计划包括目标、环境、依赖、数据、训练、测试、指标、结果表格和风险提示。
- 系统不会自动运行真实训练实验。
- 计划必须在使用前由人工检查数据集、权重、硬件、命令和指标。

## 5. Verifier Demo

操作：

1. 运行完整 Agent 工作流，或在评测模块中填写 Agent 输出。
2. 查看 Verifier 输出。

讲解重点：

- Verifier 的作用是风险提示和证据归因。
- Verifier 会区分论文证据、代码证据、模型推断、缺少证据、人工确认项和潜在幻觉。
- Verifier 不保证事实正确性，也不能完全替代人工审查。

## 6. Evaluation Demo

操作：

1. 打开 `实验评测` Tab。
2. 点击 `Generate Evaluation Benchmark` 生成固定 benchmark 表。
3. 或运行：

```bash
python scripts/run_manual_evaluation_template.py
```

讲解重点：

- Evaluation 比较 Ordinary RAG、Agent Workflow、Agent Workflow + Verifier 三种模式。
- 评分指标包括 Answer Completeness、Citation Correctness、Unsupported Claim Count、Reproduction Plan Executability 和 Human Review Notes。
- 评测模板用于人工可复核记录，不是自动裁判。

## 7. Known Limitations

- 系统不会自动运行真实训练实验。
- Verifier 是风险提示和证据归因模块，不是事实正确性保证。
- PDF 页码来自解析器页序，必要时应与原始 PDF 阅读器核对。
- 如果使用 hashing fallback，语义检索质量可能弱于真实 embedding 模型。
- 代码分析可以读取关键文件，但无法保证仓库依赖、数据和硬件条件都可直接满足。
