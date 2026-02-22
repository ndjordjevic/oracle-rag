# Oracle-RAG Requirements Checklist

## Phase 0: Planning & Setup

- [x] **Framework decision** — Start with LangChain for Phase 1
- [x] **Project setup** — Structure, dependencies, dev environment

---

## Phase 1: MVP - Core Functionality

**Goal:** Get a working PDF RAG that can load PDFs, answer questions, and provide basic source citations.

### PDF Processing
- [x] **Load single PDF**
  - Extract text from PDF files
  - Handle basic text-based PDFs (Phase 1: text-only; ValueError if no text extracted)
  - Support simple PDF structures

- [x] **Basic metadata extraction** (per-page documents; chunk metadata when chunking is added)
  - Page numbers for each document/page
  - Source document identifier (file name)
  - Document title (and author when present in PDF)

### Chunking & Embeddings
- [x] **Chunking strategy**
  - Configurable chunk size (default 1000) and overlap (default 200)
  - RecursiveCharacterTextSplitter (sentence/paragraph boundaries)
  - Preserve page numbers and document identifier in chunks (chunk_index, document_id)

- [x] **Embedding setup** (provider: **OpenAI API** — see [embedding-provider-decision.md](embedding-provider-decision.md))
  - Embedding model client (text-embedding-3-small)
  - Generate embeddings (client ready; batch “for all chunks” when storing in vector store)
  - Pipeline test: PDF → chunk → embed (`tests/test_embeddings.py`)

### Vector Store
- [x] **Vector database selection** (see [vector-database-decision.md](vector-database-decision.md))
  - Chosen: **Chroma** (local, persist dir `chroma_db`)
  - Install and configure (`chromadb`, `langchain-chroma`; `get_chroma_store()`)
  - Unit tests: get_chroma_store, persist dir, add_documents + similarity_search (`tests/test_vectorstore.py`)

- [x] **Vector store implementation** (via `index_pdf` & `query_index`; tests in `test_indexing.py`, `test_vectorstore.py`)
  - Store embeddings with metadata (add chunk docs to Chroma with page, file_name, etc.)
  - Similarity search / top-k retrieval
  - Test basic retrieval (index sample PDF, run query, verify results)

### LLM Setup
- [x] **LLM provider and client**
  - Choose LLM provider (OpenAI for chat/completion)
  - Set up LLM client (`ChatOpenAI`, gpt-4o-mini)
  - Test basic LLM calls (`tests/test_llm.py`, `scripts/test_llm_cli.py`)

### Response Generation
- [x] **Answer generation**
  - Generate answers using retrieved context (RAG chain: `get_rag_chain()` + `rag_cli.py`)
  - Include basic source citations (document name, page numbers from chunk metadata)
  - Format responses clearly (answer text + "Sources" section)

### Observability & Development Tools
- [x] **LangSmith setup** (see `notes/langsmith-setup.md`)
  - Configure LangSmith tracing (API key, endpoint, project)
  - Automatic trace capture for LCEL chains (no code changes)
  - Trace execution flow, timing, inputs/outputs, token counts

### MCP Server Integration
- [x] **Basic MCP tools** (Phase 1)
  - [x] `query_pdf` - Query across all PDFs
  - [x] `add_pdf` - Add new PDF to index
  - [x] `remove_pdf` - Remove a PDF and its chunks from the index
  - [x] `list_pdfs` - List indexed PDFs (document_id, optional metadata)

---

## Phase 1.5: Configuration, Persistence & Error Handling

### Configuration & Persistence
- [ ] **Configuration management**
  - Config file (YAML/JSON/env)
  - Configurable chunk size and overlap
  - Configurable embedding model and LLM provider

- [ ] **Persistence**
  - Persist vector store
  - Test persistence across restarts
  - Handle data directory setup

- [ ] **Duplicate PDF detection**
  - On add_pdf: check if document_id already in index; warn or offer replace to avoid duplicate chunks

### Error Handling
- [ ] **Basic error handling**
  - Handle PDF loading, embedding, retrieval, LLM errors
  - Basic error messages

---

## Phase 2: Enhanced Features

**Goal:** Add document management, better metadata, improved retrieval capabilities, and modernize the RAG chain.

### RAG Chain Rewrite
- [ ] **Replace LCEL with plain Python + LangGraph**
  - Rewrite LCEL chain as a plain Python function for readability
  - Preserve LangSmith tracing via `@traceable` decorator
  - Evaluate LangGraph `StateGraph` for Studio support and future extensibility
  - *Context*: LangChain maintainers confirmed LCEL/Runnables are effectively deprecated in favor of LangGraph + `create_agent`.

### PDF Processing
- [ ] **Load multiple PDFs**
  - Batch processing of multiple PDF files
  - Handle duplicate content across PDFs

- [ ] **Enhanced metadata extraction**
  - Section/heading information
  - Document upload timestamp
  - Document size/metadata (author, creation date if available)

### Chunking & Embedding
- [ ] **Intelligent chunking**
  - Respect document structure (don't split mid-paragraph)
  - Preserve context across chunk boundaries
  - Better handling of tables and multi-column layouts

- [ ] **Enhanced chunk metadata**
  - Section/heading the chunk belongs to
  - Character offsets (start/end positions)
  - Timestamp when chunk was created

### Vector Store & Retrieval
- [ ] **Metadata filtering**
  - Filter by document (e.g., "only search in document X")
  - Filter by page range (e.g., "only pages 1-10")
  - Filter by section

- [ ] **Query handling**
  - Query preprocessing (cleaning, normalization)
  - Better query understanding

- [ ] **Retriever abstraction (oracle-rag 2.0)**
  - Use LangChain Retriever (`store.as_retriever()`) in the RAG chain instead of direct `query_index` / `similarity_search`
  - Integrate with the rewritten chain (plain Python or LangGraph)

### Document Management
- [ ] **Add documents**
  - Process and index automatically
  - Update existing documents (re-index if PDF changes)

- [x] **Remove documents** (done in Phase 1 via `remove_pdf` MCP tool)
  - Delete PDF and all associated chunks
  - Remove embeddings from vector store

- [x] **List documents** (done in Phase 1 via `list_pdfs` MCP tool)
  - View all indexed PDFs
  - Show document metadata (name, pages, upload date)
  - [ ] Show chunk count per document

- [ ] **Document status**
  - Track processing status (pending, processing, completed, error)
  - Handle processing errors gracefully

### Response Generation
- [ ] **Enhanced source attribution**
  - Show which documents were used
  - Display page numbers for citations
  - Better citation formatting

- [ ] **Response metadata**
  - Track which chunks were used in answer
  - Query timestamp

### MCP Server Integration
- [ ] **Additional MCP tools**
  - [x] `remove_pdf` — done in Phase 1
  - [x] `list_pdfs` — done in Phase 1
  - [ ] `query_specific_pdf` - Query within a specific PDF
  - [ ] Per-document chunk count in list_pdfs output

- [ ] **MCP resources**
  - Expose document metadata
  - Expose chunk information

### Technical Improvements
- [ ] **Enhanced error handling**
  - Handle corrupted PDFs
  - Handle retrieval failures
  - Graceful degradation

- [ ] **Performance**
  - Fast query response times
  - Efficient batch processing

---

## Phase 3: Advanced Features

**Goal:** Add sophisticated retrieval strategies, multi-step reasoning, and advanced user experience features.

### Evaluation & Retrieval
- [ ] **Evaluation framework** (do before complex retrieval changes)
  - Evaluation dataset (question / expected-answer or relevance pairs)
  - Measure retrieval quality (e.g. precision@k, recall) and answer quality
  - Use metrics to validate hybrid search, re-ranking, multi-query before/after

- [ ] **Advanced retrieval strategies**
  - Hybrid search (semantic + keyword, if supported)
  - Re-ranking for better relevance
  - Multi-query expansion

- [ ] **Retrieval quality checks**
  - Evaluate if retrieved chunks are relevant
  - Fallback strategies if retrieval quality is low
  - Re-query with different parameters if needed

### PDF Processing - Advanced
- [ ] **OCR support**
  - [x] Research OCR solutions (ocrmypdf + Tesseract used externally)
  - [ ] Integrate OCR into pipeline (detect image-only pages, run OCR automatically or as option in add_pdf)
  - [ ] Support complex PDF structures (multi-column, tables)
  - [ ] Better handling of images and diagrams

### Response Generation
- [ ] **Prompt engineering iteration**
  - Evaluate and iterate on RAG prompt using evaluation dataset
  - Test different system messages, few-shot examples, or chain-of-thought

- [ ] **Context window management**
  - Handle context window limits (truncate, summarize, or select fewer chunks when context exceeds model limit)

- [ ] **Streaming responses**
  - Stream answer generation token by token
  - Better user experience for long answers

- [ ] **Advanced source attribution**
  - Link back to original document sections
  - Confidence scores (if available)

### Advanced Features
- [ ] **Query classification**
  - Identify query type (factual, analytical, code-related)
  - Route to different retrieval strategies based on type

- [ ] **Multi-step reasoning**
  - Break complex queries into sub-queries
  - Iterative retrieval and refinement
  - Synthesis of information from multiple sources

- [ ] **Conversation history**
  - Maintain context across multiple queries
  - Follow-up question handling
  - Reference previous answers

### MCP Server Integration
- [ ] **Advanced MCP features**
  - Expose query history
  - Streaming support via MCP
  - Advanced filtering options

### Technical Enhancements
- [ ] **Performance optimization**
  - Scalable to hundreds of PDFs
  - Optimized batch processing
  - Caching strategies

---

## Phase 4: Polish & Production Ready

**Goal:** Production-grade reliability, monitoring, and advanced optimizations.

### Deployment & Operations
- [ ] **Deployment packaging**
  - Docker image, or installable CLI via `pip install oracle-rag`, or hosted MCP server
- [ ] **Backup and restore**
  - Chroma index backup and restore (export/import) for migration and recovery

### Monitoring & Observability
- [ ] **Metrics & logging**
  - Query performance metrics
  - Retrieval quality metrics
  - Comprehensive logging and error tracking
- [ ] **Usage analytics** (optional)
  - Query patterns, most-queried documents, response quality

### Security & Access Control
- [ ] **Security features**
  - Document-level access control
  - Query authentication
  - Audit logging
  - Security review

### Scalability
- [ ] **Performance optimization**
  - Optimize batch processing
  - Caching strategies
  - Test scalability with hundreds of PDFs
  - Consider distributed vector store if needed

### Advanced Features
- [ ] **Advanced query understanding**
  - Query intent detection
  - Multi-lingual support
  - Complex query parsing

- [ ] **Document versioning**
  - Track document versions
  - Handle document updates intelligently
  - Version-aware retrieval

### Future / If Needed
- Horizontal scaling, load balancing, distributed vector store — when serving many concurrent users
- A/B testing, feature flags — when running experiments in production

---

## Framework Evaluation

### Phase 1: LangChain + LCEL ✅ (current)
**LangChain is sufficient for Phase 1 MVP:**
- PDF processing, chunking, embeddings
- Vector store with Chroma
- RAG chain via LCEL (`RunnablePassthrough`, `RunnableLambda`)
- LangSmith observability (automatic with LCEL)
- MCP tool integration

> **Note:** LCEL/Runnables are effectively deprecated per LangChain maintainers (not formally removed yet, but no longer recommended). The current Phase 1 chain works and won't break, but should be migrated in Phase 2.

### Phase 2: Plain Python + LangGraph evaluation ⚠️
**Planned migration:**
- Rewrite LCEL chain as plain Python for readability
- Evaluate LangGraph `StateGraph` as the orchestration layer
- Use `@traceable` from LangSmith to preserve per-step tracing
- LangGraph enables LangChain Studio support

### Phase 3: LangGraph (if adopted in Phase 2)
**LangGraph becomes essential for:**
- Query classification with conditional routing
- Multi-step reasoning with state persistence
- Retrieval quality checks with fallback logic
- Complex conversation history management
- Iterative refinement workflows

**Recommendation:** LangChain maintainers recommend LangGraph + `create_agent` + deepagents as the current SOTA patterns. For a deterministic RAG pipeline, LangGraph `StateGraph` is the most relevant migration target.
