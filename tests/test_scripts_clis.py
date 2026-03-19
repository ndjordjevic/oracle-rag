"""Smoke tests: script CLIs accept --help and exit cleanly (no API calls)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"

# Argparse-based scripts under scripts/ (skip eval/util-only entry points).
_SCRIPTS_HELP = (
    "index_cli.py",
    "index_discord_channels.py",
    "list_indexed_docs_cli.py",
    "print_pdf_all_metadata.py",
    "print_pdf_chunks.py",
    "print_pdf_page.py",
    "query_rag_cli.py",
    "rag_cli.py",
    "test_llm_cli.py",
    "create_multiquery_stress_dataset.py",
)


@pytest.mark.parametrize("filename", _SCRIPTS_HELP)
def test_script_help_exits_zero(filename: str) -> None:
    script = SCRIPTS / filename
    assert script.is_file(), f"Missing {script}"
    result = subprocess.run(
        [sys.executable, str(script), "--help"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"{filename}: stderr={result.stderr!r}"


def test_print_pdf_page_missing_file_exits_nonzero() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "print_pdf_page.py"), "/no/such/file.pdf", "1"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
