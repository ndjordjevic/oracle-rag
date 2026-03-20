"""Pytest fixtures and configuration for PinRAG tests."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from langchain_core.embeddings import Embeddings


@pytest.fixture
def fake_embeddings() -> "Embeddings":
    """Deterministic embeddings for Chroma tests (no API keys)."""
    from langchain_core.embeddings import FakeEmbeddings

    return FakeEmbeddings(size=32)


@pytest.fixture
def repo_root() -> Path:
    """Repository root (parent of tests/)."""
    return Path(__file__).resolve().parents[1]


@pytest.fixture
def sample_pdf_path(repo_root: Path) -> Path:
    """Path to bundled sample PDF; skips if missing (``integration``: optional asset)."""
    path = repo_root / "data" / "pdfs" / "sample-text.pdf"
    if not path.exists():
        pytest.skip("sample PDF not present")
    return path


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Tag tests that use ``sample_pdf_path`` so ``-m 'not integration'`` excludes them."""
    integration = pytest.mark.integration
    for item in items:
        fixturenames = getattr(item, "fixturenames", ()) or ()
        if "sample_pdf_path" in fixturenames:
            item.add_marker(integration)
