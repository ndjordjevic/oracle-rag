# Oracle-RAG Implementation Checklist

## Phase 0: Planning & Setup

- [x] **Framework Decision**
  - [x] Evaluate LangChain for simple RAG pipeline
  - [x] Evaluate LangGraph for complex workflows with state management
  - [x] Make decision and document rationale (✅ Decision: Start with LangChain)

- [x] **Project Setup**
  - [x] Initialize Python project structure
  - [x] Set up dependency management (requirements.txt or pyproject.toml)
  - [x] Create project directory structure
  - [x] Set up development environment

---

## Phase 1: MVP - Core Functionality **(v1.0.0)**

**Goal:** Working PDF RAG that can load PDFs, answer questions, and provide basic source citations.

### PDF Processing
- [x] **PDF Library Selection**
  - [x] Research PDF parsing libraries (PyPDF2, pdfplumber, pypdf, etc.)
  - [x] Choose PDF library (**pypdf**)
  - [x] Install and test basic PDF text extraction (**pypdf** smoke-tested)

- [x] **Basic PDF Processing**
  - [x] Implement single PDF loading
  - [x] Extract text from PDF files
  - [x] Test parsing with sample PDFs and verify output (e.g. `scripts/print_pdf_page.py`)
  - [x] Extract basic metadata (page numbers, document name, document title/author from PDF)
  - [x] Handle basic text-based PDFs (raise ValueError when no text extracted; Phase 1 text-only)

### Chunking & Embeddings
- [x] **Chunking Strategy**
  - [x] Choose chunk size (default: 1000 chars)
  - [x] Choose chunk overlap (default: 200 chars)
  - [x] Implement text splitter (LangChain RecursiveCharacterTextSplitter)
  - [x] Preserve page numbers in chunks
  - [x] Add document identifier to chunks

- [x] **Embedding Setup**
  - [x] Choose embedding model (**OpenAI API** — see [embedding-provider-decision.md](embedding-provider-decision.md))
  - [x] Set up embedding model client
  - [x] Test embedding generation (incl. pipeline test: PDF load → chunk → embed a few chunks in `tests/test_embeddings.py::test_embed_pdf_chunks`)

### Vector Store
- [x] **Vector Database Selection**
  - [x] Research vector databases (Chroma, FAISS, Pinecone, etc.) — see [vector-database-decision.md](vector-database-decision.md)
  - [x] Choose vector database (**Chroma** for local, simple setup)
  - [x] Install and configure vector database (`chromadb`, `langchain-chroma`; `oracle_rag.vectorstore.get_chroma_store()` with persist dir `chroma_db`)
  - [x] Unit tests for Chroma store (`tests/test_vectorstore.py`: get_chroma_store, persist dir, add_documents + similarity_search)

- [x] **Vector Store Implementation**
  - [x] Implement embedding storage with metadata (via `index_pdf` → `get_chroma_store().add_documents()`)
  - [x] Implement similarity search/retrieval (`query_index` + Chroma `similarity_search`; tests in `tests/test_indexing.py` and `tests/test_vectorstore.py`)
  - [x] Test basic retrieval functionality (CLI: `scripts/index_pdf_cli.py`, `scripts/query_rag_cli.py`; tests: `test_indexing.py`, `test_vectorstore.py`)

### RAG Pipeline
- [x] **LLM Setup**
  - [x] Choose LLM provider (OpenAI for chat/completion)
  - [x] Set up LLM client (`oracle_rag.llm.get_chat_model()` — ChatOpenAI, gpt-4o-mini; OPENAI_API_KEY from env)
  - [x] Test basic LLM calls (`tests/test_llm.py`, `scripts/test_llm_cli.py`)

- [x] **RAG Chain Implementation**
  - [x] Design prompt template with context and question (`oracle_rag.rag.prompts.RAG_PROMPT`)
  - [x] Implement retrieval step (wire `query_index` in chain)
  - [x] Implement context formatting (`format_docs`, numbered with doc/page for citations)
  - [x] Implement generation step (prompt | llm | StrOutputParser)
  - [x] Implement response formatting with citations (`format_sources`, `RAGResult`-like output)
  - [x] Build RAG pipeline (plain Python `run_rag()` with `@traceable`; CLI: `scripts/rag_cli.py`)

- [x] **Observability & Development Tools**
  - [x] Setup LangSmith (tracing, observability; see `notes/langsmith-setup.md`)
  - [x] Learn how to read and interpret LangSmith traces (understand trace structure, timing, inputs/outputs, debugging workflow)
  - [x] Understand all code written so far (review PDF processing, chunking, embeddings, vector store, RAG chain, scripts/CLIs, tests) before moving to MCP implementation

### MCP Server - Basic
- [x] **MCP Server Setup**
  - [x] Research MCP server implementation patterns (see `notes/mcp-server-research.md`)
  - [x] Install MCP Python SDK (`mcp>=1.26.0`)
  - [x] Create `src/oracle_rag/mcp/` module structure
  - [x] Set up FastMCP server framework (`mcp/server.py`)
  - [x] Create entry point script (`scripts/mcp_server.py`)

- [x] **Basic MCP Tools**
  - [x] Implement `query_pdf` tool (wraps `run_rag()`)
  - [x] Implement `add_pdf` tool (wraps `index_pdf()`)
  - [x] Implement `remove_pdf` tool (remove PDF and all its chunks/embeddings from Chroma)
  - [x] Implement `list_pdfs` tool (list all indexed books in Oracle-RAG)
  - [x] Add error handling and input validation
  - [x] Test with MCP Inspector (`npx @modelcontextprotocol/inspector`)
  - [x] Add unit tests (`tests/test_mcp_server.py`)
  - [x] Test MCP server from Cursor (add Oracle-RAG to Cursor MCP config, invoke query_pdf / add_pdf / list_pdfs; see `notes/cursor-mcp-setup.md` and `.cursor/mcp.json`)

---

## Phase 1.5: Configuration, Persistence & Error Handling

### Configuration & Persistence
- [x] **Configuration Management** (env vars)
  - [x] Set up configuration file (YAML/JSON/env) — using `.env` + `ORACLE_RAG_*` vars; see `.env.example`
  - [x] Make chunk size configurable (`ORACLE_RAG_CHUNK_SIZE`, default 1000)
  - [x] Make chunk overlap configurable (`ORACLE_RAG_CHUNK_OVERLAP`, default 200)

- [x] **Persistence** (done in Phase 1)
  - [x] Implement vector store persistence — Chroma persists to `chroma_db` (or custom path) on disk
  - [x] Test persistence across restarts — `test_index_pdf_smoke` re-opens store and queries; index survives process restarts
  - [x] Handle data directory setup — `get_chroma_store()` creates persist dir if missing (`mkdir(parents=True, exist_ok=True)`)

- [x] **Duplicate PDF detection**
  - [x] On add_pdf/index_pdf: if document_id (file name) already in index, delete existing chunks then add new ones (replace) to avoid duplicates

### Error Handling
- [x] **Basic Error Handling**
  - [x] Handle PDF loading errors — propagate; tools raise FileNotFoundError, ValueError with clear messages
  - [x] Handle embedding generation errors — propagate; logged and returned to client
  - [x] Handle retrieval errors — propagate; logged and returned to client
  - [x] Handle LLM generation errors — propagate; logged and returned to client
  - [x] Add basic error messages — tools validate and raise with clear messages; `_log_tool_errors` decorator logs to stderr (Cursor Output) then re-raises

### Testing - MVP
- [x] **Basic Testing**
  - [x] Test PDF loading with sample PDF (`tests/test_pypdf_loader.py`)
  - [x] Test chunking and metadata preservation (`tests/test_chunking.py`)
  - [x] Test embedding generation (`tests/test_embeddings.py`)
  - [x] Test retrieval functionality (`tests/test_vectorstore.py`, `tests/test_indexing.py`)
  - [x] Test end-to-end RAG pipeline (`tests/test_rag.py`)
  - [x] Test MCP tools

- [x] **Configuration, Persistence & Error Handling**
  - [x] Test configuration (load config, override chunk size/overlap) — `tests/test_config.py` (env getters); `test_index_pdf_uses_config_chunk_size_from_env` (index_pdf uses env); `test_index_pdf_respects_chunk_size_override` (override via kwargs)
  - [x] Test persistence (index PDF, restart or new process, verify index survives and queries work) — covered by `test_index_pdf_smoke`
  - [x] Test error handling (PDF load failures, embedding/retrieval/LLM errors return clear messages; CLI and MCP) — `test_mcp_server.py` covers validation errors; errors propagate and are logged via `_log_tool_errors`
  - [x] Test duplicate PDF detection (add same PDF twice: replace; verify no duplicate chunks) — `test_index_pdf_replaces_duplicate`

### Deployment & Distribution - MVP
- [x] **Document how others can start and use this MCP**
  - [x] PyPI install: `pip install oracle-rag` → `oracle-rag-mcp` CLI; config from cwd or `~/.config/oracle-rag/` (see `README.md`, `notes/distribution-options.md`)
  - [x] Cursor MCP config: command `oracle-rag-mcp` (no cwd needed; uses ~/.oracle-rag/ for .env and chroma_db)
  - **Publish new version to PyPI:** Bump `version` in `pyproject.toml` → `git add -A && git commit -m "vX.Y.Z: ..." && git push` → `git tag -a vX.Y.Z -m "Release vX.Y.Z" && git push origin vX.Y.Z` → `uv build && uv publish` (use `__token__` + PyPI API token when prompted; or `uv cache clean` before `uv tool install oracle-rag --force` to get latest)
  - [x] Github action to publish to PyPI on a new tag/release

---

## Phase 2: Enhanced Features

**Goal:** Document management, better metadata, improved retrieval, modernize the RAG chain.

### Releases - GitHub
- [x] **Manual GitHub Release for stable versions**
  - [x] When ready (e.g. after Phase 2 milestone), pick the latest `vX.Y.Z` tag and create a GitHub Release with notes (no assets).
  - [x] Prefer a **manual** release (not per-tag) so only meaningful milestones get a Release page.
  - [x] CLI option: `gh release create vX.Y.Z --notes \"Summary of changes\"` (requires GitHub CLI + auth).

### RAG Chain Rewrite
- [x] **Replace LCEL with plain Python (2-step RAG)**
  - *Done*: `run_rag()` plain function + `@traceable` now powers the RAG pipeline (retrieve → format context → generate answer + sources). LCEL (`RunnablePassthrough`/`RunnableLambda`/`StrOutputParser`) has been removed in favor of this pattern from the LangChain docs.

### PDF Processing - Enhanced
- [x] **Multiple PDF Support**
  - [x] Implement batch PDF loading (new `add_pdfs` MCP tool)
  - [x] Test with multiple PDFs (unit coverage for partial success/failure)

- [x] **Enhanced Metadata**
  - [x] Add explicit section/heading labels to chunk metadata (`section` key; heading-like lines detected and carried forward)
  - [x] Add upload timestamps for indexed documents (stored on chunks, aggregated per document in list_pdfs)
  - [x] Store document size stats (pages, bytes, total chunks) per document (stored on chunks, aggregated per document in list_pdfs)

### Chunking - Enhanced
- [x] **Section/heading metadata** — done (heading-like lines detected; `section` key added to chunk metadata)
- [x] **Character offsets** — enable `add_start_index=True` on `RecursiveCharacterTextSplitter`; each chunk gets `start_index` metadata (char offset in page)

### Vector Store - Enhanced
- [x] **Document Tag** (single tag per document)
  - [x] Add optional per-document tag at indexing time (e.g. `tag: "amiga"`)
  - [x] Persist tag on all chunks for that document (queryable via metadata filters)
  - [x] Expose tag in `list_pdfs` output (per-document details)

- [x] **Metadata Filtering**
  - [x] Implement filter by document (optional `document_id` on query_index, run_rag, query_pdf)
  - [x] Implement filter by page range (optional `page_min`, `page_max`; single page: page_min=64, page_max=64)
  - [x] Implement filter by tag (optional `tag` on query_index, run_rag, query_pdf)

---

## Phase 3: Advanced Configuration & Deployment

### Configuration - Enhanced
- [x] **Embedding and LLM configuration**
  - [x] Make embedding model configurable (env or config file)
  - [x] Make LLM provider configurable (env or config file)

### MCP Server - Enhanced
- [x] **MCP Resources** (read-only data by URI)
  - [x] Expose list of indexed documents as resource (`oracle-rag://documents`)

- [x] **MCP Prompts** (pre-built templates with parameters)
  - [x] “Ask about this document prompt” (`ask_about_documents`)

### Retriever Abstraction
- [x] **Retriever abstraction (oracle-rag 2.0)**
  - [x] Use LangChain Retriever (`store.as_retriever()`) in RAG pipeline instead of `query_index`
  - [x] Refactor `run_rag()` to accept a retriever

### Error Handling - Enhanced
- [x] **Advanced Error Handling**
  - [x] **Handle corrupted or unreadable PDFs** — In `load_pdf_as_documents`, catch `PyPdfError` and `OSError` when opening/reading the PDF and re-raise as `ValueError` with a user-facing message.
  - [x] **Zero-retrieval and LLM failure handling (graceful degradation)** — In `run_rag`: when retrieval returns 0 chunks, return early with a clear message (no LLM call); when the LLM invoke fails, return a short error message (rate limit, timeout, or generic) instead of propagating the traceback.

### Testing - Enhanced
- [x] **Comprehensive Testing**
  - [x] Integration tests for multiple PDFs — `test_run_rag_multiple_pdfs_document_id_and_tag_filters` in `test_rag.py`: indexes two PDFs (same content, different names/tags), then queries with document_id and tag filters and asserts sources are from the correct document; unfiltered query returns sources from either doc.

---

## Phase 4: Advanced Retrieval & Evaluation

**Goal:** Close the correctness gap (currently 60% OpenAI vs 73% Anthropic baseline) by improving retrieval quality, then iterate on prompts using evaluation results.

### Evaluation Iteration
- [ ] **Evaluation framework** (do before complex retrieval changes). See `notes/evaluation-strategy.md`.
  - [x] Create evaluation dataset (question / expected-answer pairs). Golden dataset **oracle-rag-golden** in LangSmith: 30 examples from *Bare-metal Amiga programming 2021_ocr.pdf* (easy → hard); script: `scripts/create_eval_dataset.py`.
  - [x] Implement evaluators and target: correctness, relevance, groundedness, retrieval relevance (LLM-as-judge) plus code evaluators (has_sources, answer_not_empty, source_in_expected_docs); target function wrapping `run_rag` with `document_id`/`tag` from dataset inputs. See evaluation-strategy §4–5.
  - [x] Run the first experiment with Anthropic for LLM and Cohere for embeddings.
  - [x] Re-run the experiment with OpenAI both for LLM and embeddings.
  - [x] Make sure you understand the metrics and why the results are like they are and some answers are wrong. **Why grades are bad:** (1) Retrieval often misses expected pages (93% of failures) → multi-query, hybrid search, increase k; (2) deep-in-book content underretrieved (55% of wrong-answer pages > page 100) → hybrid search, reranker; (3) topically adjacent wrong chunks rank high → reranker, multi-query; (4) nearly-correct answers marked 0 (~2–3 cases) → lenient reference or partial-credit grader.
  - [x] **Increase retrieval k (one constant):** In `src/oracle_rag/evaluation/target.py`, change `k=5` to e.g. `k=8` or `k=10` in `create_retriever(...)`; re-run evaluation and compare correctness. **Done (k=10):** correctness 53.3% → 60.0% (+2 questions); baseline 73.3% — modest gain, gap remains; next: multi-query / hybrid / reranker.

### Retrieval Improvement
- [ ] **Advanced Retrieval Strategies** (ordered by expected impact for this project: 93% of failures = retrieval miss; 55% of wrong-answer pages > 100 = deep-in-book; topically adjacent wrong chunks rank high)
  - [ ] **Re-ranking** ⭐ — After retrieval, re-score and re-order documents before passing to the LLM. Directly addresses "topically adjacent wrong chunks rank high" and "deep-in-book underretrieved". Retrieve k=10, rerank to top 5. Options: (1) Cohere Re-Rank via `ContextualCompressionRetriever` + `CohereRerank`; (2) RAG Fusion reciprocal rank fusion. Ref: rag-from-scratch 15. **Highest bang-for-buck: one wrapper around the existing retriever, no re-indexing.**
  - [ ] **Query translation / multi-query** ⭐ — Generate 3–5 differently worded variants of the user query via LLM, run retrieval per variant, merge (unique union or RAG Fusion), then run RAG on merged context. Directly addresses "retrieval misses expected pages" (93%) and the fact that MCP queries are often terse/unpolished. Optionally combine with RAG Fusion for merging. Ref: LangChain multi-query; rag-from-scratch 5–9.
  - [ ] **RAG Fusion: top-K after merge** — Natural follow-on to multi-query: use reciprocal rank fusion to merge per-query result lists; pass only top K (e.g. 10) to the LLM. Keeps prompt focused after multi-query broadens recall.
  - [ ] **Hybrid search** — Add a keyword (BM25) retrieval path alongside vector search and combine scores. **High impact for deep-in-book content** (specific register names, opcodes, exact terms that embeddings spread across semantic neighbours). Chroma has no native BM25; options: `BM25Retriever` + `EnsembleRetriever` over the same docs in memory, or switch to a DB with native hybrid search (e.g. Qdrant, Weaviate).
  - [ ] **HyDE (Hypothetical Document Embeddings)** — Embed a LLM-generated hypothetical answer passage instead of the raw question; retrieves docs closer in style/length to the actual chunks. Useful here because short technical questions and dense manual paragraphs sit in different embedding spaces. Low effort once multi-query is in place. Ref: HyDE paper; rag-from-scratch series.
  - [ ] **Add query preprocessing** — Normalize or lightly expand the user query before retrieval (e.g. expand abbreviations, strip MCP boilerplate). Low effort, marginal gain on its own; do before or alongside multi-query.
  - [ ] **Long-context ordering (optional)** — Order retrieved docs so best-ranked chunks appear at the start and end of the context ("lost in the middle" effect). Easy win after reranking is in place. Ref: Lost in the middle; rag-from-scratch 18.
  - [ ] **Lenient / partial-credit grader (optional)** — For the ~2–3 nearly-correct answers marked 0: relax reference expectations or add a partial-credit correctness grader. Improves metrics fairness, not retrieval.
  - [ ] **Step back prompting (optional)** — Generate an abstract "step back" question, retrieve on both original and step-back, combine contexts. Useful when docs mix high-level concepts and specifics (e.g. textbooks). Ref: Google step back prompting; rag-from-scratch series.
  - [ ] **Query decomposition (optional)** — Decompose multi-part questions into sub-questions, run RAG per sub-question, combine answers. Differs from multi-query (rephrasing vs decomposing). Ref: rag-from-scratch 5–9, Part 7.
  - [ ] **ColBERT (optional)** — Token-level retrieval (MaxSim scoring); avoids compressing a full chunk into one vector. High recall ceiling but requires a ColBERT index (e.g. RAGatouille) and re-indexing. Consider if reranker + hybrid still leave a large gap. Ref: ColBERT; rag-from-scratch 14.
  - [ ] **CRAG (optional)** — Corrective RAG: route by retrieval confidence; fall back to LLM-only or web search when retrieval quality is low. Useful when some queries have no good matches in the index. Ref: CRAG paper; rag-from-scratch 16.
  - [ ] **Self-RAG (optional)** — Adaptive retrieval with self-reflection: decide whether to retrieve, critique retrieved docs and own answer, iterate. High factuality ceiling; high implementation complexity. Ref: Self-RAG paper; rag-from-scratch 17.
- [ ] **Prompt engineering iteration** — Evaluate and iterate on RAG prompt template using evaluation dataset; test different system messages, few-shot examples, or chain-of-thought instructions. **Try pairwise experiments** when comparing two prompt variants: run both as separate LangSmith experiments on the golden dataset, then use `langsmith.evaluate(("exp-A-id", "exp-B-id"), evaluators=[ranked_preference])` to have an LLM judge pick the better answer head-to-head — more informative than absolute scores when both prompts produce partially-correct answers. See `intro-to-langsmith/notebooks/module_2/pairwise_experiments.ipynb`.

### Chunking Improvement
- [ ] **Chunk size tuning** (needs evaluation framework first) — Tune chunk size to ~512 tokens (~2000 chars) with 10–20% overlap; benchmark retrieval quality before/after with evaluation dataset.
- [ ] **Parent-child retrieval** — Embed small chunks (128–256 tokens) for precise matching, return larger parent chunks (1000–2000 tokens) for context. Evaluate LangChain `ParentDocumentRetriever`.
- [ ] **Structure-aware chunking** — Detect and preserve tables and code blocks as atomic chunks (avoid splitting mid-table or mid-block).

### Response Generation
- [ ] **Streaming** — Implement streaming response generation in `run_rag` and expose via MCP server.
- [ ] **Context window management** — Handle context window limits (truncate, summarize, or select fewer chunks when total context exceeds model limit).

---

## Phase 5: Polish & Production Ready

**Goal:** Production-grade reliability, observability, deployment packaging, and documentation.

### Deployment & Operations
- [ ] **Deployment packaging** — Package as Docker image, installable CLI (`pip install oracle-rag`), or hosted MCP server.
- [ ] **Backup and restore** — Implement Chroma index backup/restore (export/import) for migration and recovery.

### Monitoring & Observability
- [ ] **Metrics & Logging** — Query performance metrics, retrieval quality metrics, comprehensive logging, error tracking.
- [ ] **Usage analytics** (optional) — Track query patterns, most-queried documents, average response quality.

### Security & Access Control
- [ ] **Security Features** — Document-level access control, query authentication, audit logging, security review.

### Scalability
- [ ] **Performance Optimization** — Caching strategies, batch indexing parallelism (`ThreadPoolExecutor`), scalability test with hundreds of PDFs.

### Documentation
- [ ] **Complete Documentation** — API docs, usage examples, configuration guide, deployment instructions, architecture overview, troubleshooting guide.

### Production Readiness
- [ ] **Final Polish** — Code review, performance optimization pass, security audit, documentation review, deployment testing.

---

## Phase 6: Document Intelligence & Advanced Indexing

**Goal:** Smarter document understanding — richer PDF parsing, better chunking strategies, and query-time document intelligence.

### Advanced PDF Processing
- [ ] **OCR integration** — Detect image-only pages and run OCR automatically (or offer as option in `add_pdf`). Research done: ocrmypdf + Tesseract used externally.
- [ ] **Complex structure handling** — Handle multi-column layouts, tables (preserve as atomic chunks), code blocks, and embedded images/diagrams.
- [ ] **Richer structure signals** — Use PDF outline/bookmarks as section/heading labels; detect headings via font size/style (pdfplumber or PyMuPDF).
- [ ] **Filter by section** — Implement section filter in `query_index`, `run_rag`, `query_pdf` (depends on reliable `section` metadata above).

### Advanced Chunking
- [ ] **Parent-child retrieval** — Embed small chunks (128–256 tokens) for precise matching, return larger parent chunks (1000–2000 tokens) for context. Evaluate LangChain `ParentDocumentRetriever`.
- [ ] **Multi-representation indexing** (optional) — Embed per-chunk summaries/propositions in the vector store; store full raw docs in a separate doc store keyed by doc_id. Ref: rag-from-scratch 12.
- [ ] **RAPTOR / hierarchical indexing** (optional) — Cluster leaf chunks, summarize clusters, recurse; index all levels together. Ref: RAPTOR paper; rag-from-scratch 13.

### Document Intelligence
- [ ] **Document name resolution** — Accept fuzzy doc references in queries (e.g. "pico debug probe manual"), resolve to exact `document_id` from `list_pdfs`; add auto-complete helper.
- [ ] **Query structuring** (optional) — LLM converts natural language into structured metadata filters (Pydantic schema: `document_id`, `tag`, `page_min`, `page_max`). Ref: rag-from-scratch 11; LangChain query analysis.
- [ ] **Document update/re-indexing** — Implement update beyond remove + re-add; document status tracking; version-aware retrieval.

### Advanced MCP & Citations
- [ ] **Advanced MCP Features** — Expose query history; streaming support; advanced filtering options.
- [ ] **Advanced Citations** — Confidence scores per source chunk; link back to document sections; improved citation formatting.

---

## Phase 7: Agentic Reasoning & LangGraph

**Goal:** Move from a fixed retrieve→generate pipeline to a stateful, agentic graph that can route, loop, decompose, and hold conversation context.

### Routing
- [ ] **Logical routing** — LLM with structured output (Pydantic) picks data source or retrieval strategy per query. Ref: rag-from-scratch 10.
- [ ] **Semantic routing** — Embed question + candidate strategy prompts, pick most similar. Ref: rag-from-scratch 10.

### Multi-step Reasoning
- [ ] **Query classification & conditional routing** — Detect query type (factual, conceptual, multi-part); route to different retrieval strategies via LangGraph conditional edges.
- [ ] **Query decomposition** — Decompose multi-part questions into sub-questions; run RAG per sub-question in parallel or sequentially; synthesize final answer.
- [ ] **Iterative retrieval** — Loop: generate partial answer → check if more retrieval needed → retrieve again → refine answer.

### Conversation History
- [ ] **Conversation state** — Design state schema; implement context tracking across turns; handle follow-up questions.

### LangGraph Migration
- [ ] **`StateGraph` rewrite** — Wrap RAG pipeline in a LangGraph `StateGraph`; add conditional edges for routing and loops.
- [ ] **State persistence** — Add checkpointer for multi-step reasoning and conversation history.
- [ ] **LangChain Studio integration** — Configure `langgraph.json`; test visualization and debugging in Studio; document setup (`studio/README.md`).

### Future / If Needed
- **Horizontal scaling, load balancing, distributed vector store** — when serving many concurrent users
- **A/B testing, feature flags** — when running experiments in production
- **Multi-lingual support, query intent detection** — when user base requires it

---

## Framework Evaluation

### Phase 1: LangChain + Plain Python RAG ✅ (current)
- PDF processing, chunking, embeddings, vector store with Chroma
- RAG pipeline via plain Python `run_rag()` with `@traceable` (2-step: retrieve → generate)
- LangSmith observability via `@traceable` decorator
- MCP tool integration

### Phase 2: Complete ✅
- Plain Python `run_rag()` replaces LCEL; `ChatPromptTemplate` stays; `RunnablePassthrough`/`RunnableLambda`/`StrOutputParser` removed

### Phase 3: Advanced Configuration & Deployment ✅
- Embedding and LLM configurable (env/config; swap providers, tune chunk settings)
- MCP resources (`oracle-rag://documents`), MCP prompts (`ask_about_documents`)
- Retriever abstraction: `store.as_retriever()`, `run_rag()` accepts optional retriever
- Error handling: corrupted PDFs (user-facing ValueError), zero-retrieval and LLM failure (graceful degradation)
- Testing: integration test for multiple PDFs with document_id/tag filters

### Phase 4: Advanced Retrieval & Evaluation
- Evaluation framework: golden dataset, 7 evaluators, LangSmith experiments
- Baselines: Anthropic 73.3%, OpenAI k=5 53.3%, OpenAI k=10 60.0%
- Next: re-ranking, multi-query, hybrid search, chunk tuning

### Phase 5: Polish & Production Ready
- Deployment, monitoring, security, scalability, documentation

### Phase 6: Document Intelligence & Advanced Indexing
- OCR, richer PDF structure, advanced chunking (parent-child, RAPTOR), document name resolution, query structuring

### Phase 7: Agentic Reasoning & LangGraph
- Routing, query classification, multi-step reasoning, conversation history, LangGraph `StateGraph` migration, Studio integration

**Note:** LangChain docs recommend plain Python + `@traceable` for a deterministic 2-step RAG. `AgentMiddleware` + `create_agent` is for agentic RAG (LLM decides when to retrieve). LangGraph `StateGraph` is the right target if the pipeline needs routing, loops, or Studio visibility — deferred to Phase 7.
