# Run Oracle-RAG MCP tool

Run an Oracle-RAG MCP tool via `call_mcp_tool` with server `user-oracle-rag`.

## Available tools

| Tool | Purpose |
|------|---------|
| `query_tool` | Query indexed documents; returns answer with citations. Requires `query` (str). Optional: `document_id`, `page_min`, `page_max`, `tag`, `response_style`. |
| `list_documents_tool` | List indexed documents and chunk counts. Optional: `tag` (filter by tag). |
| `add_file_tool` | Index a file or directory (PDF, Discord export). Requires `path`. Optional: `tag`. |
| `add_files_tool` | Index multiple paths. Requires `paths` (list). Optional: `tags`. |
| `remove_document_tool` | Remove a document from the index. Requires `document_id`. |

## Steps

1. Determine which tool the user wants from their message (e.g. a question → `query_tool`, "list docs" → `list_documents_tool`).
2. Call `call_mcp_tool` with:
   - `server`: `"user-oracle-rag"`
   - `toolName`: the tool name (e.g. `"query_tool"`)
   - `arguments`: a dict with the required and any optional parameters
3. Present the result clearly to the user.

## Examples

- User: "What's Amiga AGA?" → `query_tool` with `{"query": "What's Amiga AGA?"}`
- User: "list documents" → `list_documents_tool` with `{}`
- User: "search only in Bare-metal Amiga programming 2021_ocr.pdf" → `query_tool` with `{"query": "...", "document_id": "Bare-metal Amiga programming 2021_ocr.pdf"}`

If the user does not specify a tool or query, ask what they want to do.
