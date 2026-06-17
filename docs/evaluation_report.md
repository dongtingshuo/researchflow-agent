# Evaluation Report

## Evaluation Goal

The evaluation goal is to check whether ResearchFlow-Agent outputs are reviewable, evidence-supported, and easy for humans to inspect. The evaluation focuses on paper QA, citation quality, repository analysis, experiment planning, and Verifier uncertainty classification.

评测目标是检查 ResearchFlow-Agent 的输出是否可复核、是否有证据支持、是否便于人工检查。评测重点包括论文问答、引用质量、仓库分析、实验规划和 Verifier 不确定性分类。

## Evaluation Modes

The evaluation compares three modes:

1. Ordinary RAG
2. Agent Workflow
3. Agent Workflow + Verifier

评测比较三种模式：

1. 普通 RAG
2. Agent Workflow
3. Agent Workflow + Verifier

## Evaluation Dataset Design

The recommended evaluation set contains 5 papers. Each paper contains 5 questions, for a total of 25 questions.

建议评测集包含 5 篇论文。每篇论文包含 5 个问题，总计 25 个问题。

Each paper should include the following question types:

每篇论文应包含以下问题类型：

- method
- dataset
- metric
- result
- limitation

The dataset is a template for repeatable manual evaluation. It does not require downloading a specific PDF in advance, and it does not claim that all questions have already been executed.

该数据集是可重复人工评测模板，不要求预先下载指定 PDF，也不声称所有问题已经完成运行。

## Metrics

| Metric | Scale | Description |
| --- | --- | --- |
| Answer Completeness | 1-5 | Whether the answer covers the expected key points. |
| Citation Correctness | 0/1 or percentage | Whether cited pages and snippets directly support the answer. |
| Unsupported Claim Count | integer | Number of claims not supported by paper or code evidence. |
| Reproduction Plan Executability | 1-5 | Whether the plan contains practical environment, data, training, testing, and metric steps. |
| Human Review Notes | text | Manual comments about evidence, uncertainty, missing context, or reproduction risks. |

| 指标 | 分值 | 说明 |
| --- | --- | --- |
| Answer Completeness | 1-5 | 回答是否覆盖预期关键点。 |
| Citation Correctness | 0/1 或百分比 | 引用页码和片段是否直接支持回答。 |
| Unsupported Claim Count | 整数 | 缺少论文或代码证据支持的结论数量。 |
| Reproduction Plan Executability | 1-5 | 计划是否包含可操作的环境、数据、训练、测试和指标步骤。 |
| Human Review Notes | 文本 | 关于证据、不确定性、缺失上下文或复现风险的人工备注。 |

## Result Table Template

| paper_id | question_id | question_type | ordinary_rag_answer | agent_answer | agent_verifier_answer | answer_completeness_score | citation_correctness | unsupported_claim_count | reproduction_plan_executability_score | human_notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| paper_001 | paper_001_method | method |  |  |  |  |  |  |  |  |
| paper_001 | paper_001_dataset | dataset |  |  |  |  |  |  |  |  |
| paper_001 | paper_001_metric | metric |  |  |  |  |  |  |  |  |
| paper_001 | paper_001_result | result |  |  |  |  |  |  |  |  |
| paper_001 | paper_001_limitation | limitation |  |  |  |  |  |  |  |  |

## Sample Result

This is a sample result. It is not a large-scale benchmark. It should be manually verified.

这是一个示例结果。它不是大规模 benchmark。该结果应由人工复核。

| paper_id | question_id | question_type | ordinary_rag_answer | agent_answer | agent_verifier_answer | answer_completeness_score | citation_correctness | unsupported_claim_count | reproduction_plan_executability_score | human_notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| clip_example | clip_method | method | The model uses contrastive language-image pre-training with cited paper snippets. | The workflow adds repository analysis and an experiment plan. | The verifier marks paper evidence and missing reproduction evidence separately. | 4 | 1 | 1 | 3 | Check exact page number against the original PDF viewer. |

## Limitations

- Evaluation still requires human review.
- Verifier classifies evidence, inference, and uncertainty, but does not guarantee factual correctness.
- The system does not automatically run real training experiments.
- Reproduction plans must be checked before use.
- If hashing fallback is used, retrieval quality may be weaker than real semantic embeddings.

## 局限性

- 评测仍然需要人工复核。
- Verifier 会分类证据、推断和不确定性，但不保证事实完全正确。
- 系统不会自动运行真实训练实验。
- 复现计划在使用前必须检查。
- 如果使用 hashing fallback，检索质量可能弱于真实语义 embedding。
