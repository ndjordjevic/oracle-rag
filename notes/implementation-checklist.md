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

### Response Generation - Enhanced
- [ ] **Response metadata**
  - [ ] Track which chunks were used in generating the answer
  - [ ] Include query timestamp in response

### MCP Server - Enhanced
- [ ] **Additional MCP Tools**
  - [ ] Implement `query_specific_pdf` tool (filter retrieval to a single document by name)

- [ ] **MCP Resources** (read-only data by URI)
  - [ ] Expose list of indexed documents as resource
  - [ ] Expose chunk preview for a document as resource
  - [ ] Expose document metadata as resource

- [ ] **MCP Prompts** (pre-built templates with parameters)
  - [ ] e.g. “Ask about this document”, “Summarize” with parameters

### Retriever Abstraction
- [ ] **Retriever abstraction (oracle-rag 2.0)**
  - [ ] Use LangChain Retriever (`store.as_retriever()`) in RAG pipeline instead of `query_index`
  - [ ] Refactor `run_rag()` to accept a retriever

### Document Management - Enhanced
- [ ] **Document Operations** (advanced)
  - [ ] Implement document status tracking
  - [ ] Implement document update/re-indexing (beyond remove + re-add)

### Error Handling - Enhanced
- [ ] **Advanced Error Handling**
  - [ ] Handle corrupted PDFs gracefully
  - [ ] Improve error messages
  - [ ] Add error logging
  - [ ] Implement graceful degradation

### Testing - Enhanced
- [ ] **Comprehensive Testing**
  - [ ] Unit tests for document management
  - [ ] Unit tests for metadata filtering
  - [ ] Integration tests for multiple PDFs
  - [ ] Test error scenarios
  - [ ] Test MCP tools thoroughly

---

## Phase 4: Advanced Features

**Goal:** Sophisticated retrieval strategies, multi-step reasoning, and advanced user experience.

### Retrieval - Advanced
- [ ] **Evaluation framework** (do before complex retrieval changes)
  - [ ] Create evaluation dataset (question / expected-answer or relevance pairs)
  - [ ] Measure retrieval quality (e.g. precision@k, recall) and answer quality
  - [ ] Use metrics to validate hybrid search, re-ranking, multi-query before/after

- [ ] **Advanced Retrieval Strategies** (ordered roughly simplest → hardest to implement)
  - [ ] Research hybrid search options
  - [ ] Add query preprocessing
  - [ ] **Long-context impact (optional)** — Long-context LLMs often underuse information in the middle of the prompt (“lost in the middle”). When building context from retrieved docs: order so the most relevant chunks appear at the start and end of the context; consider limiting to a small number of top passages (e.g. 3–5) or reranking and taking top-K; avoid packing many weak passages. Ref: Lost in the middle; rag-from-scratch 18.
  - [ ] Implement re-ranking
  - [ ] **Re-ranking (optional)** — After retrieval, re-score and re-order documents before passing to the LLM. Options: (1) Dedicated reranker: retrieve more (e.g. k=10), then use a cross-encoder-style reranker (e.g. Cohere Re-Rank via LangChain `ContextualCompressionRetriever` + `CohereRerank`) to return top N; (2) RAG Fusion: multiple queries + reciprocal rank fusion to merge and rerank (see RAG Fusion bullet above). Ref: rag-from-scratch 15.
  - [ ] Implement hybrid search (if supported by vector DB)
  - [ ] **Query translation / multi-query** — Take the user query (e.g. from Cursor via MCP), generate 3–5 differently worded questions via LLM, run retrieval per question, merge results (e.g. unique union), then run RAG on merged context. Improves retrieval when the original query is ambiguous or poorly aligned with document embeddings; Cursor does not polish or expand the question before calling the MCP, so this belongs inside oracle-rag. Optionally follow with RAG Fusion (reciprocal rank fusion) for merging. Ref: LangChain query translation / multi-query (e.g. rag-from-scratch 5–9).
  - [ ] **RAG Fusion: top-K after merge** — When using reciprocal rank fusion, the merged list is sorted by fused score; send only the top K docs (e.g. 10) to the LLM for context to limit prompt size and focus on best-ranked results.
  - [ ] **Step back prompting (optional)** — Generate a more abstract/higher-level “step back” question from the user question via few-shot LLM (e.g. “What is task composition for LLM agents?” → “What is the process of task composition?”). Retrieve on both the original and the step back question; combine both contexts and pass to the final answer prompt. Use when docs mix high-level concepts and specifics (e.g. textbooks, technical docs); the step back pulls conceptual content that supports the specific answer. Ref: Google step back prompting; rag-from-scratch series.
  - [ ] **HyDE (Hypothetical Document Embeddings, optional)** — Generate a hypothetical document that would answer the user question (e.g. prompt: "Write a passage to answer the following question"), embed that passage instead of the raw question, and run retrieval with it; then use retrieved docs + original question for the final RAG answer. Rationale: questions and documents sit in different regions of embedding space; a hypothetical doc is closer in style/length to real chunks and can improve retrieval. Tune the generation prompt per domain (e.g. "Write a technical manual section..."). Ref: HyDE paper; rag-from-scratch series.
  - [ ] **Query decomposition (optional)** — For complex questions: decompose into sub-questions via LLM, run RAG per sub-question (parallel: independent answers then concatenate; or sequential/IRC-style: pass prior Q&A into each step), then combine into final answer. Use when the question is multi-part (e.g. “What are the components and how do they interact?”). Differs from multi-query (same question rephrased → merge retrievals → one answer). Ref: rag-from-scratch 5–9, Part 7.
  - [ ] **ColBERT (optional)** — Token-level retrieval instead of one vector per chunk: tokenize doc and question, produce a vector per token (with positional weighting); score = sum over question tokens of max similarity to any document token (MaxSim). Avoids compressing a full chunk into one vector; can improve recall. Requires a ColBERT-style model and index (e.g. RAGatouille); latency and production readiness need evaluation. Consider for longer documents; check max token/context limits. Ref: ColBERT; rag-from-scratch 14.
  - [ ] **CRAG (optional)** — Corrective RAG: evaluate retrieval quality (e.g. similarity-score distribution or a small evaluator) and route by confidence. Use tunable thresholds: if confidence is high, use retrieved docs as usual; if ambiguous, refine query or context; if low, skip retrieval and answer from LLM only or trigger fallback (e.g. web search). Reduces hallucinations when the retriever returns irrelevant docs. Can be implemented as a graph (e.g. LangGraph) with conditional edges. Ref: CRAG paper; rag-from-scratch 16; LangGraph CRAG examples.
  - [ ] **Self-RAG (optional)** — Adaptive retrieval and self-reflection: the system decides whether to retrieve (no fixed retrieval every time), generates from retrieved passages when used, then critiques both the retrieved docs and its own answer (e.g. relevance, support, correctness) and can iterate. Improves factuality and citation accuracy; often implemented with a single model or graph that interleaves retrieval, generation, and reflection steps. Ref: Self-RAG paper; rag-from-scratch 17; LangGraph Self-RAG examples.

- [ ] **Document name resolution**
  - [ ] Accept fuzzy document references in queries (e.g. \"pico debug probe manual\") and resolve them to exact `document_id` values from `list_pdfs`
  - [ ] Add a helper in MCP/CLI to suggest or auto-complete document names based on partial input

- [ ] **Query structuring (optional)** — Convert natural language into structured metadata filters for the vector store. Define a Pydantic schema for available filters (e.g. document_id, tag, page_min, page_max); use LLM with structured output (function calling) so the user can say e.g. “only in the Pico manual” or “docs tagged AMIGA, pages 10–20” and get back a structured query object that drives `query_index(..., document_id=..., tag=..., page_min=..., page_max=...)`. Complements document name resolution by handling all filter types from one NL question. Ref: rag-from-scratch 11; LangChain query analysis / structured output.

- [ ] **Retrieval Quality**
  - [ ] Implement retrieval quality evaluation
  - [ ] Implement fallback strategies
  - [ ] Add re-query logic with different parameters

### Response Generation - Advanced
- [ ] **Use of Rich Metadata**
  - [ ] Design how metadata fields (`section`, `chunk_index`, `start_index`, document_title/author, size stats) should influence retrieval, ranking, and/or answer formatting (e.g. section-aware answers, filters, section-aware citations, jump-to-source in UI)

- [ ] **Prompt engineering iteration**
  - [ ] Evaluate and iterate on RAG prompt template using evaluation dataset
  - [ ] Test different system messages, few-shot examples, or chain-of-thought instructions

- [ ] **Context window management**
  - [ ] Handle context window limits (truncate, summarize, or select fewer chunks when total context exceeds model limit)

- [ ] **Streaming**
  - [ ] Implement streaming response generation
  - [ ] Test streaming functionality
  - [ ] Add streaming support to MCP server

- [ ] **Advanced Citations**
  - [ ] Improve citation formatting
  - [ ] Add confidence scores
  - [ ] Link back to document sections

### Advanced Features
- [ ] **Routing (optional)** — Route a question to the right data source or chain before retrieval. Two approaches: (1) **Logical routing**: LLM with structured output (Pydantic) chooses one of a few options (e.g. python_docs vs js_docs, or tag-based collections); (2) **Semantic routing**: embed question + candidate prompts, pick most similar. Useful when oracle-rag has multiple collections, tags, or retrieval strategies (e.g. route to multi-query vs HyDE). Ref: rag-from-scratch 10; LangChain routing docs.
- [ ] **Query Classification** (Consider LangGraph migration)
  - [ ] Implement query type detection
  - [ ] Implement conditional routing based on query type
  - [ ] Test different retrieval strategies per query type

- [ ] **Multi-step Reasoning** (Consider LangGraph migration)
  - [ ] Design multi-step workflow
  - [ ] Implement query decomposition
  - [ ] Implement iterative retrieval
  - [ ] Implement answer synthesis

- [ ] **Conversation History** (Consider LangGraph migration)
  - [ ] Design conversation state management
  - [ ] Implement context tracking
  - [ ] Implement follow-up question handling

### Framework Migration
- [ ] **LangGraph for Advanced Features** (builds on Phase 2 RAG chain rewrite)
  - [ ] Extend LangGraph `StateGraph` with conditional routing for query classification
  - [ ] Add state persistence for multi-step reasoning and conversation history
  - [ ] Define edges and routing logic for different retrieval strategies
  - [ ] **LangChain Studio Integration** (requires LangGraph)
    - [ ] Configure `langgraph.json` for Studio
    - [ ] Test RAG chain visualization and debugging in LangChain Studio
    - [ ] Document Studio setup and usage (`studio/README.md`)

### MCP Server - Advanced
- [ ] **Advanced MCP Features**
  - [ ] Expose query history
  - [ ] Add streaming support via MCP
  - [ ] Implement advanced filtering options

### Advanced PDF Processing
- [ ] **OCR Support**
  - [x] Research OCR solutions (ocrmypdf + Tesseract used externally; see notes)
  - [ ] Integrate OCR into pipeline (detect image-only pages, run OCR automatically or offer as option in add_pdf)
  - [ ] Handle complex PDF structures (multi-column, tables)
  - [ ] Handle images and diagrams

- [ ] **Richer PDF Structure Signals**
  - [ ] Use PDF outline/bookmarks (when present) as an additional source of section/heading labels
  - [ ] Experiment with font size/style per text span (e.g. via pdfplumber or PyMuPDF/fitz) to treat larger-font lines as headings in chunk metadata

- [ ] **Filter by section** (after section recognition is improved)
  - [ ] Implement filter by section in query_index, run_rag, query_pdf (depends on reliable `section` metadata from Richer PDF Structure Signals)

### Chunking - Advanced
- [ ] **Chunk size tuning** (needs evaluation framework first)
  - [ ] Tune chunk size to ~512 tokens (~2000 chars) with 10-20% overlap
  - [ ] Benchmark retrieval quality before/after with evaluation dataset
- [ ] **Parent-child retrieval**
  - [ ] Embed small chunks (128-256 tokens) for precise matching, return larger parent chunks (1000-2000 tokens) for context
  - [ ] Evaluate LangChain `ParentDocumentRetriever` (requires secondary storage layer)
- [ ] **Multi-representation indexing (optional)** — Decouple retrieval representation from generation content: at index time, produce a summary (or “proposition”) per document (or per section) via LLM, embed summaries in the vector store; store full raw documents in a separate doc store keyed by doc_id. At query time, similarity search on summaries → get doc_ids → fetch full document(s) from doc store → pass full doc(s) to LLM. Improves retrieval (summary optimized for matching) and gives long-context LLMs full-document context. Ref: proposition indexing; rag-from-scratch 12.
- [ ] **RAPTOR / hierarchical indexing (optional)** — Build a hierarchical index: start with leaf chunks (or docs), cluster by embedding similarity, summarize each cluster with an LLM; recurse (cluster summaries → summarize again) until one root or a depth limit. Index all levels together in the same vector store (leaves + every summary level). High-level questions tend to match higher-level summary chunks; low-level questions match leaf chunks; improves coverage when K is small and the question needs information spread across many chunks. More complex indexing (clustering, recursive summarization). Ref: RAPTOR paper; rag-from-scratch 13.
- [ ] **Structure-aware chunking**
  - [ ] Detect and preserve tables as atomic chunks (avoid splitting mid-table)
  - [ ] Detect and preserve code blocks as atomic chunks

### Performance
- [ ] **Performance Optimization**
  - [ ] Scalable to hundreds of PDFs
  - [ ] Optimized batch processing
  - [ ] Implement caching strategies
  - [ ] Parallelize batch indexing (`add_pdfs`) with threads (e.g. `ThreadPoolExecutor`) while keeping per-file error reporting

### Testing - Advanced
- [ ] **Advanced Testing**
  - [ ] Test streaming functionality
  - [ ] Test query classification
  - [ ] Test multi-step reasoning
  - [ ] Performance testing with large document sets
  - [ ] Load testing

---

## Phase 5: Polish & Production Ready

**Goal:** Production-grade reliability, monitoring, deployment, and advanced optimizations.

### Deployment & Operations
- [ ] **Deployment packaging**
  - [ ] Package for deployment (Docker image, or installable CLI via `pip install oracle-rag`, or hosted MCP server)
- [ ] **Backup and restore**
  - [ ] Implement Chroma index backup and restore (export/import) for migration and recovery

### Monitoring & Observability
- [ ] **Metrics & Logging**
  - [ ] Implement query performance metrics
  - [ ] Implement retrieval quality metrics
  - [ ] Add comprehensive logging
  - [ ] Set up error tracking
- [ ] **Usage analytics** (optional)
  - [ ] Track query patterns, most-queried documents, average response quality

### Security & Access Control
- [ ] **Security Features**
  - [ ] Implement document-level access control
  - [ ] Add query authentication
  - [ ] Implement audit logging
  - [ ] Security review

### Scalability
- [ ] **Performance Optimization**
  - [ ] Optimize batch processing
  - [ ] Implement caching strategies
  - [ ] Test scalability with hundreds of PDFs
  - [ ] Consider distributed vector store (see Future section if not needed soon)

### Advanced Query Understanding
- [ ] **Query Intelligence**
  - [ ] Query intent detection
  - [ ] Multi-lingual support
  - [ ] Complex query parsing

### Document Versioning
- [ ] **Version Management**
  - [ ] Track document versions
  - [ ] Handle document updates intelligently
  - [ ] Version-aware retrieval

### Advanced Configuration
- [ ] **Dynamic Configuration**
  - [ ] Dynamic configuration updates
  - [ ] A/B testing support (optional; see Future)
  - [ ] Feature flags (optional; see Future)

### Documentation
- [ ] **Complete Documentation**
  - [ ] API documentation
  - [ ] Usage examples
  - [ ] Configuration guide
  - [ ] Deployment instructions
  - [ ] Architecture documentation
  - [ ] Troubleshooting guide

### Production Readiness
- [ ] **Final Polish**
  - [ ] Code review
  - [ ] Performance optimization
  - [ ] Security audit
  - [ ] Documentation review
  - [ ] Deployment testing

### Future / If Needed
- **Horizontal scaling, load balancing, distributed vector store** — when serving many concurrent users
- **A/B testing, feature flags** — when running experiments in production

---

## Framework Evaluation

### Phase 1: LangChain + Plain Python RAG ✅ (current)
- PDF processing, chunking, embeddings, vector store with Chroma
- RAG pipeline via plain Python `run_rag()` with `@traceable` (2-step: retrieve → generate)
- LangSmith observability via `@traceable` decorator
- MCP tool integration

### Phase 2: Complete ✅
- Plain Python `run_rag()` replaces LCEL; `ChatPromptTemplate` stays; `RunnablePassthrough`/`RunnableLambda`/`StrOutputParser` removed

### Phase 3: Advanced Configuration & Deployment
- Embedding and LLM configuration (swap providers, tune chunk settings)
- MCP resources/prompts, retriever abstraction, document management, error handling

### Phase 4: Advanced Features
- Query translation / multi-query, hybrid search, re-ranking
- Query classification with conditional routing (consider LangGraph)
- Multi-step reasoning, conversation history
- Evaluate wrapping as a LangGraph `StateGraph` for Studio support and future extensibility

### Phase 5: Polish & Production Ready
- Deployment, monitoring, security, scalability, documentation

**Note:** LangChain docs recommend plain Python + `@traceable` for a deterministic 2-step RAG. `AgentMiddleware` + `create_agent` is for agentic RAG (LLM decides when to retrieve). LangGraph `StateGraph` is the right target if the pipeline needs routing, loops, or Studio visibility — deferred to Phase 3/4.
