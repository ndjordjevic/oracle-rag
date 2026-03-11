# PinRAG — Agent Instructions

PinRAG is a multi-format RAG system exposed as an MCP server.
Source code lives in `src/pinrag/`; tests in `tests/`.

## Git

- **Do not commit or push** until I explicitly ask you to.
- Keep commit messages to one or two sentences. No bullet-point bodies.

## Code Style

- Python 3.12+. Follow the conventions already in `src/pinrag/`.
- Type-annotate all public functions and methods.
- Every public module, class, and function should have a docstring.
- Lint with `ruff` and run `pytest` before considering any change done.
- Do not add comments that merely narrate what the code does.

## Project Layout

```
src/pinrag/
  rag/          # RAG pipeline (chain, prompts, formatting, rerank, multiquery)
  indexing/     # Loaders + indexers per format (PDF, YouTube, Discord, GitHub)
  mcp/          # MCP server & tool definitions (add_file, query, list, remove)
  vectorstore/  # Chroma client, retriever, parent docstore
  chunking/     # Text splitter (structure-aware, parent-child)
  embeddings/   # OpenAI / Cohere embedding clients
  llm/          # OpenAI / Anthropic chat model clients
  evaluation/   # LangSmith evaluators and baseline runner
  config.py     # All env-var configuration (PINRAG_*)
  cli.py        # CLI entry point for the MCP server
```

## Key Conventions

- Configuration is driven by `PINRAG_*` environment variables; see `config.py`.
- Each indexing format has a **loader** (parse → Documents) and an **indexer** (chunk → Chroma).
- Indexing always replaces existing chunks for the same `document_id` (upsert semantics).
- Parent-child retrieval is optional (`PINRAG_USE_PARENT_CHILD`); embed small children, store large parents in a local docstore.

## Documentation & References

- For LangChain / LangGraph APIs: use MCP servers `user-docs-langchain` (primary) and `user-context7` (fallback). See `.cursor/rules/` for details.
- For workspace reference projects: read `notes/workspace-projects-overview.md` first.
- Always cite sources. Never fabricate information — say "I don't know" when unsure.
