# Oracle-RAG: Distribution Options for End Users

How others can use Oracle-RAG MCP **without cloning the GitHub repo**. Options range from simple downloads to cloud-hosted services.

---

## 1. PyPI Package (pip / uv install)

**What:** Publish to [PyPI](https://pypi.org). Users run `pip install oracle-rag` or `uv add oracle-rag`.

**User flow:**
```bash
pip install oracle-rag
# or: uv tool install oracle-rag
oracle-rag-mcp   # if we add a CLI entry point
```

**Pros:**
- Standard Python distribution; familiar to Python users
- Versioned releases (`pip install oracle-rag==1.0.0`)
- Works with `pip`, `uv`, `poetry`, `conda`
- No clone required; install from anywhere

**Cons:**
- Requires Python 3.12+ on the user's machine
- User must configure Cursor MCP to run `oracle-rag-mcp` (or `python -m oracle_rag.mcp`) with correct cwd for `.env` and `chroma_db`

**Implementation:**
- Add `[project.scripts]` to `pyproject.toml`, e.g. `oracle-rag-mcp = "oracle_rag.mcp:main"` (or point to a small CLI that loads `.env` from cwd or `~/.config/oracle-rag/`)
- Decide where config and `chroma_db` live when installed globally (e.g. `~/.local/share/oracle-rag/` or current working directory)
- Publish: `uv build` → `uv publish` (or `twine upload`)

---

## 2. pipx run (no permanent install)

**What:** Users run `pipx run oracle-rag` without installing. Similar to `npx` for Node.

**User flow:**
```bash
pipx run oracle-rag   # downloads, runs in temp env, exits
```

**Pros:**
- No permanent install; good for trying the tool
- Isolated from system Python

**Cons:**
- Requires `pipx` and Python
- Each run fetches/caches the package; first run can be slow
- MCP servers are long-lived (Cursor spawns them), so `pipx run` is less natural than `pipx install` for this use case

**Best for:** Quick try-before-install. For daily use, `pipx install oracle-rag` is better.

---

## 3. GitHub Release (zip / tarball)

**What:** Attach a source archive (`.zip`, `.tar.gz`) or a built wheel (`.whl`) to GitHub Releases.

**User flow:**
```bash
# Download from GitHub Releases, e.g. v1.0.0
curl -L -o oracle-rag.zip https://github.com/you/oracle-rag/releases/download/v1.0.0/oracle-rag-1.0.0.zip
unzip oracle-rag.zip && cd oracle-rag-1.0.0
uv sync   # or pip install -e .
# Configure .env, then point Cursor to: uv run python scripts/mcp_server.py
```

**Pros:**
- No PyPI account or publishing step
- Users get a specific version; no clone
- Can also attach pre-built wheels for `pip install oracle-rag-1.0.0-py3-none-any.whl`

**Cons:**
- Manual download and setup; more steps than `pip install`
- User still needs Python and uv/pip

---

## 4. Docker Image

**What:** Package as a Docker image. Users run `docker run <image>`.

**Pros:**
- No Python install on host; works on any OS with Docker
- Reproducible environment
- Easy to deploy to cloud (e.g. AWS ECS, GCP Cloud Run)

**Cons:**
- MCP stdio transport expects a local process. For Docker, we need either:
  - **Option A:** Run the container with a volume; Cursor runs `docker run -i oracle-rag` and talks via stdio (possible, but Cursor config is trickier).
  - **Option B:** Run the server in HTTP/SSE mode inside the container and expose a port; users connect to `http://localhost:8000` (or a remote URL). Requires implementing SSE transport.
- Chroma persistence: need a volume for `chroma_db`; user must manage `OPENAI_API_KEY` (env or config)

**Implementation:**
- Use MCP’s SSE transport for remote servers (or Streamable HTTP per newer spec)
- Add `Dockerfile`; expose HTTP port; document `docker run -p 8000:8000 -e OPENAI_API_KEY=... -v ./chroma_db:/app/chroma_db oracle-rag`

---

## 5. Cloud Hosting (Remote MCP Server)

**What:** Deploy the MCP server to a cloud provider. Users connect from Cursor or other clients to a remote URL (no local install).

**Pros:**
- Zero local setup for users; just add the server URL in Cursor
- Centralized updates; no version drift
- Secrets (e.g. `OPENAI_API_KEY`) stay on the server; users don’t need API keys
- Team can share one index

**Cons:**
- Requires implementing SSE (or Streamable HTTP) transport
- Hosting cost and ops
- Data privacy: PDFs and embeddings go to your server; users must trust you

**Possible hosting models:**
- **Cloud VM (AWS EC2, GCP GCE, DigitalOcean):** Full control; run Python + FastAPI/Starlette; reverse proxy (Nginx) for long-lived connections
- **Serverless (AWS Lambda, GCP Cloud Functions):** Stateless; less suitable for long-lived MCP sessions
- **PaaS (Railway, Fly.io, Render, Heroku):** Simple deploy; Docker or buildpack
- **Cloudflare Workers:** Edge runtime; 50ms per event limit may be tight for RAG/LLM calls

**User flow:**
- You host at `https://oracle-rag.yourdomain.com`
- User adds MCP server in Cursor: type **URL**, URL = `https://oracle-rag.yourdomain.com/sse`
- Cursor connects over HTTP; no local Python or Docker

---

## 6. Standalone Executable (PyInstaller / Nuitka)

**What:** Build a single binary (e.g. `oracle-rag-mcp.exe` on Windows, `oracle-rag-mcp` on macOS/Linux). No Python install needed.

**Pros:**
- One binary; no Python, pip, or uv
- Works on machines without Python

**Cons:**
- Large binaries; build per platform (Windows, macOS, Linux)
- Chroma, LangChain, etc. add size; binary can be 100–300 MB
- Need CI to build for each platform

**Implementation:**
- Use PyInstaller or Nuitka; entry point = MCP server
- Distribute via GitHub Releases (e.g. `oracle-rag-mcp-1.0.0-macos-arm64`)

---

## 7. System Package Managers (Homebrew, Chocolatey, apt)

**What:** Package for Homebrew (macOS), Chocolatey (Windows), or apt (Linux).

**Pros:**
- Familiar for users of those platforms
- `brew install oracle-rag` or `choco install oracle-rag`

**Cons:**
- Separate packaging for each platform
- Often wraps a Python package or binary; more maintenance
- Smaller user base for niche tools

**Implementation:**
- Homebrew: create a formula that `pip install`s or uses a pre-built binary
- Chocolatey: similar; install script downloads and runs

---

## 8. Cursor / MCP Marketplace (if available)

**What:** If Cursor (or another MCP client) adds a marketplace, users could add Oracle-RAG with one click.

**Status:** As of early 2025, no public Cursor MCP marketplace is widely documented. This could change in the future.

---

## Comparison Summary

| Option | User effort | Your effort | Best for |
|--------|-------------|-------------|----------|
| **PyPI (pip install)** | Low | Low | Python users; standard distribution |
| **pipx (run)** | Low | Low | Quick try |
| **GitHub Release (zip)** | Medium | Low | Users who prefer a zip over pip |
| **Docker** | Medium | Medium | Users with Docker; cloud deploy |
| **Cloud hosting** | Very low | High | Teams; no local install |
| **Standalone binary** | Low | Medium | Non-Python users |
| **Homebrew / Chocolatey** | Low | Medium | macOS / Windows power users |

---

## Recommended Path

1. **Short term:** Publish to **PyPI** and add a **GitHub Release** with a source zip and wheels. Most users can `pip install oracle-rag` or download the release.
2. **Medium term:** Add **Docker** support with SSE transport for users who prefer containers or want to deploy to cloud.
3. **Long term:** If you want a hosted offering, deploy **cloud-hosted** MCP for teams or users who want zero local setup.

---

## Implementation Checklist (for PyPI)

- [x] Add `[project.scripts]` entry point for `oracle-rag-mcp`
- [x] Configure default paths for config: `.env` loaded from cwd, `~/.config/oracle-rag/`, `~/.oracle-rag/`; `chroma_db` in cwd by default
- [x] Document `pip install oracle-rag` and Cursor MCP config in README
- [x] Create PyPI account; `uv build` and `uv publish`
- [ ] Optional: GitHub Action to publish on tag (e.g. `v1.0.1`)

### How to publish

1. **Build:** `uv build` (creates `dist/` with sdist and wheel).
2. **API token required:** PyPI no longer accepts username/password. Create a token at [pypi.org/manage/account/token/](https://pypi.org/manage/account/token/).
3. **Publish:** `uv publish`.
   - When prompted: username = `__token__`, password = your `pypi-...` token.
   - Or: `export UV_PUBLISH_TOKEN=pypi-your-token` then `uv publish`.

### Test this deployment (regular user flow)

1. **Install:**
   ```bash
   pipx install oracle-rag
   # or: uv tool install oracle-rag
   ```
2. **Configure:**
   ```bash
   mkdir -p ~/.oracle-rag
   echo "OPENAI_API_KEY=sk-..." > ~/.oracle-rag/.env
   ```
3. **Verify:**
   ```bash
   oracle-rag-mcp
   ```
   Server should start and wait for stdio input (Ctrl+C to stop).
4. **Cursor MCP:** Add to `~/.cursor/mcp.json`:
   ```json
   "oracle-rag": {
     "command": "oracle-rag-mcp"
   }
   ```
   Restart Cursor; verify `add_pdf`, `list_pdfs`, `query_pdf`, `remove_pdf` tools appear.
   No `cwd` needed — index is stored in `~/.oracle-rag/chroma_db` by default.
