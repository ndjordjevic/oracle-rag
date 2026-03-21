# Investigation: Adding PinRAG MCP to Cursor's MCP Server List

**Date:** March 2025  
**Status:** Investigation complete  
**Related:** [implementation-checklist.md](../implementation-checklist.md) — "Investigate how to add pinrag mcp to cursor mcp server list"

---

## Executive Summary

Cursor does **not** have a single built-in MCP marketplace like VS Code's Extensions view. Instead, discovery happens through **third-party directories** and **Cursor's official GitHub repo**. There are four main paths to get PinRAG listed:

| Platform | Effort | Process | One-Click Install |
|----------|--------|---------|-------------------|
| **cursor/mcp-servers** (official) | Low | Submit GitHub issue with template | Yes — `cursor.com/en/install-mcp` |
| **cursor.store** | Low | Web form at cursor.store/mcp/new | Yes |
| **mcp-marketplace.io** | Low | Sign up, submit at /submit | Yes |
| **cursormcp.dev** | Unknown | No public submission; may auto-discover from GitHub | N/A |

**Recommendation:** Submit to **cursor/mcp-servers** first (official, highest visibility), then **cursor.store** and **mcp-marketplace.io** for broader reach.

---

## 1. Cursor's Official MCP List: cursor/mcp-servers

### 1.1 Overview

- **Repo:** [github.com/cursor/mcp-servers](https://github.com/cursor/mcp-servers)
- **Purpose:** Curated collection of MCP servers for developer tools
- **Visibility:** Listed servers get one-click "Install" links that add the server to the user's `mcp.json`
- **Examples:** GitHub, Slack, Playwright, firecrawl, DuckDB (uvx), dbt Labs, etc.

### 1.2 Submission Process

1. Open [Server Request Template](https://github.com/cursor/mcp-servers/issues/new?template=server-request.yml)
2. Fill in the form:
   - **Server Name:** PinRAG
   - **Server URL/Repository:** https://github.com/ndjordjevic/pinrag (or pypi.org/project/pinrag)
   - **Description:** RAG system for PDFs, YouTube, GitHub repos, Discord exports. Index documents, query with citations via MCP tools.
   - **Requirements Check:** ✓ Installation docs, ✓ Developer-focused, ✓ Icon (create square SVG)
   - **Configuration JSON:** See below
   - **Icon:** Attach square SVG logo

3. Submit the issue. Cursor team reviews, tests, and adds to the README if accepted.

### 1.3 Configuration JSON for PinRAG

**Option A — pinrag-mcp (user must `pipx install pinrag` first):**

```json
{
  "command": "pinrag-mcp",
  "env": {
    "OPENAI_API_KEY": "",
    "ANTHROPIC_API_KEY": ""
  }
}
```

**Option B — uvx (no prior install; requires `uv` on PATH):**

```json
{
  "command": "uvx",
  "args": ["--from", "pinrag", "pinrag-mcp"],
  "env": {
    "OPENAI_API_KEY": "",
    "ANTHROPIC_API_KEY": ""
  }
}
```

**Recommendation:** Use **Option B (uvx)** as primary — fewer setup steps. The PyPI package exposes **`pinrag-mcp`**, not `pinrag`, so use `uvx --from pinrag pinrag-mcp` (not `uvx pinrag`). Document that users need [uv](https://docs.astral.sh/uv/) installed. PinRAG reads only the process environment (MCP `env` in `mcp.json` or exported shell vars); there is no built-in `.env` loader.

### 1.4 One-Click Install URL Format

Cursor uses: `https://cursor.com/en/install-mcp?name={name}&config={base64}`

Example for PinRAG (uvx — user should fill `env` with API keys):

```javascript
const config = { command: "uvx", args: ["--from", "pinrag", "pinrag-mcp"], env: {} };
const b64 = btoa(JSON.stringify(config));
const url = `https://cursor.com/en/install-mcp?name=pinrag&config=${encodeURIComponent(b64)}`;
```

**Note:** `btoa` in browser; in Node use `Buffer.from(JSON.stringify(config)).toString('base64')`.

### 1.5 Requirements (from CONTRIBUTING.md)

- Valid MCP server with proper protocol implementation ✓
- Actively maintained and publicly available ✓
- Clear installation and usage documentation ✓
- Solves real development problems ✓ (RAG for docs, codebases)
- Professional presentation ✓

**What they don't accept:** Personal projects without broad appeal, consumer apps, duplicates.

**PinRAG fit:** Developer-focused (index PDFs, GitHub repos, ask questions with citations). Fits "knowledge bases, wikis, documentation" and "API documentation" categories.

### 1.6 Icon Requirement

The template requires: *"I've attached a square SVG logo to this issue"*. Create or export a square SVG for PinRAG (e.g. from existing assets or a simple RAG/document icon).

---

## 2. cursor.store

### 2.1 Overview

- **URL:** [cursor.store](https://www.cursor.store/)
- **Submit:** [List your MCP (free)](https://www.cursor.store/mcp/new)
- **Type:** Curated marketplace; free listing, optional paid featured placement ($49/mo)

### 2.2 Requirements (from [rules](https://www.cursor.store/rules))

- **Metadata:** name, slug, short/long description, category, tags, author, repo URL, install snippet, permissions
- **Install snippet:** Must work in Cursor; use secure defaults; no real credentials
- **Permission level:** Declare `low` | `medium` | `high`
  - PinRAG: **medium** (uses API keys for OpenAI/Anthropic, reads/writes local files for Chroma)
- **Quality:** README with install/usage; valid MCP responses; graceful errors

### 2.3 Categories

PinRAG fits: **AI / ML Helpers**, **Data & APIs**, or **Developer Tools**.

### 2.4 Install Snippet for Listing

```json
{
  "mcpServers": {
    "pinrag": {
      "command": "uvx",
      "args": ["--from", "pinrag", "pinrag-mcp"],
      "env": {
        "OPENAI_API_KEY": "<YOUR_OPENAI_KEY>",
        "ANTHROPIC_API_KEY": "<YOUR_ANTHROPIC_KEY>"
      }
    }
  }
}
```

---

## 3. mcp-marketplace.io

### 3.1 Overview

- **URL:** [mcp-marketplace.io](https://mcp-marketplace.io/)
- **Submit:** [Submit Your Tool](https://mcp-marketplace.io/submit) (requires sign-in: GitHub or email)
- **Features:** Security scanning, one-click install, 2400+ tools
- **Categories:** Developer Tools, Data & Analytics, Productivity, Content & Media, etc.

### 3.2 Submission

1. Create account (GitHub or email)
2. Go to /submit
3. Provide tool details; platform scans and lists

**PyPI packages:** They discover MCP servers from PyPI. PinRAG is already on PyPI as `pinrag`; consider ensuring the package has `-mcp` in the name or clear MCP metadata for discoverability (optional; they may also accept manual submission).

---

## 4. cursormcp.dev

### 4.1 Overview

- **URL:** [cursormcp.dev](https://cursormcp.dev/)
- **Size:** 1,544 servers, 1,236 developers
- **Submission:** No public "Submit" or "Add" flow found. May aggregate from:
  - GitHub (stars, MCP-related repos)
  - cursor/mcp-servers
  - Other sources

### 4.2 Action

If PinRAG is added to **cursor/mcp-servers**, cursormcp.dev may pick it up automatically. Otherwise, check the site for contact/submission options or wait for organic discovery.

---

## 5. Cursor Install URL (Direct Use)

Even without being listed, you can provide a one-click install link in the PinRAG README:

```
https://cursor.com/en/install-mcp?name=pinrag&config=eyJjb21tYW5kIjoidXZ4IiwiYXJncyI6WyItLWZyb20iLCJwaW5yYWciLCJwaW5yYWctbWNwIl0sImVudiI6e319
```

(Decodes to `{"command":"uvx","args":["--from","pinrag","pinrag-mcp"],"env":{}}` — user should add keys to `env` in `mcp.json` or export them before starting the client.)

**Generate dynamically:**

```javascript
const config = { command: "uvx", args: ["--from", "pinrag", "pinrag-mcp"], env: {} };
const url = `https://cursor.com/en/install-mcp?name=pinrag&config=${btoa(JSON.stringify(config))}`;
```

---

## 6. Cursor MCP Extension API (Programmatic Registration)

For enterprise/MDM use, Cursor exposes [vscode.cursor.mcp.registerServer](https://cursor.com/docs/context/mcp-extension-api). This is for **extensions** that register MCP servers programmatically, not for getting listed in directories. PinRAG could be wrapped in a Cursor extension (similar to VS Code) that calls `registerServer` — see [vscode-marketplace-investigation.md](vscode-marketplace-investigation.md) for the extension approach.

---

## 7. Recommended Action Plan

### Phase 1: Official List (1–2 hours)

1. **Create PinRAG icon** — Square SVG (e.g. 64×64 or 128×128)
2. **Submit to cursor/mcp-servers** via [Server Request Template](https://github.com/cursor/mcp-servers/issues/new?template=server-request.yml)
   - Use uvx config; document MCP `env` for API keys
   - Attach SVG icon
3. **Add one-click install to README** — Link to `cursor.com/en/install-mcp?name=pinrag&config=...` in Cursor section

### Phase 2: Other Directories (30 min each)

1. **cursor.store** — Submit at [mcp/new](https://www.cursor.store/mcp/new) with metadata and install snippet
2. **mcp-marketplace.io** — Sign up, submit at [submit](https://mcp-marketplace.io/submit)

### Phase 3: Monitor

- Watch for cursormcp.dev listing (may be automatic after cursor/mcp-servers)
- Respond to any feedback from Cursor team on the GitHub issue

---

## 8. References

- [cursor/mcp-servers](https://github.com/cursor/mcp-servers) — Official list
- [CONTRIBUTING.md](https://github.com/cursor/mcp-servers/blob/main/CONTRIBUTING.md)
- [Server Request Template](https://github.com/cursor/mcp-servers/issues/new?template=server-request.yml)
- [cursor.store](https://www.cursor.store/) — [List MCP](https://www.cursor.store/mcp/new), [Rules](https://www.cursor.store/rules)
- [mcp-marketplace.io](https://mcp-marketplace.io/) — [Submit](https://mcp-marketplace.io/submit)
- [cursormcp.dev](https://cursormcp.dev/) — Directory (no clear submit)
- [Cursor MCP Extension API](https://cursor.com/docs/context/mcp-extension-api)
