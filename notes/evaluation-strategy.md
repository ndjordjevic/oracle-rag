# Oracle-RAG Evaluation Strategy

This document defines how we evaluate oracle-rag as we add, optimise, and improve features.
Evaluation is built on **LangSmith** — datasets, `client.evaluate()`, and LLM-as-judge evaluators.

---

## 1. Why evaluate?

Every change to the RAG pipeline (chunking, re-ranking, embedding model, prompt, etc.) can
regress one dimension while improving another. Without a baseline you can only "vibe check."

An evaluation framework gives us:

- **A baseline** to compare against before/after any change.
- **Quantified trade-offs** — e.g. re-ranking improves precision but adds latency and cost.
- **Regression safety net** — automated checks that flag regressions.
- **Confidence to ship** — data-backed decisions instead of guessing.

---

## 2. What we evaluate — four RAG dimensions

| # | Dimension | What is compared | Needs reference? |
|---|-----------|-----------------|------------------|
| 1 | **Correctness** | Response vs reference answer | Yes |
| 2 | **Relevance** | Response vs input question | No |
| 3 | **Groundedness** | Response vs retrieved chunks | No |
| 4 | **Retrieval relevance** | Retrieved chunks vs input question | No |

Plus three code-based checks (no LLM cost):

| Evaluator | What it checks |
|-----------|---------------|
| `has_sources` | Answer includes at least one source citation |
| `answer_not_empty` | Answer is not blank or an error message |
| `source_in_expected_docs` | At least one returned source matches expected document IDs |

---

## 3. Dataset

**Dataset name:** `oracle-rag-golden` (in LangSmith)
**Size:** 30 examples

### Example structure

```json
{
  "inputs": {
    "question": "What is OpenOCD and how is it used with Pico?",
    "document_id": "RP-008276-DS-1-getting-started-with-pico.pdf",
    "tag": "PI_PICO"
  },
  "outputs": {
    "answer": "OpenOCD is an open-source on-chip debugger that ...",
    "expected_document_ids": ["RP-008276-DS-1-getting-started-with-pico.pdf"],
    "expected_pages": [15, 16]
  }
}
```

Fields `document_id` and `tag` in inputs are optional — when present they are passed to
`create_retriever()` as metadata filters so retrieval is scoped to that document/channel.

---

## 4. Evaluator implementations

All evaluators live in `src/oracle_rag/evaluation/evaluators.py`.
LLM-as-judge graders use **gpt-4o-mini** and require `OPENAI_API_KEY`.

### 4.1 Correctness

Compares `outputs["answer"]` to `reference_outputs["answer"]` using an LLM judge.
Returns `score: 1` if factually correct, `score: 0` otherwise.

### 4.2 Relevance

Compares `outputs["answer"]` to `inputs["question"]` (reference-free).
Returns `score: 1` if the answer addresses the question.

### 4.3 Groundedness

Compares `outputs["answer"]` to `outputs["documents"]` (the retrieved chunks).
Returns `score: 1` if the answer is supported by the retrieved context (no hallucination).

### 4.4 Retrieval relevance

Compares `outputs["documents"]` to `inputs["question"]`.
Returns `score: 1` if the retrieved chunks are relevant to the question.

---

## 5. Target function

`src/oracle_rag/evaluation/target.py` — `oracle_rag_target(inputs) -> dict`

1. Reads `question`, `document_id`, `tag`, `page_min`, `page_max` from dataset inputs.
2. Calls `create_retriever(k=10, ...)` with any metadata filters.
3. Calls `run_rag(question, llm, retriever=retriever)`.
4. Returns `{"answer": ..., "sources": [...], "documents": [...]}`.

The `documents` list is the raw retrieved chunks — needed by groundedness and retrieval
relevance evaluators. The `sources` list is the deduplicated source metadata returned
by `run_rag`.

> **Note:** The target always uses `k=10`. If `ORACLE_RAG_USE_RERANK=true` is set in `.env`,
> `run_rag` will apply Cohere re-ranking on top, reducing chunks to `ORACLE_RAG_RERANK_TOP_N`
> (default 5) before passing to the LLM. To evaluate re-ranking, set that env var before running.

---

## 6. Running an evaluation experiment

```bash
# From oracle-rag project root:
uv run python -m oracle_rag.evaluation \
  --dataset oracle-rag-golden \
  --prefix oracle-rag-baseline \
  --limit 30 \
  --metadata '{"version":"3.0.1","rerank":"false"}'
```

All CLI options:

| Flag | Default | Description |
|------|---------|-------------|
| `--dataset` | `oracle-rag-golden` | LangSmith dataset name |
| `--prefix` | `oracle-rag-baseline` | Experiment name prefix |
| `--limit N` | all | Max examples to run (use 30 for full golden set) |
| `--metadata '{...}'` | none | JSON metadata attached to the experiment |

Results are visible at [smith.langchain.com](https://smith.langchain.com/) under the
`oracle-rag` project.

### Before/after workflow

1. Run baseline experiment → record scores.
2. Implement the change (re-ranking, new prompt, etc.).
3. Re-run with a different `--prefix` (e.g. `oracle-rag-rerank`).
4. Compare side-by-side in LangSmith.

---

## 7. Evaluation gates / thresholds

| Metric | Initial gate | Target gate |
|--------|-------------|-------------|
| Correctness | >= 0.6 | >= 0.8 |
| Relevance | >= 0.7 | >= 0.9 |
| Groundedness | >= 0.8 | >= 0.9 |
| Retrieval relevance | >= 0.6 | >= 0.8 |
| has_sources | == 1.0 | == 1.0 |
| answer_not_empty | == 1.0 | == 1.0 |

---

## 8. Baseline results

Experiment: `oracle-rag-baseline-29f537be`
Config: `version=3.0.1`, `rerank=true`, `collection=oracle_rag`, `embedding=openai/text-embedding-3-small`, `llm=openai/gpt-4o-mini`
Dataset: `oracle-rag-golden` (30 examples)
Date: 2026-01-26

| Metric | Score | n | Notes |
|--------|-------|---|-------|
| correctness | 0.500 | 30 | LLM-as-judge vs reference answers |
| relevance | 0.900 | 30 | Reference-free; answer addresses question |
| groundedness | 0.967 | 30 | Answer supported by retrieved chunks |
| retrieval_relevance | 0.967 | 30 | Retrieved chunks relevant to question |
| has_sources | 1.000 | 30 | All answers include source citations |
| answer_not_empty | 1.000 | 30 | No blank or error answers |
| source_in_expected_docs | 1.000 | 30 | Source doc IDs match expected |

View in LangSmith: https://eu.smith.langchain.com/o/2f856061-2221-4d62-8edd-5996160a1943/datasets/0afddd1c-2722-4849-9416-7b8e188cfee1/compare?selectedSessions=ebc46a04-b217-4d69-940b-5d77ed8d9653
