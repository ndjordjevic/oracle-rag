"""CLI to query the indexed chunks in Chroma and print matching chunks."""

from __future__ import annotations

import argparse
from pathlib import Path

from oracle_rag.indexing import query_index


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Query the Chroma index and print matching chunks."
    )
    parser.add_argument("query", help="Natural language query")
    parser.add_argument(
        "--k",
        type=int,
        default=5,
        help="Number of top chunks to return (default: 5)",
    )
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
    parser.add_argument(
        "--preview",
        type=int,
        default=240,
        help="Max characters of chunk text to show (0 = full, default: 240)",
    )
    args = parser.parse_args()

    persist_dir = Path(args.persist_dir).expanduser().resolve()
    docs = query_index(
        args.query,
        k=args.k,
        persist_directory=persist_dir,
        collection_name=args.collection,
    )

    if not docs:
        print("No results.")
        return

    print(f"Query: {args.query!r}")
    print(f"Results: {len(docs)} (top {args.k})\n")

    for i, doc in enumerate(docs, start=1):
        meta = doc.metadata or {}
        file_name = meta.get("file_name") or meta.get("source") or "unknown"
        page = meta.get("page", "?")
        chunk_index = meta.get("chunk_index", "?")
        header = f"[{i}] file={file_name}, page={page}, chunk_index={chunk_index}"
        print(header)
        print("-" * len(header))
        text = doc.page_content or ""
        if args.preview and len(text) > args.preview:
            print(text[: args.preview].rstrip())
            print("...")
        else:
            print(text)
        print()


if __name__ == "__main__":
    main()

