# PDF text extraction: layout vs plain (why one chunk from SAMS 1987)

## What happened

When indexing **SAMS_Inside_the_Amiga_with_C_1987.pdf** (447 pages), Oracle-RAG produced **only 1 chunk**. The book does have extractable text (it’s not image-only).

## Root cause

The loader uses pypdf’s **`extraction_mode="layout"`** by default (better spacing for modern PDFs). For this 1987 PDF:

- **With `extraction_mode="layout"`:** pypdf extracted text from **1 page only** (page 447) — the footer line “This was brought to you from the archives of http://retro-commodore.eu” (75 chars). All other 446 pages yielded **0 characters**.
- **With `extraction_mode="plain"`:** pypdf extracted text from **430 pages** and **~593k characters** total.

So the body of the book is only extractable with **plain** mode. Layout mode fails for this PDF’s structure (likely due to age, fonts, or how the text is encoded).

## Implication

- For **this PDF**, indexing with the current default (`layout`) gives one chunk (the footer). To get full content, use **plain** extraction (e.g. by making `extraction_mode` configurable and passing `"plain"` when calling the loader/indexer).
- **Generic fix:** Either make `extraction_mode` configurable end-to-end (loader → index_pdf → MCP add_pdf), or add a fallback: if layout yields very little text (e.g. &lt; 2 pages or &lt; N chars), retry with `extraction_mode="plain"`.

## Quick check for other PDFs

If a PDF yields surprisingly few chunks, run:

```python
from pypdf import PdfReader
r = PdfReader("path/to.pdf")
for i, p in enumerate(r.pages[:5]):  # first 5 pages
    t = (p.extract_text(extraction_mode="layout") or "").strip()
    print(f"Page {i+1} layout: {len(t)} chars")
    t2 = (p.extract_text(extraction_mode="plain") or "").strip()
    print(f"Page {i+1} plain:  {len(t2)} chars")
```

If “plain” gives much more text than “layout”, that PDF is a candidate for plain mode or a layout→plain fallback.
