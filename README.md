# PinRAG

A powerful PDF RAG (Retrieval-Augmented Generation) system built with LangChain, designed as an MCP (Model Context Protocol) server for Cursor, VS Code (GitHub Copilot), and other AI assistants.

## Overview

PinRAG provides intelligent document querying and retrieval capabilities for PDFs, YouTube transcripts, and Discord exports. Index documents, ask questions, and get answers with source citations—all via MCP tools in your editor.

## Features

- **Multi-format indexing** — PDF (.pdf), YouTube (URL or video ID), Discord export (.txt)
- **RAG with citations** — Ask questions, get answers with source (document + page for PDFs, timestamp for YouTube)
- **Document tags** — Tag documents at index time (e.g. `AMIGA`, `PI_PICO`) for filtered search
- **Metadata filtering** — Query by document, page range (PDF only), or tag
- **MCP tools** — `add_document_tool`, `query_tool`, `list_documents_tool`, `remove_document_tool`
- **MCP resource** — Read-only list of indexed documents (`pinrag://documents`); click in Cursor’s MCP panel to view
- **MCP prompt** — `ask_about_documents` (parameter: question) for guided RAG queries
- **Configurable LLM** — Anthropic (default) or OpenAI; set via `PINRAG_LLM_PROVIDER` and model in `.env`
- **Configurable embeddings** — OpenAI (default) or Cohere; set via `PINRAG_EMBEDDING_PROVIDER`. Use the same provider for indexing and querying (e.g. re-index after switching).
- **Built with** — LangChain, Chroma; optional OpenAI, Anthropic, Cohere

## Installation

```bash
pipx install pinrag
# or: uv tool install pinrag
```

Requires Python 3.12+. Both `pipx` and `uv tool install` create an isolated environment and put `pinrag-mcp` on your PATH.

### Updating

```bash
pipx upgrade pinrag
# or: uv cache clean && uv tool install pinrag --force
```

Restart your editor after updating so the MCP server picks up the new version.

## Quick Start

### 1. Create config

```bash
mkdir -p ~/.pinrag
# Default: Anthropic (Claude) for LLM, OpenAI for embeddings; rerank off (set PINRAG_USE_RERANK=true to enable)
echo "ANTHROPIC_API_KEY=sk-ant-..." > ~/.pinrag/.env
echo "OPENAI_API_KEY=sk-..." >> ~/.pinrag/.env
# Optional: Cohere for re-ranking (COHERE_API_KEY + PINRAG_USE_RERANK=true); see Configuration below
```

### 2. Add MCP server

**Cursor:** Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "pinrag": {
      "command": "pinrag-mcp"
    }
  }
}
```

**VS Code (GitHub Copilot):** Run **MCP: Open User Configuration** from the Command Palette, then add:

```json
{
  "servers": {
    "pinrag": {
      "command": "pinrag-mcp"
    }
  }
}
```

Or create `.vscode/mcp.json` in your workspace for project-specific setup. Restart VS Code or Cursor after editing.

> **Where the MCP finds `.env`:** The server loads `.env` from the **current working directory (cwd)** of the MCP process, which is usually the **workspace folder** you have open. If you use a global `~/.cursor/mcp.json` and open a different project, cwd is that project—so the MCP will not see a `.env` that lives only in another folder (e.g. an pinrag project). You can either put your `.env` in `~/.pinrag/` or `~/.config/pinrag/` (so it is always found), or add an `env` block to your MCP config and set all required variables there (API keys, `PINRAG_*`, etc.). Do not put secrets in a project-level `.cursor/mcp.json` if that file is committed to git.

> **Backup:** Back up `~/.pinrag/chroma_db` (or your `PINRAG_PERSIST_DIR`) if your indexed documents are important — deleting it removes all indexes.

> **Note:** MCP in VS Code requires GitHub Copilot and VS Code 1.102+. Enterprise users may need an admin to enable "MCP servers in Copilot."

### 3. Use in chat

| Action | Tool |
|--------|------|
| Add files or YouTube videos | `add_document_tool` — path(s) as list (e.g. `paths=["/path/to/file.pdf"]` or `paths=["https://youtu.be/xyz"]`); optionally `tags` (one per path) |
| List indexed documents | `list_documents_tool` — shows documents, chunk counts, tags, upload times |
| Query with filters | `query_tool` — filter by `document_id`, `page_min`/`page_max` (PDF only), or `tag` |
| Remove a document | `remove_document_tool` |
| View indexed documents (read-only) | Click **Resources** → `_documents_resource` in the MCP panel |

Ask in chat: *"Add /path/to/amiga-book.pdf with tag AMIGA"* or *"Index https://youtu.be/xyz and ask what it says"*. The AI will invoke the tools for you. Citations show page numbers for PDFs and timestamps (e.g. `t. 1:23`) for YouTube.

## Configuration

`.env` is loaded from (first existing file wins):

1. `~/.config/pinrag/.env`
2. `~/.pinrag/.env`
3. `{cwd}/.env` (current working directory of the process)

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| **LLM** | | |
| `PINRAG_LLM_PROVIDER` | `anthropic` | `openai` or `anthropic` |
| `PINRAG_LLM_MODEL` | *(provider default)* | e.g. `claude-haiku-4-5`, `claude-sonnet-4-6`, `gpt-4o-mini` |
| `OPENAI_API_KEY` | *(required for OpenAI)* | OpenAI API key (LLM or embeddings) |
| `ANTHROPIC_API_KEY` | *(required for Anthropic)* | Anthropic API key (when `PINRAG_LLM_PROVIDER=anthropic` or `PINRAG_EVALUATOR_PROVIDER=anthropic`) |
| **Evaluators (LLM-as-judge)** | | |
| `PINRAG_EVALUATOR_PROVIDER` | `openai` | `openai` or `anthropic` — which LLM grades correctness/relevance/groundedness/retrieval |
| `PINRAG_EVALUATOR_MODEL` | *(provider default)* | Model for correctness/relevance (e.g. `gpt-4o`, `claude-sonnet-4-6`) |
| `PINRAG_EVALUATOR_MODEL_CONTEXT` | *(provider default)* | Model for groundedness/retrieval (context-heavy; e.g. `gpt-4o-mini`, `claude-haiku-4-5`) |
| **Embeddings** | | |
| `PINRAG_EMBEDDING_PROVIDER` | `openai` | `openai` or `cohere` |
| `PINRAG_EMBEDDING_MODEL` | *(provider default)* | e.g. `text-embedding-3-small`, `embed-english-v3.0` |
| `COHERE_API_KEY` | *(required for Cohere)* | Cohere API key; install with `pip install pinrag[cohere]` when using Cohere embeddings or re-ranking |
| **Storage & chunking** | | |
| `PINRAG_PERSIST_DIR` | `chroma_db` | Chroma vector store directory (project-local by default; use `~/.pinrag/chroma_db` for global) |
| `PINRAG_CHUNK_SIZE` | `1000` | Text chunk size |
| `PINRAG_CHUNK_OVERLAP` | `200` | Chunk overlap |
| `PINRAG_COLLECTION_NAME` | `pinrag` | Chroma collection name. Single shared collection by default. |
| **Parent-child retrieval** | | |
| `PINRAG_USE_PARENT_CHILD` | `false` | Set to `true` to embed small chunks (precise matching) and return larger parent chunks (rich context). Requires re-indexing. |
| `PINRAG_PARENT_CHUNK_SIZE` | `2000` | Parent chunk size (chars) when `PINRAG_USE_PARENT_CHILD=true`. |
| `PINRAG_CHILD_CHUNK_SIZE` | `800` | Child chunk size (chars) when `PINRAG_USE_PARENT_CHILD=true`. |
| **Retrieval** | | |
| `PINRAG_RETRIEVE_K` | `20` | Number of chunks to retrieve. When rerank is on, this is the fallback for the pre-rerank fetch if `PINRAG_RERANK_RETRIEVE_K` is unset. |
| **Re-ranking** | | |
| `PINRAG_USE_RERANK` | `false` | Set to `true` to enable Cohere Re-Rank: fetch more chunks, re-score with Cohere, pass top N to the LLM. Requires `pip install pinrag[cohere]` and `COHERE_API_KEY`. |
| `PINRAG_RERANK_RETRIEVE_K` | `20` | Chunks to fetch before reranking when `PINRAG_USE_RERANK=true`. If unset, uses `PINRAG_RETRIEVE_K`. |
| `PINRAG_RERANK_TOP_N` | `10` | Number of chunks the reranker returns to the LLM (only when `PINRAG_USE_RERANK=true`). |
| **Multi-query** | | |
| `PINRAG_USE_MULTI_QUERY` | `false` | Set to `true` to generate 3–5 query variants via LLM, retrieve per variant, merge (unique union). Improves recall for terse or ambiguous queries. |
| `PINRAG_MULTI_QUERY_COUNT` | `4` | Number of alternative queries to generate when `PINRAG_USE_MULTI_QUERY=true`. |
| **Response style** | | |
| `PINRAG_RESPONSE_STYLE` | `thorough` | RAG answer style: `thorough` (detailed) or `concise`. Used by evaluation target and as default when MCP `query` omits `response_style`. |

> **Re-indexing when changing embedding provider:** Changing `PINRAG_EMBEDDING_PROVIDER` requires re-indexing existing documents (indexes use provider-specific embedding dimensions). Alternatively use separate collections per provider (default behavior) and index into each when needed.
>
> **Re-indexing when enabling parent-child:** Setting `PINRAG_USE_PARENT_CHILD=true` requires re-indexing; the new structure (child chunks in Chroma, parent chunks in docstore) is created only during indexing.

### Multiple providers and collections

Embedding dimension depends on the provider (OpenAI 1536, Cohere 1024). To avoid dimension mismatches:

- **Default:** Collection name is `pinrag`. Use one embedding provider; if you switch provider, re-index or you will get dimension errors.
- **Per-provider collections:** Set `PINRAG_COLLECTION_NAME` to a provider-specific name (e.g. `pinrag_openai`, `pinrag_cohere`) when indexing, and use the same name when querying with that provider. You can index the same PDFs into multiple collections (switch env and index again) and switch by changing `PINRAG_EMBEDDING_PROVIDER` and `PINRAG_COLLECTION_NAME` in `.env`.
- **MCP tools:** The server uses `PINRAG_COLLECTION_NAME` (default `pinrag`) for all tools. Collection is not configurable per call; change it via `.env` to target a different collection.

## Query Filtering

`query_tool` supports optional filters to narrow retrieval:

| Parameter | Description |
|-----------|-------------|
| `document_id` | Search only in this document (e.g. `mybook.pdf` or video ID from `list_documents_tool`) |
| `page_min`, `page_max` | Restrict to page range (PDF only; single page: `page_min=16`, `page_max=16`) |
| `tag` | Search only documents with this tag (e.g. `AMIGA`, `PI_PICO`) |
| `document_type` | Search only by type: `pdf`, `youtube`, or `discord` |
| `response_style` | Answer style: `thorough` (default) or `concise` |

Filters can be combined. Sources include `page` for PDFs and `start` (timestamp in seconds) for YouTube. Example: *"What is OpenOCD? In the Pico doc, pages 16–17 only"* →  
`query_tool(query="...", document_id="RP-008276-DS-1-getting-started-with-pico.pdf", page_min=16, page_max=17)`.

## Development

```bash
git clone https://github.com/ndjordjevic/pinrag.git
cd pinrag
uv sync --extra dev
uv run pytest
```

Run MCP server from source:

```bash
uv run pinrag-mcp
```

For local development, point the MCP config to your venv:

**Cursor** (`.cursor/mcp.json`):
```json
{
  "mcpServers": {
    "pinrag": {
      "command": "/path/to/pinrag/.venv/bin/pinrag-mcp"
    }
  }
}
```

**VS Code** (`.vscode/mcp.json`):
```json
{
  "servers": {
    "pinrag": {
      "command": "/path/to/pinrag/.venv/bin/pinrag-mcp"
    }
  }
}
```

## License

MIT License. See [LICENSE](LICENSE) for details.
