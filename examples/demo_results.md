# Demo Results

These results summarize the real-paper smoke tests used to validate the current RAG pipeline.

## Environment

- Python environment: `researchflow`
- Embedding: `sentence-transformers/all-MiniLM-L6-v2`
- Reranker: `cross-encoder/ms-marco-MiniLM-L-6-v2`
- LLM provider: OpenAI-compatible API
- Test command: real PDF indexing plus end-to-end QA through `PaperRAGService`

## Results

| Case | Question | Expected Answer | Observed Result | Evidence Check |
| --- | --- | --- | --- | --- |
| CLIP | How many image-text pairs were used to train CLIP? | 400 million image-text pairs | Answer included `400 million`; top citation was Page 2. | Source snippet contained `400 million (image, text) pairs`. |
| ReAct | Which tasks or benchmarks are used in ReAct? | HotPotQA, Fever, ALFWorld, WebShop | Answer preserved the named benchmarks. | Source snippets cited Pages 1 and 3. |
| RAG | What are the two RAG formulations? | RAG-Sequence and RAG-Token | Answer named both formulations and explained same-document vs different-document behavior. | Source snippets cited Pages 1 and 3. |

## Remaining Manual Checks

- Verify PDF page numbering against the original viewer for each uploaded PDF.
- Confirm code-repository run commands manually before claiming successful reproduction.
- Use the Verifier output to mark missing dataset, checkpoint, metric, or hardware evidence.
