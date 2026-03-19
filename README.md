# PinRAG

[![PyPI version](https://img.shields.io/pypi/v/pinrag)](https://pypi.org/project/pinrag/) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A powerful RAG (Retrieval-Augmented Generation) system built with LangChain, designed as an MCP (Model Context Protocol) server for Cursor, VS Code (GitHub Copilot), and other AI assistants.

## Overview

PinRAG provides intelligent document querying and retrieval capabilities for PDFs, YouTube transcripts, Discord exports, and GitHub repositories. Index documents, ask questions, and get answers with source citations—all via MCP tools in your editor.

## Features

- **Multi-format indexing** — PDF (.pdf), YouTube (URL or video ID), Discord export (.txt), plain text (.txt), GitHub repo (URL)
- **RAG with citations** — Ask questions, get answers with source (document + page for PDFs, timestamp for YouTube)
- **Document tags** — Tag documents at index time (e.g. `AMIGA`, `PI_PICO`) for filtered search
- **Metadata filtering** — Query by document, page range (PDF only), or tag
- **MCP tools** — `add_document_tool`, `query_tool`, `list_documents_tool`, `remove_document_tool`
- **MCP resources** — `pinrag://documents` (indexed documents) and `pinrag://server-config` (env vars and config); click in Cursor’s MCP panel to view
- **MCP prompt** — `use_pinrag` (parameter: request) for querying, indexing, listing, or removing documents
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

Set API keys in your MCP server `env` block (shown in step 2). This is the
recommended setup for OSS because `pinrag-mcp` is launched by your editor from
MCP config.

**Minimum required env vars (validated at startup):**

The server validates required API keys at startup and exits with a clear error
if any are missing. In OSS MCP mode, set all env vars in your MCP `env` block.

- **Default setup** (Anthropic LLM + OpenAI embeddings): set both `OPENAI_API_KEY` and `ANTHROPIC_API_KEY`. Embeddings use OpenAI; queries use Anthropic.
- **OpenAI only:** set `PINRAG_LLM_PROVIDER=openai` and only `OPENAI_API_KEY` (one key for both embeddings and chat).
- **Cohere embeddings:** set `PINRAG_EMBEDDING_PROVIDER=cohere` and `COHERE_API_KEY`; you still need an LLM key (OpenAI or Anthropic) per above.

### 2. Add MCP server

**Cursor:** Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "pinrag": {
      "command": "pinrag-mcp",
      "env": {
        "OPENAI_API_KEY": "sk-...",
        "ANTHROPIC_API_KEY": "sk-ant-..."
      }
    }
  }
}
```

**VS Code (GitHub Copilot):** Run **MCP: Open User Configuration** from the Command Palette, then add:

```json
{
  "servers": {
    "pinrag": {
      "command": "pinrag-mcp",
      "env": {
        "OPENAI_API_KEY": "sk-...",
        "ANTHROPIC_API_KEY": "sk-ant-..."
      }
    }
  }
}
```

Or create `.vscode/mcp.json` in your workspace for project-specific setup. Restart VS Code or Cursor after editing.

> **Where the OSS MCP reads env vars:** PinRAG does not load `.env` files in OSS
> MCP mode. Configure variables only in your MCP `env` block.
> If you previously used `~/.pinrag/.env` or project `.env`, move those keys to
> MCP `env`.
> **Backup:** Back up `~/.pinrag/chroma_db` (or your `PINRAG_PERSIST_DIR`) if your indexed documents are important — deleting it removes all indexes.

### 3. Use in chat

| Action | Tool |
|--------|------|
| Add files or YouTube videos | `add_document_tool` — path(s) as list (e.g. `paths=["/path/to/file.pdf"]` or `paths=["https://youtu.be/xyz"]`); optionally `tags` (one per path) |
| List indexed documents | `list_documents_tool` — shows documents, chunk counts, tags, upload times |
| Query with filters | `query_tool` — filter by `document_id`, `page_min`/`page_max` (PDF only), or `tag` |
| Remove a document | `remove_document_tool` |
| View indexed documents (read-only) | Click **Resources** → `_documents_resource` in the MCP panel |

Ask in chat: *"Add /path/to/amiga-book.pdf with tag AMIGA"*, *"Index https://youtu.be/xyz and ask what it says"*, or *"Index https://github.com/owner/repo and ask about the codebase"*. The AI will invoke the tools for you. Citations show page numbers for PDFs, timestamps (e.g. `t. 1:23`) for YouTube, and file paths for GitHub.

### GitHub indexing

Index a GitHub repository to ask questions about its code and docs. Use `add_document_tool` with a GitHub URL:

- `https://github.com/owner/repo`
- `https://github.com/owner/repo/tree/branch`
- `github.com/owner/repo` (no scheme)

Optional parameters for GitHub URLs: `branch`, `include_patterns` (e.g. `["*.md", "src/**/*.py"]`), `exclude_patterns`. Set `GITHUB_TOKEN` in `.env` for private repos or higher API rate limits. Large files (>512 KB by default) and binaries are skipped.

### YouTube indexing and IP blocking

YouTube often blocks transcript requests from IPs that have made too many requests or from cloud provider IPs (AWS, GCP, Azure, etc.). When indexing playlists or many videos, you may see errors like *"YouTube is blocking requests from your IP"*.

**Workaround:** Use an HTTP/HTTPS proxy. Add to `.env`:

```env
PINRAG_YT_PROXY_HTTP_URL=http://user:pass@proxy.example.com:80
PINRAG_YT_PROXY_HTTPS_URL=http://user:pass@proxy.example.com:80
```

Rotating proxy services (e.g. [Webshare](https://www.webshare.io/)) work well; residential proxies are often more reliable than datacenter IPs for avoiding YouTube blocks. The proxy is used only for fetching transcripts via `youtube-transcript-api`.

When indexing fails, `add_document_tool` returns a `fail_summary` with counts by reason: `blocked` (IP blocking), `disabled` (transcripts disabled by creator), `missing_transcript`, and `other`.

## Configuration

The MCP resource `pinrag://server-config` shows the main operational vars (LLM, embeddings, chunking, retrieval, logging) and API key status. The table below documents all supported variables.

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| **LLM** | | |
| `PINRAG_LLM_PROVIDER` | `anthropic` | `openai` or `anthropic` |
| `PINRAG_LLM_MODEL` | *(provider default)* | e.g. `claude-haiku-4-5`, `claude-sonnet-4-6`, `gpt-4o-mini` |
| `OPENAI_API_KEY` | *(required for OpenAI)* | OpenAI API key (LLM or embeddings) |
| `ANTHROPIC_API_KEY` | *(required for Anthropic)* | Anthropic API key (when `PINRAG_LLM_PROVIDER=anthropic` or `PINRAG_EVALUATOR_PROVIDER=anthropic`) |
| **Embeddings** | | |
| `PINRAG_EMBEDDING_PROVIDER` | `openai` | `openai` or `cohere` |
| `PINRAG_EMBEDDING_MODEL` | *(provider default)* | e.g. `text-embedding-3-small`, `embed-english-v3.0` |
| `COHERE_API_KEY` | *(required for Cohere)* | Cohere API key; install with `pip install pinrag[cohere]` when using Cohere embeddings or re-ranking |
| **Storage & chunking** | | |
| `PINRAG_PERSIST_DIR` | `chroma_db` | Chroma vector store directory (project-local by default; use `~/.pinrag/chroma_db` for global) |
| `PINRAG_CHUNK_SIZE` | `1000` | Text chunk size (chars) |
| `PINRAG_CHUNK_OVERLAP` | `200` | Chunk overlap (chars) |
| `PINRAG_STRUCTURE_AWARE_CHUNKING` | `true` | Apply structure-aware chunking heuristics for code/table boundaries |
| `PINRAG_COLLECTION_NAME` | `pinrag` | Chroma collection name. Single shared collection by default. |
| **Retrieval** | | |
| `PINRAG_RETRIEVE_K` | `20` | Number of chunks to retrieve. When rerank is on, this is the fallback for the pre-rerank fetch if `PINRAG_RERANK_RETRIEVE_K` is unset. |
| **Parent-child retrieval** | | |
| `PINRAG_USE_PARENT_CHILD` | `false` | Set to `true` to embed small chunks (precise matching) and return larger parent chunks (rich context). Requires re-indexing. |
| `PINRAG_PARENT_CHUNK_SIZE` | `2000` | Parent chunk size (chars) when `PINRAG_USE_PARENT_CHILD=true`. |
| `PINRAG_CHILD_CHUNK_SIZE` | `800` | Child chunk size (chars) when `PINRAG_USE_PARENT_CHILD=true`. |
| **Re-ranking** | | |
| `PINRAG_USE_RERANK` | `false` | Set to `true` to enable Cohere Re-Rank: fetch more chunks, re-score with Cohere, pass top N to the LLM. Requires `pip install pinrag[cohere]` and `COHERE_API_KEY`. |
| `PINRAG_RERANK_RETRIEVE_K` | `20` | Chunks to fetch before reranking when `PINRAG_USE_RERANK=true`. If unset, uses `PINRAG_RETRIEVE_K`. |
| `PINRAG_RERANK_TOP_N` | `10` | Number of chunks the reranker returns to the LLM (only when `PINRAG_USE_RERANK=true`). |
| **Multi-query** | | |
| `PINRAG_USE_MULTI_QUERY` | `false` | Set to `true` to generate 3–5 query variants via LLM, retrieve per variant, merge (unique union). Improves recall for terse or ambiguous queries. |
| `PINRAG_MULTI_QUERY_COUNT` | `4` | Number of alternative queries to generate when `PINRAG_USE_MULTI_QUERY=true`. |
| **Response style** | | |
| `PINRAG_RESPONSE_STYLE` | `thorough` | RAG answer style: `thorough` (detailed) or `concise`. Used by evaluation target and as default when MCP `query` omits `response_style`. |
| **GitHub indexing** | | |
| `GITHUB_TOKEN` | *(optional)* | Personal access token for GitHub API. Required for private repos; increases rate limits for public repos. |
| `PINRAG_GITHUB_MAX_FILE_BYTES` | `524288` (512 KB) | Skip files larger than this when indexing GitHub repos. |
| `PINRAG_GITHUB_DEFAULT_BRANCH` | `main` | Default branch when not specified in the GitHub URL. |
| **Plain text indexing** | | |
| `PINRAG_PLAINTEXT_MAX_FILE_BYTES` | `524288` (512 KB) | Skip plain .txt files larger than this when indexing. |
| **YouTube transcript proxy** | | |
| `PINRAG_YT_PROXY_HTTP_URL` | *(none)* | HTTP proxy URL for transcript fetches (e.g. `http://user:pass@proxy:80`). Use when YouTube blocks your IP. |
| `PINRAG_YT_PROXY_HTTPS_URL` | *(none)* | HTTPS proxy URL for transcript fetches. Same as HTTP when using a generic proxy. |
| **Logging (MCP output)** | | |
| `PINRAG_LOG_TO_STDERR` | `false` | Set to `true` to send PinRAG logs (tool calls, completion timing, indexing messages) to stderr so they appear in the MCP server output in VS Code or Cursor. Default is off to avoid noisy or misleading badges in the editor. |
| `PINRAG_LOG_LEVEL` | `INFO` | Log level when `PINRAG_LOG_TO_STDERR=true`: `DEBUG`, `INFO`, `WARNING`, or `ERROR`. |
| **Evaluators (LLM-as-judge)** | | |
| `PINRAG_EVALUATOR_PROVIDER` | `openai` | `openai` or `anthropic` — which LLM grades correctness/relevance/groundedness/retrieval. Used only during evaluation runs (LangSmith experiments). |
| `PINRAG_EVALUATOR_MODEL` | *(provider default)* | Model for correctness/relevance (e.g. `gpt-4o`, `claude-sonnet-4-6`) |
| `PINRAG_EVALUATOR_MODEL_CONTEXT` | *(provider default)* | Model for groundedness/retrieval (context-heavy; e.g. `gpt-4o-mini`, `claude-haiku-4-5`) |

> **Re-indexing when changing embedding provider:** Changing `PINRAG_EMBEDDING_PROVIDER` requires re-indexing existing documents (indexes use provider-specific embedding dimensions). Alternatively use separate collections per provider (default behavior) and index into each when needed.
>
> **Re-indexing when enabling parent-child:** Setting `PINRAG_USE_PARENT_CHILD=true` requires re-indexing; the new structure (child chunks in Chroma, parent chunks in docstore) is created only during indexing.

### Monitoring & Observability

For query performance metrics (latency, timing, token usage) and debugging, use [LangSmith](https://smith.langchain.com). Set `LANGSMITH_TRACING=true` and `LANGSMITH_API_KEY` in `.env`; traces are sent automatically. For EU region, add `LANGSMITH_ENDPOINT=https://eu.api.smith.langchain.com`. See `notes/langsmith-setup.md` for setup. With `PINRAG_LOG_TO_STDERR=true`, tool completion timing is also logged to stderr.

### Multiple providers and collections

Embedding dimension depends on the provider (OpenAI 1536, Cohere 1024). To avoid dimension mismatches:

- **Default:** Collection name is `pinrag`. Use one embedding provider; if you switch provider, re-index or you will get dimension errors.
- **Per-provider collections:** Set `PINRAG_COLLECTION_NAME` to a provider-specific name (e.g. `pinrag_openai`, `pinrag_cohere`) when indexing, and use the same name when querying with that provider. You can index the same PDFs into multiple collections (switch env and index again) and switch by changing `PINRAG_EMBEDDING_PROVIDER` and `PINRAG_COLLECTION_NAME` in `.env`.
- **MCP tools:** The server uses `PINRAG_COLLECTION_NAME` (default `pinrag`) for all tools. Collection is not configurable per call; change it via `.env` to target a different collection.

## MCP Tools Reference

### `query_tool`

Ask a question and get an answer with citations. Optional filters narrow retrieval:

| Parameter | Description |
|-----------|-------------|
| `query` | Natural language question (required) |
| `document_id` | Search only in this document (e.g. `mybook.pdf` or video ID from `list_documents_tool`) |
| `page_min`, `page_max` | Restrict to page range (PDF only; single page: `page_min=16`, `page_max=16`) |
| `tag` | Search only documents with this tag (e.g. `AMIGA`, `PI_PICO`) |
| `document_type` | Search only by type: `pdf`, `youtube`, `discord`, `github`, or `plaintext` |
| `file_path` | Search only within this file (GitHub: e.g. `src/ria/api/atr.c`). Use `list_documents_tool` to see files. |
| `response_style` | Answer style: `thorough` (default) or `concise` |

Filters can be combined. Sources include `page` for PDFs and `start` (timestamp in seconds) for YouTube. Example: *"What is OpenOCD? In the Pico doc, pages 16–17 only"* →  
`query_tool(query="...", document_id="RP-008276-DS-1-getting-started-with-pico.pdf", page_min=16, page_max=17)`.

### `add_document_tool`

Index files, directories, YouTube videos, or GitHub repos.

| Parameter | Description |
|-----------|-------------|
| `paths` | List of paths to index (required). File, directory, YouTube URL, or GitHub URL. |
| `tags` | Optional list of tags, one per path (same order as paths) |
| `branch` | For GitHub URLs: override branch (default: main). Ignored for other formats. |
| `include_patterns` | For GitHub URLs: glob patterns for files to include (e.g. `["*.md", "src/**/*.py"]`) |
| `exclude_patterns` | For GitHub URLs: glob patterns to exclude |

### `list_documents_tool`

List indexed documents and chunk counts.

| Parameter | Description |
|-----------|-------------|
| `tag` | Optional: only list documents that have this tag |

### `remove_document_tool`

Remove a document and all its chunks from the index.

| Parameter | Description |
|-----------|-------------|
| `document_id` | Document identifier to remove (from `list_documents_tool`) |

### MCP Resources

Read-only resources; click in Cursor’s MCP panel to view:

| Resource | Description |
|----------|-------------|
| `pinrag://documents` | Indexed documents (IDs, chunk counts, tags, metadata) |
| `pinrag://server-config` | Env vars and config (LLM, embeddings, chunking, retrieval, logging; API key status) |

## Running tests

From the repo root (with dev dependencies, e.g. `uv sync --extra dev`):

- **Fast (no integration tests):** `uv run pytest tests/ -q -m "not integration"` — skips tests that need API keys, network, or the bundled sample PDF at `data/pdfs/sample-text.pdf`.
- **Full suite:** `uv run pytest tests/ -q` — set `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` as needed and ensure the sample PDF exists where tests expect it.

## License

MIT License. See [LICENSE](LICENSE) for details.
