"""Split documents into chunks with configurable size and overlap."""

from __future__ import annotations

import re
from typing import Optional

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200

# Max length for a line to be treated as a section heading (get its own paragraph break before it)
HEADING_LINE_MAX_LEN = 60


def _is_heading_line(line: str) -> bool:
    """True if the line looks like a section heading.

    Heuristic:
    - short (<= HEADING_LINE_MAX_LEN chars)
    - no trailing sentence punctuation (. ! ?)
    - does not contain characters typical of code/register names (one of # / = ;)"""
    stripped = line.strip()
    if not stripped:
        return False
    # Filter out very code-y lines (e.g. MOVE.W #$00F0, $DFF... // comment)
    if re.search(r"[#/=;]", stripped):
        return False
    return (
        len(stripped) <= HEADING_LINE_MAX_LEN
        and not bool(re.search(r"[.!?]\s*$", stripped))
    )


def _extract_heading_from_chunk(content: str) -> str | None:
    """Return the first line if it looks like a heading, else None."""
    first_line = content.split("\n")[0].strip() if content else ""
    return first_line if _is_heading_line(first_line) else None


def _ensure_heading_paragraph_breaks(text: str) -> str:
    """Insert \\n\\n before lines that look like section headings so they start a new segment.

    RecursiveCharacterTextSplitter splits on \\n\\n first. So a short title line like
    "The system memory" that appears after a paragraph will stay with that paragraph
    unless we put a break before the title. This function adds \\n\\n before lines that:
    - are short (<= HEADING_LINE_MAX_LEN chars),
    - do not end with sentence punctuation (. ! ?),
    - are not empty.
    so the splitter tends to keep the heading with the following paragraph.
    """
    lines = text.split("\n")
    out: list[str] = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            out.append(line)
            continue
        # Short line, no trailing . ! ? → likely a heading
        if len(stripped) <= HEADING_LINE_MAX_LEN and not re.search(r"[.!?]\s*$", stripped):
            # Ensure paragraph break before this line (so splitter sees it as start of new segment)
            if out and out[-1].strip() != "":
                out.append("")
            out.append(line)
        else:
            out.append(line)
    return "\n".join(out)


def chunk_documents(
    documents: list[Document],
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    document_id_key: str = "file_name",
    respect_heading_lines: bool = True,
) -> list[Document]:
    """Split documents into smaller chunks, preserving metadata and adding chunk_index.

    Uses LangChain RecursiveCharacterTextSplitter (paragraph → sentence → word
    boundaries). When respect_heading_lines is True (default), inserts paragraph
    breaks before short lines that look like section headings so they stay with
    the following paragraph (e.g. "The system memory" starts a new segment).

    Each chunk keeps the source document's metadata (source, file_name,
    page, total_pages, document_title/author when present) and gets:
    - chunk_index: 0-based index of this chunk within the same page
    - document_id: stable document identifier (from document_id_key, default file_name)
    - section: explicit section/heading label when the chunk starts with or follows a heading-like line

    Args:
        documents: LangChain Documents (e.g. from load_pdf_as_documents).
        chunk_size: Target size of each chunk in characters.
        chunk_overlap: Overlap between consecutive chunks in characters.
        document_id_key: Metadata key to use as document_id (default: file_name).
        respect_heading_lines: If True, add paragraph breaks before heading-like
            lines so they start a new segment (default: True).

    Returns:
        List of chunk Documents with preserved and added metadata.
    """
    if not documents:
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        is_separator_regex=False,
    )

    chunks: list[Document] = []
    for doc in documents:
        content = doc.page_content
        if respect_heading_lines:
            content = _ensure_heading_paragraph_breaks(content)
            doc = Document(page_content=content, metadata=dict(doc.metadata))
        doc_id = doc.metadata.get(document_id_key) or doc.metadata.get("source", "")
        split_chunks = splitter.split_documents([doc])
        current_section = ""
        for idx, chunk in enumerate(split_chunks):
            meta = dict(chunk.metadata)
            meta["chunk_index"] = idx
            meta["document_id"] = doc_id
            heading = _extract_heading_from_chunk(chunk.page_content)
            if heading is not None:
                current_section = heading
            meta["section"] = current_section
            chunks.append(Document(page_content=chunk.page_content, metadata=meta))
    return chunks
