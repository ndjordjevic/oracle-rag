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

## index_pdf_cli.py

Index a PDF into the local Chroma vector store using the project’s indexing pipeline.

**Arguments**

| Argument | Description |
|----------|-------------|
| `pdf_path` | Path to the PDF file to index (positional). |
| `--persist-dir` | Directory for Chroma persistence (default: `chroma_db`). |
| `--collection` | Chroma collection name (default: `oracle_rag`). |

**Examples**

```bash
# Index a sample PDF into the default store
uv run python scripts/index_pdf_cli.py data/pdfs/sample-text.pdf

# Index into a custom directory and collection
uv run python scripts/index_pdf_cli.py data/pdfs/your.pdf --persist-dir my_chroma --collection my_collection
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
# After indexing a PDF with index_pdf_cli.py
uv run python scripts/rag_cli.py "What is this document about?"
uv run python scripts/rag_cli.py "Summarize the main points." --k 8
```

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
