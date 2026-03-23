<!-- mcp-name: io.github.ndjordjevic/pinrag -->

<p align="center">
  <img src="https://raw.githubusercontent.com/ndjordjevic/pinrag/main/docs/pinrag-icon.svg" width="96" height="96" alt="PinRAG logo" />
</p>

# PinRAG

[![PyPI](https://img.shields.io/github/v/release/ndjordjevic/pinrag?logo=pypi&logoColor=white&label=PyPI&sort=semver)](https://pypi.org/project/pinrag/) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![io.github.ndjordjevic/pinrag on MCP Marketplace](https://mcp-marketplace.io/api/badge?slug=io-github-ndjordjevic-pinrag)](https://mcp-marketplace.io/server/io-github-ndjordjevic-pinrag)

A powerful RAG (Retrieval-Augmented Generation) system built with LangChain, designed as an MCP (Model Context Protocol) server for Cursor, VS Code (GitHub Copilot), and other AI assistants.

## Overview

PinRAG provides intelligent document querying and retrieval for PDFs, plain text files, Discord chat exports, YouTube transcripts, and GitHub repositories. Index documents, ask questions, and get answers with source citations—all via MCP tools in your editor.

## Features

- **Multi-format indexing** — PDF (.pdf), local files or directories, plain text (.txt), Discord export (.txt), YouTube (video or playlist URL, or video ID), GitHub repo (URL)
- **RAG with citations** — Answers cite source context: PDF page, YouTube timestamp, document name for plain text and Discord, file path for GitHub repos
- **Document tags** — Tag documents at index time (e.g. `AMIGA`, `PI_PICO`) for filtered search
- **Metadata filtering** — `query_tool` supports `document_id`, `tag`, `document_type`, PDF `page_min`/`page_max`, GitHub `file_path`, and `response_style` (thorough or concise)
- **MCP tools** — `add_document_tool` (files, dirs, or URLs), `add_url_tool` (YouTube/GitHub URLs only), `query_tool`, `list_documents_tool`, `remove_document_tool`
- **MCP resources** — `pinrag://documents` (indexed documents) and `pinrag://server-config` (env vars and config); click in Cursor’s MCP panel to view
- **MCP prompt** — `use_pinrag` (parameter: request) for querying, indexing, listing, or removing documents
- **Configurable LLM** — OpenAI (default) or Anthropic; set via `PINRAG_LLM_PROVIDER` and `PINRAG_LLM_MODEL` in MCP `env` or your shell
- **Configurable embeddings** — OpenAI (default) or Cohere; set via `PINRAG_EMBEDDING_PROVIDER`. Use the same provider for indexing and querying (e.g. re-index after switching).
- **Retrieval & chunking options** — Structure-aware chunking (on by default); optional Cohere re-ranking, multi-query expansion, and parent-child chunks for PDFs (see Configuration)
- **Observability** — Optional [LangSmith](https://smith.langchain.com) tracing; optional stderr logging via `PINRAG_LOG_TO_STDERR`
- **Built with** — LangChain, Chroma; optional OpenAI, Anthropic, Cohere

## Installation

Most people add PinRAG **through the editor**—you do **not** need `pip install` or `pipx` first. Typical paths:

| Where | Link |
|-------|------|
| **MCP Marketplace** | [PinRAG on MCP Marketplace](https://mcp-marketplace.io/server/io-github-ndjordjevic-pinrag) |
| **Cursor Store** | [PinRAG on Cursor Store](https://www.cursor.store/mcp/ndjordjevic/pinrag) |
| **One-click (Cursor & VS Code)** | [Quick Start — One-click install](#one-click-install-cursor--vs-code) below |

Those flows use **`uvx --from pinrag pinrag-mcp`** (or the same idea in generated config) so the package is pulled from PyPI when the MCP server starts.

**Optional — global CLI on `PATH`:** If you want to run `pinrag-mcp` without `uvx` (for example `"command": "pinrag-mcp"` in `mcp.json`):

```bash
pipx install pinrag
# or: uv tool install pinrag
```

Requires Python 3.12+. Both `pipx` and `uv tool install` create an isolated environment and put `pinrag-mcp` on your PATH.

### Updating

**`uvx` / marketplace / one-click** (no global `pipx` install): PinRAG is resolved from PyPI when the MCP server starts, but **`uv` caches** that environment. After a new release on PyPI, refresh the cache so the next launch gets the latest build:

```bash
uvx --refresh --from pinrag pinrag-mcp
```

Alternatively, clear the tool cache (broader than refresh): `uv cache clean`. Then **restart Cursor / VS Code** (or toggle the MCP server) so it spawns a fresh `pinrag-mcp` process.

Re-running a marketplace “install” or re-applying one-click usually **does not** bump the cached `uvx` env by itself—you still need `--refresh` / cache clean when you want a new PyPI version.

If you use **`pipx` / `uv tool`**:

```bash
pipx upgrade pinrag
# or: uv tool upgrade pinrag
```

Restart your editor after updating so the MCP server picks up the new version.

## Quick Start

### One-click install (Cursor & VS Code)

These links add PinRAG to your editor’s MCP config using **`uvx --from pinrag pinrag-mcp`** (runs the latest PinRAG from PyPI without a prior `pip install`). You need [**uv**](https://docs.astral.sh/uv/) installed and on your `PATH`.

| Editor | Action |
|--------|--------|
| **Cursor** | [Install PinRAG MCP in Cursor](https://cursor.com/en/install-mcp?name=pinrag&config=eyJjb21tYW5kIjoidXZ4IiwiYXJncyI6WyItLWZyb20iLCJwaW5yYWciLCJwaW5yYWctbWNwIl0sImVudiI6eyJPUEVOQUlfQVBJX0tFWSI6IiIsIlBJTlJBR19QRVJTSVNUX0RJUiI6IiJ9fQ) |
| **VS Code** | [Install PinRAG MCP in VS Code](https://ndjordjevic.github.io/pinrag/vscode-mcp-install.html) |

The one-click links **pre-fill** your MCP `env` with empty `OPENAI_API_KEY` (required—paste your key) and `PINRAG_PERSIST_DIR` (optional—set an absolute path for a stable index location, or remove the key). No secrets are embedded. If you prefer **`pinrag-mcp`** after `pipx install pinrag`, use the JSON snippets in the next section instead of the links above.

To pick up a **new PyPI release** with this `uvx` setup, follow [Updating](#updating) above (`uvx --refresh`, then restart the editor).

To **see which version you’re on**, run `pipx list` if you use pipx, or `uvx --from pinrag python -c "import importlib.metadata as m; print(m.version('pinrag'))"` to print the version `uvx` resolves (PyPI metadata).

> **VS Code:** GitHub does not allow `vscode:` URLs as clickable links in READMEs. The table link opens a small landing page (GitHub Pages) with the real **Install in VS Code** button. If the page is not yet live, open [`docs/vscode-mcp-install.html`](docs/vscode-mcp-install.html) from a local clone.

### Configure MCP server

Add `pinrag` to your editor’s MCP config and set API keys in the same `env` block. This is the recommended setup for OSS: `pinrag-mcp` is launched by the editor from MCP config, not from a shell that loads `.env`.

**Minimum required env vars (validated at startup):**

The server validates required API keys at startup and exits with a clear error
if any are missing. Set keys in your MCP `env` block as in the examples below.

- **Default setup** (OpenAI embeddings + OpenAI chat): set `OPENAI_API_KEY` only.
- **Anthropic for queries:** set `PINRAG_LLM_PROVIDER=anthropic` and `ANTHROPIC_API_KEY` (keep `OPENAI_API_KEY` for default embeddings unless you also change embedding provider).
- **Cohere embeddings:** set `PINRAG_EMBEDDING_PROVIDER=cohere` and `COHERE_API_KEY`; you still need an LLM key (`OPENAI_API_KEY` or `ANTHROPIC_API_KEY` depending on `PINRAG_LLM_PROVIDER`).

A longer commented reference for optional `PINRAG_*` variables is in [`notes/env-vars.example.md`](notes/env-vars.example.md).

**Cursor:** Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "pinrag": {
      "command": "pinrag-mcp",
      "env": {
        "OPENAI_API_KEY": "sk-..."
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
        "OPENAI_API_KEY": "sk-..."
      }
    }
  }
}
```

Or create `.vscode/mcp.json` in your workspace for project-specific setup. Restart VS Code or Cursor after editing.

> **Env vars and `.env`:** The `pinrag-mcp` entry point does not load `.env` files.
> Configure variables in your MCP `env` block (or export them in your shell when running other scripts).
> If you previously used `~/.pinrag/.env` or project `.env`, move those keys to MCP `env`.
> **Backup:** Back up your vector store directory (`PINRAG_PERSIST_DIR`). If unset, the default is `chroma_db` relative to the **current working directory of the `pinrag-mcp` process** (depends on the editor—often the folder you have open, but not guaranteed). Set `PINRAG_PERSIST_DIR` to an absolute path (e.g. `~/.pinrag/chroma_db`) if you want a predictable location. Deleting that directory removes all indexes.

### Use in chat

| Action | Tool |
|--------|------|
| Index files, directories, or URLs | `add_document_tool` — `paths` as a list (e.g. PDFs, `.txt`, dirs, YouTube or playlist URLs, GitHub URLs); optional `tags` (one per path). For **URLs only**, you can use `add_url_tool` instead. |
| List indexed documents | `list_documents_tool` — document IDs, chunk counts, optional tag filter; `document_details` includes metadata such as tags, page counts, titles, and `upload_timestamp` when stored |
| Query with filters | `query_tool` — optional `document_id`, `tag`, `document_type`, `page_min`/`page_max` (PDF), `file_path` (GitHub), `response_style` |
| Remove a document | `remove_document_tool` |
| View resources (read-only) | In the MCP panel, open **Resources** and select `pinrag://documents` (indexed docs) or `pinrag://server-config` (effective config) |

Ask in chat: *"Add /path/to/amiga-book.pdf with tag AMIGA"*, *"Index https://youtu.be/xyz and ask what it says"*, or *"Index https://github.com/owner/repo and ask about the codebase"*. The AI will invoke the tools for you. Citations show page numbers for PDFs, timestamps (e.g. `t. 1:23`) for YouTube, document names for plain text and Discord exports, and file paths for GitHub.

### GitHub indexing

Index a GitHub repository to ask questions about its code and docs. Use `add_document_tool` with a GitHub URL (or `add_url_tool` if you only pass URLs):

- `https://github.com/owner/repo`
- `https://github.com/owner/repo/tree/branch`
- `github.com/owner/repo` (no scheme)

Optional parameters for GitHub URLs: `branch`, `include_patterns` (e.g. `["*.md", "src/**/*.py"]`), `exclude_patterns`. Set `GITHUB_TOKEN` in MCP `env` or your shell for private repos or higher API rate limits. Files larger than `PINRAG_GITHUB_MAX_FILE_BYTES` (default 512 KiB) are skipped. By default, only common text/source extensions are indexed; other paths are omitted unless you widen the set with `include_patterns` (defaults also exclude many non-text artifacts such as images and archives).

**Authentication and rate limits:** Without a token, GitHub’s API applies **unauthenticated** per-IP rate limits (suitable for light use of public repos). For **private** repositories, or to reduce throttling when indexing large repos, set **`GITHUB_TOKEN`** (classic PAT or fine-grained token with read access to the repo). PinRAG does not implement OAuth for end users; the token is the supported way to authenticate the server process to GitHub.

### YouTube indexing and IP blocking

YouTube often blocks transcript requests from IPs that have made too many requests or from cloud provider IPs (AWS, GCP, Azure, etc.). When indexing playlists or many videos, you may see errors like *"YouTube is blocking requests from your IP"*.

**Workaround:** Use an HTTP/HTTPS proxy. Set in MCP `env` or your shell:

```env
PINRAG_YT_PROXY_HTTP_URL=http://user:pass@proxy.example.com:80
PINRAG_YT_PROXY_HTTPS_URL=http://user:pass@proxy.example.com:80
```

Rotating proxy services (e.g. [Webshare](https://www.webshare.io/)) work well; residential proxies are often more reliable than datacenter IPs for avoiding YouTube blocks. `PINRAG_YT_PROXY_*` is wired only into `youtube-transcript-api` transcript fetches (other steps, such as title lookup or playlist listing via yt-dlp, do not use these variables).

When `add_document_tool` or `add_url_tool` returns any failed paths (e.g. some videos in a playlist), the response includes a `fail_summary` when failures are present. Counts are grouped by matching error text—mainly useful for transcript issues: `blocked` (IP blocking), `disabled` (transcripts disabled by creator), `missing_transcript`, and `other` (everything else, including non-YouTube failures).

### Tips

- **`pinrag-mcp` not found:** The editor runs MCP with your login environment. After `pipx` / `uv tool install`, restart the editor and confirm `pinrag-mcp` is on `PATH` (e.g. `which pinrag-mcp` in a terminal).
- **Stable vector store path:** Add `PINRAG_PERSIST_DIR` to the MCP `env` block (absolute path, e.g. `~/.pinrag/chroma_db`) so indexes are not tied to the server process working directory.
- **Cohere embeddings or re-ranking:** Install the extra in the same environment as `pinrag-mcp`, e.g. `pipx install 'pinrag[cohere]'` or `uv tool install 'pinrag[cohere]'` (see **Configuration**).
- **Check the running server:** Open the `pinrag://server-config` resource in the MCP panel to see effective LLM, embeddings, chunking, and API key status.

## Configuration

The MCP resource `pinrag://server-config` shows the main operational vars (LLM, embeddings, chunking, retrieval, logging) and API key status. The table below documents all supported variables.

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| **LLM** | | |
| `PINRAG_LLM_PROVIDER` | `openai` | `openai` or `anthropic` |
| `PINRAG_LLM_MODEL` | *(provider default)* | e.g. `claude-haiku-4-5`, `claude-sonnet-4-6`, `gpt-4o-mini` |
| `OPENAI_API_KEY` | *(required for OpenAI)* | OpenAI API key (LLM or embeddings) |
| `ANTHROPIC_API_KEY` | *(required for Anthropic)* | Anthropic API key (when `PINRAG_LLM_PROVIDER=anthropic` or `PINRAG_EVALUATOR_PROVIDER=anthropic`) |
| **Embeddings** | | |
| `PINRAG_EMBEDDING_PROVIDER` | `openai` | `openai` or `cohere` |
| `PINRAG_EMBEDDING_MODEL` | *(provider default)* | e.g. `text-embedding-3-small`, `embed-english-v3.0` |
| `COHERE_API_KEY` | *(required for Cohere)* | Cohere API key; install with `pip install pinrag[cohere]` when using Cohere embeddings or re-ranking |
| **Storage & chunking** | | |
| `PINRAG_PERSIST_DIR` | `chroma_db` | Chroma vector store directory (default is relative to the server process cwd unless you set an absolute path; e.g. `~/.pinrag/chroma_db` for a fixed location) |
| `PINRAG_CHUNK_SIZE` | `1000` | Text chunk size (chars) |
| `PINRAG_CHUNK_OVERLAP` | `200` | Chunk overlap (chars) |
| `PINRAG_STRUCTURE_AWARE_CHUNKING` | `true` | Apply structure-aware chunking heuristics for code/table boundaries |
| `PINRAG_COLLECTION_NAME` | `pinrag` | Chroma collection name. Single shared collection by default. |
| `ANONYMIZED_TELEMETRY` | `False` if unset | Chroma reads this for anonymous usage telemetry (PostHog). PinRAG sets it to `False` at startup when unset, to reduce noise in MCP/editor logs. Set explicitly in MCP `env` or your shell if you want Chroma’s default. |
| **Retrieval** | | |
| `PINRAG_RETRIEVE_K` | `20` | Chunks to retrieve when re-ranking is off. When `PINRAG_USE_RERANK=true`, `PINRAG_RERANK_RETRIEVE_K` defaults to this value if unset. |
| **Parent-child retrieval** | | |
| `PINRAG_USE_PARENT_CHILD` | `false` | Set to `true` to embed small chunks and return larger parent chunks (supported for PDF, GitHub, YouTube, and Discord indexing—not plain `.txt`). Requires re-indexing. |
| `PINRAG_PARENT_CHUNK_SIZE` | `2000` | Parent chunk size (chars) when `PINRAG_USE_PARENT_CHILD=true`. |
| `PINRAG_CHILD_CHUNK_SIZE` | `800` | Child chunk size (chars) when `PINRAG_USE_PARENT_CHILD=true`. |
| **Re-ranking** | | |
| `PINRAG_USE_RERANK` | `false` | Set to `true` to enable Cohere Re-Rank: fetch more chunks, re-score with Cohere, pass top N to the LLM. Requires `pip install pinrag[cohere]` and `COHERE_API_KEY`. |
| `PINRAG_RERANK_RETRIEVE_K` | `20` | Chunks to fetch before reranking when `PINRAG_USE_RERANK=true`. If unset, uses `PINRAG_RETRIEVE_K`. |
| `PINRAG_RERANK_TOP_N` | `10` | Chunks passed to the LLM after re-ranking when `PINRAG_USE_RERANK=true` (capped by the pre-rerank fetch size). |
| **Multi-query** | | |
| `PINRAG_USE_MULTI_QUERY` | `false` | Set to `true` to generate alternative phrasings of the user query via LLM, retrieve per variant, and merge (unique union). Improves recall for terse or ambiguous queries. |
| `PINRAG_MULTI_QUERY_COUNT` | `4` | Number of **alternative** queries to generate (default 4, max 10). The original query is still included in retrieval when merging. |
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
| `PINRAG_EVALUATOR_PROVIDER` | `openai` | `openai` or `anthropic` — which LLM runs LLM-as-judge graders. Used only during evaluation runs (LangSmith experiments). |
| `PINRAG_EVALUATOR_MODEL` | *(provider default)* | Model for **correctness** grading (e.g. `gpt-4o`, `claude-sonnet-4-6`) |
| `PINRAG_EVALUATOR_MODEL_CONTEXT` | *(provider default)* | Model for **groundedness** grading (large retrieved context; e.g. `gpt-4o-mini`, `claude-haiku-4-5`) |

> **Re-indexing when changing embedding provider:** Changing `PINRAG_EMBEDDING_PROVIDER` requires re-indexing existing documents (indexes use provider-specific embedding dimensions). Alternatively use separate collections per provider (default behavior) and index into each when needed.
>
> **Re-indexing when enabling parent-child:** Setting `PINRAG_USE_PARENT_CHILD=true` requires re-indexing; the new structure (child chunks in Chroma, parent chunks in docstore) is created only during indexing for supported document types (not plain `.txt`).

### Monitoring & Observability

For query performance metrics (latency, timing, token usage) and debugging, use [LangSmith](https://smith.langchain.com). Set `LANGSMITH_TRACING=true` and `LANGSMITH_API_KEY` in MCP `env` or your shell; traces are sent automatically. For EU region, add `LANGSMITH_ENDPOINT=https://eu.api.smith.langchain.com`. See `notes/langsmith-setup.md` for setup. With `PINRAG_LOG_TO_STDERR=true`, tool completion timing is also logged to stderr.

### Multiple providers and collections

Embedding dimension depends on the provider (OpenAI 1536, Cohere 1024). To avoid dimension mismatches:

- **Default:** Collection name is `pinrag`. Use one embedding provider; if you switch provider, re-index or you will get dimension errors.
- **Per-provider collections:** Set `PINRAG_COLLECTION_NAME` to a provider-specific name (e.g. `pinrag_openai`, `pinrag_cohere`) when indexing, and use the same name when querying with that provider. You can index the same PDFs into multiple collections (switch env and index again) and switch by changing `PINRAG_EMBEDDING_PROVIDER` and `PINRAG_COLLECTION_NAME` in MCP `env` or your shell.
- **MCP tools:** The server uses `PINRAG_COLLECTION_NAME` (default `pinrag`) for all tools. Collection is not configurable per call; change it via MCP `env` or your shell to target a different collection.

## MCP reference

Tools, optional prompt, and read-only resources from the PinRAG MCP server (`pinrag-mcp`). Indexing tools return `indexed` / `failed` / totals (and `fail_summary` when some paths fail); `query_tool` returns an answer plus citation metadata.

### `query_tool`

Ask a question and get an answer with citations. Optional filters narrow retrieval (omit or leave empty when unused):

| Parameter | Description |
|-----------|-------------|
| `query` | Natural language question (required) |
| `document_id` | Search only in this document (e.g. `mybook.pdf` or video ID from `list_documents_tool`) |
| `page_min`, `page_max` | Restrict to page range (PDF only; single page: `page_min=16`, `page_max=16`) |
| `tag` | Search only documents with this tag (e.g. `AMIGA`, `PI_PICO`) |
| `document_type` | Search only by type: `pdf`, `youtube`, `discord`, `github`, or `plaintext` |
| `file_path` | Search only within this file (GitHub: e.g. `src/ria/api/atr.c`). Use `list_documents_tool` to see files. |
| `response_style` | Answer style: `thorough` (default) or `concise` (invalid values fall back to `PINRAG_RESPONSE_STYLE`) |

Filters can be combined. Citations use PDF **page** numbers, YouTube **start** time (seconds), **document** identifiers for plain text and Discord, and repo **file paths** for GitHub. Example: *"What is OpenOCD? In the Pico doc, pages 16–17 only"* →  
`query_tool(query="...", document_id="RP-008276-DS-1-getting-started-with-pico.pdf", page_min=16, page_max=17)`.

### `add_document_tool`

Index local files or directories, plain or Discord `.txt`, PDFs, YouTube (video, playlist, or ID), or GitHub repos (URL may omit `https://`). Batches multiple paths; one failure does not roll back the rest.

| Parameter | Description |
|-----------|-------------|
| `paths` | List of paths to index (required). File, directory, YouTube URL or ID, or GitHub URL. |
| `tags` | Optional list of tags, one per path (same order as paths) |
| `branch` | For GitHub URLs: override branch (default: main). Ignored for other formats. |
| `include_patterns` | For GitHub URLs: glob patterns for files to include (e.g. `["*.md", "src/**/*.py"]`) |
| `exclude_patterns` | For GitHub URLs: glob patterns to exclude |

### `add_url_tool`

Same indexing pipeline as `add_document_tool`, but **only HTTP(S) URLs**—each entry must start with `http://` or `https://`. Use this for remote YouTube or GitHub only; for local paths or schemeless `github.com/...` URLs, use `add_document_tool`.

| Parameter | Description |
|-----------|-------------|
| `paths` | List of URLs to index (required). YouTube video/playlist or GitHub repo. |
| `tags` | Optional list of tags, one per URL |
| `branch` | For GitHub URLs: override branch (default: main) |
| `include_patterns` | For GitHub URLs: glob patterns for files to include |
| `exclude_patterns` | For GitHub URLs: glob patterns to exclude |

### `list_documents_tool`

List indexed document IDs, total chunk count, `persist_directory`, `collection_name`, and per-document metadata in `document_details` (tags, titles, `upload_timestamp`, GitHub file lists when applicable).

| Parameter | Description |
|-----------|-------------|
| `tag` | Optional: only list documents that have this tag |

### `remove_document_tool`

Remove one logical document and all its chunks from the index.

| Parameter | Description |
|-----------|-------------|
| `document_id` | Document identifier to remove (from `list_documents_tool`) |

### MCP prompt: `use_pinrag`

Returns fixed guidance text for the assistant describing when to call each tool. Optional parameter **`request`** is embedded at the top (what to index, list, query, or remove); the rest summarizes `query_tool`, `add_url_tool`, `add_document_tool`, `list_documents_tool`, and `remove_document_tool`. Shown in clients that list MCP prompts (e.g. Cursor).

| Parameter | Description |
|-----------|-------------|
| `request` | Free-text goal (optional; may be empty). |

### MCP resources

Read-only URIs; open from the MCP panel in Cursor or VS Code:

| Resource | Description |
|----------|-------------|
| `pinrag://documents` | Plain-text list of indexed documents (IDs, chunk counts, tags, and format-specific metadata) |
| `pinrag://server-config` | Effective env and config (LLM, embeddings, chunking, retrieval, logging; API key presence) |

## Running tests

From the repo root (with dev dependencies, e.g. `uv sync --extra dev`):

- **Fast (exclude `integration`):** `uv run pytest tests/ -q -m "not integration"` — skips tests marked `integration` (see `pyproject.toml`: API keys, network, optional assets, MCP stdio). Tests that use the `sample_pdf_path` fixture are tagged as `integration` automatically (`tests/conftest.py`). A few non-integration tests may still `skip` if `data/pdfs/sample-text.pdf` is missing.
- **Full suite:** `uv run pytest tests/ -q` — set `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` via the environment or `tests/.mcp_stdio_integration.env` (copy from `tests/mcp_stdio_integration.env.example`; environment wins over the file). PDF/RAG tests and MCP stdio integration tests (`test_mcp_stdio_*.py`) expect `data/pdfs/sample-text.pdf` locally (under `data/`, gitignored); override path or query with `PINRAG_MCP_ITEST_PDF` / `PINRAG_MCP_ITEST_QUERY` for the stdio tests. To skip the PyPI-based MCP test (network / `uv tool run --from pinrag pinrag-mcp`), use `-m "not pypi_mcp"` or `PINRAG_MCP_ITEST_SKIP_PYPI=1`. For live logs from those tests, add `--log-cli-level=INFO`.

The `data/` tree is gitignored (create `data/pdfs/` or `data/discord-channels/` locally; nothing under `data/` is committed).

## License

MIT License. Full text in [LICENSE](LICENSE).
