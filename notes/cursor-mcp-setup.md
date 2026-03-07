# Cursor MCP Setup (Oracle-RAG)

How to add Oracle-RAG as an MCP server in Cursor and test the tools.

## 1. Add Oracle-RAG to Cursor MCP config

**Option A: Project-level (recommended)**

With the **oracle-rag** folder open as your Cursor workspace, Cursor will use `.cursor/mcp.json` in this repo. That file is already set up to run the Oracle-RAG MCP server.

**Option B: Via Cursor UI**

1. Open **Cursor Settings** → **Tools & MCP** (or search "MCP" in settings).
2. Click **Add new MCP server**.
3. Set:
   - **Name:** `oracle-rag` (or any label).
   - **Type:** **Command** (stdio).
   - **Command:** `uv run python scripts/mcp_server.py`
   - **Working directory:** the full path to the oracle-rag project (e.g. `/Users/you/PythonProjects/oracle-rag`), if your UI has a "cwd" or "working directory" field. If not, ensure you opened the oracle-rag folder as the workspace so the command runs from project root.
4. Save and **restart Cursor** (full restart).

**Option C: Global config**

Edit `~/.cursor/mcp.json` and add the same `oracle-rag` entry as in `.cursor/mcp.json`, but use an **absolute path** for the project if you use a wrapper script, or ensure the "command" is run from the oracle-rag directory (e.g. by opening that folder in Cursor).

## 2. Ensure environment

- **OPENAI_API_KEY** must be set. The server loads `.env` from the project root when it starts, so put `OPENAI_API_KEY=...` in `oracle-rag/.env`.
- Optional: set `LANGSMITH_*` in `.env` if you want traces when Cursor calls the tools.

## 3. Restart Cursor

After changing MCP config, **fully quit and reopen Cursor** so it picks up the new server.

## 4. Test in Cursor

- In chat, the model can use MCP tools. Ask e.g.:
  - *"Use add_file_tool to index the PDF at …"*
  - *"Use query_tool to ask: What is this document about?"*
  - *"List the documents indexed in Oracle-RAG"* (list_documents_tool)

Tool names in Cursor: `query_tool`, `add_file_tool`, `add_files_tool`, `list_documents_tool`, `remove_document_tool`.

## 5. Troubleshooting

- **Server not listed / tools not available:** Restart Cursor; ensure the workspace is the oracle-rag folder when using project-level `.cursor/mcp.json`.
- **OPENAI_API_KEY not set:** Add it to `oracle-rag/.env`; the server loads it on startup.
- **"Command not found: uv":** Install [uv](https://docs.astral.sh/uv/) or use the full path to `uv` in the MCP command, and ensure `python` and `scripts/mcp_server.py` are run from the oracle-rag directory.
