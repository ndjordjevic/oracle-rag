"""Integration test: stdio MCP from **PyPI** via ``uv tool run --from pinrag pinrag-mcp``.

Same tool sequence as ``test_mcp_stdio_repo.py``, but the subprocess runs the published
package from PyPI (not the local repo).

Requires ``uv`` (same as ``uvx --from <spec> pinrag-mcp``). API keys: same as the repo
stdio test — see ``tests/mcp_stdio_integration.env.example``.

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

from tests.helpers.mcp_stdio_env import build_server_env_for_mcp_itest, truthy_env
from tests.helpers.mcp_stdio_flow import run_amiga_pdf_stdio_flow

_REPO_ROOT = Path(__file__).resolve().parents[1]
_AMIGA_PDF = _REPO_ROOT / "data" / "pdfs" / "Bare-metal Amiga programming 2021_ocr.pdf"

_COLLECTION_ITEST_PYPI = "pinrag_itest_pypi"
_QUERY_TEXT = "What's Amiga AGA?"

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
def test_amiga_pdf_roundtrip_pypi_package(tmp_path: Path) -> None:
    """PyPI package: spawn ``pinrag-mcp`` from the index, same PDF roundtrip; isolated Chroma."""
    if truthy_env("PINRAG_MCP_ITEST_SKIP_PYPI"):
        pytest.skip("PINRAG_MCP_ITEST_SKIP_PYPI set")

    chroma_dir = tmp_path / "chroma_itest_pypi"
    pypi_spec = _pypi_spec()
    logger.info("MCP stdio integration — PyPI package (spec=%s)", pypi_spec)
    logger.info("PDF path: %s (exists=%s)", _AMIGA_PDF, _AMIGA_PDF.is_file())

    env = build_server_env_for_mcp_itest(
        chroma_dir,
        collection_name=_COLLECTION_ITEST_PYPI,
        test_file=Path(__file__),
    )

    if not env.get("OPENAI_API_KEY", "").strip():
        pytest.skip(f"OPENAI_API_KEY not set. {_SKIP_KEYS_HINT}")
    if not env.get("ANTHROPIC_API_KEY", "").strip():
        pytest.skip(f"ANTHROPIC_API_KEY not set. {_SKIP_KEYS_HINT}")
    if not _AMIGA_PDF.is_file():
        pytest.skip("Amiga PDF not present")
    uv_bin = _uv_bin()
    if not uv_bin:
        pytest.skip("uv not found (install uv or set PINRAG_TEST_UV)")
    logger.info("uv binary: %s", uv_bin)

    async def _run() -> None:
        params = StdioServerParameters(
            command=uv_bin,
            args=["tool", "run", "--from", pypi_spec, "pinrag-mcp"],
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
                    await run_amiga_pdf_stdio_flow(
                        session,
                        pdf_path=_AMIGA_PDF,
                        query_text=_QUERY_TEXT,
                        log=logger,
                    )
        finally:
            logger.info("Removing temp chroma dir: %s", chroma_dir)
            shutil.rmtree(chroma_dir, ignore_errors=True)

    asyncio.run(_run())
