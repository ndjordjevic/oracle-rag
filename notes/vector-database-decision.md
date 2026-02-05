# Vector Database Decision

## Options Considered

| Option | Pros | Cons |
|--------|------|------|
| **Chroma** | Local, simple API, metadata filtering, LangChain integration | Single-node; not for huge scale |
| **FAISS** | Fast, in-memory, good for prototyping | No persistence by default; no metadata filtering out of the box |
| **Pinecone** | Managed, scalable, serverless | Cost, data in cloud, vendor lock-in |
| **Weaviate / Qdrant / Milvus** | Feature-rich, metadata, hybrid search | Heavier setup; often overkill for MVP |

## Decision

**We use Chroma** for Phase 1.

- Local: no API key, data stays on disk.
- Already in `pyproject.toml`; LangChain has `Chroma` integration.
- Stores embeddings + metadata (e.g. page, file_name); supports similarity search and optional metadata filters.
- Persistence to a directory; good fit for single-user or small-team RAG.

Can be swapped later (e.g. Pinecone for scale) if we keep a thin store abstraction.
