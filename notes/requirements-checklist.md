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

### Chunking & Embedding
- [x] **Basic chunking**
  - Configurable chunk size (default 1000) and overlap (default 200)
  - Basic overlap between chunks
  - Respect sentence boundaries (RecursiveCharacterTextSplitter)

- [x] **Essential chunk metadata**
  - Source document identifier (document_id from file_name)
  - Page number(s) the chunk spans (page preserved)
  - Chunk index within document (chunk_index per page)

- [ ] **Embedding generation**
  - Generate embeddings for all chunks
  - Store embeddings in vector database
  - Associate embeddings with basic metadata

### Vector Store & Retrieval
- [ ] **Vector database setup**
  - Store embeddings with metadata
  - Support similarity search
  - Efficient retrieval of top-k similar chunks

- [ ] **Basic retrieval**
  - Basic similarity search
  - Single query processing

### Response Generation
- [ ] **Answer generation**
  - Generate answers using retrieved context
  - Include basic source citations (document name, page numbers)
  - Format responses clearly

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

**Goal:** Add document management, better metadata, and improved retrieval capabilities.

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

### Phase 1-2: LangChain ✅
**LangChain is sufficient for:**
- All Phase 1 requirements (MVP)
- All Phase 2 requirements (enhanced features)
- Multiple PDF loading and processing
- Chunking with metadata
- Vector store with metadata filtering
- Basic and enhanced retrieval
- Document management operations
- MCP tool integration

### Phase 3: Consider LangGraph ⚠️
**LangGraph becomes beneficial for:**
- Query classification with conditional routing
- Multi-step reasoning with state persistence
- Retrieval quality checks with fallback logic
- Complex conversation history management
- Iterative refinement workflows

**Recommendation:** Start with LangChain for Phases 1-2. Evaluate migration to LangGraph at Phase 3 if advanced features require conditional logic or complex state management.
