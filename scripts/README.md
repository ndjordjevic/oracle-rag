# Scripts

Helper scripts for testing and inspecting PDF loading and chunking. Run from the project root with `uv run python scripts/<script>.py ...`.

---

## print_pdf_page.py

Print the extracted text of a single PDF page (with optional reflow for readability).

**Arguments**

| Argument | Description |
|----------|-------------|
| `pdf_path` | Path to the PDF file (positional). |
| `page` | 1-based page number to print (positional). |
| `--extraction-mode` | pypdf extraction mode (default: `layout`). |
| `--width` | Wrap reflowed text to N columns (default: `72`). Ignored if `--raw`. |
| `--raw` | Print raw extracted text without reflow/pretty-print. |

**Examples**

```bash
# Page 7, reflowed to 72 columns (default)
uv run python scripts/print_pdf_page.py data/pdfs/sample.pdf 7

# Page 7, raw output (no reflow)
uv run python scripts/print_pdf_page.py data/pdfs/sample.pdf 7 --raw

# Page 7, wrap at 88 columns
uv run python scripts/print_pdf_page.py data/pdfs/sample.pdf 7 --width 88
```

---

## print_pdf_all_metadata.py

Print every metadata entry in a PDF (title, author, creator, creation date, etc.) as returned by pypdf.

**Arguments**

| Argument | Description |
|----------|-------------|
| `pdf_path` | Path to the PDF file (positional). |
| `--raw` | Print values with `repr()` (e.g. for debugging types). |

**Examples**

```bash
uv run python scripts/print_pdf_all_metadata.py data/pdfs/sample.pdf

uv run python scripts/print_pdf_all_metadata.py data/pdfs/sample.pdf --raw
```

---

## print_pdf_chunks.py

Load a PDF, split it into chunks with the project’s chunker, and print each chunk with its metadata (page, chunk_index, document_id).

**Arguments**

| Argument | Description |
|----------|-------------|
| `pdf_path` | Path to the PDF file (positional). |
| `--chunk-size` | Chunk size in characters (default: `1000`). |
| `--chunk-overlap` | Overlap between chunks in characters (default: `200`). |
| `--page` | Show only chunks from this page (1-based; `0` = all pages). |
| `--limit` | Show only the first N chunks (`0` = all). |
| `--preview` | Max characters of chunk content to print (`0` = full). Default: `200`. |
| `--extraction-mode` | pypdf extraction mode (default: `layout`). |

**Examples**

```bash
# All chunks, 200-char preview per chunk
uv run python scripts/print_pdf_chunks.py data/pdfs/sample.pdf

# All chunks for page 7 only, full content
uv run python scripts/print_pdf_chunks.py data/pdfs/sample.pdf --page 7 --preview 0

# First 5 chunks, smaller chunks, 150-char preview
uv run python scripts/print_pdf_chunks.py data/pdfs/sample.pdf --chunk-size 400 --chunk-overlap 80 --limit 5 --preview 150

# Page 7, first 2 chunks, 300-char preview
uv run python scripts/print_pdf_chunks.py data/pdfs/sample.pdf --page 7 --limit 2 --preview 300
```

---

## index_cli.py

Unified CLI to index PDFs and Discord exports into Chroma. Replaces existing chunks per document. Uses  from  when set (parent-child retrieval).

**Arguments**

| Argument | Description |
|----------|-------------|
| `paths` | Paths to index (files or directories). Omit with `--from-chroma` to reindex from Chroma metadata. |
| `--from-chroma` | Discover paths from existing Chroma metadata and reindex those documents. |
| `--persist-dir` | Chroma persistence directory (default: from config). |
| `--collection` | Chroma collection name (default: from config). |
| `--tag` | Optional tag for indexed documents. |
| `--dry-run` | List documents that would be indexed without indexing. |

**Examples**

```bash
# Index specific files
uv run python scripts/index_cli.py data/pdfs/sample-text.pdf
uv run python scripts/index_cli.py data/discord-channels/alicia1200/file.txt

# Index directories (recursive)
uv run python scripts/index_cli.py data/pdfs/ data/discord-channels/alicia1200/

# Reindex all documents whose source paths are stored in Chroma
uv run python scripts/index_cli.py --from-chroma

# Dry run
uv run python scripts/index_cli.py --from-chroma --dry-run
```

---

## index_discord_channels.py

Index all Discord channel exports in `data/discord-channels/` (and subfolders) into Chroma. Scans for `.txt` files in DiscordChatExporter format. Run manually or via cron.

**Arguments**

| Argument | Description |
|----------|-------------|
| `--base-dir` | Base directory with channel folders (default: `data/discord-channels`). |
| `--persist-dir` | Chroma persistence directory. |
| `--collection` | Chroma collection name. |
| `--tag` | Optional tag for all indexed documents. |

**Examples**

```bash
# Index all Discord exports in default location
uv run python scripts/index_discord_channels.py

# Custom base directory
uv run python scripts/index_discord_channels.py --base-dir /path/to/discord-exports
```

---

## list_indexed_docs_cli.py

List which documents are currently indexed in the local Chroma store.

**Arguments**

| Argument | Description |
|----------|-------------|
| `--persist-dir` | Directory for Chroma persistence (default: `chroma_db`). |
| `--collection` | Chroma collection name (default: `oracle_rag`). |

**Examples**

```bash
# List docs in the default index
uv run python scripts/list_indexed_docs_cli.py

# List docs in a custom store
uv run python scripts/list_indexed_docs_cli.py --persist-dir my_chroma --collection my_collection
```

---

## test_llm_cli.py

Call the OpenAI chat model with a test prompt (requires `OPENAI_API_KEY` in `.env` or environment).

**Arguments**

| Argument | Description |
|----------|-------------|
| `prompt` | Optional prompt (default: simple greeting). |

**Examples**

```bash
uv run python scripts/test_llm_cli.py
uv run python scripts/test_llm_cli.py "What is 2+2? Reply with one number."
```

---

## rag_cli.py

Run the full RAG chain: ask a question over indexed PDFs and get an answer with source citations (requires `OPENAI_API_KEY`).

**Arguments**

| Argument | Description |
|----------|-------------|
| `query` | Natural language question (positional). |
| `--k` | Number of chunks to retrieve (default: `5`). |
| `--persist-dir` | Chroma persistence directory (default: `chroma_db`). |
| `--collection` | Chroma collection name (default: `oracle_rag`). |

**Examples**

```bash
# After indexing with index_cli.py
uv run python scripts/rag_cli.py "What is this document about?"
uv run python scripts/rag_cli.py "Summarize the main points." --k 8
```

---

## mcp_server.py

Run the Oracle-RAG MCP (Model Context Protocol) server, exposing RAG tools (`query_pdf`, `add_pdf`) to MCP-compatible clients like Claude Desktop, Cursor, or the MCP Inspector.

**Requirements**

- `OPENAI_API_KEY` must be set in `.env` or environment variables
- PDFs can be indexed using either:
  - The `add_pdf` MCP tool (via MCP client)
  - The `index_cli.py` CLI script

**Transport**

The server uses `stdio` transport (standard for MCP), reading from stdin and writing to stdout. Logs are written to stderr to avoid corrupting JSON-RPC messages.

**Available Tools**

- `query_pdf`: Query indexed PDFs and return answers with citations
- `add_pdf`: Index a new PDF into the vector store
- `list_pdfs`: List all indexed PDFs (document names and total chunk count)
- `remove_pdf`: Remove a PDF and all its chunks and embeddings from the index (by document_id, e.g. file name from list_pdfs)
- `list_pdfs`: List all indexed PDFs (books) in the Oracle-RAG index

**Examples**

```bash
# Run the MCP server (will run until interrupted)
uv run python scripts/mcp_server.py

# Test with MCP Inspector (one command: Inspector spawns the server)
cd /path/to/oracle-rag
npx -y @modelcontextprotocol/inspector uv run python scripts/mcp_server.py
# The terminal prints a URL like: http://localhost:6274/?MCP_PROXY_AUTH_TOKEN=<token>
# Open that full URL in your browser (the token is required). Use the Tools tab to call query_pdf and add_pdf.
# Note: OPENAI_API_KEY is required when you run the tools (for embeddings/LLM), not for the Inspector URL.
```

**Integration**

To use with MCP clients (e.g., Claude Desktop, Cursor), configure the client to run:
```bash
uv run python scripts/mcp_server.py
```
as the server command with stdio transport.

---

## query_rag_cli.py

Query the indexed chunks in Chroma and print matching chunks with metadata.

**Arguments**

| Argument | Description |
|----------|-------------|
| `query` | Natural language query string (positional). |
| `--k` | Number of top chunks to return (default: `5`). |
| `--persist-dir` | Directory for Chroma persistence (default: `chroma_db`). |
| `--collection` | Chroma collection name (default: `oracle_rag`). |
| `--preview` | Max characters of chunk text to show (`0` = full, default: `240`). |

**Examples**

```bash
# Query the default index
uv run python scripts/query_rag_cli.py "chip memory" --k 3

# Show full text of each chunk
uv run python scripts/query_rag_cli.py "chip memory" --k 3 --preview 0

# Query a custom store location
uv run python scripts/query_rag_cli.py "audio hardware" --persist-dir my_chroma --collection my_collection
```

---

## Evaluation

### create_eval_dataset.py

Create the golden evaluation dataset in LangSmith (`oracle-rag-golden`). Contains ~30 Q/A examples from the Bare-metal Amiga programming PDF, ordered easy → medium → hard across chapters. Run once; requires `LANGSMITH_API_KEY` in `.env`. If the dataset already exists, the script exits without overwriting (delete it in LangSmith first to recreate).

**Examples**

```bash
uv run python scripts/create_eval_dataset.py
```

---

### min_k_per_question.py

Find the minimum retrieval `k` per question such that the correctness evaluator passes. Tries k=5, 10, 15, … up to 50 for each question and reports the smallest k that yields a correct answer. Useful for tuning `ORACLE_RAG_RETRIEVE_K`. Disables rerank for the run. Requires `LANGSMITH_API_KEY` and `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`.

**Arguments**

| Argument | Description |
|----------|-------------|
| `dataset_name` | Optional. LangSmith dataset name (default: `oracle-rag-hard-10`). |

**Examples**

```bash
# Default dataset (oracle-rag-hard-10)
uv run python scripts/min_k_per_question.py

# Use the golden dataset
uv run python scripts/min_k_per_question.py oracle-rag-golden
```
