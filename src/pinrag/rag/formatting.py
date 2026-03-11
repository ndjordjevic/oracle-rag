"""Format retrieved documents as context and as citation sources."""

from __future__ import annotations

from langchain_core.documents import Document


def _format_timestamp(seconds: int | float) -> str:
    """Format seconds as M:SS (e.g. 83 -> '1:23')."""
    total_secs = int(round(float(seconds)))
    m, s = divmod(total_secs, 60)
    if m > 0:
        return f"{m}:{s:02d}"
    return f"0:{s:02d}"


def _citation_label(meta: dict) -> str:
    """Return citation label: 'p. N' for PDF, 't. M:SS' for YouTube, file_path for GitHub, else '?'."""
    start = meta.get("start")
    if start is not None:
        try:
            return f"t. {_format_timestamp(start)}"
        except (TypeError, ValueError):
            pass
    file_path = meta.get("file_path")
    if file_path and meta.get("document_type") == "github":
        return file_path
    if meta.get("document_type") == "discord":
        channel = meta.get("channel")
        return f"channel: {channel}" if channel else "discord"
    if meta.get("document_type") == "plaintext":
        return meta.get("document_id") or "plaintext"
    page = meta.get("page", "?")
    return f"p. {page}"


def format_docs(docs: list[Document], *, number_chunks: bool = True) -> str:
    """Turn a list of chunk documents into a single context string for the prompt.

    Each chunk is separated by newlines. If number_chunks is True, each block
    is prefixed with [N] (doc: <document_id>, <label>) so the model and users
    can refer to sources. Label is "p. <page>" for PDFs, "t. M:SS" for YouTube.

    Args:
        docs: Retrieved chunk documents (with metadata such as page, start, document_id).
        number_chunks: Whether to add [1], [2], ... and doc/label.

    Returns:
        A single string suitable for the {context} placeholder in the RAG prompt.
    """
    if not docs:
        return "No relevant context found."

    parts: list[str] = []
    for i, doc in enumerate(docs, start=1):
        meta = doc.metadata
        doc_id = meta.get("document_id") or meta.get("file_name") or meta.get("source") or "?"
        label = _citation_label(meta)
        if number_chunks:
            parts.append(f"[{i}] (doc: {doc_id}, {label})\n{doc.page_content}")
        else:
            parts.append(doc.page_content)

    return "\n\n".join(parts)


def format_sources(docs: list[Document]) -> list[dict[str, str | int]]:
    """Build a list of unique source references from retrieved documents for citations.

    Deduplicates by (document_id, page_or_start_or_file_path). Each item has "document_id",
    "page" (for PDFs), "start" when present (YouTube timestamp), "file_path" for GitHub.

    Args:
        docs: Retrieved chunk documents.

    Returns:
        List of dicts with document_id, page (0 for YouTube/GitHub), start when present,
        file_path when present (GitHub).
    """
    seen: set[tuple[str, int | str]] = set()
    out: list[dict[str, str | int]] = []
    for doc in docs:
        meta = doc.metadata
        doc_id = str(meta.get("document_id") or meta.get("file_name") or meta.get("source") or "?")
        file_path = meta.get("file_path")
        start = meta.get("start")
        if start is not None:
            try:
                start_int = int(round(float(start)))
                key = (doc_id, start_int)
                if key not in seen:
                    seen.add(key)
                    out.append({"document_id": doc_id, "page": 0, "start": start_int})
            except (TypeError, ValueError):
                key = (doc_id, 0)
                if key not in seen:
                    seen.add(key)
                    out.append({"document_id": doc_id, "page": 0})
        elif file_path and meta.get("document_type") == "github":
            key = (doc_id, file_path)
            if key not in seen:
                seen.add(key)
                out.append({"document_id": doc_id, "page": 0, "file_path": file_path})
        else:
            try:
                page = int(meta.get("page", 0))
            except (TypeError, ValueError):
                page = 0
            key = (doc_id, page)
            if key not in seen:
                seen.add(key)
                out.append({"document_id": doc_id, "page": page})
    return out
