# Experiment Runner

# 实验复现 Runner

## Goal / 目标

Experiment Runner extends ResearchFlow-Agent from paper reading and code analysis into a safer reproduction workflow. It helps identify paper-reported metrics, inspect repository entry points, plan candidate commands, optionally run low-risk commands, parse logs, compare metrics, and generate a reproduction report.

Experiment Runner 将 ResearchFlow-Agent 从论文阅读和代码分析扩展到更安全的复现工作流。它用于识别论文结果、检查仓库入口、规划候选命令、可选执行低风险命令、解析日志、对比指标并生成复现实验报告。

## Modules / 模块

| Module | Responsibility |
| --- | --- |
| `src/paper/results.py` | Extract result-related evidence, datasets, metrics, and page references from paper chunks. |
| `src/experiment/command_planner.py` | Detect entry files and configuration files, then generate candidate commands with risk levels. |
| `src/experiment/runner.py` | Run or dry-run command candidates with timeout, output capture, and JSON persistence. |
| `src/experiment/log_parser.py` | Extract common metrics from plain-text logs. |
| `src/experiment/result_comparator.py` | Compare paper-reported metrics with parsed reproduced metrics. |
| `src/experiment/report_builder.py` | Build `data/outputs/reproduction_report.md`. |
| `src/evaluation/verifier.py` | Add reproduction-specific evidence checks. |

## Command Planning / 命令规划

The command planner scans for:

命令规划器会扫描：

- `train.py`
- `evaluate.py`
- `test.py`
- `infer.py`
- `demo.py`
- `main.py`
- `scripts/*.py`
- `configs/*.yaml`
- `configs/*.yml`
- `config.py`
- `requirements.txt`
- `pyproject.toml`
- `environment.yml`

Generated commands include examples such as:

生成的命令示例：

```bash
pip install -r requirements.txt
python train.py --config configs/default.yaml
python evaluate.py --config configs/default.yaml
```

Each command is assigned one risk level:

每条命令都会标注风险等级：

- `safe`: low-risk inspection commands, such as help output.
- `needs_confirm`: training, dependency installation, repository scripts, or checkpoint-dependent commands.
- `unsafe`: destructive commands, shell pipes, privileged commands, or unparseable commands.

## Runner Behavior / Runner 行为

The runner defaults to dry-run mode. In dry-run mode, it records the planned command and saves a JSON result without executing repository code.

Runner 默认使用 dry-run 模式。该模式只记录计划命令并保存 JSON 结果，不执行仓库代码。

When execution is enabled, repository scripts additionally require explicit trust confirmation. Every execution has:

启用执行时，仓库脚本还需要显式信任确认。每次执行都会包含：

- working directory
- timeout
- stdout capture
- stderr capture
- return code
- duration
- JSON result file under `data/outputs/experiment_runs/`
- workspace path validation
- a sanitized child-process environment that excludes API keys

`--help` and `--dry-run` do not make an untrusted Python file safe. The runner controls execution and records evidence, but it is not a container sandbox.

`--help` 和 `--dry-run` 不会让不可信 Python 文件自动变得安全。Runner 负责控制执行和保存证据，但它不是容器沙箱。

## Log Metrics / 日志指标

The log parser extracts:

- `loss`
- `val_loss`
- `accuracy`
- `acc`
- `top1`
- `top5`
- `precision`
- `recall`
- `f1`
- `dice`
- `iou`
- `miou`
- `bleu`
- `rouge`

The parser is regex-based and should be treated as an assistive extractor. Parsed metrics should be checked against the original log.

日志解析基于正则表达式，应作为辅助抽取工具使用。解析出的指标需要与原始日志人工核对。

## Report Output / 报告输出

The generated report is saved to:

```text
data/outputs/reproduction_report.md
```

The report includes paper information, repository information, environment files, candidate commands, executed commands, log summaries, metrics, result comparison, verifier checks, and follow-up recommendations.

报告包含论文信息、代码仓库信息、环境文件、候选命令、实际执行命令、日志摘要、指标、结果对比、Verifier 检查和后续建议。
