"""Load plain text files into LangChain Documents for RAG indexing."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from langchain_core.documents import Document

PathLike = str | Path


@dataclass(frozen=True)
class PlaintextLoadResult:
    """Result of loading a plain text file into Documents."""

    source_path: Path
    documents: list[Document]
    total_chars: int


def load_plaintext_as_documents(
    path: PathLike,
    *,
    document_id: str | None = None,
    max_file_bytes: int = 524288,
) -> PlaintextLoadResult:
    """Load a plain text file into a single LangChain Document.

    Reads the file as UTF-8 (with replacement on decode errors). If the file
    exceeds max_file_bytes, returns an empty documents list so the indexer can
    skip or clear existing chunks.

    Args:
        path: Path to the .txt file.
        document_id: Override for document_id. If None, uses path.name.
        max_file_bytes: Skip files larger than this (default 512 KB).

    Returns:
        PlaintextLoadResult with documents (one Document with full text, or empty
        if file too large), source_path, and total_chars.

    """
    txt_path = Path(path).expanduser().resolve()
    if not txt_path.is_file():
        raise FileNotFoundError(f"Plain text file not found: {txt_path}")

    size = txt_path.stat().st_size
    if size > max_file_bytes:
        doc_id = document_id or txt_path.name
        return PlaintextLoadResult(
            source_path=txt_path,
            documents=[],
            total_chars=0,
        )

    text = txt_path.read_text(encoding="utf-8", errors="replace")
    doc_id = document_id or txt_path.name
    doc = Document(
        page_content=text,
        metadata={
            "document_id": doc_id,
            "source": str(txt_path),
        },
    )
    return PlaintextLoadResult(
        source_path=txt_path,
        documents=[doc],
        total_chars=len(text),
    )
