"""CLI to list which documents are currently indexed in Chroma."""

from __future__ import annotations

import argparse
from pathlib import Path

from oracle_rag.vectorstore import get_chroma_store


def main() -> None:
    parser = argparse.ArgumentParser(
        description="List unique documents and basic stats from the Chroma index."
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
    args = parser.parse_args()

    persist_dir = Path(args.persist_dir).expanduser().resolve()
    store = get_chroma_store(
        persist_directory=persist_dir,
        collection_name=args.collection,
    )

    data = store.get(include=["metadatas"])
    metadatas = data.get("metadatas") or []
    if not metadatas:
        print("Index is empty (no chunks).")
        return

    doc_ids: set[str] = set()
    for meta in metadatas:
        if not isinstance(meta, dict):
            continue
        doc_id = (
            meta.get("document_id")
            or meta.get("file_name")
            or meta.get("source")
            or "unknown"
        )
        doc_ids.add(str(doc_id))

    print(f"Persist dir: {persist_dir}")
    print(f"Collection:  {args.collection}")
    print(f"Total chunks: {len(metadatas)}")
    print("Documents:")
    for d in sorted(doc_ids):
        print(f"  - {d}")


if __name__ == "__main__":
    main()

