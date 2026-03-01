from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from oracle_rag.pdf.pypdf_loader import load_pdf_as_documents, iter_pdf_page_text


def test_load_pdf_as_documents_missing_file() -> None:
    with pytest.raises(FileNotFoundError):
        load_pdf_as_documents("does-not-exist.pdf")


def test_load_pdf_as_documents_smoke() -> None:
    # Uses the sample PDF we downloaded during setup. Skip if not present.
    repo_root = Path(__file__).resolve().parents[1]
    sample_pdf = repo_root / "data" / "pdfs" / "sample-text.pdf"
    if not sample_pdf.exists():
        pytest.skip("sample PDF not present; skipping smoke test")

    result = load_pdf_as_documents(sample_pdf)
    assert result.total_pages > 0
    assert len(result.documents) > 0
    assert all("page" in d.metadata for d in result.documents)
    assert any(d.page_content.strip() for d in result.documents)


def test_load_pdf_as_documents_metadata_keys() -> None:
    """Each document has required metadata; document_title/author when present in PDF."""
    repo_root = Path(__file__).resolve().parents[1]
    sample_pdf = repo_root / "data" / "pdfs" / "sample-text.pdf"
    if not sample_pdf.exists():
        pytest.skip("sample PDF not present; skipping metadata test")

    result = load_pdf_as_documents(sample_pdf)
    assert len(result.documents) >= 1
    doc = result.documents[0]
    required = {"source", "file_name", "page", "total_pages"}
    assert required.issubset(doc.metadata.keys())
    assert doc.metadata["file_name"] == sample_pdf.name
    assert doc.metadata["page"] >= 1
    assert doc.metadata["total_pages"] == result.total_pages
    # document_title / document_author only if present in PDF
    for key in ("document_title", "document_author"):
        if key in doc.metadata:
            assert isinstance(doc.metadata[key], str)
            assert len(doc.metadata[key]) > 0


def test_load_pdf_as_documents_corrupted_pdf_raises() -> None:
    """Raises ValueError with user-facing message when PDF is corrupted or unreadable."""
    from pypdf.errors import PyPdfError

    repo_root = Path(__file__).resolve().parents[1]
    sample_pdf = repo_root / "data" / "pdfs" / "sample-text.pdf"
    if not sample_pdf.exists():
        pytest.skip("sample PDF not present; skipping corrupted-PDF test")

    with patch("oracle_rag.pdf.pypdf_loader.PdfReader") as mock_reader:
        mock_reader.side_effect = PyPdfError("Invalid PDF structure")
        with pytest.raises(ValueError, match="PDF appears corrupted or unreadable"):
            load_pdf_as_documents(sample_pdf)


def test_load_pdf_as_documents_no_text_raises() -> None:
    """Raises ValueError when no text is extracted (e.g. image-only PDF)."""
    from pypdf import PageObject

    repo_root = Path(__file__).resolve().parents[1]
    sample_pdf = repo_root / "data" / "pdfs" / "sample-text.pdf"
    if not sample_pdf.exists():
        pytest.skip("sample PDF not present; skipping no-text test")

    with patch.object(PageObject, "extract_text", return_value=""):
        with pytest.raises(ValueError, match="No text extracted"):
            load_pdf_as_documents(sample_pdf, skip_empty_pages=True)


def test_iter_pdf_page_text() -> None:
    """Test iter_pdf_page_text and print page results to console (run with pytest -s)."""
    repo_root = Path(__file__).resolve().parents[1]
    sample_pdf = repo_root / "data" / "pdfs" / "sample-text.pdf"
    if not sample_pdf.exists():
        pytest.skip("sample PDF not present; skipping test")

    pages = list(iter_pdf_page_text(sample_pdf))
    assert len(pages) > 0
    for page_number, text in pages:
        assert isinstance(page_number, int)
        assert page_number >= 1
        assert isinstance(text, str)
        preview = (text[:80] + "…") if len(text) > 80 else text
        print(f"Page {page_number}: {preview!r}")

    # Consistency with load_pdf_as_documents (same doc count, same content per page)
    result = load_pdf_as_documents(sample_pdf, skip_empty_pages=False)
    assert len(pages) == len(result.documents)
    for (page_num, text), doc in zip(pages, result.documents):
        assert page_num == doc.metadata["page"]
        assert text == doc.page_content

