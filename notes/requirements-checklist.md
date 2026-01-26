# Oracle-RAG Requirements Checklist

## Core PDF Processing

- [ ] **Load single PDF**
  - Extract text from PDF files
  - Handle different PDF formats (text-based, scanned with OCR)
  - Support various PDF structures (single column, multi-column, tables)

- [ ] **Load multiple PDFs**
  - Batch processing of multiple PDF files
  - Track which document each chunk comes from
  - Handle duplicate content across PDFs

- [ ] **Metadata extraction**
  - Page numbers for each chunk
  - Section/heading information
  - Document title and source file name
  - Document upload timestamp
  - Document size/metadata (author, creation date if available)

## Chunking & Embedding

- [ ] **Intelligent chunking**
  - Configurable chunk size
  - Overlap between chunks
  - Respect document structure (don't split mid-sentence, mid-paragraph)
  - Preserve context across chunk boundaries

- [ ] **Chunk metadata storage**
  - Source document identifier
  - Page number(s) the chunk spans
  - Section/heading the chunk belongs to
  - Chunk index within document
  - Character offsets (start/end positions)
  - Timestamp when chunk was created

- [ ] **Embedding generation**
  - Generate embeddings for all chunks
  - Store embeddings in vector database
  - Associate embeddings with chunk metadata

## Vector Store & Retrieval

- [ ] **Vector database**
  - Store embeddings with metadata
  - Support similarity search
  - Filter by metadata (e.g., "only search in document X", "only pages 1-10")
  - Efficient retrieval of top-k similar chunks

- [ ] **Retrieval strategies**
  - Basic similarity search
  - Metadata filtering (by document, page range, section)
  - Hybrid search (semantic + keyword, if supported)
  - Re-ranking (optional, for better relevance)

- [ ] **Query handling**
  - Single query processing
  - Multi-query expansion (optional)
  - Query preprocessing (cleaning, normalization)

## Document Management

- [ ] **Add documents**
  - Upload new PDFs
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

## Response Generation

- [ ] **Answer generation**
  - Generate answers using retrieved context
  - Include source citations (document name, page numbers)
  - Format responses clearly

- [ ] **Source attribution**
  - Show which documents were used
  - Display page numbers for citations
  - Link back to original document sections

- [ ] **Response metadata**
  - Track which chunks were used in answer
  - Confidence scores (if available)
  - Query timestamp

## Advanced Features (Future Considerations)

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

- [ ] **Streaming responses**
  - Stream answer generation token by token
  - Better user experience for long answers

- [ ] **Retrieval quality checks**
  - Evaluate if retrieved chunks are relevant
  - Fallback strategies if retrieval quality is low
  - Re-query with different parameters if needed

## MCP Server Integration

- [ ] **MCP tools**
  - `query_pdf` - Query across all PDFs
  - `add_pdf` - Add new PDF to index
  - `remove_pdf` - Remove PDF from index
  - `list_pdfs` - List all indexed PDFs
  - `query_specific_pdf` - Query within a specific PDF

- [ ] **MCP resources**
  - Expose document metadata
  - Expose chunk information
  - Expose query history (optional)

## Technical Requirements

- [ ] **Error handling**
  - Handle corrupted PDFs
  - Handle embedding failures
  - Handle retrieval failures
  - Graceful degradation

- [ ] **Performance**
  - Fast query response times
  - Efficient batch processing
  - Scalable to hundreds of PDFs

- [ ] **Configuration**
  - Configurable chunk size and overlap
  - Configurable embedding model
  - Configurable vector database
  - Configurable LLM provider

- [ ] **Persistence**
  - Persist vector store
  - Persist document metadata
  - Handle restarts gracefully

## Evaluation Criteria for LangChain vs LangGraph

### Can LangChain handle this?

**✅ LangChain can handle:**
- Multiple PDF loading and processing
- Chunking with metadata
- Vector store with metadata filtering
- Basic retrieval and generation
- Document management operations
- MCP tool integration (simple input/output)

**❓ LangChain limitations:**
- Conditional routing (e.g., different strategies based on query type)
- Multi-step reasoning with state persistence
- Retrieval quality checks with fallback logic
- Complex conversation history management
- Iterative refinement workflows

**💡 Key Question:**
Do we need conditional logic, state management, or multi-step workflows, or is a linear chain sufficient?
