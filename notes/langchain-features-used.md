# LangChain / LangGraph Features Used

## LangChain (so far)

| Area | Component | Use in project |
|------|-----------|----------------|
| **Core** | `langchain_core.documents.Document` | PDF loader returns per-page `Document`s; chunking consumes/produces `Document`s with `page_content` + `metadata`. |
| **Text splitters** | `langchain_text_splitters.RecursiveCharacterTextSplitter` | Chunking with configurable `chunk_size`, `chunk_overlap`; `split_documents()`. |
| **Embeddings** | `langchain_openai.OpenAIEmbeddings` | Embedding client (text-embedding-3-small); `embed_query()`, `embed_documents()`. |
| **Vector store** | `langchain_chroma.Chroma` | Persisted Chroma store; `add_documents()`, `similarity_search()`. |
| **Core** | `langchain_core.embeddings.Embeddings` | Type for injectable embedding (e.g. mock in tests). |
| **Chat models** | `langchain_openai.ChatOpenAI` | LLM client for answer generation; used directly (`get_chat_model`) and inside the RAG chain. |
| **Prompts** | `langchain_core.prompts.ChatPromptTemplate` | RAG prompt with system + human messages (`RAG_PROMPT`), templated with `{context}` and `{question}`. |
| **LCEL / Runnables** | `langchain_core.runnables.RunnablePassthrough`, `RunnableLambda` | RAG chain wiring: assign retrieval (`query_index`), context formatting, and answer generation in `get_rag_chain()`. |
| **Output parsing** | `langchain_core.output_parsers.StrOutputParser` | Converts Chat model output to plain string as the `answer` field in the RAG result. |

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
| **Advanced** | Retrieval (retriever abstraction) | Using `query_index()` which calls `store.similarity_search()` directly. Could use `store.as_retriever()` instead, but `query_index()` already provides the needed abstraction (handles persist_directory, collection_name, embedding config) and fits our LCEL chain pattern. |
| **Advanced** | Long-term memory | Not used. |
| **Agent development** | LangSmith Studio / Test / Observability | Not used. |
| **Deploy** | Deployment, Observability | Not used. |
