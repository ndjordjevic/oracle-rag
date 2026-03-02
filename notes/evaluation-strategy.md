# Oracle-RAG Evaluation Strategy

This document defines how we evaluate oracle-rag as we add, optimise, and improve features.
It covers **what** to measure, **how** to measure it, **when** to run evaluations, and the
concrete implementation plan. All evaluation is built on **LangSmith** (datasets, `evaluate()`,
LLM-as-judge, online evaluators) so results live next to traces we already collect.

---

## 1. Why evaluate before changing retrieval / generation?

Every change to the RAG pipeline (new chunking strategy, multi-query, re-ranking, different
embedding model, prompt rewrite, etc.) can *regress* one dimension while improving another.
Without a baseline you can only "vibe check."

An evaluation framework gives us:

- **A baseline** to compare against before/after any change.
- **Quantified trade-offs** — e.g. multi-query improves recall but adds latency and cost.
- **Regression safety net** — automated checks that flag regressions in nightly / CI runs.
- **Confidence to ship** — data-backed decisions instead of guessing.

This is why the implementation checklist puts evaluation *before* advanced retrieval strategies.

---

## 2. What to evaluate — the four RAG dimensions

A RAG system has two moving parts: **retrieval** and **generation**. Each can be evaluated
in isolation and together. LangSmith's official RAG tutorial defines four evaluator types
that map to these parts:

| # | Dimension | What is compared | Needs reference? | Goal |
|---|-----------|-----------------|-------------------|------|
| 1 | **Correctness** | Response vs reference answer | Yes | Is the answer factually right? |
| 2 | **Relevance** | Response vs input question | No | Does the answer address the question? |
| 3 | **Groundedness** (faithfulness) | Response vs retrieved chunks | No | Is the answer supported by evidence? |
| 4 | **Retrieval relevance** | Retrieved chunks vs input question | No | Are the retrieved docs relevant? |

### 2.1 Retrieval metrics (what the retriever returns)

| Metric | What it measures | How we compute it |
|--------|-----------------|-------------------|
| **Retrieval relevance** | Are the top-k chunks related to the question? | LLM-as-judge: pass retrieved docs + question, grade relevant/not |
| **Context precision@k** | What fraction of retrieved chunks are actually relevant? | LLM-as-judge per chunk, average over dataset |
| **Context recall** | Does retrieval cover the evidence needed for the reference answer? | LLM-as-judge: can the reference answer be derived from the chunks? |
| **Hit@k** | Is there at least one relevant chunk in top-k? | Boolean per example |

### 2.2 Generation metrics (what the LLM produces)

| Metric | What it measures | How we compute it |
|--------|-----------------|-------------------|
| **Correctness** | Factual accuracy vs reference answer | LLM-as-judge with structured output (bool) |
| **Relevance** | Does the answer address the user's intent? | LLM-as-judge (reference-free) |
| **Groundedness / faithfulness** | Is the answer grounded in the retrieved context? | LLM-as-judge: facts from chunks vs answer |
| **Conciseness** | Is the answer appropriately concise? | Code evaluator: `len(output) < threshold` or LLM-as-judge |

---

## 3. Evaluation dataset design

### 3.1 Golden dataset structure

Each example in the dataset has:

```
{
  "inputs": {
    "question": "What is OpenOCD and how is it used with Pico?",
    "document_id": "RP-008276-DS-1-getting-started-with-pico.pdf",  // optional filter
    "tag": "PI_PICO"                                                 // optional filter
  },
  "outputs": {
    "answer": "OpenOCD is an open-source on-chip debugger that ...",  // reference answer
    "expected_document_ids": ["RP-008276-DS-1-getting-started-with-pico.pdf"],
    "expected_pages": [15, 16]                                       // optional: expected source pages
  }
}
```

### 3.2 Dataset categories (split labels)

| Split | Purpose | Size |
|-------|---------|------|
| `golden` | Expert-curated, high-confidence pairs for calibrating LLM judges | 5–10 examples |
| `general` | Broader coverage across indexed documents | 15–30 examples |
| `filtered` | Questions with metadata filters (document_id, tag, page range) | 5–10 examples |
| `edge-cases` | Adversarial / out-of-scope / ambiguous queries | 5–10 examples |
| `multi-doc` | Questions that require information from multiple documents | 5–10 examples |

### 3.3 How to build the dataset

**Phase 1 — Manual curation (start here):**
1. For each indexed PDF, write 2–3 question/answer pairs where you know the answer and the page.
2. Include questions of varying difficulty (factual lookup, synthesis, comparison).
3. Include at least 2–3 questions that should *fail* (no relevant content in RAG).
4. Upload to LangSmith via SDK:

```python
from langsmith import Client

client = Client()
dataset = client.create_dataset(
    "oracle-rag-golden",
    description="Golden evaluation dataset for oracle-rag pipeline"
)
client.create_examples(dataset_id=dataset.id, examples=[...])
```

**Phase 2 — Production-trace bootstrapping:**
1. Use LangSmith automation rules to capture high-quality production traces.
2. Filter by positive user feedback or high online-evaluator scores.
3. Add to dataset via `client.create_examples()` or LangSmith UI annotation queue.

**Phase 3 — Synthetic augmentation:**
1. For each document, use an LLM to generate question/answer pairs from chunks.
2. Human-review generated pairs before adding to dataset.

---

## 4. Evaluator implementations

### 4.1 Correctness (response vs reference)

```python
from typing_extensions import Annotated, TypedDict
from langchain_openai import ChatOpenAI

class CorrectnessGrade(TypedDict):
    explanation: Annotated[str, ..., "Step-by-step reasoning"]
    correct: Annotated[bool, ..., "True if factually correct"]

CORRECTNESS_PROMPT = """You are a teacher grading a quiz.
QUESTION: {question}
GROUND TRUTH ANSWER: {reference}
STUDENT ANSWER: {answer}

Grade based ONLY on factual accuracy relative to ground truth.
It is OK if the student answer has more information, as long as it is accurate.
Explain your reasoning step by step."""

grader_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0).with_structured_output(
    CorrectnessGrade, method="json_schema", strict=True
)

def correctness(inputs: dict, outputs: dict, reference_outputs: dict) -> bool:
    grade = grader_llm.invoke([
        {"role": "system", "content": CORRECTNESS_PROMPT.format(
            question=inputs["question"],
            reference=reference_outputs["answer"],
            answer=outputs["answer"],
        )}
    ])
    return grade["correct"]
```

### 4.2 Relevance (response vs question, reference-free)

```python
class RelevanceGrade(TypedDict):
    explanation: Annotated[str, ..., "Step-by-step reasoning"]
    relevant: Annotated[bool, ..., "True if answer addresses the question"]

RELEVANCE_PROMPT = """You are a teacher grading a quiz.
QUESTION: {question}
STUDENT ANSWER: {answer}

Is the answer concise, relevant, and helpful for the question?
Explain your reasoning step by step."""

relevance_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0).with_structured_output(
    RelevanceGrade, method="json_schema", strict=True
)

def relevance(inputs: dict, outputs: dict) -> bool:
    grade = relevance_llm.invoke([
        {"role": "system", "content": RELEVANCE_PROMPT.format(
            question=inputs["question"],
            answer=outputs["answer"],
        )}
    ])
    return grade["relevant"]
```

### 4.3 Groundedness / faithfulness (response vs retrieved docs)

```python
class GroundednessGrade(TypedDict):
    explanation: Annotated[str, ..., "Step-by-step reasoning"]
    grounded: Annotated[bool, ..., "True if no hallucination beyond the facts"]

GROUNDEDNESS_PROMPT = """You are a teacher grading a quiz.
FACTS (retrieved documents):
{context}

STUDENT ANSWER: {answer}

Is the answer grounded in the FACTS? Does it hallucinate information not in FACTS?
Explain your reasoning step by step."""

grounded_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0).with_structured_output(
    GroundednessGrade, method="json_schema", strict=True
)

def groundedness(inputs: dict, outputs: dict) -> bool:
    context = "\n\n".join(doc.page_content for doc in outputs["documents"])
    grade = grounded_llm.invoke([
        {"role": "system", "content": GROUNDEDNESS_PROMPT.format(
            context=context,
            answer=outputs["answer"],
        )}
    ])
    return grade["grounded"]
```

### 4.4 Retrieval relevance (retrieved docs vs question)

```python
class RetrievalRelevanceGrade(TypedDict):
    explanation: Annotated[str, ..., "Step-by-step reasoning"]
    relevant: Annotated[bool, ..., "True if retrieved docs are relevant"]

RETRIEVAL_RELEVANCE_PROMPT = """You are a teacher grading a quiz.
QUESTION: {question}
FACTS (retrieved documents):
{context}

Are the FACTS relevant to the QUESTION? It is OK if some facts are tangential as long
as they contain keywords or semantic meaning related to the question.
Explain your reasoning step by step."""

retrieval_relevance_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0).with_structured_output(
    RetrievalRelevanceGrade, method="json_schema", strict=True
)

def retrieval_relevance(inputs: dict, outputs: dict) -> bool:
    context = "\n\n".join(doc.page_content for doc in outputs["documents"])
    grade = retrieval_relevance_llm.invoke([
        {"role": "system", "content": RETRIEVAL_RELEVANCE_PROMPT.format(
            question=inputs["question"],
            context=context,
        )}
    ])
    return grade["relevant"]
```

### 4.5 Code-based evaluators (no LLM cost)

```python
def has_sources(inputs: dict, outputs: dict) -> bool:
    """Answer includes at least one source citation."""
    return len(outputs.get("sources", [])) > 0

def answer_not_empty(inputs: dict, outputs: dict) -> bool:
    """Answer is not empty or a failure message."""
    answer = outputs.get("answer", "")
    return bool(answer.strip()) and "failed" not in answer.lower()

def source_in_expected_docs(inputs: dict, outputs: dict, reference_outputs: dict) -> bool:
    """At least one source document_id matches expected documents."""
    expected = set(reference_outputs.get("expected_document_ids", []))
    if not expected:
        return True
    actual = {s.get("document_id") for s in outputs.get("sources", [])}
    return bool(actual & expected)
```

---

## 5. Target function — adapting oracle-rag for evaluation

The LangSmith `evaluate()` function needs a **target** that takes dataset inputs and returns
outputs. We need to adapt `run_rag` to return both the answer and the retrieved documents
(for groundedness and retrieval relevance evaluators).

```python
from oracle_rag.rag import run_rag
from oracle_rag.llm import get_chat_model
from oracle_rag.embeddings import get_embedding_model
from oracle_rag.vectorstore.retriever import create_retriever

def oracle_rag_target(inputs: dict) -> dict:
    """Target function for LangSmith evaluate().

    Accepts dataset inputs, runs oracle-rag pipeline, returns answer + docs + sources.
    """
    question = inputs["question"]
    document_id = inputs.get("document_id")
    tag = inputs.get("tag")
    page_min = inputs.get("page_min")
    page_max = inputs.get("page_max")

    llm = get_chat_model()
    retriever = create_retriever(
        k=5,
        document_id=document_id,
        page_min=page_min,
        page_max=page_max,
        tag=tag,
    )

    docs = retriever.invoke(question)
    result = run_rag(question, llm, retriever=retriever)

    return {
        "answer": result.answer,
        "sources": result.sources,
        "documents": docs,
    }
```

### Running an experiment

```python
from langsmith import Client

client = Client()

experiment_results = client.evaluate(
    oracle_rag_target,
    data="oracle-rag-golden",
    evaluators=[
        correctness,
        relevance,
        groundedness,
        retrieval_relevance,
        has_sources,
        answer_not_empty,
        source_in_expected_docs,
    ],
    experiment_prefix="oracle-rag-baseline-v3.0.1",
    metadata={"version": "3.0.1", "llm": "anthropic", "embedding": "cohere"},
)
```

---

## 6. Evaluation workflow — when to run

### 6.1 Before/after any pipeline change (offline, manual)

This is the most important workflow. Before implementing multi-query, re-ranking, or any
retrieval change:

1. **Run baseline experiment** on the golden dataset with current pipeline → record scores.
2. **Implement the change.**
3. **Run the same experiment** with the updated pipeline → compare scores side-by-side in LangSmith.
4. **Decide**: if metrics improve (or hold steady) → ship. If they regress → investigate.

```
┌─────────────┐     ┌──────────────┐     ┌──────────────────┐
│  Golden      │────▶│  evaluate()  │────▶│  Experiment A    │
│  Dataset     │     │  baseline    │     │  (scores)        │
└─────────────┘     └──────────────┘     └──────────────────┘
                                                │
                                         ┌──────▼───────┐
                                         │   Implement   │
                                         │   change      │
                                         └──────┬───────┘
                                                │
┌─────────────┐     ┌──────────────┐     ┌──────▼──────────┐
│  Same        │────▶│  evaluate()  │────▶│  Experiment B    │
│  Dataset     │     │  with change │     │  (compare)       │
└─────────────┘     └──────────────┘     └──────────────────┘
```

### 6.2 Pairwise comparison

LangSmith supports **pairwise experiments** for direct A/B comparison:

```python
from langsmith import Client

client = Client()

client.evaluate(
    ("experiment-A-id", "experiment-B-id"),
    evaluators=[pairwise_preference_evaluator],
)
```

Use this when comparing two retrieval strategies (e.g. vanilla vs multi-query) on the
same dataset.

### 6.3 Online evaluation (production monitoring)

Once the evaluation framework is stable, add online evaluators in LangSmith to monitor
live MCP traffic:

1. **Set up LLM-as-judge online evaluator** for relevance (reference-free) on `query_pdf` traces.
2. **Set up code-based online evaluator** for `has_sources` and `answer_not_empty`.
3. **Configure automation rules:**
   - Traces with low relevance scores → add to annotation queue for human review.
   - Traces with errors → extend data retention.
   - 10% sample of all traces → route to human review queue.
4. **Backtesting:** periodically export production traces to dataset, re-evaluate with new pipeline.

### 6.4 CI integration (future)

Once the dataset and evaluators are stable:

1. Add a `pytest` test that runs `client.evaluate()` on a small subset (5 examples).
2. Assert minimum thresholds: `correctness >= 0.8`, `groundedness >= 0.9`.
3. Run in CI on every PR that touches `rag/`, `vectorstore/`, `indexing/`, or `mcp/tools.py`.

---

## 7. Evaluation gates and thresholds

Start with loose gates and tighten as we accumulate data:

| Metric | Initial gate | Target gate | Notes |
|--------|-------------|-------------|-------|
| Correctness | >= 0.6 | >= 0.8 | Requires golden dataset with reference answers |
| Relevance | >= 0.7 | >= 0.9 | Reference-free; should be high from the start |
| Groundedness | >= 0.8 | >= 0.9 | Critical — hallucination prevention |
| Retrieval relevance | >= 0.6 | >= 0.8 | Improves as we add re-ranking, multi-query |
| has_sources | == 1.0 | == 1.0 | Every answer must have sources (except edge cases) |
| answer_not_empty | == 1.0 | == 1.0 | No blank or error answers on golden set |

---

## 8. RAGAS integration (optional, Phase 4+)

RAGAS provides a complementary set of metrics that can run alongside LangSmith evaluators.
Particularly useful for finer-grained retrieval metrics:

```python
from ragas.integrations.langchain import EvaluatorChain
from ragas.metrics import (
    answer_correctness,
    answer_relevancy,
    context_precision,
    context_recall,
    faithfulness,
)

ragas_evaluators = [
    EvaluatorChain(metric)
    for metric in [
        answer_correctness,
        answer_relevancy,
        context_precision,
        context_recall,
        faithfulness,
    ]
]
```

RAGAS requires the target function to return `"answer"` and `"contexts"` (list of strings).
Our target function already returns `"documents"` — we just need a thin adapter.

**When to add RAGAS:** After the core LangSmith evaluators are working and we have a stable
golden dataset. RAGAS adds LLM cost per evaluation (each metric calls the judge LLM), so
start with the four LangSmith evaluators and add RAGAS when needed for deeper retrieval analysis.

---

## 9. Implementation plan

### Step 1: Create golden dataset (manual, ~2 hours)

- [ ] Write 5–10 Q&A pairs from currently indexed PDFs (Pico, Amiga books).
- [ ] Include: 2 factual lookups, 2 synthesis questions, 2 with document_id/tag filters,
      2 edge cases (out-of-scope, ambiguous).
- [ ] Upload to LangSmith as `oracle-rag-golden` dataset.

### Step 2: Implement evaluators and target function (~3 hours)

- [ ] Create `src/oracle_rag/evaluation/` package.
- [ ] Implement `target.py` — the target function wrapping `run_rag`.
- [ ] Implement `evaluators.py` — all four LLM-as-judge evaluators + code evaluators.
- [ ] Implement `run_evaluation.py` — script to run `client.evaluate()` with all evaluators.

### Step 3: Run baseline experiment (~30 min)

- [ ] Run baseline experiment on golden dataset with current v3.0.1 pipeline.
- [ ] Record baseline scores in LangSmith.
- [ ] Document baseline in this file (Section 10).

### Step 4: Validate with a small change (~1 hour)

- [ ] Make a controlled change (e.g. adjust k from 5 to 3, or tweak prompt).
- [ ] Re-run experiment.
- [ ] Verify that LangSmith comparison view shows meaningful difference.
- [ ] Revert the test change.

### Step 5: Integrate into development workflow

- [ ] Before any Phase 4 retrieval change, run baseline.
- [ ] After implementing change, run comparison experiment.
- [ ] Document results per feature (multi-query, re-ranking, etc.).

### Step 6: Online evaluation (after Step 5 is routine)

- [ ] Configure LLM-as-judge online evaluator in LangSmith for `query_pdf` traces.
- [ ] Set up automation rules for low-score traces.
- [ ] Set up annotation queue for human review.

---

## 10. Baseline results

*To be filled after Step 3.*

| Metric | v3.0.1 baseline | Date | Notes |
|--------|----------------|------|-------|
| Correctness | — | — | — |
| Relevance | — | — | — |
| Groundedness | — | — | — |
| Retrieval relevance | — | — | — |
| has_sources | — | — | — |
| answer_not_empty | — | — | — |

---

## 11. References and workspace project patterns

### LangSmith official docs

- [Evaluate a RAG application](https://docs.langchain.com/langsmith/evaluate-rag-tutorial) —
  Full tutorial with correctness, relevance, groundedness, retrieval relevance evaluators.
- [Evaluation concepts](https://docs.langchain.com/langsmith/evaluation-concepts) —
  Offline vs online, evaluator types, dataset management.
- [Code evaluators](https://docs.langchain.com/langsmith/code-evaluator-sdk) —
  Function signatures, return types.
- [Online evaluators](https://docs.langchain.com/langsmith/online-evaluations) —
  LLM-as-judge on production traces.
- [Automation rules](https://docs.langchain.com/langsmith/rules) —
  Filter → sample → action (annotation queue, dataset, webhook).

### Workspace project patterns used

- **`intro-to-langsmith` Module 2** — `evaluate()` with custom evaluators, dataset creation
  via `create_examples()`, summary evaluators (F1), pairwise comparison, LLM-as-judge
  with structured output. Directly applicable pattern for oracle-rag.

- **`langsmith-cookbook/testing-examples/rag_eval`** — Full RAG evaluation with answer
  correctness, hallucination, document relevance evaluators. Uses `run.outputs` to access
  both answer and retrieved docs.

- **`langsmith-cookbook/testing-examples/ragas`** — RAGAS integration via `EvaluatorChain`,
  all five core metrics (answer_correctness, answer_relevancy, context_precision,
  context_recall, faithfulness). Requires output format with `"answer"` and `"contexts"`.

- **`langsmith-cookbook/feedback-examples`** — Real-time RAG evaluation with
  `EvaluatorCallbackHandler`, relevance + faithfulness evaluators running on every response.
  Pattern for online monitoring.

- **`deep_research_from_scratch` notebooks** — Per-component evaluation before composing:
  scoping (criteria captured + no hallucination), research agent (continue vs stop decision),
  supervisor (correct parallelization). Same philosophy: evaluate each component in isolation
  before testing the full pipeline.

- **`langsmith-cookbook/testing-examples/backtesting`** — Turn production runs into dataset,
  re-evaluate with new chain version. Pattern for production-to-eval loop.
