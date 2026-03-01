# LangChain / LangGraph Features Used

## LangChain (so far)

| Area | Component | Use in project |
|------|-----------|----------------|
| **Core** | `langchain_core.documents.Document` | PDF loader returns per-page `Document`s; chunking consumes/produces `Document`s with `page_content` + `metadata`. |
| **Text splitters** | `langchain_text_splitters.RecursiveCharacterTextSplitter` | Chunking with configurable `chunk_size`, `chunk_overlap`; `split_documents()`. |
| **Embeddings** | `langchain_openai.OpenAIEmbeddings` | Embedding client (text-embedding-3-small); `embed_query()`, `embed_documents()`. |
| **Vector store** | `langchain_chroma.Chroma` | Persisted Chroma store; `add_documents()`, `similarity_search()`, `as_retriever()`. |
| **Retrieval** | `langchain_core.retrievers.BaseRetriever` / `store.as_retriever()` | RAG pipeline uses a retriever: `create_retriever()` builds one with `search_kwargs` (k, filter); `run_rag(retriever=...)` accepts a retriever or builds one from legacy params. |
| **Core** | `langchain_core.embeddings.Embeddings` | Type for injectable embedding (e.g. mock in tests). |
| **Chat models** | `langchain_openai.ChatOpenAI` | LLM client for answer generation; used directly (`get_chat_model`) and inside the RAG chain. |
| **Prompts** | `langchain_core.prompts.ChatPromptTemplate` | RAG prompt with system + human messages (`RAG_PROMPT`), templated with `{context}` and `{question}`. |
| **Plain Python + LangSmith** | `langsmith.traceable` | RAG pipeline (`run_rag`) is a plain Python function decorated with `@traceable` for per-step LangSmith tracing. Replaces LCEL. |

---

## LangChain features not used (so far)

From [LangChain docs](https://python.langchain.com/docs/):

| Area | Feature | Notes |
|------|---------|--------|
| **Core** | Agents | `create_agent`, tool-calling; not used (no agent yet). |
| **Core** | Messages | Chat message format (user/assistant/system); implicitly used via `ChatPromptTemplate` and `ChatOpenAI` but no custom message classes. |
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
| **Advanced** | Long-term memory | Not used. |
| **Agent development** | LangSmith Studio / Test / Observability | Not used. |
| **Deploy** | Deployment, Observability | Not used. |
