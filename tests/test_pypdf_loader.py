from __future__ import annotations

from pathlib import Path

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

