"""Print text from a specific PDF page to the console."""

from __future__ import annotations

import argparse
import textwrap
from pathlib import Path

from oracle_rag.pdf.pypdf_loader import iter_pdf_page_text


def reflow_text(text: str, width: int = 72) -> str:
    """Merge scattered PDF lines into paragraphs and wrap to width."""
    # Strip and drop empty lines; collapse runs of whitespace (layout PDFs have huge gaps)
    lines = [" ".join(ln.split()) for ln in text.splitlines() if ln.strip()]
    if not lines:
        return text.strip()

    paragraphs: list[list[str]] = []
    current: list[str] = []

    for line in lines:
        if not current:
            current.append(line)
            continue
        prev = current[-1]
        # Start new paragraph when previous looks like end of sentence and this like a new one
        if (
            prev.endswith((".", "!", "?"))
            and len(prev) > 40
            and line
            and line[0].isupper()
        ):
            paragraphs.append(current)
            current = [line]
        else:
            current.append(line)

    if current:
        paragraphs.append(current)

    return "\n\n".join(
        textwrap.fill(" ".join(p), width=width) for p in paragraphs
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Print text from a specific PDF page."
    )
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument("page", type=int, help="1-based page number to print")
    parser.add_argument(
        "--extraction-mode",
        default="layout",
        help="pypdf extraction mode (default: layout)",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=72,
        metavar="N",
        help="Wrap reflowed text to N columns (default: 72). Ignored if --raw.",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Print raw extracted text without reflow/pretty-print.",
    )
    args = parser.parse_args()

    pdf_path = Path(args.pdf_path).expanduser().resolve()
    target_page = args.page

    for page_num, text in iter_pdf_page_text(
        pdf_path, extraction_mode=args.extraction_mode
    ):
        if page_num == target_page:
            print(f"--- Page {page_num} ---")
            if args.raw:
                print(text)
            else:
                print(reflow_text(text, width=args.width))
            return

    raise SystemExit(f"Page {target_page} not found in {pdf_path}")


if __name__ == "__main__":
    main()
