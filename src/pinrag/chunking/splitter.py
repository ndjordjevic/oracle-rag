"""Split documents into chunks with configurable size and overlap."""

from __future__ import annotations

import re

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200

# Max length for a line to be treated as a section heading (get its own paragraph break before it)
HEADING_LINE_MAX_LEN = 60

# Heuristics for structure-aware chunking on plain-text PDF extracts.
_CODE_DIRECTIVE_PREFIXES = ("#include", "#define", "#if", "#pragma")
_C_KEYWORD_LINE_RE = re.compile(
    r"^(?:int|void|static|struct|typedef|return)\b|^(?:if|for|while|switch)\s*\(|^case\b|^default:"
)
_C_FUNCTION_SIG_RE = re.compile(
    r"^(?:[A-Za-z_][\w\s\*]{0,40})\s+[A-Za-z_]\w*\s*\([^)]*\)\s*\{?\s*$"
)
_ASM_MNEMONIC_RE = re.compile(
    r"^(?:MOVE(?:\.[BWL])?|LEA|ADD(?:\.[BWL])?|SUB(?:\.[BWL])?|BNE|BEQ|JSR|RTS)\b",
    re.IGNORECASE,
)
_CODE_OPERATOR_RE = re.compile(r"(?:->|<<|>>|\|=|&=|\+=|-=|\*=|/=|[{}=;()])")
_TABLE_COL_SPLIT_RE = re.compile(r"\s{2,}")


def _is_heading_line(line: str) -> bool:
    """Return whether the line looks like a section heading.

    Heuristic:
    - short (<= HEADING_LINE_MAX_LEN chars)
    - no trailing sentence punctuation (. ! ?)
    - does not contain characters typical of code/register names (one of # / = ;)
    """
    stripped = line.strip()
    if not stripped:
        return False
    # Filter out very code-y lines (e.g. MOVE.W #$00F0, $DFF... // comment)
    if re.search(r"[#/=;]", stripped):
        return False
    return len(stripped) <= HEADING_LINE_MAX_LEN and not bool(
        re.search(r"[.!?]\s*$", stripped)
    )


def _extract_heading_from_chunk(content: str) -> str | None:
    """Return the first line if it looks like a heading, else None."""
    first_line = content.split("\n")[0].strip() if content else ""
    return first_line if _is_heading_line(first_line) else None


def _ensure_heading_paragraph_breaks(text: str) -> str:
    """Insert a blank line before heading-like lines so they start a new paragraph segment.

    RecursiveCharacterTextSplitter splits on double newlines first. So a short title line like
    "The system memory" that appears after a paragraph will stay with that paragraph
    unless we put a break before the title. This function adds an extra newline (blank line) before lines that:
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
        if _is_heading_line(stripped):
            # Ensure paragraph break before this line (so splitter sees it as start of new segment)
            if out and out[-1].strip() != "":
                out.append("")
            out.append(line)
        else:
            out.append(line)
    return "\n".join(out)


def _is_code_line(line: str) -> bool:
    """Return True when a line looks like C or 68k assembly code."""
    stripped = line.strip()
    if not stripped:
        return False
    left = line.lstrip()

    # Avoid treating bullets/summaries as code unless there's strong evidence.
    if left.startswith(("●", "-", "*")) and not _CODE_OPERATOR_RE.search(stripped):
        return False

    if left.startswith(_CODE_DIRECTIVE_PREFIXES):
        return True
    if _C_KEYWORD_LINE_RE.search(left):
        return True
    if _C_FUNCTION_SIG_RE.search(left):
        return True
    if _ASM_MNEMONIC_RE.search(left):
        return True
    if ";" in stripped and (
        re.search(r"\$[0-9A-Fa-f]+", stripped) or _ASM_MNEMONIC_RE.search(left)
    ):
        return True
    if _CODE_OPERATOR_RE.search(stripped) and left.startswith(
        ("for ", "if ", "while ", "switch ", "return ")
    ):
        return True
    if line.startswith(("    ", "\t")) and _CODE_OPERATOR_RE.search(stripped):
        return True
    return False


def _is_table_row(line: str) -> bool:
    """Return True when a line looks like a table row."""
    stripped = line.strip()
    if not stripped or len(stripped) < 12:
        return False

    # Common register-table style.
    if "|" in stripped:
        cols = [c.strip() for c in stripped.split("|") if c.strip()]
        return len(cols) >= 2

    # Aligned columns separated by repeated spaces.
    cols = [c for c in _TABLE_COL_SPLIT_RE.split(stripped) if c]
    if len(cols) < 3:
        return False
    alpha_cols = sum(1 for c in cols if re.search(r"[A-Za-z]", c))
    digit_cols = sum(1 for c in cols if re.search(r"\d", c))
    return alpha_cols >= 2 and (digit_cols >= 1 or len(cols) >= 4)


def _ensure_code_block_breaks(text: str) -> str:
    """Insert paragraph breaks at prose↔code transitions to preserve code blocks."""
    lines = text.split("\n")
    out: list[str] = []
    prev_nonempty_is_code: bool | None = None

    for line in lines:
        if not line.strip():
            out.append(line)
            continue

        is_code = _is_code_line(line)
        if prev_nonempty_is_code is not None and is_code != prev_nonempty_is_code:
            if out and out[-1].strip() != "":
                out.append("")
        out.append(line)
        prev_nonempty_is_code = is_code

    return "\n".join(out)


def _ensure_table_breaks(text: str) -> str:
    """Insert paragraph breaks at prose↔table transitions to preserve table blocks."""
    lines = text.split("\n")
    if not lines:
        return text

    table_mask = [_is_table_row(line) for line in lines]

    # Keep one-line table headers with their table block.
    for i in range(1, len(lines)):
        if table_mask[i] and not table_mask[i - 1]:
            header = lines[i - 1].strip()
            if header and len(header) <= 120 and not re.search(r"[.!?]\s*$", header):
                table_mask[i - 1] = True

    # Allow a blank separator inside a table region.
    for i in range(1, len(lines) - 1):
        if not lines[i].strip() and table_mask[i - 1] and table_mask[i + 1]:
            table_mask[i] = True

    out: list[str] = []
    prev_nonempty_is_table: bool | None = None
    for i, line in enumerate(lines):
        if not line.strip():
            out.append(line)
            continue
        is_table = table_mask[i]
        if prev_nonempty_is_table is not None and is_table != prev_nonempty_is_table:
            if out and out[-1].strip() != "":
                out.append("")
        out.append(line)
        prev_nonempty_is_table = is_table

    return "\n".join(out)


def chunk_documents(
    documents: list[Document],
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    document_id_key: str = "file_name",
    respect_heading_lines: bool = True,
    respect_structure: bool = True,
) -> list[Document]:
    """Split documents into smaller chunks, preserving metadata and adding chunk_index.

    Uses LangChain RecursiveCharacterTextSplitter (paragraph → sentence → word
    boundaries). When enabled, applies lightweight structure heuristics:
    - respect_heading_lines: inserts paragraph breaks before heading-like lines.
    - respect_structure: inserts paragraph breaks around code/table regions.

    Each chunk keeps the source document's metadata (source, file_name,
    page, total_pages, document_title/author when present) and gets:
    - chunk_index: 0-based index of this chunk within the same page
    - document_id: stable document identifier (from document_id_key, default file_name)
    - section: explicit section/heading label when the chunk starts with or follows a heading-like line
    - start_index: character offset in the text passed to the splitter (after any heading/code/table
      preprocessing) where this chunk begins (for source traceability)

    Args:
        documents: LangChain Documents (e.g. from load_pdf_as_documents).
        chunk_size: Target size of each chunk in characters.
        chunk_overlap: Overlap between consecutive chunks in characters.
        document_id_key: Metadata key to use as document_id (default: file_name).
        respect_heading_lines: If True, add paragraph breaks before heading-like
            lines so they start a new segment (default: True).
        respect_structure: If True, add paragraph breaks at prose↔code and
            prose↔table transitions (default: True).

    Returns:
        List of chunk Documents with preserved and added metadata.

    """
    if not documents:
        return []
    if chunk_overlap >= chunk_size:
        raise ValueError(
            f"chunk_overlap ({chunk_overlap}) must be smaller than chunk_size ({chunk_size})."
        )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        is_separator_regex=False,
        add_start_index=True,
    )

    chunks: list[Document] = []
    for doc in documents:
        content = doc.page_content
        if respect_heading_lines:
            content = _ensure_heading_paragraph_breaks(content)
        if respect_structure:
            content = _ensure_code_block_breaks(content)
            content = _ensure_table_breaks(content)
        if content != doc.page_content:
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
