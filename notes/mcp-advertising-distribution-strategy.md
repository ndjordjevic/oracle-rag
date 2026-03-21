# PinRAG MCP: Advertising & Distribution Strategy

**Date:** March 2026  
**Status:** Investigation complete  
**Related:** [implementation-checklist.md](implementation-checklist.md) line 299, [vscode-marketplace-investigation.md](vscode-marketplace-investigation.md), [cursor-mcp-list-investigation.md](cursor-mcp-list-investigation.md)

---

## Executive Summary

Two complementary tracks:

1. **Distribution** — Get PinRAG listed in directories, marketplaces, and IDE galleries so people can *find and install* it.
2. **Advertising** — Drive awareness so people actually *visit* those listings, star the repo, and try PinRAG.

Neither works alone. Listings without promotion = buried among 17,000+ servers. Promotion without listings = nowhere for interested users to land with a one-click install.

---

## 1. Distribution: Where to List PinRAG

### Tier 1: High-Impact (Do First)

| # | Channel | Why | Effort | Status |
|---|---------|-----|--------|--------|
| 1 | **Official MCP Registry** (`modelcontextprotocol.io/registry`) | Authoritative source backed by Anthropic, GitHub, Block, Microsoft. Feeds downstream into VS Code, GitHub MCP, Pulse MCP. Supports PyPI packages. | Medium | Not started |
| 2 | **cursor/mcp-servers** GitHub issue | Official Cursor curated list. One-click install. High visibility among Cursor users. | Low | Not started |
| 3 | **mcp.so** | Largest directory (17,000+ servers). Simple web/CLI submission. | Low | Not started |
| 4 | **awesome-mcp-servers** GitHub PR | 83.7k stars. Enormous organic visibility. | Low | Not started |
| 5 | **VS Code one-click install URL** in README | Zero friction for VS Code users. Works today. | Very Low | Not started |
| 6 | **Cursor one-click install URL** in README | Zero friction for Cursor users. Works today. | Very Low | Not started |

### Tier 2: Broader Reach (Do Next)

| # | Channel | Why | Effort | Status |
|---|---------|-----|--------|--------|
| 7 | **cursor.store** | Curated Cursor marketplace. Free listing. | Low | Not started |
| 8 | **mcp-marketplace.io** | Security-scanned marketplace. One-click install. 2,400+ tools. | Low | Not started |
| 9 | **Windsurf.run** | Windsurf/Codeium MCP directory. | Low | Not started |
| 10 | **MCP Market** (`mcpmarket.com`) | Largest marketplace (21,700+ servers). | Low | Not started |
| 11 | **MCPCentral** (`mcpcentral.io`) | Additional directory with `mcp-publisher` CLI support. | Low | Not started |

### Tier 3: Higher Effort / Future

| # | Channel | Why | Effort | Blocker |
|---|---------|-----|--------|---------|
| 12 | **VS Code Extension** (marketplace) | Discoverability in Extensions view (`@mcp pinrag`). | 1–2 days | TypeScript wrapper needed; see [vscode-marketplace-investigation.md](vscode-marketplace-investigation.md) |
| 13 | **Smithery** (`smithery.ai`) | 2,880+ servers. Hosted gateway. | High | Requires Streamable HTTP transport (PinRAG is stdio-only). Only viable with PinRAG Cloud or adding HTTP transport. |
| 14 | **Glama** (`glama.ai`) | 9,000–19,000+ servers. Managed hosting. | Medium | Uses MCP Registry; may auto-discover once published there. |

---

## 2. Distribution Details

### 2.1 Official MCP Registry

The single most strategic listing — cascades into VS Code, GitHub, and potentially more clients.

**Prerequisites:**
- GitHub account (for `io.github.ndjordjevic/*` namespace)
- PinRAG already on PyPI ✓

**Steps:**
1. Install `mcp-publisher` CLI:
   ```bash
   curl -L "https://github.com/modelcontextprotocol/registry/releases/latest/download/mcp-publisher_darwin_arm64.tar.gz" | tar xz
   ```
2. Add ownership verification to PyPI README — include `mcp-name: io.github.ndjordjevic/pinrag` somewhere in the package README (PyPI checks this string).
3. Create `server.json` in the repo:
   ```json
   {
     "name": "io.github.ndjordjevic/pinrag",
     "registryType": "pypi",
     "package": "pinrag",
     "description": "RAG system for PDFs, YouTube, GitHub repos, Discord exports. Index documents and query with citations via MCP tools.",
     "homepage": "https://github.com/ndjordjevic/pinrag"
   }
   ```
4. Authenticate and publish:
   ```bash
   mcp-publisher login github
   mcp-publisher publish
   ```
5. Optional: Automate with GitHub Actions on tag (see `modelcontextprotocol.io/registry/github-actions`).

**Important:** The registry is in preview. Version metadata is immutable once published. Deletion/unpublishing is not currently available.

**Alternative Python tool:** `pip install publish-mcp-server` — a Python-native helper for the same flow.

**Refs:** [Registry quickstart](https://modelcontextprotocol.io/registry/quickstart), [Package types (PyPI)](https://modelcontextprotocol.io/registry/package-types), [Authentication](https://modelcontextprotocol.io/registry/authentication), [GitHub Actions](https://modelcontextprotocol.io/registry/github-actions)

### 2.2 cursor/mcp-servers

See full details in [cursor-mcp-list-investigation.md](cursor-mcp-list-investigation.md).

**Steps:**
1. Create square SVG icon for PinRAG.
2. Submit via [Server Request Template](https://github.com/cursor/mcp-servers/issues/new?template=server-request.yml).
3. Config JSON (uvx):
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

### 2.3 mcp.so

**Steps:**
1. Go to [mcp.so/submit](https://mcp.so/submit).
2. Type: MCP Server. Name: PinRAG. URL: `https://github.com/ndjordjevic/pinrag`.
3. Submit.

Alternative: `npx mcp-index https://github.com/ndjordjevic/pinrag`

**Requirements:** Open-source with permissive license (MIT ✓).

### 2.4 awesome-mcp-servers

**Repo:** [punkpeye/awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers) (83.7k stars)

**Steps:**
1. Fork the repo.
2. Add PinRAG under the appropriate category (e.g. "Knowledge & Memory") in alphabetical order:
   ```
   - [PinRAG](https://github.com/ndjordjevic/pinrag) - RAG system for PDFs, YouTube, GitHub repos, Discord exports. Index documents and query with citations. 🐍 🏠
   ```
3. Submit PR.

**Note:** 1,029 open PRs as of March 2026 — may take time to merge.

### 2.5 One-Click Install URLs (README)

The PyPI package exposes the **`pinrag-mcp`** console script (not `pinrag`), so the correct `uvx` invocation is **`uvx --from pinrag pinrag-mcp`** — not `uvx pinrag`.

**Cursor:**
```
https://cursor.com/en/install-mcp?name=pinrag&config=eyJjb21tYW5kIjoidXZ4IiwiYXJncyI6WyItLWZyb20iLCJwaW5yYWciLCJwaW5yYWctbWNwIl0sImVudiI6e319
```
Decodes to `{"command":"uvx","args":["--from","pinrag","pinrag-mcp"],"env":{}}`.

**VS Code:**
```
vscode:mcp/install?%7B%22name%22%3A%22pinrag%22%2C%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22--from%22%2C%22pinrag%22%2C%22pinrag-mcp%22%5D%7D
```
Decodes to `{"name":"pinrag","command":"uvx","args":["--from","pinrag","pinrag-mcp"]}`.

Add both as badges/buttons in the README Quick Start section. Users still need to add API keys to `mcp.json` after install.

### 2.6 cursor.store

See [cursor-mcp-list-investigation.md §2](cursor-mcp-list-investigation.md).

Submit at [cursor.store/mcp/new](https://www.cursor.store/mcp/new). Free listing. Category: AI / ML Helpers or Developer Tools. Permission: medium.

### 2.7 mcp-marketplace.io

Submit at [mcp-marketplace.io/submit](https://mcp-marketplace.io/submit) (GitHub sign-in). Category: Developer Tools or Data & Analytics. Pricing: Free. Optional: add `LAUNCHGUIDE.md` to the repo for auto-fill.

### 2.8 Windsurf.run

[windsurf.run](https://windsurf.run/) — Windsurf/Codeium MCP directory. Check for a "Submit" flow or contact. PinRAG config for Windsurf (`~/.codeium/windsurf/mcp_config.json`) uses the same Claude Desktop schema.

### 2.9 MCP Market (mcpmarket.com)

Submit via their web form. 21,700+ servers. Additional reach.

### 2.10 MCPCentral (mcpcentral.io)

Submit at [mcpcentral.io/submit-server](https://mcpcentral.io/submit-server). Uses `mcp-publisher` CLI.

### 2.11 VS Code Extension

See full details in [vscode-marketplace-investigation.md](vscode-marketplace-investigation.md).

**Summary:** TypeScript extension spawning `uvx --from pinrag pinrag-mcp`. Registers via `mcpServerDefinitionProviders`. Makes PinRAG discoverable via `@mcp pinrag` in Extensions view. Effort: 1–2 days.

**Decision:** Do after Tier 1 & 2 listings. The one-click URL and MCP Registry give most of the value without building an extension.

### 2.12 .well-known/mcp.json (Future)

Emerging standard (SEP-1960) for automated server discovery. AI clients (Claude, ChatGPT, Cursor) can auto-detect MCP servers at `/.well-known/mcp.json` endpoints. Only relevant when PinRAG has a web endpoint (PinRAG Cloud). Not applicable to stdio-only distribution.

---

## 3. Advertising: How to Promote PinRAG

### 3.1 README & Repository Optimization (Organic)

| Action | Details |
|--------|---------|
| **One-click install badges** | Cursor + VS Code install buttons at the top of README |
| **PyPI badge** | Already present |
| **GitHub Topics** | Ensure `mcp`, `mcp-server`, `rag`, `pdf`, `langchain`, `model-context-protocol` topics are set |
| **Demo GIF/screenshot** | Add a short demo showing: install → index PDF → query → get answer with citations |
| **Stars / social proof** | Encourage early users to star |

### 3.2 Content Marketing

| Channel | Format | Topic Ideas |
|---------|--------|-------------|
| **Dev.to / Hashnode** | Blog post | "How I Built a RAG MCP Server in Python", "Give Your AI Assistant a Memory for Documents" |
| **YouTube** | Demo video (2–3 min) | Install PinRAG, index a PDF, query from Cursor — show the whole flow |
| **Medium** | Tutorial | "Index Your PDFs, YouTube Videos, and GitHub Repos for AI Coding Assistants" |

### 3.3 Community Engagement

| Community | How |
|-----------|-----|
| **Reddit** — r/MCP, r/LocalLLaMA, r/langchain, r/cursor | Share PinRAG, explain the use case, answer questions |
| **Hacker News** — Show HN | "Show HN: PinRAG — MCP server that lets AI assistants query your PDFs, YouTube, GitHub repos" |
| **Twitter/X** | Post + demo GIF. Tag @AnthropicAI, @cursor_ai, @LangChainAI |
| **LangChain Discord** | Community showcase / show-and-tell |
| **MCP-focused Discord servers** | Share and discuss |

### 3.4 Ecosystem Partnerships

| Partner | How |
|---------|-----|
| **LangChain** | Submit to LangChain integrations page or community gallery |
| **Cursor** | Beyond the listing — write a "How to use PinRAG with Cursor" blog post |
| **VS Code** | If extension is published, it shows in Extensions view |

---

## 4. Recommended Execution Order

### Phase 1: Foundation (1–2 hours)

- [x] Add one-click install URLs to README (Cursor + VS Code) — see README **Quick Start → One-click install**
- [x] Ensure GitHub Topics are set (`mcp`, `mcp-server`, `rag`, etc.) — **done:** repo `ndjordjevic/pinrag` topics (polished): **chromadb, cursor, discord, github-repos, langchain, mcp, mcp-server, model-context-protocol, pdf, pypi, python, rag, vscode, youtube** (removed generic `github`; added MCP + PyPI + language/indexing tags).
- [x] Create square SVG icon for PinRAG — [`docs/pinrag-icon.svg`](../docs/pinrag-icon.svg) (128×128 viewBox; document + pin). Attach or link for `cursor/mcp-servers` / store submissions.

### Phase 2: Tier 1 Listings (half day)

- [ ] Submit to **Official MCP Registry** (add `mcp-name` to README, create `server.json`, publish)
- [ ] Submit to **cursor/mcp-servers** (GitHub issue with SVG icon)
- [ ] Submit to **mcp.so** (web form or CLI)
- [ ] Submit PR to **awesome-mcp-servers**

### Phase 3: Tier 2 Listings (1–2 hours)

- [ ] Submit to **cursor.store**
- [ ] Submit to **mcp-marketplace.io**
- [ ] Submit to **Windsurf.run** (if submission process exists)
- [ ] Submit to **MCP Market** (mcpmarket.com)
- [ ] Submit to **MCPCentral** (mcpcentral.io)

### Phase 4: Content & Community (ongoing)

- [ ] Create demo GIF/video for README
- [ ] Write first blog post (Dev.to or Hashnode)
- [ ] Post on Reddit (r/MCP, r/langchain)
- [ ] Post on Twitter/X
- [ ] Consider Hacker News Show HN

### Phase 5: Higher Effort (future)

- [ ] Build VS Code Extension (TypeScript wrapper)
- [ ] Explore Smithery listing (requires HTTP transport — PinRAG Cloud)
- [ ] Implement `.well-known/mcp.json` (PinRAG Cloud)

---

## 5. Key Observations

1. **The Official MCP Registry is the single most strategic listing** — it cascades into VS Code, GitHub MCP, and potentially Cursor. PyPI support means PinRAG qualifies today.

2. **One-click install URLs should go in the README immediately** — zero effort, high conversion for both Cursor and VS Code users.

3. **The VS Code Extension is nice-to-have, not urgent** — the one-click URL + MCP Registry cover most of the value. The extension adds organic discoverability in the Extensions view.

4. **Smithery requires Streamable HTTP** — PinRAG's stdio transport means Smithery is blocked until PinRAG Cloud or an HTTP transport layer is added.

5. **awesome-mcp-servers has a massive PR backlog** (1,029 open) — submit early, expect a wait.

6. **Content marketing matters more than directory count** — a single Hacker News post or popular Reddit thread drives more installs than 10 marketplace listings.

7. **A demo video/GIF is the highest-ROI content asset** — shows value instantly; reusable across README, blog posts, social media, and marketplace listings.

---

## 6. References

### Official MCP Registry
- [Registry overview](https://modelcontextprotocol.io/registry/about)
- [Quickstart](https://modelcontextprotocol.io/registry/quickstart)
- [Package types (PyPI support)](https://modelcontextprotocol.io/registry/package-types)
- [Authentication](https://modelcontextprotocol.io/registry/authentication)
- [GitHub Actions automation](https://modelcontextprotocol.io/registry/github-actions)
- [FAQ](https://modelcontextprotocol.io/registry/faq)

### Directories & Marketplaces
- [mcp.so/submit](https://mcp.so/submit) — Largest directory (17,000+ servers)
- [awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers) — 83.7k stars
- [cursor/mcp-servers](https://github.com/cursor/mcp-servers) — Official Cursor list
- [cursor.store/mcp/new](https://www.cursor.store/mcp/new) — Cursor marketplace
- [mcp-marketplace.io/submit](https://mcp-marketplace.io/submit) — Security-scanned marketplace
- [windsurf.run](https://windsurf.run/) — Windsurf/Codeium directory
- [mcpmarket.com](https://mcpmarket.com/) — 21,700+ servers
- [mcpcentral.io/submit-server](https://mcpcentral.io/submit-server) — MCPCentral

### IDE Integration
- [VS Code MCP Developer Guide](https://code.visualstudio.com/api/extension-guides/mcp)
- [VS Code MCP configuration](https://code.visualstudio.com/docs/copilot/reference/mcp-configuration)
- [Windsurf MCP docs](https://docs.codeium.com/windsurf/mcp)

### Related Notes
- [vscode-marketplace-investigation.md](vscode-marketplace-investigation.md)
- [cursor-mcp-list-investigation.md](cursor-mcp-list-investigation.md)

### Tools
- [mcp-publisher CLI](https://github.com/modelcontextprotocol/registry) — Official registry publisher
- [publish-mcp-server](https://pypi.org/project/publish-mcp-server/) — Python helper for registry publishing
- [mcp-index CLI](https://mcp.so/server/mcp-index) — mcp.so submission tool
