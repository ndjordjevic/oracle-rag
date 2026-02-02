"""Print all PDF metadata entries for a file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pypdf import PdfReader


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Print all metadata entries for a PDF file."
    )
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Print raw values as returned by pypdf without casting to str.",
    )
    args = parser.parse_args()

    pdf_path = Path(args.pdf_path).expanduser().resolve()
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    if not pdf_path.is_file():
        raise ValueError(f"Path is not a file: {pdf_path}")
    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a .pdf file, got: {pdf_path.name}")

    reader = PdfReader(str(pdf_path))
    meta = reader.metadata

    print(pdf_path.name)
    if meta is None:
        print("  (no metadata)")
        return

    items = list(meta.items())
    if not items:
        print("  (no metadata)")
        return

    for key, value in sorted(items, key=lambda kv: str(kv[0])):
        if args.raw:
            print(f"  {key}: {value!r}")
        else:
            print(f"  {key}: {value}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
