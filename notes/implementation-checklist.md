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

## Phase 1: MVP - Core Functionality

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

- [ ] **Observability & Development Tools**
  - [x] Setup LangSmith (tracing, observability; see `notes/langsmith-setup.md`)
  - [ ] Learn how to read and interpret LangSmith traces (understand trace structure, timing, inputs/outputs, debugging workflow)

### MCP Server - Basic
- [ ] **MCP Server Setup**
  - [ ] Research MCP server implementation patterns
  - [ ] Set up MCP server structure
  - [ ] Implement basic MCP server framework

- [ ] **Basic MCP Tools**
  - [ ] Implement `query_pdf` tool
  - [ ] Implement `add_pdf` tool
  - [ ] Test MCP server integration

### Configuration & Persistence
- [ ] **Configuration Management**
  - [ ] Set up configuration file (YAML/JSON/env)
  - [ ] Make chunk size configurable
  - [ ] Make chunk overlap configurable
  - [ ] Make embedding model configurable
  - [ ] Make LLM provider configurable

- [ ] **Persistence**
  - [ ] Implement vector store persistence
  - [ ] Test persistence across restarts
  - [ ] Handle data directory setup

### Error Handling
- [ ] **Basic Error Handling**
  - [ ] Handle PDF loading errors
  - [ ] Handle embedding generation errors
  - [ ] Handle retrieval errors
  - [ ] Handle LLM generation errors
  - [ ] Add basic error messages

### Testing - MVP
- [ ] **Basic Testing**
  - [x] Test PDF loading with sample PDF (`tests/test_pypdf_loader.py`)
  - [x] Test chunking and metadata preservation (`tests/test_chunking.py`)
  - [x] Test embedding generation (`tests/test_embeddings.py`)
  - [x] Test retrieval functionality (`tests/test_vectorstore.py`, `tests/test_indexing.py`)
  - [x] Test end-to-end RAG pipeline (`tests/test_rag.py`)
  - [ ] Test MCP tools

---

## Phase 2: Enhanced Features

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
  - [ ] Implement document removal (delete PDF and chunks)
  - [ ] Implement document listing
  - [ ] Implement document status tracking
  - [ ] Implement document update/re-indexing
  - [ ] Add document metadata display

### MCP Server - Enhanced
- [ ] **Additional MCP Tools**
  - [ ] Implement `remove_pdf` tool
  - [ ] Implement `list_pdfs` tool
  - [ ] Implement `query_specific_pdf` tool

- [ ] **MCP Resources**
  - [ ] Expose document metadata as resource
  - [ ] Expose chunk information as resource

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

### Retrieval - Advanced
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
  - [ ] Research OCR solutions
  - [ ] Implement OCR for scanned PDFs
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

### Monitoring & Observability
- [ ] **Metrics & Logging**
  - [ ] Implement query performance metrics
  - [ ] Implement retrieval quality metrics
  - [ ] Add comprehensive logging
  - [ ] Set up error tracking

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
  - [ ] Consider distributed vector store

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
  - [ ] A/B testing support
  - [ ] Feature flags

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
