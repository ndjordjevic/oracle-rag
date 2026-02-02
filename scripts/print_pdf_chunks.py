"""Load a PDF, chunk it, and print chunks with metadata to the console."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from oracle_rag.chunking import chunk_documents
from oracle_rag.pdf.pypdf_loader import load_pdf_as_documents


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Chunk a PDF and print each chunk with metadata."
    )
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1000,
        metavar="N",
        help="Chunk size in characters (default: 1000)",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=200,
        metavar="N",
        help="Overlap between chunks in characters (default: 200)",
    )
    parser.add_argument(
        "--page",
        type=int,
        default=0,
        metavar="N",
        help="Print only chunks from this page (1-based; 0 = all pages)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        metavar="N",
        help="Print only first N chunks (0 = all)",
    )
    parser.add_argument(
        "--preview",
        type=int,
        default=200,
        metavar="N",
        help="Max characters of chunk content to print (0 = full). Default: 200",
    )
    parser.add_argument(
        "--extraction-mode",
        default="layout",
        help="pypdf extraction mode (default: layout)",
    )
    args = parser.parse_args()

    pdf_path = Path(args.pdf_path).expanduser().resolve()
    try:
        result = load_pdf_as_documents(
            pdf_path, extraction_mode=args.extraction_mode
        )
    except Exception as e:  # noqa: BLE001
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    chunks = chunk_documents(
        result.documents,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )

    if args.page:
        chunks = [c for c in chunks if c.metadata.get("page") == args.page]
        if not chunks:
            print(f"No chunks for page {args.page}. PDF has {result.total_pages} page(s).", file=sys.stderr)
            sys.exit(1)

    to_show = chunks[: args.limit] if args.limit else chunks
    print(f"PDF: {pdf_path.name}")
    if args.page:
        print(f"Page: {args.page}  →  Chunks: {len(chunks)}")
    else:
        print(f"Pages: {result.total_pages}  →  Chunks: {len(chunks)}")
    if args.limit and len(chunks) > args.limit:
        print(f"(showing first {args.limit} of {len(chunks)} chunks)")
    print()

    for i, chunk in enumerate(to_show):
        meta = chunk.metadata
        page = meta.get("page", "?")
        cidx = meta.get("chunk_index", "?")
        doc_id = meta.get("document_id", "?")
        print(f"--- Chunk {i + 1} (page {page}, chunk_index {cidx}, document_id={doc_id}) ---")
        if args.preview and len(chunk.page_content) > args.preview:
            print(chunk.page_content[: args.preview].rstrip())
            print("...")
        else:
            print(chunk.page_content)
        print()


if __name__ == "__main__":
    main()
