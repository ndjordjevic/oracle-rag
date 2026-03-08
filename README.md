# Oracle-RAG

A powerful PDF RAG (Retrieval-Augmented Generation) system built with LangChain, designed as an MCP (Model Context Protocol) server for Cursor, VS Code (GitHub Copilot), and other AI assistants.

## Overview

Oracle-RAG provides intelligent document querying and retrieval capabilities for PDF documents. Index PDFs, ask questions, and get answers with source citations—all via MCP tools in your editor.

## Features

- **PDF processing** — Index single or multiple PDFs; batch add via `add_pdfs`
- **RAG with citations** — Ask questions, get answers with source (document + page)
- **Document tags** — Tag documents at index time (e.g. `AMIGA`, `PI_PICO`) for filtered search
- **Metadata filtering** — Query by document, page range, or tag
- **MCP tools** — `query_pdf`, `add_pdf`, `add_pdfs`, `list_pdfs`, `remove_pdf`
- **MCP resource** — Read-only list of indexed documents (`oracle-rag://documents`); click in Cursor’s MCP panel to view
- **MCP prompt** — `ask_about_documents` (parameter: question) for guided RAG queries
- **Configurable LLM** — Anthropic (default) or OpenAI; set via `ORACLE_RAG_LLM_PROVIDER` and model in `.env`
- **Configurable embeddings** — OpenAI (default) or Cohere; set via `ORACLE_RAG_EMBEDDING_PROVIDER`. Use the same provider for indexing and querying (e.g. re-index after switching).
- **Built with** — LangChain, Chroma; optional OpenAI, Anthropic, Cohere

## Installation

```bash
pipx install oracle-rag
# or: uv tool install oracle-rag
```

Requires Python 3.12+. Both `pipx` and `uv tool install` create an isolated environment and put `oracle-rag-mcp` on your PATH.

### Updating

```bash
pipx upgrade oracle-rag
# or: uv cache clean && uv tool install oracle-rag --force
```

Restart your editor after updating so the MCP server picks up the new version.

## Quick Start

### 1. Create config

```bash
mkdir -p ~/.oracle-rag
# Default: Anthropic (Claude) for LLM, OpenAI for embeddings; rerank off (set ORACLE_RAG_USE_RERANK=true to enable)
echo "ANTHROPIC_API_KEY=sk-ant-..." > ~/.oracle-rag/.env
echo "OPENAI_API_KEY=sk-..." >> ~/.oracle-rag/.env
# Optional: Cohere for re-ranking (COHERE_API_KEY + ORACLE_RAG_USE_RERANK=true); see Configuration below
```

### 2. Add MCP server

**Cursor:** Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "oracle-rag": {
      "command": "oracle-rag-mcp"
    }
  }
}
```

**VS Code (GitHub Copilot):** Run **MCP: Open User Configuration** from the Command Palette, then add:

```json
{
  "servers": {
    "oracle-rag": {
      "command": "oracle-rag-mcp"
    }
  }
}
```

Or create `.vscode/mcp.json` in your workspace for project-specific setup. Restart VS Code or Cursor after editing.

> **Where the MCP finds `.env`:** The server loads `.env` from the **current working directory (cwd)** of the MCP process, which is usually the **workspace folder** you have open. If you use a global `~/.cursor/mcp.json` and open a different project, cwd is that project—so the MCP will not see a `.env` that lives only in another folder (e.g. an oracle-rag project). You can either put your `.env` in `~/.oracle-rag/` or `~/.config/oracle-rag/` (so it is always found), or add an `env` block to your MCP config and set all required variables there (API keys, `ORACLE_RAG_*`, etc.). Do not put secrets in a project-level `.cursor/mcp.json` if that file is committed to git.

> **Backup:** Back up `~/.oracle-rag/chroma_db` (or your `ORACLE_RAG_PERSIST_DIR`) if your indexed documents are important — deleting it removes all indexes.

> **Note:** MCP in VS Code requires GitHub Copilot and VS Code 1.102+. Enterprise users may need an admin to enable "MCP servers in Copilot."

### 3. Use in chat

| Action | Tool |
|--------|------|
| Add a PDF | `add_pdf_tool` — optionally with `tag` (e.g. `AMIGA`) |
| Add multiple PDFs | `add_pdfs_tool` — optionally with `tags` (one per PDF) |
| List indexed PDFs | `list_pdfs_tool` — shows documents, chunk counts, tags, upload times |
| Query with filters | `query_pdf_tool` — filter by `document_id`, `page_min`/`page_max`, or `tag` |
| Remove a PDF | `remove_pdf_tool` |
| View indexed documents (read-only) | Click **Resources** → `_documents_resource` in the MCP panel |

Ask in chat: *"Add /path/to/amiga-book.pdf with tag AMIGA"* or *"What are AGA chips? Search only AMIGA-tagged docs"*. The AI will invoke the tools for you.

## Configuration

`.env` is loaded from (first existing file wins):

1. `~/.config/oracle-rag/.env`
2. `~/.oracle-rag/.env`
3. `{cwd}/.env` (current working directory of the process)

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| **LLM** | | |
| `ORACLE_RAG_LLM_PROVIDER` | `anthropic` | `openai` or `anthropic` |
| `ORACLE_RAG_LLM_MODEL` | *(provider default)* | e.g. `claude-haiku-4-5`, `claude-sonnet-4-6`, `gpt-4o-mini` |
| `OPENAI_API_KEY` | *(required for OpenAI)* | OpenAI API key (LLM or embeddings) |
| `ANTHROPIC_API_KEY` | *(required for Anthropic)* | Anthropic API key (when `ORACLE_RAG_LLM_PROVIDER=anthropic` or `ORACLE_RAG_EVALUATOR_PROVIDER=anthropic`) |
| **Evaluators (LLM-as-judge)** | | |
| `ORACLE_RAG_EVALUATOR_PROVIDER` | `openai` | `openai` or `anthropic` — which LLM grades correctness/relevance/groundedness/retrieval |
| `ORACLE_RAG_EVALUATOR_MODEL` | *(provider default)* | Model for correctness/relevance (e.g. `gpt-4o`, `claude-sonnet-4-6`) |
| `ORACLE_RAG_EVALUATOR_MODEL_CONTEXT` | *(provider default)* | Model for groundedness/retrieval (context-heavy; e.g. `gpt-4o-mini`, `claude-haiku-4-5`) |
| **Embeddings** | | |
| `ORACLE_RAG_EMBEDDING_PROVIDER` | `openai` | `openai` or `cohere` |
| `ORACLE_RAG_EMBEDDING_MODEL` | *(provider default)* | e.g. `text-embedding-3-small`, `embed-english-v3.0` |
| `COHERE_API_KEY` | *(required for Cohere)* | Cohere API key; install with `pip install oracle-rag[cohere]` when using Cohere embeddings or re-ranking |
| **Storage & chunking** | | |
| `ORACLE_RAG_PERSIST_DIR` | `chroma_db` | Chroma vector store directory (project-local by default; use `~/.oracle-rag/chroma_db` for global) |
| `ORACLE_RAG_CHUNK_SIZE` | `1000` | Text chunk size |
| `ORACLE_RAG_CHUNK_OVERLAP` | `200` | Chunk overlap |
| `ORACLE_RAG_COLLECTION_NAME` | `oracle_rag` | Chroma collection name. Single shared collection by default. |
| `ORACLE_RAG_RETRIEVE_K` | `20` | Number of chunks to retrieve. When rerank is on, this is the fallback for the pre-rerank fetch if `ORACLE_RAG_RERANK_RETRIEVE_K` is unset. |
| **Re-ranking** | | |
| `ORACLE_RAG_USE_RERANK` | `false` | Set to `true` to enable Cohere Re-Rank: fetch more chunks, re-score with Cohere, pass top N to the LLM. Requires `pip install oracle-rag[cohere]` and `COHERE_API_KEY`. |
| `ORACLE_RAG_RERANK_RETRIEVE_K` | `20` | Chunks to fetch before reranking when `ORACLE_RAG_USE_RERANK=true`. If unset, uses `ORACLE_RAG_RETRIEVE_K`. |
| `ORACLE_RAG_RERANK_TOP_N` | `10` | Number of chunks the reranker returns to the LLM (only when `ORACLE_RAG_USE_RERANK=true`). |

> **Re-indexing when changing embedding provider:** Changing `ORACLE_RAG_EMBEDDING_PROVIDER` requires re-indexing existing documents (indexes use provider-specific embedding dimensions). Alternatively use separate collections per provider (default behavior) and index into each when needed.

### Multiple providers and collections

Embedding dimension depends on the provider (OpenAI 1536, Cohere 1024). To avoid dimension mismatches:

- **Default:** Collection name is `oracle_rag`. Use one embedding provider; if you switch provider, re-index or you will get dimension errors.
- **Per-provider collections:** Set `ORACLE_RAG_COLLECTION_NAME` to a provider-specific name (e.g. `oracle_rag_openai`, `oracle_rag_cohere`) when indexing, and use the same name when querying with that provider. You can index the same PDFs into multiple collections (switch env and index again) and switch by changing `ORACLE_RAG_EMBEDDING_PROVIDER` and `ORACLE_RAG_COLLECTION_NAME` in `.env`.
- **MCP tools:** When you call `query_pdf_tool` without a `collection` argument, the server uses `ORACLE_RAG_COLLECTION_NAME` (default `oracle_rag`). Pass `collection` explicitly to target a different collection.

## Query Filtering

`query_pdf_tool` supports optional filters to narrow retrieval:

| Parameter | Description |
|-----------|-------------|
| `document_id` | Search only in this PDF (e.g. `mybook.pdf` from `list_pdfs`) |
| `page_min`, `page_max` | Restrict to page range (single page: `page_min=16`, `page_max=16`) |
| `tag` | Search only documents with this tag (e.g. `AMIGA`, `PI_PICO`) |

Filters can be combined. Example: *"What is OpenOCD? In the Pico doc, pages 16–17 only"* →  
`query_pdf_tool(query="...", document_id="RP-008276-DS-1-getting-started-with-pico.pdf", page_min=16, page_max=17)`.

## Development

```bash
git clone https://github.com/ndjordjevic/oracle-rag.git
cd oracle-rag
uv sync --extra dev
uv run pytest
```

Run MCP server from source:

```bash
uv run oracle-rag-mcp
```

For local development, point the MCP config to your venv:

**Cursor** (`.cursor/mcp.json`):
```json
{
  "mcpServers": {
    "oracle-rag": {
      "command": "/path/to/oracle-rag/.venv/bin/oracle-rag-mcp"
    }
  }
}
```

**VS Code** (`.vscode/mcp.json`):
```json
{
  "servers": {
    "oracle-rag": {
      "command": "/path/to/oracle-rag/.venv/bin/oracle-rag-mcp"
    }
  }
}
```

## License

MIT License. See [LICENSE](LICENSE) for details.
