from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Union

from langchain_core.documents import Document
from pypdf import PdfReader
from pypdf.errors import PyPdfError


PathLike = Union[str, Path]

# Minimum total chars from layout extraction to avoid fallback to plain (for multi-page PDFs).
_LAYOUT_MIN_CHARS_FOR_NO_FALLBACK = 500


def _extract_with_mode(
    reader: PdfReader,
    pdf_path: Path,
    total_pages: int,
    extraction_mode: str,
    skip_empty_pages: bool,
    document_title: Optional[str],
    document_author: Optional[str],
) -> list[Document]:
    """Extract per-page Documents using the given pypdf extraction_mode."""
    docs: list[Document] = []
    for page_index, page in enumerate(reader.pages):
        page_number = page_index + 1
        text = page.extract_text(extraction_mode=extraction_mode) or ""
        text = text.strip()
        if skip_empty_pages and not text:
            continue
        doc_meta: dict = {
            "source": str(pdf_path),
            "file_name": pdf_path.name,
            "page": page_number,
            "total_pages": total_pages,
        }
        if document_title is not None:
            doc_meta["document_title"] = document_title
        if document_author is not None:
            doc_meta["document_author"] = document_author
        docs.append(Document(page_content=text, metadata=doc_meta))
    return docs


@dataclass(frozen=True)
class PdfLoadResult:
    """Result of loading a PDF into per-page LangChain Documents."""

    source_path: Path
    documents: list[Document]
    total_pages: int


def load_pdf_as_documents(
    path: PathLike,
    *,
    extraction_mode: Optional[str] = "layout",
    skip_empty_pages: bool = True,
) -> PdfLoadResult:
    """Load a PDF into per-page LangChain `Document`s using `pypdf`.

    Notes:
    - Phase 1 assumes text-based PDFs (digitally-born, no OCR). Raises ValueError
      if no text is extracted from any page.
    - Metadata uses 1-indexed page numbers. Each document gets: source, file_name,
      page, total_pages; and document_title / document_author when present in the PDF.
    By default, tries layout first; if layout yields very little text (fewer than
    2 pages with text or fewer than 500 total characters), retries with plain
    and uses whichever mode extracted more text. Pass extraction_mode="layout"
    or "plain" to force a single mode with no fallback.

    Notes:
    - Phase 1 assumes text-based PDFs (digitally-born, no OCR). Raises ValueError
      if no text is extracted from any page.
    - Metadata uses 1-indexed page numbers. Each document gets: source, file_name,
      page, total_pages; and document_title / document_author when present in the PDF.

    Sources:
    - pypdf extract_text docs: https://pypdf.readthedocs.io/en/stable/user/extract-text.html
    """
    pdf_path = Path(path).expanduser().resolve()
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    if not pdf_path.is_file():
        raise ValueError(f"Path is not a file: {pdf_path}")
    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a .pdf file, got: {pdf_path.name}")

    try:
        reader = PdfReader(str(pdf_path))
        total_pages = len(reader.pages)

        meta = reader.metadata
        document_title: Optional[str] = None
        document_author: Optional[str] = None
        if meta is not None:
            if meta.title is not None:
                document_title = str(meta.title).strip() or None
            if meta.author is not None:
                document_author = str(meta.author).strip() or None

        mode = extraction_mode or "layout"
        docs = _extract_with_mode(
            reader, pdf_path, total_pages, mode, skip_empty_pages, document_title, document_author
        )

        # If layout yielded very little, try plain and use the better result.
        if mode == "layout" and total_pages > 0:
            total_chars = sum(len(d.page_content) for d in docs)
            if len(docs) < 2 or total_chars < _LAYOUT_MIN_CHARS_FOR_NO_FALLBACK:
                docs_plain = _extract_with_mode(
                    reader,
                    pdf_path,
                    total_pages,
                    "plain",
                    skip_empty_pages,
                    document_title,
                    document_author,
                )
                total_chars_plain = sum(len(d.page_content) for d in docs_plain)
                if len(docs_plain) > len(docs) or total_chars_plain > total_chars:
                    docs = docs_plain

        if total_pages > 0 and len(docs) == 0:
            raise ValueError(
                f"No text extracted from {pdf_path.name} ({total_pages} page(s)). "
                "File may be image-only (scan) or empty; Phase 1 supports text-based PDFs only."
            )

        return PdfLoadResult(source_path=pdf_path, documents=docs, total_pages=total_pages)
    except (ValueError, FileNotFoundError):
        raise
    except PyPdfError as e:
        raise ValueError(
            f"PDF appears corrupted or unreadable: {pdf_path.name}. {e!s}"
        ) from e
    except OSError as e:
        raise ValueError(
            f"Could not read PDF file: {pdf_path.name}. {e!s}"
        ) from e


def iter_pdf_page_text(
    path: PathLike,
    *,
    extraction_mode: Optional[str] = "layout",
) -> Iterable[tuple[int, str]]:
    """Yield `(page_number, text)` for each page in a PDF.

    This is a lightweight helper when you don't want LangChain `Document`s yet.
    """

    result = load_pdf_as_documents(
        path, extraction_mode=extraction_mode, skip_empty_pages=False
    )
    for doc in result.documents:
        yield int(doc.metadata["page"]), doc.page_content

