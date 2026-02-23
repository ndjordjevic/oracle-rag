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

Phase 1 complete = first release; package version in `pyproject.toml` is set to `1.0.0` and tagged as `v1.0.0` in git.

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
  - [x] Build LangChain chain (RunnablePassthrough pattern in `get_rag_chain()`; CLI: `scripts/rag_cli.py`)

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
  - [x] Implement `query_pdf` tool (wraps `get_rag_chain()`)
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

  **Approach (MCP / Cursor):**
  - **Return to caller:** Keep raising from tools (ValueError, FileNotFoundError, etc.). The MCP SDK turns these into error responses so the Cursor agent (or any MCP client) receives a clear error message and can retry or report to the user.
  - **Log to server output:** Use Python `logging` with a handler to stderr (or log in a central place). Cursor’s “Output” panel for the oracle-rag MCP shows the server process’s stderr, so errors will appear there for debugging. Option: wrap tool calls in a decorator or server-level try/except that logs the exception (tool name, message, optional traceback at DEBUG) then re-raises, so every tool gets logging without duplicating try/except.
  - **Summary:** Raise → client gets the error; log (e.g. `logging.error(...)`) → Output window shows it.

  **How to test** (`tests/test_mcp_server.py`):
  - **Validation / input errors:** `test_add_pdf_empty_path_raises`, `test_add_pdf_file_not_found_raises`, `test_query_pdf_empty_query_raises`, `test_query_pdf_missing_persist_dir_raises`, etc. — assert tools raise with clear messages.
  - **PDF loading errors:** `test_add_pdf_pdf_loading_error_propagates` — mock `index_pdf` to raise (e.g. `ValueError("No text extracted")`), assert exception propagates.
  - **Retrieval / LLM errors:** `test_query_pdf_chain_error_propagates` — mock `chain.invoke` to raise (e.g. `RuntimeError("OpenAI API rate limit")`), assert exception propagates.
  - **Log then re-raise:** `test_server_tool_logs_on_failure` — patch server `_log`, trigger a tool failure, assert `_log.exception` was called and exception is re-raised.

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

- [x] **Document how others can start and use this MCP**
  - [x] PyPI install: `pip install oracle-rag` → `oracle-rag-mcp` CLI; config from cwd or `~/.config/oracle-rag/` (see `README.md`, `notes/distribution-options.md`)
  - [x] Cursor MCP config: command `oracle-rag-mcp`, cwd = folder with `.env` and `chroma_db`

---

## Phase 2: Enhanced Features

**Goal:** Document management, better metadata, improved retrieval, modernize the RAG chain.

### Configuration - Enhanced
- [ ] **Embedding and LLM configuration**
  - [ ] Make embedding model configurable (env or config file)
  - [ ] Make LLM provider configurable (env or config file)

### RAG Chain Rewrite
- [ ] **Replace LCEL with plain Python + LangGraph**
  - [ ] Rewrite LCEL chain (`RunnablePassthrough`/`RunnableLambda`) as a plain Python function for readability
  - [ ] Add `@traceable` decorator (from `langsmith`) to preserve per-step LangSmith tracing
  - [ ] Evaluate wrapping as a LangGraph `StateGraph` for Studio support and future extensibility
  - [ ] Update tests to work with the new implementation
  - *Context*: LangChain maintainers confirmed LCEL/Runnables are effectively deprecated in favor of LangGraph + `create_agent`. Plain Python is clearer for a deterministic RAG pipeline.

### PDF Processing - Enhanced
- [ ] **Multiple PDF Support**
  - [ ] Implement batch PDF loading
  - [ ] Handle duplicate content detection
  - [ ] Test with multiple PDFs

- [ ] **Enhanced Metadata**
  - [ ] Extract section/heading information
  - [ ] Extract document metadata (author, creation date)
  - [ ] Add upload timestamps
  - [ ] Store document size information

### Chunking - Enhanced
- [ ] **Intelligent Chunking**
  - [ ] Improve chunking to respect paragraph boundaries
  - [ ] Better handling of document structure
  - [ ] Add section/heading metadata to chunks
  - [ ] Add character offsets to chunks

### Vector Store - Enhanced
- [ ] **Metadata Filtering**
  - [ ] Implement filter by document
  - [ ] Implement filter by page range
  - [ ] Implement filter by section
  - [ ] Test metadata filtering

- [ ] **Retriever abstraction (oracle-rag 2.0)**
  - [ ] Use LangChain Retriever (`store.as_retriever()`) in RAG chain instead of `query_index`
  - [ ] Refactor `get_rag_chain()` to accept a retriever runnable

### Document Management
- [ ] **Document Operations**
  - [x] Implement document removal (delete PDF and chunks) — done in Phase 1 via `remove_pdf` MCP tool
  - [x] Implement document listing — done in Phase 1 via `list_pdfs` MCP tool
  - [ ] Implement document status tracking
  - [ ] Implement document update/re-indexing
  - [ ] Add document metadata display (e.g. chunk count per document in list_pdfs)

### Response Generation - Enhanced
- [ ] **Response metadata**
  - [ ] Track which chunks were used in generating the answer
  - [ ] Include query timestamp in response

### MCP Server - Enhanced
- [ ] **Additional MCP Tools**
  - [x] Implement `remove_pdf` tool — done in Phase 1
  - [x] Implement `list_pdfs` tool — done in Phase 1
  - [ ] Implement `query_specific_pdf` tool (filter retrieval to a single document by name)
  - [ ] Add per-document chunk count to list_pdfs output

- [ ] **MCP Resources** (read-only data by URI)
  - [ ] Expose list of indexed documents as resource
  - [ ] Expose chunk preview for a document as resource
  - [ ] Expose document metadata as resource

- [ ] **MCP Prompts** (pre-built templates with parameters)
  - [ ] e.g. “Ask about this document”, “Summarize” with parameters

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

- [ ] **Retrieval Quality**
  - [ ] Implement retrieval quality evaluation
  - [ ] Implement fallback strategies
  - [ ] Add re-query logic with different parameters

### Response Generation - Advanced
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

### Performance
- [ ] **Performance Optimization**
  - [ ] Scalable to hundreds of PDFs
  - [ ] Optimized batch processing
  - [ ] Implement caching strategies

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

### Phase 1: LangChain + LCEL ✅ (current)
- PDF processing, chunking, embeddings, vector store with Chroma
- RAG chain via LCEL (`RunnablePassthrough`, `RunnableLambda`)
- LangSmith observability (automatic with LCEL)
- MCP tool integration

> **Note:** LCEL/Runnables are effectively deprecated per LangChain maintainers (not formally removed yet, but no longer recommended). The Phase 1 chain works and won't break, but should be migrated in Phase 2.

### Phase 2: Plain Python + LangGraph evaluation ⚠️
- Rewrite LCEL chain as plain Python for readability
- Evaluate LangGraph `StateGraph` as the orchestration layer
- Use `@traceable` from LangSmith to preserve per-step tracing
- LangGraph enables LangChain Studio support

### Phase 3: LangGraph (if adopted in Phase 2)
- Query classification with conditional routing
- Multi-step reasoning with state persistence
- Retrieval quality checks with fallback logic
- Conversation history management
- Iterative refinement workflows

**Recommendation:** LangChain maintainers recommend LangGraph + `create_agent` as the current pattern. For a deterministic RAG pipeline, LangGraph `StateGraph` is the most relevant migration target.
