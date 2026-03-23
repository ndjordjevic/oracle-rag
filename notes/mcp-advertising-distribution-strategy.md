# PinRAG MCP: Advertising & Distribution Strategy

**Date:** March 2026  
**Status:** Investigation complete  
**Related:** [implementation-checklist.md](implementation-checklist.md) line 299, [vscode-marketplace-investigation.md](vscode-marketplace-investigation.md), [cursor-mcp-list-investigation.md](cursor-mcp-list-investigation.md), plugin repo [ndjordjevic/pinrag-plugin](https://github.com/ndjordjevic/pinrag-plugin)

---

## Executive Summary

Two complementary tracks:

1. **Distribution** — Get PinRAG listed in directories, marketplaces, and IDE galleries so people can *find and install* it.
2. **Advertising** — Drive awareness so people actually *visit* those listings, star the repo, and try PinRAG.

Neither works alone. Listings without promotion = buried among 17,000+ servers. Promotion without listings = nowhere for interested users to land with a one-click install.

**Two-tier distribution:** (1) **MCP-only** — PyPI package `pinrag` / `pinrag-mcp`; works in every MCP client. (2) **Plugin bundle** — separate repo [pinrag-plugin](https://github.com/ndjordjevic/pinrag-plugin) with `.cursor-plugin/`, `.claude-plugin/`, `.mcp.json`, and `skills/use-pinrag/` for editors that support Open Plugins / Agent Skills (Cursor, Claude Code, VS Code Copilot, Amp) plus a Goose-ready subtree under `pinrag/`. See §1.1 and §2.0.

---

## 1. Distribution: Where to List PinRAG

### 1.1 MCP-only vs plugin bundle (ecosystem)

| Tool | Bundling | How PinRAG fits |
|------|------------|-----------------|
| **Cursor** | Yes — plugin (MCP + skills + rules + hooks) | [pinrag-plugin](https://github.com/ndjordjevic/pinrag-plugin): `.cursor-plugin/`, `.mcp.json`, `skills/use-pinrag/` |
| **Claude Code** | Yes — plugin | Same repo: `.claude-plugin/`, official marketplace submit |
| **VS Code Copilot** | Yes — agent plugins (Preview); accepts Claude-format | Same repo; install from Git URL or marketplace |
| **Amp** | Yes — skill dir with `mcp.json` | `amp skill add ndjordjevic/pinrag-plugin/skills/use-pinrag` |
| **Goose** | Yes — Agent Skills ([block/agent-skills](https://github.com/block/agent-skills)) | `pinrag/SKILL.md` in pinrag-plugin; PR [block/agent-skills#18](https://github.com/block/agent-skills/pull/18) (pending) |
| **OpenCode** | MCP in `opencode.json`; “plugins” are npm JS hooks — not SKILL bundles | **MCP-only:** add server in config; no pinrag-plugin install path |
| **JetBrains + Copilot** | MCP only (registry UI + `mcp.json`) | **MCP-only** |
| **Windsurf** | MCP only (`mcp_config.json` + marketplace) | **MCP-only** |
| **Zed** | MCP via extensions / settings | **MCP-only** |

### Tier 1: High-Impact (Do First)

| # | Channel | Why | Effort | Status |
|---|---------|-----|--------|--------|
| 1 | **Official MCP Registry** (`modelcontextprotocol.io/registry`) | Authoritative source backed by Anthropic, GitHub, Block, Microsoft. Feeds downstream into VS Code, GitHub MCP, Pulse MCP. Supports PyPI packages. | Medium | **Done** — `io.github.ndjordjevic/pinrag` (latest on registry); [`server.json`](../server.json); verify with `jq` below (search returns multiple versions; do not assume `servers[0]` is latest). |
| 2 | **mcp-marketplace.io** | Security-scanned marketplace; picks up registry-backed servers. One-click install. ~2,700+ tools ([browse](https://mcp-marketplace.io/browse)). | Low | **Listed** (Mar 2026) — Medium findings addressed in **v0.9.8** on PyPI (`[project.urls]`, dependency floors, GitHub URL validation); **scanner may lag** until the marketplace pulls the new package metadata (no documented force-rescan). |
| 3 | **Cursor Directory** ([cursor.directory](https://cursor.directory)) | Official Cursor listing (replaces deprecated [cursor/mcp-servers](https://github.com/cursor/mcp-servers)). One-click **Add to Cursor**. | Low | **Submitted** Mar 2026 — pending approval |
| 4 | **mcp.so** | Largest directory (17,000+ servers). Simple web/CLI submission. | Low | Not started |
| 5 | **awesome-mcp-servers** GitHub PR | 83.7k stars. Enormous organic visibility. | Low | Not started |
| 6 | **VS Code one-click install URL** in README | Zero friction for VS Code users. Works today. | Very Low | **Done** — README Quick Start (GitHub Pages → `vscode:` button; see §2.5). |
| 7 | **Cursor one-click install URL** in README | Zero friction for Cursor users. Works today. | Very Low | **Done** — README Quick Start (`cursor.com/en/install-mcp` + base64 config). |

### Tier 2: Broader Reach (Do Next)

| # | Channel | Why | Effort | Status |
|---|---------|-----|--------|--------|
| 8 | **cursor.store** | Curated Cursor marketplace. Free listing. | Low | Not started |
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

Highest-leverage listing; downstream tools (VS Code, GitHub MCP, etc.) consume it.

**Status:** **Done** (March 2026) — Server id **`io.github.ndjordjevic/pinrag`**. Editable source: [`server.json`](../server.json).

**Requirements:** GitHub namespace `io.github.ndjordjevic`; package on PyPI; README includes `<!-- mcp-name: io.github.ndjordjevic/pinrag -->` so PyPI’s long description passes [ownership verification](https://modelcontextprotocol.io/registry/package-types).

**Per release:** Match `X.Y.Z` in `pyproject.toml` and `server.json` (top-level `version` and `packages[0].version`). Top-level `description` ≤ **100** characters or `mcp-publisher publish` returns **422**. Create a **GitHub Release** — [`.github/workflows/publish.yml`](../.github/workflows/publish.yml) publishes to PyPI then runs `mcp-publisher` via OIDC ([registry GitHub Actions](https://modelcontextprotocol.io/registry/github-actions)); manual fallback is `mcp-publisher login github` + `publish` from the repo root. Install CLI and full checklist: [pinrag-release SKILL](../.cursor/skills/pinrag-release/SKILL.md).

**Verify latest** (search returns multiple rows; do not trust `servers[0]` alone):

```bash
curl -fsS "https://registry.modelcontextprotocol.io/v0.1/servers?search=io.github.ndjordjevic/pinrag" | jq -r '.servers[] | select(._meta["io.modelcontextprotocol.registry/official"].isLatest == true) | .server.version'
```

Registry is [preview](https://modelcontextprotocol.io/registry/about); published metadata for a version is effectively immutable. Optional: `pip install publish-mcp-server` for a Python-oriented publish helper. Docs: [quickstart](https://modelcontextprotocol.io/registry/quickstart), [authentication](https://modelcontextprotocol.io/registry/authentication).

### 2.0 Plugin bundle ([pinrag-plugin](https://github.com/ndjordjevic/pinrag-plugin))

Separate from the Python package: a **Git repo** that bundles the same **`uvx --from pinrag pinrag-mcp`** MCP config with a **`use-pinrag`** skill (and a Goose-formatted copy under `pinrag/`). Keeps PyPI/build concerns out of the main [pinrag](https://github.com/ndjordjevic/pinrag) repo.

**Done (Mar 2026):** Repo published — [github.com/ndjordjevic/pinrag-plugin](https://github.com/ndjordjevic/pinrag-plugin). Goose marketplace PR opened — [block/agent-skills#18](https://github.com/block/agent-skills/pull/18) (awaiting maintainer merge / CI).

**Still to do (marketplaces):**

| Channel | Action |
|---------|--------|
| **Cursor Marketplace** (curated) | [cursor.com/marketplace/publish](https://cursor.com/marketplace/publish) |
| **Claude Code official** | [claude.ai/settings/plugins/submit](https://claude.ai/settings/plugins/submit) or [platform.claude.com/plugins/submit](https://platform.claude.com/plugins/submit) |
| **VS Code Copilot** | PR to [awesome-copilot](https://github.com/github/awesome-copilot) and/or install-via-Git; see [Agent plugins](https://code.visualstudio.com/docs/copilot/customization/agent-plugins) |
| **Cursor Directory** | Re-submit or edit listing to point at pinrag-plugin so **Auto (GitHub)** can scan `.cursor-plugin/` + `.mcp.json` |

### 2.2 Cursor Directory (official Cursor listing)

The GitHub repo [cursor/mcp-servers](https://github.com/cursor/mcp-servers) is **deprecated**; its README points to **[cursor.directory](https://cursor.directory)**. New listings use the **Open Plugins**–style flow at **[Submit a Plugin](https://cursor.directory/plugins/new)** (Manual if the repo has no `mcp.json` / rules / skills at root for Auto scan).

See full details in [cursor-mcp-list-investigation.md](cursor-mcp-list-investigation.md).

**Steps:**
1. Use square SVG icon — [`docs/pinrag-icon.svg`](../docs/pinrag-icon.svg).
2. Submit via Manual: name, description, repo URL, homepage (e.g. PyPI), keywords; add **Component → MCP Server** and paste install config (below).
3. Config JSON (uvx) — same as README / one-click install; users add API keys in `mcp.json` after install:
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
   Or full `.mcp.json` wrapper for **Content** if the form expects it: `{ "mcpServers": { "pinrag": { ... } } }`.

**Status (PinRAG):** Submitted to Cursor Directory (pending approval as of Mar 2026).

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
https://cursor.com/en/install-mcp?name=pinrag&config=eyJjb21tYW5kIjoidXZ4IiwiYXJncyI6WyItLWZyb20iLCJwaW5yYWciLCJwaW5yYWctbWNwIl0sImVudiI6eyJPUEVOQUlfQVBJX0tFWSI6IiIsIlBJTlJBR19QRVJTSVNUX0RJUiI6IiJ9fQ
```
Decodes to `{"command":"uvx","args":["--from","pinrag","pinrag-mcp"],"env":{"OPENAI_API_KEY":"","PINRAG_PERSIST_DIR":""}}`.

**VS Code:** GitHub’s README renderer does **not** make `vscode:` URLs clickable (custom schemes are stripped). The README therefore links to an **HTTPS landing page** that contains the real `vscode:` button: [`docs/vscode-mcp-install.html`](../docs/vscode-mcp-install.html), served via **GitHub Pages** at `https://ndjordjevic.github.io/pinrag/vscode-mcp-install.html` (Pages enabled on `main:/docs`).

Raw `vscode:` URL (for local README preview or manual paste):
```
vscode:mcp/install?%7B%22name%22%3A%22pinrag%22%2C%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22--from%22%2C%22pinrag%22%2C%22pinrag-mcp%22%5D%2C%22env%22%3A%7B%22OPENAI_API_KEY%22%3A%22%22%2C%22PINRAG_PERSIST_DIR%22%3A%22%22%7D%7D
```
Decodes to `{"name":"pinrag","command":"uvx","args":["--from","pinrag","pinrag-mcp"],"env":{"OPENAI_API_KEY":"","PINRAG_PERSIST_DIR":""}}`.

Add Cursor link + VS Code HTTPS landing page in the README Quick Start section. One-click installs pre-fill `OPENAI_API_KEY` and optional `PINRAG_PERSIST_DIR` (empty strings); users paste their OpenAI key.

### 2.6 cursor.store

See [cursor-mcp-list-investigation.md §2](cursor-mcp-list-investigation.md).

Submit at [cursor.store/mcp/new](https://www.cursor.store/mcp/new). Free listing. Category: AI / ML Helpers or Developer Tools. Permission: medium.

### 2.7 mcp-marketplace.io

Submit at [mcp-marketplace.io/submit](https://mcp-marketplace.io/submit) (GitHub sign-in). Category: Developer Tools or Data & Analytics. Pricing: Free. Optional: add `LAUNCHGUIDE.md` to the repo for auto-fill ([creator docs](https://mcp-marketplace.io/docs)).

**PinRAG (Mar 2026):** Listed; automated scan reads **`pyproject.toml`** from the published PyPI sdist. **v0.9.8** bumps patched dependencies (e.g. `pypdf`, `requests`, `yt-dlp`), adds **`[project.urls]`** (`Homepage` / `Repository` → GitHub) for package verification, and documents **`GITHUB_TOKEN`** tradeoffs in the README. After publishing, the dashboard may still show older findings until the marketplace re-evaluates the new version—there is no documented “rescan” button; a new PyPI release + time, or asking [support](https://mcp-marketplace.io/faq) / [Discord](https://discord.gg/8uWz69aQH), is the practical path.

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
- [x] Create square SVG icon for PinRAG — [`docs/pinrag-icon.svg`](../docs/pinrag-icon.svg) (128×128 viewBox; document + pin). Use for Cursor Directory / store submissions.

### Phase 2: Tier 1 Listings (half day)

- [x] Submit to **Official MCP Registry** — README `mcp-name` comment, [`server.json`](../server.json), PyPI release then `mcp-publisher publish` (`io.github.ndjordjevic/pinrag`; `description` ≤ 100 chars)
- [x] **mcp-marketplace.io** — listed (Mar 2026); confirm Medium / supply-chain items clear after **v0.9.8** is indexed
- [x] Submit to **Cursor Directory** — [cursor.directory/plugins/new](https://cursor.directory/plugins/new) (Manual + MCP Server component; replaces deprecated [cursor/mcp-servers](https://github.com/cursor/mcp-servers)); **pending approval** (Mar 2026)
- [ ] After approval: spot-check one-click install / discoverability from Cursor Directory
- [ ] Submit to **mcp.so** (web form or CLI)
- [ ] Submit PR to **awesome-mcp-servers**

### Phase 2b: Plugin bundle (pinrag-plugin)

- [x] Publish **[pinrag-plugin](https://github.com/ndjordjevic/pinrag-plugin)** — MCP + `skills/use-pinrag/` + Goose subtree `pinrag/`
- [x] Open **[block/agent-skills](https://github.com/block/agent-skills) PR** — [PR #18](https://github.com/block/agent-skills/pull/18) (Goose Skills Marketplace; pending review)
- [ ] Submit to **Cursor Marketplace** (official) — [cursor.com/marketplace/publish](https://cursor.com/marketplace/publish)
- [ ] Submit to **Claude Code** official plugin marketplace — [claude.ai/settings/plugins/submit](https://claude.ai/settings/plugins/submit)
- [ ] **VS Code Copilot** — list or PR against [awesome-copilot](https://github.com/github/awesome-copilot); document **Install plugin from source** URL
- [ ] **Cursor Directory** — update listing to **pinrag-plugin** repo (optional Auto scan) once approved or in parallel

### Phase 3: Tier 2 Listings (1–2 hours)

- [ ] Submit to **cursor.store**
- [ ] Submit to **Windsurf.run** (if submission process exists)
- [ ] Submit to **MCP Market** (mcpmarket.com)
- [ ] Submit to **MCPCentral** (mcpcentral.io)

### Phase 4: Content & Community (ongoing)

**Origin story (reminder — optional for ads later):** PinRAG was conceived as an **MCP RAG** where you **index your own sources**—PDFs, YouTube transcripts, GitHub repo contents, Discord channel exports—so you can **study a topic** by asking questions across those resources in the IDE. We have not decided whether to foreground this narrative in public marketing; revisit when writing posts or demos.

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

8. **Plugin bundle (pinrag-plugin) targets a subset of tools** — Cursor, Claude Code, VS Code Copilot, Amp, Goose; everyone else stays on PyPI MCP-only. One SKILL.md can serve Goose (block/agent-skills) and the plugin skill with small frontmatter differences.

---

## 6. References

### Official MCP Registry
- [Registry overview](https://modelcontextprotocol.io/registry/about)
- [Quickstart](https://modelcontextprotocol.io/registry/quickstart)
- [Package types (PyPI support)](https://modelcontextprotocol.io/registry/package-types)
- [Authentication](https://modelcontextprotocol.io/registry/authentication)
- [GitHub Actions automation](https://modelcontextprotocol.io/registry/github-actions)
- [FAQ](https://modelcontextprotocol.io/registry/faq)

### Plugin bundle & skills
- [ndjordjevic/pinrag-plugin](https://github.com/ndjordjevic/pinrag-plugin) — MCP + skill bundle for Cursor, Claude Code, VS Code Copilot, Amp
- [block/agent-skills#18](https://github.com/block/agent-skills/pull/18) — Goose Agent Skills PR (pending)
- [Cursor Marketplace — publish](https://cursor.com/marketplace/publish)
- [Claude Code — submit plugin](https://claude.ai/settings/plugins/submit)
- [VS Code — Agent plugins](https://code.visualstudio.com/docs/copilot/customization/agent-plugins)
- [github/awesome-copilot](https://github.com/github/awesome-copilot) — Copilot plugin marketplace repos

### Directories & Marketplaces
- [mcp.so/submit](https://mcp.so/submit) — Largest directory (17,000+ servers)
- [awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers) — 83.7k stars
- [cursor/mcp-servers](https://github.com/cursor/mcp-servers) — Deprecated; use [Cursor Directory](https://cursor.directory) instead
- [cursor.store/mcp/new](https://www.cursor.store/mcp/new) — Cursor marketplace
- [mcp-marketplace.io/submit](https://mcp-marketplace.io/submit) — Security-scanned marketplace ([docs](https://mcp-marketplace.io/docs), [FAQ](https://mcp-marketplace.io/faq))
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
