"""Print PDF metadata (title, author) for one or more PDFs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from oracle_rag.pdf.pypdf_loader import load_pdf_as_documents


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Print title and author metadata for PDF file(s)."
    )
    parser.add_argument(
        "pdf_paths",
        nargs="+",
        help="Path(s) to PDF file(s)",
    )
    parser.add_argument(
        "--extraction-mode",
        default="layout",
        help="pypdf extraction mode (default: layout)",
    )
    args = parser.parse_args()

    failed = 0
    for path_arg in args.pdf_paths:
        pdf_path = Path(path_arg).expanduser().resolve()
        try:
            result = load_pdf_as_documents(
                pdf_path, extraction_mode=args.extraction_mode
            )
        except Exception as e:  # noqa: BLE001
            print(f"{pdf_path.name}: ERROR — {e}", file=sys.stderr)
            failed += 1
            continue

        if not result.documents:
            print(f"{pdf_path.name}: (no pages with text)")
            continue

        meta = result.documents[0].metadata
        title = meta.get("document_title") or "—"
        author = meta.get("document_author") or "—"
        pages = result.total_pages
        print(f"{pdf_path.name}")
        print(f"  Title:  {title}")
        print(f"  Author: {author}")
        print(f"  Pages:  {pages}")
        print()

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
