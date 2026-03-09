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

**Multi-query stress dataset:** `oracle-rag-multiquery-stress` (15 examples) — terse or incomplete phrases from "Bare-metal Amiga programming 2021_ocr.pdf" (e.g. "cookie cut blitter operation", "Copper danger bit lower registers"). Questions are short but have enough semantic content for query expansion to help; bare 1–2 word acronyms (e.g. "BPLCON3") are avoided because multi-query often hurts those. Use to measure improvement from `ORACLE_RAG_USE_MULTI_QUERY=true`. Create or overwrite with `uv run python scripts/create_multiquery_stress_dataset.py` (use `--force` to replace an existing dataset).

### Example structure

```json
{
  "inputs": {
    "question": "What is OpenOCD and how is it used with Pico?"
  },
  "outputs": {
    "answer": "OpenOCD is an open-source on-chip debugger that ...",
    "expected_document_ids": ["RP-008276-DS-1-getting-started-with-pico.pdf"],
    "expected_pages": [15, 16]
  }
}
```

Inputs contain only `question` — retrieval is unfiltered (no `document_id` or `tag`).
`expected_document_ids` in outputs is used by the `source_in_expected_docs` evaluator.

---

## 4. Evaluator implementations

All evaluators live in `src/oracle_rag/evaluation/evaluators.py`.
LLM-as-judge graders require `OPENAI_API_KEY`. **gpt-4o** is used for `correctness` and `relevance` (consistent grading of technical synonyms); **gpt-4o-mini** is used for `groundedness` and `retrieval_relevance` (context-heavy, would hit gpt-4o TPM limits at k=30–40).

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

1. Reads `question`, `document_id`, `page_min`, `page_max` from dataset inputs.
2. Calls `run_rag(question, llm, retriever=None, ...)` so the chain builds the retriever internally.
3. Returns `{"answer": ..., "sources": [...], "documents": [...]}`.

The `documents` list is the raw retrieved chunks — needed by groundedness and retrieval
relevance evaluators. The `sources` list is the deduplicated source metadata returned
by `run_rag`.

> **Note:** `k` comes from `ORACLE_RAG_RETRIEVE_K` (default 10). When rerank is on, `ORACLE_RAG_RERANK_RETRIEVE_K` can override the pre-rerank fetch count; `ORACLE_RAG_RERANK_TOP_N` (default 5) sets chunks passed to the LLM.

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

### Multi-query stress comparison

To compare single-query vs multi-query on the stress dataset (rerank off):

```bash
ORACLE_RAG_USE_RERANK=false ORACLE_RAG_USE_MULTI_QUERY=false uv run python -m oracle_rag.evaluation --dataset oracle-rag-multiquery-stress --prefix oracle-rag-mq-off --limit 20
ORACLE_RAG_USE_RERANK=false ORACLE_RAG_USE_MULTI_QUERY=true  uv run python -m oracle_rag.evaluation --dataset oracle-rag-multiquery-stress --prefix oracle-rag-mq-on  --limit 20
```

Compare correctness (and cost, in LangSmith) between the two experiments.

To compare **response style** (thorough vs concise), set `ORACLE_RAG_RESPONSE_STYLE` and use distinct prefixes:

```bash
ORACLE_RAG_RESPONSE_STYLE=thorough uv run python -m oracle_rag.evaluation --dataset oracle-rag-golden --prefix thorough --limit 30
ORACLE_RAG_RESPONSE_STYLE=concise uv run python -m oracle_rag.evaluation --dataset oracle-rag-golden --prefix concise --limit 30
```

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

## 8. Experiment results

**Setup:** Embedding text-embedding-3-small, collection `oracle_rag`. Judge: gpt-4o (correctness/relevance), gpt-4o-mini (groundedness/retrieval_relevance).

Early runs showed correctness improves with k and with prompt/ref-answer fixes; the judge was set to gpt-4o for correctness/relevance to grade technical answers consistently. Min-k sweep on `oracle-rag-golden` (30 Qs): all questions pass with **k=10** (two need k=10, rest k=5).

### Rerank and no-rerank (hard-10 and golden)

| LLM | Config | hard-10 | golden (30) |
|-----|--------|---------|-------------|
| claude-haiku-4-5 | rerank k=20→top_n=10 | 10/10 | 30/30 |
| claude-haiku-4-5 | rerank k=30→top_n=10 | 10/10 | — |
| claude-haiku-4-5 | rerank k=40→top_n=15 | 10/10 | 30/30 |
| gpt-4o-mini | k=10, no rerank | — | 30/30 |
| gpt-4o-mini | k=30, no rerank | 10/10 | — |

**Recommended:** Rerank on → k=20, top_n=10 with claude-haiku-4-5. Rerank off → k=10 (or 30 if you prefer a single safe value). For terse or incomplete user queries, enable multi-query (`ORACLE_RAG_USE_MULTI_QUERY=true`); on the multiquery-stress set it improves correctness with ~12% higher LLM cost. See `config.py` and `implementation-checklist.md` (Re-ranking, Query translation / multi-query).

### Multi-query and rerank (oracle-rag-multiquery-stress, 15 examples)

Runs: rerank off; LLM and embedding as in §8. Same evaluators.

| Config | Correctness | Cost (15 ex.) | Cost/example |
|--------|-------------|---------------|--------------|
| MQ off, rerank off | 11/15 (73%) | ~$0.057 | ~$0.0038 |
| **MQ on, rerank off** | **12/15 (80%)** | ~$0.064 | ~$0.0042 |
| MQ on, rerank on | 11/15 (73%) | ~$0.065 | ~$0.0043 |

**Findings:**

- Multi-query alone gives the best correctness on this stress set (+1 question vs baseline). Cost increase is ~12% (~+208 tokens/example for query expansion).
- With both MQ and rerank on, correctness drops back to 11/15: rerank recovers one question (CIA TOD) but demotes the right chunks for two others (cookie cut blitter, sprite DMA), so the model no longer sees the best passage. On this dataset the best config is **MQ on, rerank off**.
- Cost above is target (RAG) LLM only; evaluator LLM calls and Cohere rerank are not included.

### Datasets

| Dataset | Size | Use |
|---------|------|-----|
| `oracle-rag-golden` | 30 | Full regression |
| `oracle-rag-hard-10` | 10 | Fast tuning (~3 min/run) |
| `oracle-rag-multiquery-stress` | 15 | Multi-query vs single-query; terse phrases, same doc as golden |
