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

- [ ] **Vector Store Implementation**
  - [ ] Implement embedding storage with metadata
  - [ ] Implement similarity search/retrieval
  - [ ] Test basic retrieval functionality

### RAG Pipeline
- [ ] **LLM Setup**
  - [ ] Choose LLM provider (OpenAI, Anthropic, local, etc.)
  - [ ] Set up LLM client
  - [ ] Test basic LLM calls

- [ ] **RAG Chain Implementation**
  - [ ] Design prompt template with context and question
  - [ ] Implement retrieval step
  - [ ] Implement context formatting
  - [ ] Implement generation step
  - [ ] Implement response formatting with citations
  - [ ] Build LangChain chain (RunnablePassthrough pattern)

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
  - [ ] Test PDF loading with sample PDF
  - [ ] Test chunking and metadata preservation
  - [ ] Test embedding generation
  - [ ] Test retrieval functionality
  - [ ] Test end-to-end RAG pipeline
  - [ ] Test MCP tools

---

## Phase 2: Enhanced Features

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

### Framework Migration (if needed)
- [ ] **Evaluate LangGraph Migration**
  - [ ] Assess if Phase 3 features require LangGraph
  - [ ] If yes: Design LangGraph structure
  - [ ] If yes: Define state schema
  - [ ] If yes: Create nodes for each step
  - [ ] If yes: Define edges and routing logic
  - [ ] If yes: Migrate existing functionality

### Testing - Advanced
- [ ] **Advanced Testing**
  - [ ] Test streaming functionality
  - [ ] Test query classification
  - [ ] Test multi-step reasoning
  - [ ] Performance testing with large document sets
  - [ ] Load testing

---

## Phase 4: Polish & Production Ready

### Advanced PDF Processing
- [ ] **OCR Support**
  - [ ] Research OCR solutions
  - [ ] Implement OCR for scanned PDFs
  - [ ] Handle images and diagrams

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
