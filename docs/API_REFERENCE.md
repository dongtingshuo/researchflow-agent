# API Reference

# 核心 API 参考

This document gives a compact reference for the main Python modules. It is not a generated full API document.

本文档简要说明主要 Python 模块，不是完整自动生成 API 文档。

## Paper Result Extraction / 论文结果抽取

Module:

```text
src.paper.results
```

Function:

```python
extract_paper_results(paper_chunks) -> PaperResultSummary
```

Input: `TextChunk`, `RetrievedChunk`, or `PageText` objects.

Output: task, datasets, metrics, evidence pages, status, and notes.

输入：`TextChunk`、`RetrievedChunk` 或 `PageText` 对象。  
输出：任务、数据集、指标、证据页码、状态和备注。

Example:

```python
from src.paper.results import extract_paper_results

summary = extract_paper_results(chunks)
print(summary.metrics_dict())
```

## Command Planner / 命令规划

Module:

```text
src.experiment.command_planner
```

Function:

```python
plan_reproduction_commands(code_analysis) -> CommandPlan
```

Input: `CodeAnalysisResult`.

Output: entry files, config files, candidate commands, risk levels, and warnings.

输入：`CodeAnalysisResult`。  
输出：入口文件、配置文件、候选命令、风险等级和提示。

## Runner / 受控 Runner

Module:

```text
src.experiment.runner
```

Function:

```python
run_command_candidate(
    candidate,
    cwd,
    dry_run=True,
    allow_repository_scripts=False,
) -> CommandRunResult
```

Input: command candidate, working directory, execution mode, and explicit repository-script trust flag.

Output: stdout, stderr, return code, duration, risk level, execution flag, and JSON result path.

输入：候选命令、工作目录、执行模式和显式仓库脚本信任标志。
输出：stdout、stderr、返回码、耗时、风险等级、是否执行和 JSON 结果路径。

Repository Python scripts remain blocked unless `allow_repository_scripts=True`. This flag should only be used after reviewing the repository.

只有设置 `allow_repository_scripts=True` 才会执行仓库 Python 脚本，并且应先检查仓库内容。

## Log Parser / 日志解析

Module:

```text
src.experiment.log_parser
```

Function:

```python
parse_experiment_log(log_text) -> LogParseResult
```

Extracted metrics include `accuracy`, `loss`, `f1`, `dice`, `iou`, `bleu`, and `rouge` when present in recognizable text.

可从可识别日志文本中抽取 `accuracy`、`loss`、`f1`、`dice`、`iou`、`bleu` 和 `rouge` 等指标。

## Result Comparator / 结果对比

Module:

```text
src.experiment.result_comparator
```

Function:

```python
compare_results(paper_metrics, reproduced_metrics) -> ResultComparison
```

Input: dictionaries of paper metrics and reproduced metrics.

Output: gap, status, and notes for each comparable metric.

输入：论文指标字典和复现指标字典。  
输出：每个可对比指标的差距、状态和备注。

## Verifier / 证据核验

Module:

```text
src.evaluation.verifier
```

Functions:

```python
verify_workflow_outputs(...)
verify_reproduction_artifacts(...)
```

The reproduction verifier classifies checks into paper, code, log, inference, and missing evidence.

复现实验 Verifier 会将检查项分类为论文、代码、日志、推断和缺失证据。

## Report Builder / 报告生成

Module:

```text
src.experiment.report_builder
```

Function:

```python
build_reproduction_report(...) -> ReproductionReport
```

Output:

```text
data/outputs/reproduction_report.md
```

The report includes paper information, repository information, environment files, commands, logs, metrics, comparison results, verifier checks, and follow-up suggestions.

报告包含论文信息、代码仓库信息、环境文件、命令、日志、指标、对比结果、Verifier 检查和后续建议。
