# Oracle-RAG Requirements Checklist

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
- [ ] **Basic MCP tools**
  - `query_pdf` - Query across all PDFs
  - `add_pdf` - Add new PDF to index

### Technical Foundation
- [ ] **Basic error handling**
  - Handle basic PDF errors
  - Handle embedding failures
  - Basic error messages

- [ ] **Configuration**
  - Configurable chunk size and overlap
  - Configurable embedding model
  - Configurable LLM provider

- [ ] **Persistence**
  - Persist vector store
  - Handle restarts gracefully

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

- [ ] **Remove documents**
  - Delete PDF and all associated chunks
  - Remove embeddings from vector store
  - Clean up metadata

- [ ] **List documents**
  - View all indexed PDFs
  - Show document metadata (name, pages, upload date)
  - Show chunk count per document

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
  - `remove_pdf` - Remove PDF from index
  - `list_pdfs` - List all indexed PDFs
  - `query_specific_pdf` - Query within a specific PDF

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

### PDF Processing
- [ ] **Advanced PDF handling**
  - Handle scanned PDFs with OCR
  - Support complex PDF structures (multi-column, tables)
  - Better handling of images and diagrams

### Vector Store & Retrieval
- [ ] **Advanced retrieval strategies**
  - Hybrid search (semantic + keyword, if supported)
  - Re-ranking for better relevance
  - Multi-query expansion

- [ ] **Retrieval quality checks**
  - Evaluate if retrieved chunks are relevant
  - Fallback strategies if retrieval quality is low
  - Re-query with different parameters if needed

### Response Generation
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

### Advanced Features
- [ ] **Advanced query understanding**
  - Query intent detection
  - Multi-lingual support
  - Complex query parsing

- [ ] **Document versioning**
  - Track document versions
  - Handle document updates intelligently
  - Version-aware retrieval

### Technical Excellence
- [ ] **Monitoring & Observability**
  - Query performance metrics
  - Retrieval quality metrics
  - Error tracking and alerting

- [ ] **Advanced configuration**
  - Dynamic configuration updates
  - A/B testing support
  - Feature flags

- [ ] **Security & Access Control**
  - Document-level access control
  - Query authentication
  - Audit logging

- [ ] **Scalability**
  - Distributed vector store support
  - Horizontal scaling
  - Load balancing

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
