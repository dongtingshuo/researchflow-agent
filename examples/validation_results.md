# Validation Results

# 验证结果

These results summarize the real-paper smoke tests used to validate the current RAG pipeline.

本文档总结用于验证当前 RAG 流程的真实论文 smoke tests。

## Environment / 环境

- Python environment: `researchflow`
- Python 环境：`researchflow`
- Embedding: `sentence-transformers/all-MiniLM-L6-v2`
- Embedding 模型：`sentence-transformers/all-MiniLM-L6-v2`
- Reranker: `cross-encoder/ms-marco-MiniLM-L-6-v2`
- Reranker 模型：`cross-encoder/ms-marco-MiniLM-L-6-v2`
- LLM provider: OpenAI-compatible API
- LLM 提供方：OpenAI-compatible API
- Test command: real PDF indexing plus end-to-end QA through `PaperRAGService`
- 测试方式：通过 `PaperRAGService` 对真实 PDF 建索引并进行端到端问答

## Results / 结果

| Case | Question | Expected Answer | Observed Result | Evidence Check |
| --- | --- | --- | --- | --- |
| CLIP | How many image-text pairs were used to train CLIP? | 400 million image-text pairs | Answer included `400 million`; top citation was Page 2. | Source snippet contained `400 million (image, text) pairs`. |
| ReAct | Which tasks or benchmarks are used in ReAct? | HotPotQA, Fever, ALFWorld, WebShop | Answer preserved the named benchmarks. | Source snippets cited Pages 1 and 3. |
| RAG | What are the two RAG formulations? | RAG-Sequence and RAG-Token | Answer named both formulations and explained same-document vs different-document behavior. | Source snippets cited Pages 1 and 3. |

| 案例 | 问题 | 预期答案 | 观察结果 | 证据检查 |
| --- | --- | --- | --- | --- |
| CLIP | 训练 CLIP 使用了多少 image-text pairs？ | 400 million image-text pairs | 回答包含 `400 million`，Top-1 引用为 Page 2。 | 原文片段包含 `400 million (image, text) pairs`。 |
| ReAct | ReAct 使用了哪些任务或 benchmark？ | HotPotQA、Fever、ALFWorld、WebShop | 回答保留了原始 benchmark 名称。 | 原文片段引用 Pages 1 和 3。 |
| RAG | 两种 RAG formulation 是什么？ | RAG-Sequence 和 RAG-Token | 回答列出两种 formulation，并解释 same-document 与 different-document 区别。 | 原文片段引用 Pages 1 和 3。 |

## Remaining Manual Checks / 仍需人工核对

- Verify PDF page numbering against the original viewer for each uploaded PDF.
- 对每个上传 PDF，应与原始阅读器核对页码。
- Confirm code-repository run commands before claiming a reproduction run is complete.
- 在确认复现实验完成前，应人工核对代码仓库运行命令。
- Use the Verifier output to mark missing dataset, checkpoint, metric, or hardware evidence.
- 使用 Verifier 输出标注缺失的数据集、checkpoint、指标或硬件证据。
