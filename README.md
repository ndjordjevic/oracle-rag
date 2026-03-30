<!-- mcp-name: io.github.ndjordjevic/pinrag -->

<!-- Raster PNG: many directories (e.g. MCP Market) strip HTML or block SVG in READMEs; plain Markdown image survives more often. -->
![PinRAG logo](https://raw.githubusercontent.com/ndjordjevic/pinrag/main/docs/pinrag-icon.png)

# PinRAG

[![PyPI](https://img.shields.io/github/v/release/ndjordjevic/pinrag?logo=pypi&logoColor=white&label=PyPI&sort=semver)](https://pypi.org/project/pinrag/) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![io.github.ndjordjevic/pinrag on MCP Marketplace](https://mcp-marketplace.io/api/badge?slug=io-github-ndjordjevic-pinrag)](https://mcp-marketplace.io/server/io-github-ndjordjevic-pinrag) [![pinrag MCP server](https://glama.ai/mcp/servers/ndjordjevic/pinrag/badges/score.svg)](https://glama.ai/mcp/servers/ndjordjevic/pinrag)

A powerful RAG (Retrieval-Augmented Generation) system built with LangChain, designed as an MCP (Model Context Protocol) server for Cursor, VS Code (GitHub Copilot), and other AI assistants.

## Overview

PinRAG provides intelligent document querying and retrieval for PDFs, plain text files, Discord chat exports, YouTube transcripts, and GitHub repositories. Index documents, ask questions, and get answers with source citations—all via MCP tools in your editor. For YouTube, you can optionally enrich transcript-only indexing with **vision** (on-screen code, diagrams, and UI text) merged into the same chunks—see [YouTube vision enrichment](#youtube-vision-enrichment-optional).

## Demo

Screen recording: indexing a PDF and using PinRAG from VS Code.

<video src="docs/pinrag-demo.mp4" width="100%" controls playsinline></video>

[Direct link to the video file](docs/pinrag-demo.mp4) if the player does not load.

## Features

- **Multi-format indexing** — PDF (.pdf), local files or directories, plain text (.txt), Discord export (.txt), YouTube (video or playlist URL, or video ID), GitHub repo (URL)
- **Optional YouTube vision** — Off by default. When enabled, runs a vision model (OpenAI, Anthropic, or OpenRouter native video) and merges structured on-screen context with the transcript so RAG chunks carry searchable code names, labels, and diagrams—not speech alone. OpenRouter mode avoids local ffmpeg/video download; openai/anthropic use scene keyframes and require `pinrag[vision]` + **ffmpeg** (see [YouTube vision enrichment](#youtube-vision-enrichment-optional))
- **RAG with citations** — Answers cite source context: PDF page, YouTube timestamp, document name for plain text and Discord, file path for GitHub repos
- **Document tags** — Tag documents at index time (e.g. `AMIGA`, `PI_PICO`) for filtered search
- **Metadata filtering** — `query_tool` supports `document_id`, `tag`, `document_type`, PDF `page_min`/`page_max`, GitHub `file_path`, and `response_style` (thorough or concise)
- **MCP tools** — `add_document_tool` (files, dirs, or URLs), `add_url_tool` (YouTube/GitHub URLs only), `query_tool`, `list_documents_tool`, `remove_document_tool`
- **MCP resources** — `pinrag://documents` (indexed documents) and `pinrag://server-config` (env vars and config); click in Cursor’s MCP panel to view
- **MCP prompt** — `use_pinrag` (parameter: request) for querying, indexing, listing, or removing documents
- **Configurable LLM** — OpenRouter (default, free `openrouter/free` router), OpenAI, or Anthropic; set via `PINRAG_LLM_PROVIDER` and `PINRAG_LLM_MODEL` in MCP `env` or your shell
- **Local embeddings** — Nomic (`PINRAG_EMBEDDING_MODEL`, default `nomic-embed-text-v1.5`); no API key; first run downloads model weights (~270 MB, cached)
- **Retrieval & chunking options** — Structure-aware chunking (on by default); optional FlashRank re-ranking, multi-query expansion, and parent-child chunks for PDFs (see Configuration)
- **Observability** — MCP tool notifications (`ctx.log`) plus optional [LangSmith](https://smith.langchain.com) tracing
- **Built with** — LangChain, Chroma; optional OpenRouter, OpenAI, Anthropic, FlashRank

## Installation

Most people add PinRAG **through the editor**—you do **not** need `pip install` or `pipx` first. Typical paths:

| Where | Link |
|-------|------|
| **MCP Marketplace** | [PinRAG on MCP Marketplace](https://mcp-marketplace.io/server/io-github-ndjordjevic-pinrag) |
| **MCPRepository** | [PinRAG on MCPRepository](https://mcprepository.com/ndjordjevic/pinrag) |
| **Glama** | [PinRAG on Glama](https://glama.ai/mcp/servers/ndjordjevic/pinrag) |
| **Cursor Store** | [PinRAG on Cursor Store](https://www.cursor.store/mcp/ndjordjevic/pinrag) |
| **One-click (Cursor & VS Code)** | [Quick Start — One-click install](#one-click-install-cursor--vs-code) below |

Those flows use **`uvx --refresh pinrag`** (or the same idea in generated config: `"command": "uvx"`, `"args": ["--refresh", "pinrag"]`) so each MCP launch resolves the latest `pinrag` from PyPI (`uv` caches tool environments; `--refresh` avoids stale installs).

**Optional — global CLI on `PATH`:** If you want to run `pinrag` without `uvx` (for example `"command": "pinrag"` in `mcp.json`):

```bash
pipx install pinrag
# or: uv tool install pinrag
```

Requires Python 3.12+. Both `pipx` and `uv tool install` create an isolated environment and put `pinrag` on your PATH.

### Updating

**`uvx` (marketplace / one-click / manual MCP config):** The docs and install links use **`"args": ["--refresh", "pinrag"]`**. That tells `uvx` to **re-resolve PinRAG from PyPI on every MCP startup**, so you normally **do not** bump versions by hand—new releases show up after you restart the editor or restart the server. Tradeoff: a bit **slower cold start** than `uvx` hitting a warm cache (`"args": ["pinrag"]` only).

If you **removed `--refresh`** and want the latest build without changing config, run `uvx --refresh pinrag` once, or use `uv cache clean` (broader). Then restart the MCP server or the editor. Re-applying a one-click link **without** `--refresh` in `args` will not fix a stale cache by itself.

**`pipx` / `uv tool`** (global `pinrag` on `PATH`): upgrade explicitly, then restart the editor:

```bash
pipx upgrade pinrag
# or: uv tool upgrade pinrag
```

## Quick Start

### One-click install (Cursor & VS Code)

These links add PinRAG to your editor’s MCP config using **`uvx --refresh pinrag`** (same as `"args": ["--refresh", "pinrag"]`; always resolves the latest PinRAG from PyPI without a prior `pip install`). You need [**uv**](https://docs.astral.sh/uv/) installed and on your `PATH`.

| Editor | Action |
|--------|--------|
| **Cursor** | [Install PinRAG MCP in Cursor](https://cursor.com/en/install-mcp?name=pinrag&config=eyJjb21tYW5kIjoidXZ4IiwiYXJncyI6WyItLXJlZnJlc2giLCJwaW5yYWciXSwiZW52Ijp7Ik9QRU5BSV9BUElfS0VZIjoiIiwiUElOUkFHX1BFUlNJU1RfRElSIjoiIn19) |
| **VS Code** | [Install PinRAG MCP in VS Code](https://ndjordjevic.github.io/pinrag/vscode-mcp-install.html) |

The one-click links **pre-fill** your MCP `env` with empty `OPENAI_API_KEY` (required—paste your key) and `PINRAG_PERSIST_DIR` (optional—set an absolute path for a stable index location, or remove the key). No secrets are embedded. If you prefer **`pinrag`** on `PATH` after `pipx install pinrag`, use the JSON snippets in the next section instead of the links above.

To pick up a **new PyPI release** with this `uvx` setup, use **`--refresh`** in `args` (see [Updating](#updating) above) or run `uvx --refresh pinrag` once, then restart the editor.

To **see which version you’re on**, run `pipx list` if you use pipx, or `uvx --from pinrag python -c "import importlib.metadata as m; print(m.version('pinrag'))"` to print the version `uvx` resolves (PyPI metadata). With the MCP server running, open **`pinrag://server-config`** in the MCP panel—the output starts with **`PINRAG_VERSION`**, which is the package version of that process.

> **VS Code:** GitHub does not allow `vscode:` URLs as clickable links in READMEs. The table link opens a small landing page (GitHub Pages) with the real **Install in VS Code** button. If the page is not yet live, open [`docs/vscode-mcp-install.html`](docs/vscode-mcp-install.html) from a local clone.

### Configure MCP server

Add PinRAG to your editor’s MCP config and set API keys in the same `env` block. For **PyPI installs via `uvx`**, use `"command": "uvx"` and `"args": ["--refresh", "pinrag"]` so each launch picks up the latest release (see [Updating](#updating)). If you use a **global** `pinrag` on `PATH` (`pipx` / `uv tool install`), set `"command": "pinrag"` and omit `args`. The server is launched by the editor from MCP config, not from a shell that loads `.env`.

**Minimum required env vars (validated at startup):**

The server validates required API keys at startup and exits with a clear error
if any are missing. Set keys in your MCP `env` block as in the examples below.

- **Default setup** (local embeddings + OpenRouter chat): set `OPENROUTER_API_KEY` for the LLM (get a key at [openrouter.ai](https://openrouter.ai/)).
- **OpenAI instead:** set `PINRAG_LLM_PROVIDER=openai` and `OPENAI_API_KEY`.
- **Anthropic for queries:** set `PINRAG_LLM_PROVIDER=anthropic` and `ANTHROPIC_API_KEY` (no OpenRouter/OpenAI key needed for chat unless you use them for vision or evaluators).
- **Optional re-ranking:** set `PINRAG_USE_RERANK=true` and install `pinrag[rerank]` (no API key required).

A longer commented reference for optional `PINRAG_*` variables is in [`notes/env-vars.example.md`](notes/env-vars.example.md).

**Cursor:** Add to `~/.cursor/mcp.json` (recommended **PyPI via `uvx`** — matches one-click and always-latest behavior):

```json
{
  "mcpServers": {
    "pinrag": {
      "command": "uvx",
      "args": ["--refresh", "pinrag"],
      "env": {
        "OPENAI_API_KEY": "sk-..."
      }
    }
  }
}
```

If you installed **`pinrag` globally** (`pipx` / `uv tool install`), you can use `"command": "pinrag"` without `args` instead.

**VS Code (GitHub Copilot):** Run **MCP: Open User Configuration** from the Command Palette, then add:

```json
{
  "servers": {
    "pinrag": {
      "command": "uvx",
      "args": ["--refresh", "pinrag"],
      "env": {
        "OPENAI_API_KEY": "sk-..."
      }
    }
  }
}
```

Or create `.vscode/mcp.json` in your workspace for project-specific setup. Restart VS Code or Cursor after editing.

> **Env vars and `.env`:** The `pinrag` entry point does not load `.env` files.
> Configure variables in your MCP `env` block (or export them in your shell when running other scripts).
> If you previously used `~/.pinrag/.env` or project `.env`, move those keys to MCP `env`.
> **Backup:** Back up your vector store directory (`PINRAG_PERSIST_DIR`). If unset, the default is `chroma_db` relative to the **current working directory of the `pinrag` process** (depends on the editor—often the folder you have open, but not guaranteed). Set `PINRAG_PERSIST_DIR` to an absolute path (e.g. `~/.pinrag/chroma_db`) if you want a predictable location. Deleting that directory removes all indexes.

### Use in chat

| Action | Tool |
|--------|------|
| Index files, directories, or URLs | `add_document_tool` — `paths` as a list (e.g. PDFs, `.txt`, dirs, YouTube or playlist URLs, GitHub URLs); optional `tags` (one per path). For **URLs only**, you can use `add_url_tool` instead. |
| List indexed documents | `list_documents_tool` — document IDs, chunk counts, optional tag filter; `document_details` includes metadata such as tags, page counts, titles, and `upload_timestamp` when stored |
| Query with filters | `query_tool` — optional `document_id`, `tag`, `document_type`, `page_min`/`page_max` (PDF), `file_path` (GitHub), `response_style` |
| Remove a document | `remove_document_tool` |
| View resources (read-only) | In the MCP panel, open **Resources** and select `pinrag://documents` (indexed docs) or `pinrag://server-config` (effective config, including **`PINRAG_VERSION`**) |

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

### YouTube vision enrichment (optional)

By default, YouTube indexing uses **transcripts only**. Set `PINRAG_YT_VISION_ENABLED=true` to also call a **vision model** that describes what is on screen (code editors, terminals, diagrams). Descriptions are **aligned to transcript timestamps** and merged into the same LangChain documents before chunking, with metadata such as `has_visual`, `frame_count`, and `visual_source`.

**Two vision modes (`PINRAG_YT_VISION_PROVIDER`):**

- **`openai`** (default) or **`anthropic`**: **download the video** with `yt-dlp`, detect scene changes, extract still frames, and run **one multimodal call per frame** (needs `pinrag[vision]`, **ffmpeg** on `PATH`, and `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`).
- **`openrouter`**: **single request** per video using OpenRouter’s native **`video_url`** payload and the public YouTube watch URL (default model `google/gemini-2.5-flash`); requires **`OPENROUTER_API_KEY`** only—no local download, ffmpeg, or `pinrag[vision]`.

**What to install for openai/anthropic vision (not needed for openrouter):**

| Requirement | Purpose |
|-------------|---------|
| **`pinrag[vision]`** | Python extra that pulls in PySceneDetect (and OpenCV) for scene detection. Example: `uv sync --extra vision` in a clone, or `pip install 'pinrag[vision]'` / `pipx install 'pinrag[vision]'` in the same environment as `pinrag`. |
| **ffmpeg** (and **ffprobe**, usually bundled) | Frame extraction and duration probing. Must be on `PATH` for the MCP process. |

`yt-dlp` is a core dependency and is used to **download** the video only for **openai** / **anthropic** vision.

**Operational notes:**

- **Re-index** after enabling vision or changing vision settings; existing chunks are not upgraded in place.
- **Cost and time:** For openai/anthropic, each analyzed frame is a multimodal API call; limiting frames (see `PINRAG_YT_VISION_MAX_FRAMES`) keeps MCP/tool timeouts reasonable. OpenAI `PINRAG_YT_VISION_IMAGE_DETAIL=high` improves small on-screen text at higher token usage per image. OpenRouter mode uses one larger call per video; pick a video-capable model on OpenRouter.
- **MCP stdio:** PinRAG sends yt-dlp progress to stderr so stdout stays valid JSON for the MCP transport.
- **Compliance:** Downloading and processing YouTube video may be restricted by YouTube’s Terms of Service or local law; use at your own risk.

Docker images can include vision support by building with **`BUILD_WITH_VISION=1`** (installs ffmpeg and `pinrag[vision]` in the image); see the `Dockerfile` in this repository.

### Tips

- **`pinrag` not found:** The editor runs MCP with your login environment. After `pipx` / `uv tool install`, restart the editor and confirm `pinrag` is on `PATH` (e.g. `which pinrag` in a terminal).
- **Stable vector store path:** Add `PINRAG_PERSIST_DIR` to the MCP `env` block (absolute path, e.g. `~/.pinrag/chroma_db`) so indexes are not tied to the server process working directory.
- **FlashRank re-ranking:** Install the extra in the same environment as `pinrag`, e.g. `pipx install 'pinrag[rerank]'` or `uv tool install 'pinrag[rerank]'` (see **Configuration**).
- **YouTube vision:** Set `PINRAG_YT_VISION_ENABLED=true` and choose `PINRAG_YT_VISION_PROVIDER` (`openrouter` needs `OPENROUTER_API_KEY`; `openai`/`anthropic` need `pinrag[vision]`, **ffmpeg**, and the matching API key). Re-index videos (see [YouTube vision enrichment](#youtube-vision-enrichment-optional)).
- **Check the running server:** Open the `pinrag://server-config` resource in the MCP panel to see **`PINRAG_VERSION`**, effective LLM, embeddings, chunking, and API key status.

## Configuration

The MCP resource `pinrag://server-config` shows **`PINRAG_VERSION`** (running package version) and the main operational vars (LLM, embeddings, chunking, retrieval, logging), plus API key status. The table below documents all supported environment variables (`PINRAG_VERSION` is read-only output from the resource, not an env var you set).

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| **LLM** | | |
| **Provider & model** | | |
| `PINRAG_LLM_PROVIDER` | `openrouter` | `openrouter`, `openai`, or `anthropic` |
| `PINRAG_LLM_MODEL` | *(provider default)* | When unset: OpenRouter `openrouter/free`, OpenAI `gpt-4o-mini`, Anthropic `claude-haiku-4-5`. Override with any model id (e.g. OpenRouter `anthropic/claude-sonnet-4-6`). |
| **OpenRouter** | | |
| `PINRAG_OPENROUTER_MODEL_FALLBACKS` | *(unset)* | Comma-separated fallback model slugs sent as OpenRouter’s `models` list. The gateway tries the next slug when the primary (`PINRAG_LLM_MODEL`) fails (rate limits, downtime, etc.). Use extra free models here to stay zero-cost. Legacy alias: `PINRAG_LLM_MODEL_FALLBACKS`. |
| `PINRAG_OPENROUTER_SORT` | *(unset)* | Optional `provider.sort` — `price`, `throughput`, or `latency`. When unset, OpenRouter uses its default provider selection. Prefer leaving this unset if you set `PINRAG_OPENROUTER_PROVIDER_ORDER` to pin a specific backend (avoids conflicting routing signals). |
| `PINRAG_OPENROUTER_PROVIDER_ORDER` | *(unset)* | Comma-separated provider names for `provider.order` (tried in sequence). Example: `Cerebras` with `PINRAG_LLM_MODEL=openai/gpt-oss-120b` to prefer [Cerebras-backed routing](https://openrouter.ai/docs/guides/routing/provider-selection). Use exact labels from the model’s provider list on OpenRouter. |
| `OPENROUTER_APP_URL` | `https://github.com/ndjordjevic/pinrag` | App attribution (`HTTP-Referer`). Override with your site URL (see [OpenRouter app attribution](https://openrouter.ai/docs/app-attribution)). PinRAG copies this into `OPENROUTER_HTTP_REFERER` for the OpenRouter Python SDK. |
| `OPENROUTER_APP_TITLE` | `PinRAG` | App title (`X-Title`). Override to label usage in the OpenRouter dashboard. PinRAG copies this into `OPENROUTER_X_OPEN_ROUTER_TITLE` for the SDK. |
| **API keys** | | |
| `OPENROUTER_API_KEY` | *(required for OpenRouter LLM)* | Required when `PINRAG_LLM_PROVIDER=openrouter` or `PINRAG_EVALUATOR_PROVIDER=openrouter`. |
| `OPENAI_API_KEY` | *(required for OpenAI LLM)* | Required when using OpenAI for the LLM (`PINRAG_LLM_PROVIDER=openai`). |
| `OPENAI_BASE_URL` | *(optional)* | Override OpenAI API base URL (e.g. `https://openrouter.ai/api/v1` with `OPENAI_API_KEY` set to your OpenRouter key for vision or other OpenAI-compatible calls). |
| `ANTHROPIC_API_KEY` | *(required for Anthropic)* | Required when `PINRAG_LLM_PROVIDER=anthropic` or `PINRAG_EVALUATOR_PROVIDER=anthropic`. |
| **Embeddings** | | |
| `PINRAG_EMBEDDING_MODEL` | `nomic-embed-text-v1.5` | Local Nomic model id (via `langchain-nomic`). First run downloads weights (~270 MB, cached). No API key. |
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
| `PINRAG_USE_RERANK` | `false` | Set to `true` to enable FlashRank re-ranking: fetch more chunks, re-score locally, pass top N to the LLM. Requires `pip install pinrag[rerank]` and no API key. |
| `PINRAG_RERANK_RETRIEVE_K` | `20` | Chunks to fetch before reranking when `PINRAG_USE_RERANK=true`. If unset, uses `PINRAG_RETRIEVE_K`. |
| `PINRAG_RERANK_TOP_N` | `10` | Chunks passed to the LLM after re-ranking when `PINRAG_USE_RERANK=true` (capped by the pre-rerank fetch size). |
| **Multi-query** | | |
| `PINRAG_USE_MULTI_QUERY` | `false` | Set to `true` to generate alternative phrasings of the user query via LLM, retrieve per variant, and merge (unique union). Improves recall for terse or ambiguous queries. |
| `PINRAG_MULTI_QUERY_COUNT` | `4` | Number of **alternative** queries to generate (default 4, max 10). The original query is still included in retrieval when merging. |
| **Response style** | | |
| `PINRAG_RESPONSE_STYLE` | `thorough` | RAG answer style: `thorough` (detailed) or `concise`. Used by evaluation target and as default when MCP `query` omits `response_style`. |
| **MCP notifications** | | |
| `PINRAG_VERBOSE_LOGGING` | `false` | Set `true` to emit detailed per-phase MCP notifications for tool/resource execution (format detection, transcript load, vision path/steps, chunk upserts). Default keeps concise start/ok/error lifecycle logs. |
| **GitHub indexing** | | |
| `GITHUB_TOKEN` | *(optional)* | Personal access token for GitHub API. Required for private repos; increases rate limits for public repos. |
| `PINRAG_GITHUB_MAX_FILE_BYTES` | `524288` (512 KB) | Skip files larger than this when indexing GitHub repos. |
| `PINRAG_GITHUB_DEFAULT_BRANCH` | `main` | Default branch when not specified in the GitHub URL. |
| **Plain text indexing** | | |
| `PINRAG_PLAINTEXT_MAX_FILE_BYTES` | `524288` (512 KB) | Skip plain .txt files larger than this when indexing. |
| **YouTube transcript proxy** | | |
| `PINRAG_YT_PROXY_HTTP_URL` | *(none)* | HTTP proxy URL for transcript fetches (e.g. `http://user:pass@proxy:80`). Use when YouTube blocks your IP. |
| `PINRAG_YT_PROXY_HTTPS_URL` | *(none)* | HTTPS proxy URL for transcript fetches. Same as HTTP when using a generic proxy. |
| **YouTube vision (optional)** | | |
| `PINRAG_YT_VISION_ENABLED` | `false` | Set `true` / `1` / `yes` / `on` to enable on-screen enrichment for YouTube indexing. Requires `pinrag[vision]`, ffmpeg on `PATH`, and a vision provider key. |
| `PINRAG_YT_VISION_PROVIDER` | `openai` | YouTube vision API: `openai` or `anthropic`. Independent of `PINRAG_LLM_PROVIDER` (query LLM can stay OpenAI while vision uses Anthropic, and vice versa). |
| `PINRAG_YT_VISION_MODEL` | *(provider default)* | Model id for YouTube vision calls. If unset: OpenAI default `gpt-4o-mini`, Anthropic default `claude-sonnet-4-6`. Use a **vision-capable** model (e.g. `gpt-4o`, or a current Claude Sonnet id from your Anthropic console). |
| `PINRAG_YT_VISION_MAX_FRAMES` | `8` | Maximum scene-based keyframes analyzed per video (after scene detection). Higher values improve coverage but increase time and API cost. |
| `PINRAG_YT_VISION_MIN_SCENE_SCORE` | `27.0` | PySceneDetect `AdaptiveDetector` threshold; larger values yield fewer, stronger scene cuts (see PySceneDetect docs). |
| `PINRAG_YT_VISION_IMAGE_DETAIL` | `low` | **OpenAI only:** `low`, `high`, or `auto` for `image_url.detail`. `high` reads small code better at higher image-token cost. Ignored when `PINRAG_YT_VISION_PROVIDER=anthropic` (full image is sent). |
| **LangSmith (optional)** | | |
| `LANGSMITH_TRACING` | *(off)* | Set `true` to send traces to [LangSmith](https://smith.langchain.com). Requires `LANGSMITH_API_KEY`. |
| `LANGSMITH_API_KEY` | *(none)* | API key from LangSmith **Settings → API keys**. |
| `LANGSMITH_PROJECT` | *(LangChain default)* | Project name for traces (e.g. `pinrag`). |
| `LANGSMITH_ENDPOINT` | US API (implicit) | **EU workspaces:** set `https://eu.api.smith.langchain.com` so traces land in your EU project. If your account uses `eu.smith.langchain.com` in the browser, you need this. US-region workspaces can omit it (default API host). |
| **Evaluators (LLM-as-judge)** | | |
| `PINRAG_EVALUATOR_PROVIDER` | `openai` | `openai`, `anthropic`, or `openrouter` — which LLM runs LLM-as-judge graders. Used only during evaluation runs (LangSmith experiments). |
| `PINRAG_EVALUATOR_MODEL` | *(provider default)* | Model for **correctness** grading (e.g. `gpt-4o`, `claude-sonnet-4-6`, `openrouter/free` when evaluator provider is OpenRouter). With OpenRouter, the default free router may rotate models; graders use strict JSON schema—set this to a **specific** free slug from [openrouter.ai/models](https://openrouter.ai/models) if you need stable structured output. OpenRouter routing env vars below also apply to graders when `PINRAG_EVALUATOR_PROVIDER=openrouter`. |
| `PINRAG_EVALUATOR_MODEL_CONTEXT` | *(provider default)* | Model for **groundedness** grading (large retrieved context; e.g. `gpt-4o-mini`, `claude-haiku-4-5`, `openrouter/free` when evaluator provider is OpenRouter). Same OpenRouter note as `PINRAG_EVALUATOR_MODEL`. When the evaluator provider is OpenRouter, `PINRAG_OPENROUTER_MODEL_FALLBACKS`, `PINRAG_OPENROUTER_SORT`, and `PINRAG_OPENROUTER_PROVIDER_ORDER` apply to the grader client. |

> **Re-indexing when changing embedding model:** Changing `PINRAG_EMBEDDING_MODEL` (or upgrading from indexes built with older OpenAI embeddings) requires re-indexing; vector dimensions must match the model used at index time.
>
> **Re-indexing when enabling parent-child:** Setting `PINRAG_USE_PARENT_CHILD=true` requires re-indexing; the new structure (child chunks in Chroma, parent chunks in docstore) is created only during indexing for supported document types (not plain `.txt`).
>
> **Re-indexing when toggling YouTube vision:** Turning `PINRAG_YT_VISION_ENABLED` on or off, or changing vision model/detail/frame limits, requires re-indexing affected YouTube documents for chunks to reflect the new behavior.

### Monitoring & Observability

For query performance metrics (latency, timing, token usage) and debugging, use [LangSmith](https://smith.langchain.com). Set `LANGSMITH_TRACING=true` and `LANGSMITH_API_KEY` in MCP `env` or your shell; optionally set `LANGSMITH_PROJECT` (see table above). **If your LangSmith workspace is in the EU region** (you use `eu.smith.langchain.com` in the browser), you **must** also set `LANGSMITH_ENDPOINT=https://eu.api.smith.langchain.com`; without it, traces may not show up in the EU deployment. US-region accounts use the default API host and do not need `LANGSMITH_ENDPOINT`. See [`notes/langsmith-setup.md`](notes/langsmith-setup.md) for more detail.\n\nFor MCP-side introspection, set `PINRAG_VERBOSE_LOGGING=true` to surface detailed phase events in `notifications/message` (e.g., YouTube transcript load, whether vision runs, and chunk upsert milestones).

### Multiple providers and collections

Embedding dimension depends on the embedding model (default Nomic `nomic-embed-text-v1.5` is 768). To avoid dimension mismatches:

- **Default:** Collection name is `pinrag`. If you change `PINRAG_EMBEDDING_MODEL`, re-index or you will get dimension errors.
- **Per-model collections:** Set `PINRAG_COLLECTION_NAME` to a model-specific name when indexing, and use the same name when querying with that model. You can index the same PDFs into multiple collections (switch env and index again) and switch by changing `PINRAG_EMBEDDING_MODEL` and `PINRAG_COLLECTION_NAME` in MCP `env` or your shell.
- **MCP tools:** The server uses `PINRAG_COLLECTION_NAME` (default `pinrag`) for all tools. Collection is not configurable per call; change it via MCP `env` or your shell to target a different collection.

## MCP reference

Tools, optional prompt, and read-only resources from the PinRAG MCP server (`pinrag`). Indexing tools return `indexed` / `failed` / totals (and `fail_summary` when some paths fail); `query_tool` returns an answer plus citation metadata.

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
- **Full suite:** `uv run pytest tests/ -q` — set `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` via the environment or `tests/.mcp_stdio_integration.env` (copy from `tests/mcp_stdio_integration.env.example`; environment wins over the file). PDF/RAG tests and MCP stdio integration tests (`test_mcp_stdio_*.py`) expect `data/pdfs/sample-text.pdf` locally (under `data/`, gitignored); override path or query with `PINRAG_MCP_ITEST_PDF` / `PINRAG_MCP_ITEST_QUERY` for the stdio tests. To skip the PyPI-based MCP test (network / `uv tool run --from pinrag pinrag`), use `-m "not pypi_mcp"` or `PINRAG_MCP_ITEST_SKIP_PYPI=1`. For live logs from those tests, add `--log-cli-level=INFO`.

The `data/` tree is gitignored (create `data/pdfs/` or `data/discord-channels/` locally; nothing under `data/` is committed).

## License

MIT License. Full text in [LICENSE](LICENSE).
