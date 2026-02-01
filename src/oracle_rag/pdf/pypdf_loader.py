from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Union

from langchain_core.documents import Document
from pypdf import PdfReader


PathLike = Union[str, Path]


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
    - Phase 1 assumes digitally-born PDFs (no OCR).
    - Metadata uses 1-indexed page numbers to match human expectations.
    - `pypdf` supports `extraction_mode="layout"` for better spacing fidelity.

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

    reader = PdfReader(str(pdf_path))
    total_pages = len(reader.pages)

    docs: list[Document] = []
    for page_index, page in enumerate(reader.pages):
        page_number = page_index + 1  # 1-indexed
        text = page.extract_text(extraction_mode=extraction_mode) or ""
        text = text.strip()

        if skip_empty_pages and not text:
            continue

        docs.append(
            Document(
                page_content=text,
                metadata={
                    "source": str(pdf_path),
                    "file_name": pdf_path.name,
                    "page": page_number,
                    "total_pages": total_pages,
                },
            )
        )

    return PdfLoadResult(source_path=pdf_path, documents=docs, total_pages=total_pages)


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

