"""Unified CLI to index PDFs and Discord exports into Chroma.

Indexes files or directories. Replaces existing chunks for each document.
Uses PINRAG_USE_PARENT_CHILD from .env when set (parent-child retrieval).

Usage:
    # Index specific files or directories
    python scripts/index_cli.py path/to/file.pdf path/to/discord.txt
    python scripts/index_cli.py data/pdfs/ data/discord-channels/alicia1200/

    # Reindex all documents whose source paths are stored in Chroma
    python scripts/index_cli.py --from-chroma

    # Wipe index and reindex all with parent-child (requires --from-chroma)
    python scripts/index_cli.py --wipe-and-reindex --from-chroma

    # Wipe only: clear Chroma and parent docstore (removes orphaned parents)
    python scripts/index_cli.py --wipe-only

    # Dry run (list what would be indexed)
    python scripts/index_cli.py --from-chroma --dry-run
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from pinrag.config import (  # noqa: E402
    get_collection_name,
    get_persist_dir,
    get_use_parent_child,
)
from pinrag.indexing import index_discord, index_pdf  # noqa: E402
from pinrag.vectorstore import get_chroma_store  # noqa: E402


def _detect_format(path: Path) -> Literal["pdf", "discord"] | None:
    """Detect PDF or DiscordChatExporter TXT."""
    if not path.is_file():
        return None
    if path.suffix.lower() == ".pdf":
        return "pdf"
    if path.suffix.lower() == ".txt":
        try:
            head = path.read_text(encoding="utf-8", errors="replace")[:2048]
            lines = head.split("\n")[:30]
            if any(
                line.strip().startswith("Guild:") for line in lines
            ) and any(line.strip().startswith("Channel:") for line in lines):
                return "discord"
        except OSError:
            pass
    return None


def _collect_files(paths: list[Path]) -> list[tuple[Path, Literal["pdf", "discord"]]]:
    """Collect supported files from paths (files or directories)."""
    result: list[tuple[Path, Literal["pdf", "discord"]]] = []
    seen: set[Path] = set()
    for p in paths:
        path = p.expanduser().resolve()
        if path.is_file():
            fmt = _detect_format(path)
            if fmt and path not in seen:
                result.append((path, fmt))
                seen.add(path)
        elif path.is_dir():
            for f in sorted(path.rglob("*")):
                if f.is_file():
                    fmt = _detect_format(f)
                    if fmt and f not in seen:
                        result.append((f, fmt))
                        seen.add(f)
        else:
            print(f"Skipped (not found): {path}", file=sys.stderr)
    return result


def _collect_from_chroma(persist_path: Path, collection: str) -> list[tuple[Path, Literal["pdf", "discord"]]]:
    """Extract source paths from Chroma metadata and return existing files."""
    store = get_chroma_store(
        persist_directory=str(persist_path),
        collection_name=collection,
    )
    data = store.get(include=["metadatas"])
    metadatas = data.get("metadatas") or []

    doc_to_source: dict[str, str] = {}
    for meta in metadatas:
        if not isinstance(meta, dict):
            continue
        doc_id = (
            meta.get("document_id")
            or meta.get("file_name")
            or meta.get("source")
            or ""
        )
        if not doc_id:
            continue
        source = meta.get("source")
        if source and isinstance(source, str) and source != "discord":
            if doc_id not in doc_to_source:
                doc_to_source[doc_id] = source

    result: list[tuple[Path, Literal["pdf", "discord"]]] = []
    for doc_id, source in doc_to_source.items():
        p = Path(source).expanduser().resolve()
        if p.suffix.lower() == ".pdf" and p.is_file():
            result.append((p, "pdf"))
        elif p.suffix.lower() == ".txt" and p.is_file() and _detect_format(p) == "discord":
            result.append((p, "discord"))
    return result


def _get_all_document_ids(persist_path: Path, collection: str) -> set[str]:
    """Return all unique document_id values in the Chroma collection."""
    store = get_chroma_store(
        persist_directory=str(persist_path),
        collection_name=collection,
    )
    data = store.get(include=["metadatas"])
    metadatas = data.get("metadatas") or []
    doc_ids: set[str] = set()
    for meta in metadatas:
        if not isinstance(meta, dict):
            continue
        doc_id = (
            meta.get("document_id")
            or meta.get("file_name")
            or meta.get("source")
            or ""
        )
        if doc_id:
            doc_ids.add(str(doc_id))
    return doc_ids


def _wipe_index(persist_path: Path, collection: str) -> None:
    """Remove all documents from Chroma and delete the parent docstore for this collection."""
    store = get_chroma_store(
        persist_directory=str(persist_path),
        collection_name=collection,
    )
    doc_ids = _get_all_document_ids(persist_path, collection)
    for doc_id in doc_ids:
        store._collection.delete(where={"document_id": doc_id})
    parent_dir = persist_path / f"{collection}_parents"
    if parent_dir.exists() and parent_dir.is_dir():
        shutil.rmtree(parent_dir)
        print(f"Removed parent docstore: {parent_dir}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Index PDFs and Discord exports into Chroma. Replaces existing chunks per document."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Paths to index (files or directories). Omit with --from-chroma to reindex from Chroma metadata.",
    )
    parser.add_argument(
        "--from-chroma",
        action="store_true",
        help="Discover paths from existing Chroma metadata and reindex those documents",
    )
    parser.add_argument(
        "--persist-dir",
        default=None,
        help="Chroma persistence directory (default: from PINRAG_PERSIST_DIR or chroma_db)",
    )
    parser.add_argument(
        "--collection",
        default=None,
        help="Chroma collection name (default: from PINRAG_COLLECTION_NAME or pinrag)",
    )
    parser.add_argument(
        "--tag",
        default=None,
        help="Optional tag for indexed documents",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List documents that would be indexed without indexing",
    )
    parser.add_argument(
        "--wipe-and-reindex",
        action="store_true",
        help="Delete all documents from the index (and parent docstore), then reindex. Requires --from-chroma.",
    )
    parser.add_argument(
        "--wipe-only",
        action="store_true",
        help="Clear Chroma collection and parent docstore. Removes orphaned parent chunks when Chroma is empty.",
    )
    args = parser.parse_args()

    if args.wipe_and_reindex and not args.from_chroma:
        print("--wipe-and-reindex requires --from-chroma (paths are read from Chroma before wipe).", file=sys.stderr)
        return 1

    persist_dir = (args.persist_dir or "").strip() or get_persist_dir()
    collection = (args.collection or "").strip() or get_collection_name()
    persist_path = Path(persist_dir).expanduser().resolve()
    tag = (args.tag or "").strip() or None

    if args.wipe_only:
        if not persist_path.exists():
            print(f"Persist directory does not exist: {persist_path}", file=sys.stderr)
            return 1
        print("Wiping Chroma and parent docstore...")
        _wipe_index(persist_path, collection)
        print("Done.")
        return 0

    if args.from_chroma:
        if not persist_path.exists():
            print(f"Persist directory does not exist: {persist_path}", file=sys.stderr)
            return 1
        to_index = _collect_from_chroma(persist_path, collection)
    elif args.paths:
        to_index = _collect_files([Path(p) for p in args.paths])
    else:
        parser.print_help()
        print("\nProvide paths or use --from-chroma to reindex from Chroma metadata.", file=sys.stderr)
        return 1

    if args.wipe_and_reindex and not args.dry_run:
        if not get_use_parent_child():
            print("Set PINRAG_USE_PARENT_CHILD=true in .env for parent-child reindex.", file=sys.stderr)
            return 1
        print("Wiping index and parent docstore...")
        _wipe_index(persist_path, collection)
        print("Wipe done. Reindexing...")

    if not persist_path.exists() and not args.dry_run:
        persist_path.mkdir(parents=True, exist_ok=True)

    print(f"Persist dir: {persist_path}")
    print(f"Collection:  {collection}")
    print(f"Documents:   {len(to_index)}")

    if args.dry_run:
        for path, fmt in to_index:
            print(f"  Would index ({fmt}): {path}")
        return 0

    if not to_index:
        print("No documents to index.", file=sys.stderr)
        return 1

    failed = 0
    for path, fmt in to_index:
        try:
            if fmt == "pdf":
                result = index_pdf(
                    path,
                    persist_directory=str(persist_path),
                    collection_name=collection,
                    tag=tag,
                )
                print(f"Indexed PDF: {path.name} -> {result.total_chunks} chunks")
            else:
                result = index_discord(
                    path,
                    persist_directory=str(persist_path),
                    collection_name=collection,
                    tag=tag,
                )
                print(f"Indexed Discord: {path.name} -> {result.total_chunks} chunks")
        except Exception as e:
            print(f"Failed {path}: {e}", file=sys.stderr)
            failed += 1

    print("Done.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
