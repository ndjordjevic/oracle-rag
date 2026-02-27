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
- **Built with** — LangChain, Chroma, OpenAI embeddings

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
echo "OPENAI_API_KEY=sk-..." > ~/.oracle-rag/.env
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

Or create `.vscode/mcp.json` in your workspace for project-specific setup. Restart VS Code. The server loads `.env` from `~/.oracle-rag/` (or `~/.config/oracle-rag/`) and stores the index in `~/.oracle-rag/chroma_db` by default.

> **Note:** MCP in VS Code requires GitHub Copilot and VS Code 1.102+. Enterprise users may need an admin to enable "MCP servers in Copilot."

### 3. Use in chat

| Action | Tool |
|--------|------|
| Add a PDF | `add_pdf_tool` — optionally with `tag` (e.g. `AMIGA`) |
| Add multiple PDFs | `add_pdfs_tool` — optionally with `tags` (one per PDF) |
| List indexed PDFs | `list_pdfs_tool` — shows documents, chunk counts, tags, upload times |
| Query with filters | `query_pdf_tool` — filter by `document_id`, `page_min`/`page_max`, or `tag` |
| Remove a PDF | `remove_pdf_tool` |

Ask in chat: *"Add /path/to/amiga-book.pdf with tag AMIGA"* or *"What are AGA chips? Search only AMIGA-tagged docs"*. The AI will invoke the tools for you.

## Configuration

`.env` is loaded from (first match wins):

1. `{cwd}/.env`
2. `~/.config/oracle-rag/.env`
3. `~/.oracle-rag/.env`

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | *(required)* | OpenAI API key |
| `ORACLE_RAG_PERSIST_DIR` | `~/.oracle-rag/chroma_db` | Chroma vector store directory |
| `ORACLE_RAG_CHUNK_SIZE` | `1000` | Text chunk size |
| `ORACLE_RAG_CHUNK_OVERLAP` | `200` | Chunk overlap |

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

TBD
