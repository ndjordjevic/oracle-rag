# PDF Parsing Library Analysis (Phase 1: no OCR)

## What we need (Phase 1)

- **Digitally-born PDFs only** (no OCR / no scanned-image PDFs for now)
- **Per-page text extraction** (so we can attach page numbers to chunks)
- **Reasonable layout fidelity** (enough for RAG chunks to make sense)
- **Metadata hooks** (ability to filter headers/footers later, if needed)
- **License-friendly defaults** (so we don't box ourselves in later)

## Key constraint: “sections/headings”

PDFs typically **do not contain a reliable semantic layer** for “sections” / “headings” (they are mostly positioned text). Even if a parser exposes fonts/coordinates, **section detection is usually heuristic** and we’ll implement it ourselves later.

## Candidates

### Option A — `pypdf` (recommended for Phase 1)

- **Pros**
  - Simple per-page extraction via `PdfReader(...).pages[i].extract_text()` ([docs](https://pypdf.readthedocs.io/en/stable/user/extract-text.html))
  - Has a layout-oriented extraction mode (`extraction_mode="layout"`) for better spacing ([docs](https://pypdf.readthedocs.io/en/stable/user/extract-text.html))
  - Supports visitor callbacks to selectively include/exclude text regions (useful later for headers/footers) ([docs](https://pypdf.readthedocs.io/en/stable/user/extract-text.html))
  - Permissive license: **BSD-3-Clause** ([FAQ](https://pypdf.readthedocs.io/en/latest/meta/faq.html))
- **Cons**
  - Text extraction can be memory-heavy for some PDFs (pypdf explicitly warns about this) ([docs](https://pypdf.readthedocs.io/en/stable/user/extract-text.html))
  - Limited layout/structure signals compared to coordinate-level parsers

**Fit for Oracle-RAG Phase 1:** strong (already in our deps, low friction, license-safe).

### Option B — `pdfplumber` (good Phase 2 “quality” upgrade)

- **Pros**
  - Built for detailed extraction of **characters, rectangles, lines**, plus table extraction + visual debugging ([README](https://raw.githubusercontent.com/jsvine/pdfplumber/develop/README.md))
  - “Works best on machine-generated, rather than scanned, PDFs” (matches our Phase 1 assumption) ([README](https://raw.githubusercontent.com/jsvine/pdfplumber/develop/README.md))
  - Exposes page numbers and rich per-object metadata (helpful for heading/section heuristics later) ([README](https://raw.githubusercontent.com/jsvine/pdfplumber/develop/README.md))
  - License is permissive (MIT); `pdfplumber`’s README links to license info for itself and dependencies ([README](https://raw.githubusercontent.com/jsvine/pdfplumber/develop/README.md))
- **Cons**
  - Usually slower and heavier than simpler extractors (it’s built on `pdfminer.six`)
  - More code/knobs to tune

**Fit for Oracle-RAG:** great when we need better layout + metadata for “section/page/span” attribution beyond just page numbers.

### Option C — `PyMuPDF` (fast, but licensing may be a blocker)

- **Pros**
  - Very fast text extraction; PyMuPDF’s own benchmark shows large speed differences vs PyPDF2 / PDFMiner ([performance methodology](https://pymupdf.readthedocs.io/en/latest/app4.html))
  - Multiple extraction modes (`page.get_text()` plus “blocks” / “words” suggestions to reconstruct reading order) ([text recipes](https://pymupdf.readthedocs.io/en/latest/recipes-text.html))
- **Cons**
  - Licensing: available under **AGPL** or a commercial license ([PyMuPDF docs](https://pymupdf.readthedocs.io/en/latest/about.html#license-and-copyright), [PyPI](https://pypi.org/project/PyMuPDF/))
  - AGPL can be incompatible with some distribution/commercial plans (we should decide before adopting)

**Fit for Oracle-RAG:** excellent technically, but we should only adopt if we’re comfortable with AGPL or plan for a commercial license.

## Recommendation

### Phase 1 (now)

**Use `pypdf`** for PDF text extraction. It’s already installed, straightforward, and license-friendly. We can still achieve our Phase 1 requirements (page-numbered chunks + citations) with it.

### Phase 2 (if we need better structure)

Add **`pdfplumber`** as an optional “high-fidelity extraction” backend for:
- better layout preservation,
- table-heavy PDFs,
- and extracting richer signals (coordinates, fonts, etc.) to support “section/heading” heuristics.

### Phase 3+ (scale / speed)

Re-evaluate **PyMuPDF** if we hit performance limits, but only after we make a clear call on AGPL vs commercial licensing.

## Suggested approach in code (high level)

- Implement a `PdfParser` interface with a `parse(path) -> list[DocumentChunk]` contract.
- Start with `PypdfParser` (Phase 1).
- Keep room for `PdfplumberParser` as a drop-in alternative later.

