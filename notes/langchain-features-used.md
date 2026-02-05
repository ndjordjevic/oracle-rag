# LangChain / LangGraph Features Used

## LangChain (so far)

| Area | Component | Use in project |
|------|-----------|----------------|
| **Core** | `langchain_core.documents.Document` | PDF loader returns per-page `Document`s; chunking consumes/produces `Document`s with `page_content` + `metadata`. |
| **Text splitters** | `langchain_text_splitters.RecursiveCharacterTextSplitter` | Chunking with configurable `chunk_size`, `chunk_overlap`; `split_documents()`. |
| **Embeddings** | `langchain_openai.OpenAIEmbeddings` | Embedding client (text-embedding-3-small); `embed_query()`, `embed_documents()`. |
| **Vector store** | `langchain_chroma.Chroma` | Persisted Chroma store; `add_documents()`, `similarity_search()`. |
| **Core** | `langchain_core.embeddings.Embeddings` | Type for injectable embedding (e.g. mock in tests). |

## LangGraph

Not used yet. Phase 0 decision: start with LangChain for the RAG pipeline; LangGraph may be used later for workflows with state (e.g. MCP or multi-step flows).

---

## LangChain features not used (so far)

From [LangChain docs](https://python.langchain.com/docs/):

| Area | Feature | Notes |
|------|---------|--------|
| **Core** | Agents | `create_agent`, tool-calling; not used (no agent yet). |
| **Core** | Models (LLM) | Chat/completion models; only embeddings used so far. |
| **Core** | Messages | Chat message format (user/assistant/system); not used. |
| **Core** | Tools | Agent tools; not used. |
| **Core** | Short-term memory | Conversation buffer; not used. |
| **Core** | Streaming | Stream LLM tokens; not used. |
| **Core** | Structured output | Pydantic/structured LLM output; not used. |
| **Middleware** | Built-in / custom | Not used. |
| **Advanced** | Guardrails | Not used. |
| **Advanced** | Runtime | LangChain runtime; not used. |
| **Advanced** | Context engineering | Not used. |
| **Advanced** | MCP (Model Context Protocol) | Planned for Phase 1 (MCP server). |
| **Advanced** | Human-in-the-loop | Not used. |
| **Advanced** | Multi-agent | Not used. |
| **Advanced** | Retrieval (retriever abstraction) | Chroma used directly; LangChain Retriever / RAG chain not wired yet. |
| **Advanced** | Long-term memory | Not used. |
| **Agent development** | LangSmith Studio / Test / Observability | Not used. |
| **Deploy** | Deployment, Observability | Not used. |
