# Oracle-RAG

A powerful PDF RAG (Retrieval-Augmented Generation) system built with LangChain, designed as an MCP (Model Context Protocol) server for Cursor and other AI assistants.

## Overview

Oracle-RAG provides intelligent document querying and retrieval capabilities for PDF documents. Index PDFs, ask questions, and get answers with source citations—all via MCP tools in Cursor.

## Features

- 📄 PDF document processing and indexing
- 🔍 RAG with source citations
- 🔌 MCP server: `query_pdf`, `add_pdf`, `remove_pdf`, `list_pdfs`
- 🧠 Built with LangChain and Chroma

## Installation

```bash
pip install oracle-rag
# or: uv tool install oracle-rag
```

Requires Python 3.12+.

## Quick Start

### 1. Create a project folder and config

```bash
mkdir my-rag && cd my-rag
echo "OPENAI_API_KEY=your_key_here" > .env
```

The index (`chroma_db`) and `.env` will live in this folder.

### 2. Add Oracle-RAG to Cursor MCP

In **Cursor Settings** → **Tools & MCP** → **Add new MCP server**:

- **Name:** `oracle-rag`
- **Type:** Command
- **Command:** `oracle-rag-mcp`
- **Working directory:** `/path/to/my-rag` (the folder with your `.env`)

Or add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "oracle-rag": {
      "command": "oracle-rag-mcp",
      "cwd": "/path/to/my-rag"
    }
  }
}
```

Restart Cursor. The `cwd` must point to a folder containing `.env` (with `OPENAI_API_KEY`) and where `chroma_db` will be created.

### 3. Use in Cursor

- *"Add the PDF at /path/to/doc.pdf to Oracle-RAG"*
- *"List the PDFs in Oracle-RAG"*
- *"Query Oracle-RAG: What is this document about?"*

## Config locations

When run via `oracle-rag-mcp`, `.env` is loaded from (first found):

- `{cwd}/.env`
- `~/.config/oracle-rag/.env`
- `~/.oracle-rag/.env`

Optional: `ORACLE_RAG_CHUNK_SIZE`, `ORACLE_RAG_CHUNK_OVERLAP`. See `.env.example` in the repo.

## Development

```bash
git clone https://github.com/you/oracle-rag.git
cd oracle-rag
uv sync
uv run pytest
```

Run MCP server from source: `uv run python scripts/mcp_server.py` (use project root as `cwd` in Cursor).

## License

TBD
