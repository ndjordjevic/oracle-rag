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

- [ ] **Metadata Filtering**
  - [x] Implement filter by document (optional `document_id` on query_index, run_rag, query_pdf)
  - [ ] Implement filter by page range
  - [ ] Implement filter by section
  - [ ] Implement filter by tag

---

## Phase 3: Advanced Configuration & Deployment

### Configuration - Enhanced
- [ ] **Embedding and LLM configuration**
  - [ ] Make embedding model configurable (env or config file)
  - [ ] Make LLM provider configurable (env or config file)

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

## Phase 3: Advanced Features

**Goal:** Sophisticated retrieval strategies, multi-step reasoning, and advanced user experience.

### Retrieval - Advanced
- [ ] **Evaluation framework** (do before complex retrieval changes)
  - [ ] Create evaluation dataset (question / expected-answer or relevance pairs)
  - [ ] Measure retrieval quality (e.g. precision@k, recall) and answer quality
  - [ ] Use metrics to validate hybrid search, re-ranking, multi-query before/after

- [ ] **Advanced Retrieval Strategies**
  - [ ] Research hybrid search options
  - [ ] Implement hybrid search (if supported by vector DB)
  - [ ] Implement re-ranking
  - [ ] Implement multi-query expansion
  - [ ] Add query preprocessing

- [ ] **Document name resolution**
  - [ ] Accept fuzzy document references in queries (e.g. \"pico debug probe manual\") and resolve them to exact `document_id` values from `list_pdfs`
  - [ ] Add a helper in MCP/CLI to suggest or auto-complete document names based on partial input

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

### Chunking - Advanced
- [ ] **Chunk size tuning** (needs evaluation framework first)
  - [ ] Tune chunk size to ~512 tokens (~2000 chars) with 10-20% overlap
  - [ ] Benchmark retrieval quality before/after with evaluation dataset
- [ ] **Parent-child retrieval**
  - [ ] Embed small chunks (128-256 tokens) for precise matching, return larger parent chunks (1000-2000 tokens) for context
  - [ ] Evaluate LangChain `ParentDocumentRetriever` (requires secondary storage layer)
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

## Phase 4: Polish & Production Ready

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

### Phase 3: Advanced Configuration + LangGraph
- Embedding and LLM configuration (swap providers, tune chunk settings)
- Query classification with conditional routing
- Multi-step reasoning with state persistence
- Retrieval quality checks with fallback logic
- Conversation history management
- Iterative refinement workflows
- Evaluate wrapping as a LangGraph `StateGraph` for Studio support and future extensibility

**Note:** LangChain docs recommend plain Python + `@traceable` for a deterministic 2-step RAG. `AgentMiddleware` + `create_agent` is for agentic RAG (LLM decides when to retrieve). LangGraph `StateGraph` is the right target if the pipeline needs routing, loops, or Studio visibility — deferred to Phase 3.
