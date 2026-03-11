# MMR (Maximal Marginal Relevance) — Value Analysis

**Question:** Would adding MMR to the retriever bring meaningful value to PinRAG?

## What MMR does

MMR selects documents by balancing **relevance** to the query and **diversity** among selected documents. Each chosen chunk maximizes: `λ * relevance − (1−λ) * max_similarity_to_already_selected`. So it reduces redundancy (e.g. five nearly identical adjacent chunks from the same page).

## Current PinRAG retrieval pipeline

1. **Base retriever** — Chroma `as_retriever()` with `k`; pure similarity, top-k by score.
2. **Optional: multi-query** — Several query variants → retrieve per variant → merge (union). Already adds diversity.
3. **Optional: Cohere rerank** — Fetch more (e.g. 20), rerank with Cohere, return top_n (e.g. 10). Reranker re-scores for relevance over a larger set.

## When MMR would add value

| Scenario | MMR value |
|---------|-----------|
| **Rerank OFF, multi-query OFF** | **Moderate.** Top-k from Chroma can be highly redundant (e.g. consecutive chunks from one PDF page). MMR would diversify and often improve answer quality. |
| **Rerank OFF, multi-query ON** | **Some.** Multi-query already pulls from different angles; merged set may still contain similar chunks. MMR could dedupe. |
| **Rerank ON** | **Low.** Cohere already selects “best” from a larger candidate set. Reranker is relevance-focused; adding MMR after rerank could reorder by embedding similarity and sometimes hurt relevance. |

## When MMR adds little

- **Rerank ON (default path for “best” quality):** The pipeline already does “fetch more → select best.” MMR would apply before or after rerank; after rerank it can conflict with the reranker’s ordering.
- **Small k:** With k=5–10 and Cohere rerank, the final set is already small and reranker-curated; diversity from MMR is less critical.

## Implementation note

`langchain_chroma.Chroma` supports MMR via `as_retriever(search_type="mmr", search_kwargs={"k": k, "fetch_k": fetch_k, "lambda_mult": 0.5})`. So it’s a config flag and different `search_kwargs` in `create_retriever()`.

## Recommendation

- **Optional, low priority.** Most value when **rerank is OFF** and users see repetitive or redundant context.
- **Do not enable MMR when rerank is ON** unless we A/B test; reranker ordering could be degraded.
- Add only if: (1) users report “too much repetition in answers” or (2) we explicitly support a “no rerank, max diversity” mode. Otherwise defer.
