"""Pytest fixtures and configuration for PinRAG tests."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from langchain_core.embeddings import Embeddings


@pytest.fixture
def fake_embeddings() -> Embeddings:
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


def require_working_openai_key(reason: str = "integration test") -> None:
    """Skip if ``OPENAI_API_KEY`` is missing or rejected by the API (401).

    Uses a lightweight ``models.list()`` call so invalid keys do not fail long runs.
    """
    key = (os.environ.get("OPENAI_API_KEY") or "").strip()
    if not key:
        pytest.skip(f"{reason}: OPENAI_API_KEY not set")
    try:
        from openai import APIConnectionError, AuthenticationError, OpenAI

        OpenAI().models.list()
    except AuthenticationError as e:
        pytest.skip(f"{reason}: invalid or expired OPENAI_API_KEY ({e})")
    except APIConnectionError as e:
        pytest.skip(f"{reason}: OpenAI API unreachable ({e})")


def require_working_llm_for_default_provider(reason: str = "integration test") -> None:
    """Skip if the configured LLM provider credentials are missing or invalid."""
    from pinrag.config import get_llm_provider

    provider = get_llm_provider()
    if provider == "openai":
        require_working_openai_key(reason=reason)
        return
    if provider == "anthropic":
        key = (os.environ.get("ANTHROPIC_API_KEY") or "").strip()
        if not key:
            pytest.skip(f"{reason}: ANTHROPIC_API_KEY not set")
        try:
            from anthropic import Anthropic, APIConnectionError, AuthenticationError

            Anthropic().models.list(limit=1)
        except AuthenticationError as e:
            pytest.skip(f"{reason}: invalid or expired ANTHROPIC_API_KEY ({e})")
        except APIConnectionError as e:
            pytest.skip(f"{reason}: Anthropic API unreachable ({e})")
        return
    if provider == "openrouter":
        key = (os.environ.get("OPENROUTER_API_KEY") or "").strip()
        if not key:
            pytest.skip(f"{reason}: OPENROUTER_API_KEY not set")
        try:
            import requests
        except ImportError:
            pytest.skip(f"{reason}: requests not installed")
        try:
            r = requests.get(
                "https://openrouter.ai/api/v1/key",
                headers={"Authorization": f"Bearer {key}"},
                timeout=15,
            )
        except requests.RequestException as e:
            pytest.skip(f"{reason}: OpenRouter API unreachable ({e})")
        if r.status_code == 401:
            pytest.skip(f"{reason}: invalid or expired OPENROUTER_API_KEY")
        if not r.ok:
            pytest.skip(f"{reason}: OpenRouter key check failed (HTTP {r.status_code})")


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Tag tests that use ``sample_pdf_path`` so ``-m 'not integration'`` excludes them."""
    integration = pytest.mark.integration
    for item in items:
        fixturenames = getattr(item, "fixturenames", ()) or ()
        if "sample_pdf_path" in fixturenames:
            item.add_marker(integration)
