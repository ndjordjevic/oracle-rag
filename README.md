# Oracle-RAG

A powerful PDF RAG (Retrieval-Augmented Generation) system built with LangChain, designed as an MCP (Model Context Protocol) server for Cursor and other AI assistants.

## Overview

Oracle-RAG provides intelligent document querying and retrieval capabilities for PDF documents. Index PDFs, ask questions, and get answers with source citations—all via MCP tools in Cursor.

## Features

- PDF document processing and indexing
- RAG with source citations
- MCP server: `query_pdf`, `add_pdf`, `remove_pdf`, `list_pdfs`
- Built with LangChain and Chroma

## Installation

```bash
pipx install oracle-rag
# or: uv tool install oracle-rag
```

Requires Python 3.12+. Both `pipx` and `uv tool install` create an isolated environment and put `oracle-rag-mcp` on your PATH.

## Quick Start

### 1. Create config

```bash
mkdir -p ~/.oracle-rag
echo "OPENAI_API_KEY=sk-..." > ~/.oracle-rag/.env
```

### 2. Add to Cursor MCP

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "oracle-rag": {
      "command": "oracle-rag-mcp"
    }
  }
}
```

Restart Cursor. That's it — no `cwd` needed. The server loads `.env` from `~/.oracle-rag/` (or `~/.config/oracle-rag/`) and stores the index in `~/.oracle-rag/chroma_db` by default.

### 3. Use in Cursor

- *"Add the PDF at /path/to/doc.pdf to Oracle-RAG"*
- *"List the PDFs in Oracle-RAG"*
- *"Query Oracle-RAG: What is this document about?"*

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

For local development in Cursor, add to your project's `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "oracle-rag": {
      "command": "/path/to/oracle-rag/.venv/bin/oracle-rag-mcp"
    }
  }
}
```

## License

TBD
