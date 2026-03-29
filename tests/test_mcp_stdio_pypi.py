"""Integration test: stdio MCP from **PyPI** via ``uv tool run --from pinrag pinrag``.

Same tool sequence as ``test_mcp_stdio_repo.py``, but the subprocess runs the published
package from PyPI (not the local repo).

Requires ``uv`` (same as ``uvx <spec>`` / ``uv tool run --from <spec> pinrag``). API keys: same as the repo
stdio test — see ``tests/mcp_stdio_integration.env.example``.

**PDF / query:** same defaults as the repo test (``data/pdfs/sample-text.pdf`` and a
generic question; override with ``PINRAG_MCP_ITEST_PDF`` / ``PINRAG_MCP_ITEST_QUERY``).

**Skip PyPI download / network:** set ``PINRAG_MCP_ITEST_SKIP_PYPI=1``.

**Pin the package version:** ``PINRAG_MCP_ITEST_PYPI_SPEC=pinrag==0.9.0`` (default is
``pinrag``, i.e. latest on PyPI).

Verbose progress::

    pytest tests/test_mcp_stdio_pypi.py -v -m integration --log-cli-level=INFO
"""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
from pathlib import Path

import pytest
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from tests.conftest import require_working_openai_key
from tests.helpers.mcp_stdio_env import (
    build_server_env_for_mcp_itest,
    mcp_stdio_itest_query,
    resolve_mcp_stdio_itest_pdf,
    truthy_env,
)
from tests.helpers.mcp_stdio_flow import run_pdf_stdio_roundtrip

_REPO_ROOT = Path(__file__).resolve().parents[1]

_COLLECTION_ITEST_PYPI = "pinrag_itest_pypi"

logger = logging.getLogger(__name__)

_SKIP_KEYS_HINT = (
    "Set OPENAI_API_KEY and ANTHROPIC_API_KEY in the environment, or copy "
    "tests/mcp_stdio_integration.env.example to tests/.mcp_stdio_integration.env, "
    "or set PINRAG_MCP_ITEST_ENV_FILE. Optional: PINRAG_ITEST_USE_CURSOR_MCP_JSON=1 "
    "to load keys from ~/.cursor/mcp.json pinrag-dev (deprecated)."
)


def _uv_bin() -> str | None:
    return os.environ.get("PINRAG_TEST_UV") or shutil.which("uv")


def _pypi_spec() -> str:
    return (os.environ.get("PINRAG_MCP_ITEST_PYPI_SPEC") or "pinrag").strip() or "pinrag"


@pytest.mark.integration
@pytest.mark.pypi_mcp
def test_pdf_roundtrip_pypi_package(tmp_path: Path) -> None:
    """PyPI package: spawn ``pinrag`` from the index, same PDF roundtrip; isolated Chroma."""
    if truthy_env("PINRAG_MCP_ITEST_SKIP_PYPI"):
        pytest.skip("PINRAG_MCP_ITEST_SKIP_PYPI set")

    pdf = resolve_mcp_stdio_itest_pdf(_REPO_ROOT)
    if pdf is None:
        override = (os.environ.get("PINRAG_MCP_ITEST_PDF") or "").strip()
        if override:
            pytest.skip(f"PINRAG_MCP_ITEST_PDF not found: {override}")
        pytest.skip(
            "No PDF for MCP stdio tests: add data/pdfs/sample-text.pdf or set PINRAG_MCP_ITEST_PDF."
        )
    query_text = mcp_stdio_itest_query()

    chroma_dir = tmp_path / "chroma_itest_pypi"
    pypi_spec = _pypi_spec()
    logger.info("MCP stdio integration — PyPI package (spec=%s)", pypi_spec)
    logger.info("PDF path: %s", pdf)

    env = build_server_env_for_mcp_itest(
        chroma_dir,
        collection_name=_COLLECTION_ITEST_PYPI,
        test_file=Path(__file__),
    )

    if not env.get("OPENAI_API_KEY", "").strip():
        pytest.skip(f"OPENAI_API_KEY not set. {_SKIP_KEYS_HINT}")
    require_working_openai_key(
        "PyPI MCP stdio (published package may use OpenAI for embeddings and/or LLM)"
    )
    uv_bin = _uv_bin()
    if not uv_bin:
        pytest.skip("uv not found (install uv or set PINRAG_TEST_UV)")
    logger.info("uv binary: %s", uv_bin)

    async def _run() -> None:
        params = StdioServerParameters(
            command=uv_bin,
            args=["tool", "run", "--from", pypi_spec, "pinrag"],
            env=env,
        )
        logger.info(
            "Spawning MCP server: %s %s",
            params.command,
            " ".join(params.args or []),
        )
        try:
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    logger.info(
                        "Connecting stdio client; calling session.initialize() …"
                    )
                    await session.initialize()
                    logger.info("MCP session initialized (protocol handshake done)")
                    await run_pdf_stdio_roundtrip(
                        session,
                        pdf_path=pdf,
                        query_text=query_text,
                        log=logger,
                    )
        finally:
            logger.info("Removing temp chroma dir: %s", chroma_dir)
            shutil.rmtree(chroma_dir, ignore_errors=True)

    asyncio.run(_run())
