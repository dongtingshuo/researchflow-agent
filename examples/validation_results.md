# Validation Results

# 验证记录

This document records the local validation checks performed for ResearchFlow-Agent. It is a reproducible validation note, not a large-scale benchmark.

本文档记录 ResearchFlow-Agent 的本地验证检查。它是可复核的验证记录，不是大规模 benchmark。

## Validation Scope / 验证范围

Validated components:

已验证组件：

- Project documentation consistency
- 项目文档一致性
- Manual evaluation template generation
- 手动评测模板生成
- JSON evaluation question schema
- JSON 评测问题结构
- Unit and integration tests
- 单元测试与集成测试
- CI configuration for offline-friendly tests
- 面向离线测试的 CI 配置

Not validated as completed experiment runs:

未验证为已完成实验运行的内容：

- Real model training
- 真实模型训练
- Dataset download and preprocessing for third-party repositories
- 第三方仓库的数据集下载与预处理
- Hardware-specific reproduction speed or final metrics
- 与硬件相关的复现速度或最终指标

## Environment / 环境

| Item | Value |
| --- | --- |
| Date | 2026-06-17 |
| Local environment | `researchflow` |
| Python | 3.11.x in the local conda environment |
| Test command | `conda run -n researchflow pytest tests` |
| Network requirement | No network required for tests |
| API key requirement | No API key required for tests |

## Commands Executed / 已执行命令

```bash
conda run -n researchflow pytest tests
```

Result:

结果：

```text
48 passed
```

```bash
conda run -n researchflow python scripts/run_manual_evaluation_template.py --output-dir /tmp/researchflow-manual-eval-check
```

Result:

结果：

```text
Rows: 25
```

```bash
python3 -m json.tool examples/paper_eval_questions.json
```

Result:

结果：

```text
Valid JSON
```

## Manual Evaluation Template Check / 手动评测模板检查

The manual evaluation script reads `examples/paper_eval_questions.json` and generates Markdown and CSV files without calling an LLM, reading API keys, or using the network.

手动评测脚本读取 `examples/paper_eval_questions.json`，并在不调用 LLM、不读取 API key、不联网的情况下生成 Markdown 和 CSV 文件。

Observed output:

观察结果：

| Check | Result |
| --- | --- |
| Number of paper samples | 5 |
| Questions per paper | 5 |
| Total questions | 25 |
| Markdown output | Generated successfully |
| CSV output | Generated successfully |
| LLM dependency | Not required |
| API key dependency | Not required |
| Network dependency | Not required |

## Evaluation Dataset Template Check / 评测数据模板检查

`examples/paper_eval_questions.json` contains five paper-oriented evaluation samples. Each sample includes exactly five questions covering:

`examples/paper_eval_questions.json` 包含五组面向论文的评测样例。每组样例都包含五个问题，覆盖：

- method
- dataset
- metric
- result
- limitation

Each question includes:

每个问题都包含：

- `question_id`
- `question`
- `question_type`
- `expected_evidence_type`
- `scoring_note`

## Documentation Consistency Check / 文档一致性检查

The public documentation now uses the same project positioning:

公开文档已经统一为以下项目定位：

> ResearchFlow-Agent is an AI Agent system for research workflows, supporting paper reading, repository analysis, experiment reproduction planning, technical report generation, and evidence verification.

> ResearchFlow-Agent 是一个面向科研工作流的 AI Agent 系统，支持论文阅读、代码仓库分析、实验复现规划、技术报告生成和证据核验。

The documentation also states the current limitations:

文档也明确说明了当前局限：

- The system does not automatically run real training experiments.
- 系统不会自动运行真实训练实验。
- Verifier provides evidence attribution and uncertainty classification, but does not guarantee factual correctness.
- Verifier 提供证据归因和不确定性分类，但不保证事实正确。
- Evaluation templates require human review.
- 评测模板仍需要人工复核。
- Hashing fallback may reduce retrieval quality compared with semantic embeddings.
- 与真实语义 embedding 相比，hashing fallback 可能降低检索质量。

## Recommended Real-Case Validation / 建议的真实案例验证

For a stronger validation record, run the following manual checks with locally downloaded papers and public repositories:

如需更强的验证记录，建议使用本地下载的论文和公开代码仓库执行以下人工检查：

| Area | Suggested Check | Human Review Focus |
| --- | --- | --- |
| Paper QA | Ask method, dataset, metric, result, and limitation questions. | Whether answers cite the correct page snippets. |
| Citation quality | Compare displayed snippets with the original PDF viewer. | Whether parser page numbers match the PDF viewer. |
| Repository analysis | Analyze README, dependency files, model files, and training scripts. | Whether the summary is grounded in actual file contents. |
| Experiment planning | Generate a reproduction plan from paper and code context. | Whether setup, dataset, training, and evaluation steps are actionable. |
| Verifier | Run Verifier on generated summaries and plans. | Whether unsupported claims and uncertain statements are flagged. |

## Conclusion / 结论

The current repository passes local tests and can generate offline manual evaluation artifacts. The validation record supports project stability at the software-workflow level, while real scientific claims, reproduction metrics, and third-party repository execution still require human review.

当前仓库通过了本地测试，并能生成离线手动评测文件。该验证记录支持软件工作流层面的稳定性判断；真实科研结论、复现指标和第三方仓库运行结果仍需要人工复核。
