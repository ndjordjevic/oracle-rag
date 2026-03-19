---
name: run-pinrag-mcp-tool
description: >-
  Use when the PinRAG MCP server uses stdio transport (command/args in mcp.json).
  Run PinRAG MCP tools when the user asks to query indexed documents, list
  documents, add documents, or remove documents. Use call_mcp_tool; server id
  is user- plus the mcp.json key (user-pinrag-dev for repo dev, user-pinrag for
  pipx/uv install). Only one of those servers is typically enabled at a time.
---

# Run PinRAG MCP tool

Use this skill when the PinRAG MCP entry is **stdio**: a spawned process with `command` / `args` in `mcp.json` (no `url`).

Run PinRAG MCP tools via `call_mcp_tool`. Cursor exposes the server as **`user-` + the key in `mcp.json`**:

| `mcp.json` key | `call_mcp_tool` server |
|----------------|-------------------------|
| `pinrag-dev` (local repo via `uv run --project … pinrag-mcp`) | `user-pinrag-dev` |
| `pinrag` (`pinrag-mcp` on PATH after `pipx` / `uv tool install`) | `user-pinrag` |

Use the **`call_mcp_tool` server** that matches the **single** PinRAG MCP entry they have turned on (usually only one of the two is enabled). If a call fails with “server does not exist”, the other id may be the one configured—try it once.

## Available tools

| Tool | Purpose |
|------|---------|
| `query_tool` | Query indexed documents; returns answer with citations. Requires `query` (str). Optional: `document_id`, `page_min`, `page_max`, `tag`, `response_style`. |
| `list_documents_tool` | List indexed documents and chunk counts. Optional: `tag` (filter by tag). |
| `add_document_tool` | Index files, directories, or YouTube URLs. Requires `paths` (list). Optional: `tags`. |
| `remove_document_tool` | Remove a document from the index. Requires `document_id`. |

## Steps

1. Determine which tool the user wants from their message (e.g. a question → `query_tool`, "list docs" → `list_documents_tool`).
2. Call `call_mcp_tool` with:
   - `server`: `"user-pinrag-dev"` or `"user-pinrag"`—whichever matches their enabled MCP entry (see table)
   - `toolName`: the tool name (e.g. `"query_tool"`)
   - `arguments`: a dict with the required and any optional parameters
3. Present the result clearly to the user.

## Examples

- User: "What's Amiga AGA?" → `query_tool` with `{"query": "What's Amiga AGA?"}`
- User: "list documents" → `list_documents_tool` with `{}`
- User: "search only in Bare-metal Amiga programming 2021_ocr.pdf" → `query_tool` with `{"query": "...", "document_id": "Bare-metal Amiga programming 2021_ocr.pdf"}`

If the user does not specify a tool or query, ask what they want to do.
