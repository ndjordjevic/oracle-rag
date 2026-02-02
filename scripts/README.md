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
