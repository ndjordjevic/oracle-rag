"""CLI to list which documents are currently indexed in Chroma."""

from __future__ import annotations

import argparse
from pathlib import Path

import _script_env

_script_env.load_project_dotenv()

from pinrag.config import get_collection_name, get_persist_dir  # noqa: E402
from pinrag.vectorstore import get_chroma_store  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="List unique documents and basic stats from the Chroma index."
    )
    parser.add_argument(
        "--persist-dir",
        default=None,
        help="Directory for Chroma persistence (default: PINRAG_PERSIST_DIR or chroma_db)",
    )
    parser.add_argument(
        "--collection",
        default=None,
        help="Chroma collection name (default: PINRAG_COLLECTION_NAME or pinrag)",
    )
    args = parser.parse_args()

    persist_dir = Path(
        (args.persist_dir or "").strip() or get_persist_dir()
    ).expanduser().resolve()
    collection = (args.collection or "").strip() or get_collection_name()
    store = get_chroma_store(
        persist_directory=persist_dir,
        collection_name=collection,
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
    print(f"Collection:  {collection}")
    print(f"Total chunks: {len(metadatas)}")
    print("Documents:")
    for d in sorted(doc_ids):
        print(f"  - {d}")


if __name__ == "__main__":
    main()
