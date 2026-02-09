"""CLI to index a PDF into Chroma using the project pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path

from oracle_rag.indexing import index_pdf


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Index a PDF into the local Chroma vector store."
    )
    parser.add_argument("pdf_path", help="Path to the PDF file to index")
    parser.add_argument(
        "--persist-dir",
        default="chroma_db",
        help="Directory for Chroma persistence (default: chroma_db)",
    )
    parser.add_argument(
        "--collection",
        default="oracle_rag",
        help="Chroma collection name (default: oracle_rag)",
    )
    args = parser.parse_args()

    pdf_path = Path(args.pdf_path).expanduser().resolve()
    result = index_pdf(
        pdf_path,
        persist_directory=args.persist_dir,
        collection_name=args.collection,
    )

    print(f"Indexed PDF: {result.source_path}")
    print(f"  Pages:   {result.total_pages}")
    print(f"  Chunks:  {result.total_chunks}")
    print(f"  Persist: {result.persist_directory}")
    print(f"  Coll:    {result.collection_name}")


if __name__ == "__main__":
    main()

