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

**Two-tier distribution:** (1) **MCP-only** — PyPI package `pinrag` / `pinrag-mcp`; works in every MCP client. (2) **Plugin bundle** — separate repo [pinrag-plugin](https://github.com/ndjordjevic/pinrag-plugin) with `.cursor-plugin/`, `.claude-plugin/`, `.mcp.json`, and `skills/use-pinrag/` for editors that support Open Plugins / Agent Skills (Cursor, Claude Code, VS Code Copilot, Amp) plus a Goose-ready subtree under `pinrag/`. See §1 and §2.

**Third-party directories:** [mcp.so](https://mcp.so) and [MCPRepository](https://mcprepository.com) are **different products**. The web form on mcp.so does not submit to MCPRepository, and `npx mcp-index` (MCPRepository’s CLI) does not submit to mcp.so — track and spot-check each separately (§1.1 row 10–11, §2).

---

## 1. Distribution Channels

PinRAG reaches users through two mechanisms:

1. **MCP-only** — the PyPI package (`pinrag`) added to any MCP client's config via `uvx --from pinrag pinrag-mcp`. Works in every MCP client.
2. **Plugin bundle** — the [pinrag-plugin](https://github.com/ndjordjevic/pinrag-plugin) repo ships `.cursor-plugin/`, `.claude-plugin/`, `.mcp.json`, and `skills/use-pinrag/` for editors supporting Open Plugins / Agent Skills (Cursor, Claude Code, VS Code Copilot, Amp, Goose).

### 1.1 Status Overview

| # | Channel | Type | Status | Effort |
|---|---------|------|--------|--------|
| 1 | Official MCP Registry | MCP | **Done** | Medium |
| 2 | mcp-marketplace.io | MCP | **Done** | Low |
| 3 | cursor.store | MCP | **Done** | Low |
| 4 | Cursor Directory | MCP | **Done** | Low |
| 5 | One-click install — Cursor (README) | MCP | **Done** | Very Low |
| 6 | One-click install — VS Code (README) | MCP | **Done** | Very Low |
| 7 | Manual install (README) | MCP | **Done** | — |
| 8 | Plugin bundle (pinrag-plugin) | Plugin | **Done** (repo published) | Medium |
| 9 | Goose Agent Skills PR | Plugin | **PR pending** ([#18](https://github.com/block/agent-skills/pull/18)) | Low |
| 10 | [mcp.so](https://mcp.so) | MCP | **Submitted** ([web form](https://mcp.so/submit); pending listing) | Low |
| 11 | [MCPRepository](https://mcprepository.com) | MCP | **Listed** ([PinRAG](https://mcprepository.com/ndjordjevic/pinrag); [`mcp-index` CLI](https://github.com/mcprepository/mcp-index)) | Low |
| 12 | awesome-mcp-servers PR | Visibility | **PR open** — [PR #3834](https://github.com/punkpeye/awesome-mcp-servers/pull/3834) (pending merge) | Low |
| 13 | Windsurf.run | MCP | Not started | Low |
| 14 | MCP Market (mcpmarket.com) | MCP | Not started | Low |
| 15 | MCPCentral (mcpcentral.io) | MCP | Not started | Low |
| 16 | Cursor Marketplace (official plugin) | Plugin | Not started | Low |
| 17 | Claude Code marketplace | Plugin | Not started | Low |
| 18 | VS Code Copilot marketplace | Plugin | Not started | Low |
| 19 | VS Code Extension (marketplace) | Extension | Not started | 1–2 days |
| 20 | Smithery (smithery.ai) | Hosted | **Blocked** — needs HTTP transport | High |
| 21 | Glama (glama.ai) | MCP | **Done** — [PinRAG on Glama](https://glama.ai/mcp/servers/ndjordjevic/pinrag); [`glama.json`](../glama.json) in repo | Medium |
| 22 | [cursormcp.dev](https://cursormcp.dev/) | Directory | **Unknown** — no public “add server” / submit UI; unclear how PinRAG could be listed | — |
| 23 | .well-known/mcp.json | Auto-discovery | Future — needs PinRAG Cloud | Low |

### 1.2 Tool → Channel Matrix

**Bold** = live today.

| Tool | Live channels | Planned channels |
|------|--------------|-----------------|
| **Cursor** | **MCP Registry**, **mcp-marketplace.io**, **cursor.store**, **Cursor Directory**, **mcp.so** (submitted), **MCPRepository** (listed), **Glama**, **one-click README**, **manual config**, **pinrag-plugin** | awesome-mcp-servers ([PR #3834](https://github.com/punkpeye/awesome-mcp-servers/pull/3834) pending), Cursor Marketplace (plugin), [cursormcp.dev](https://cursormcp.dev/) (no submit path known) |
| **VS Code Copilot** | **MCP Registry**, **mcp-marketplace.io**, **Glama**, **one-click README**, **manual config**, **pinrag-plugin** | mcp.so, VS Code Extension, VS Code Copilot marketplace |
| **Claude Code** | **MCP Registry**, **Glama**, **manual config**, **pinrag-plugin** | Claude Code marketplace, mcp.so |
| **JetBrains + Copilot** | **MCP Registry**, **Glama**, **manual config** | mcp.so |
| **Windsurf** | **MCP Registry**, **Glama**, **manual config** | Windsurf.run, mcp.so |
| **Zed** | **MCP Registry**, **Glama**, **manual config** | mcp.so |
| **OpenCode** | **MCP Registry**, **Glama**, **manual config** | mcp.so |
| **Amp** | **manual config**, **pinrag-plugin** | — |
| **Goose** | **pinrag-plugin** (local clone) | Goose Agent Skills (PR [#18](https://github.com/block/agent-skills/pull/18) pending) |

---

## 2. Channel Details

### Live

#### Official MCP Registry

**URL:** [modelcontextprotocol.io/registry](https://modelcontextprotocol.io/registry) | **Server id:** `io.github.ndjordjevic/pinrag` | **Source:** [`server.json`](../server.json)

Authoritative source backed by Anthropic, GitHub, Block, Microsoft. Feeds downstream into VS Code, GitHub MCP, Pulse MCP. Highest-leverage listing.

**Requirements:** GitHub namespace `io.github.ndjordjevic`; package on PyPI; README includes `<!-- mcp-name: io.github.ndjordjevic/pinrag -->` for [ownership verification](https://modelcontextprotocol.io/registry/package-types).

**Per release:** Match `X.Y.Z` in `pyproject.toml` and `server.json`. Top-level `description` ≤ **100** characters or `mcp-publisher publish` returns **422**. Create a **GitHub Release** — [`.github/workflows/publish.yml`](../.github/workflows/publish.yml) publishes to PyPI then runs `mcp-publisher` via OIDC ([GitHub Actions](https://modelcontextprotocol.io/registry/github-actions)); manual fallback: `mcp-publisher login github` + `publish`. Full checklist: [pinrag-release SKILL](../.cursor/skills/pinrag-release/SKILL.md).

**Verify latest:**

```bash
curl -fsS "https://registry.modelcontextprotocol.io/v0.1/servers?search=io.github.ndjordjevic/pinrag" | jq -r '.servers[] | select(._meta["io.modelcontextprotocol.registry/official"].isLatest == true) | .server.version'
```

Registry is [preview](https://modelcontextprotocol.io/registry/about); published metadata per version is immutable. Docs: [quickstart](https://modelcontextprotocol.io/registry/quickstart), [authentication](https://modelcontextprotocol.io/registry/authentication).

#### mcp-marketplace.io

**URL:** [mcp-marketplace.io](https://mcp-marketplace.io) — [browse](https://mcp-marketplace.io/browse)

Security-scanned marketplace (~2,700+ tools). One-click install. Listed Mar 2026. Automated scan reads `pyproject.toml` from PyPI sdist. **v0.9.8** addressed Medium findings (**[project.urls]**, dependency floors, GitHub URL validation). Scanner may lag until new metadata is pulled — no documented "rescan"; new PyPI release + time or asking [support](https://mcp-marketplace.io/faq) / [Discord](https://discord.gg/8uWz69aQH) is the practical path.

Submit at [mcp-marketplace.io/submit](https://mcp-marketplace.io/submit) (GitHub sign-in). Optional: `LAUNCHGUIDE.md` for auto-fill ([creator docs](https://mcp-marketplace.io/docs)).

#### cursor.store

**URL:** [cursor.store/mcp/ndjordjevic/pinrag](https://www.cursor.store/mcp/ndjordjevic/pinrag)

Curated Cursor marketplace. Listed Mar 2026. New submissions: [cursor.store/mcp/new](https://www.cursor.store/mcp/new). See [cursor-mcp-list-investigation.md §2](cursor-mcp-list-investigation.md).

#### Cursor Directory

**URL:** [cursor.directory](https://cursor.directory)

Official Cursor listing (replaces deprecated [cursor/mcp-servers](https://github.com/cursor/mcp-servers)). One-click **Add to Cursor**. Submitted Mar 2026 — **approved** (listed). See [cursor-mcp-list-investigation.md](cursor-mcp-list-investigation.md).

**Steps:**
1. Use square SVG icon — [`docs/pinrag-icon.svg`](../docs/pinrag-icon.svg).
2. Submit via Manual: name, description, repo URL, homepage, keywords; add **Component → MCP Server** with config:

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

#### mcp.so

**URL:** [mcp.so](https://mcp.so) — submit at [mcp.so/submit](https://mcp.so/submit)

Large public directory (~17,000+ servers). MIT license required (✓). **Submitted Mar 2026** via manual web form (name **PinRAG**, repo `https://github.com/ndjordjevic/pinrag`, server config with `uvx` / `pinrag-mcp` per README). Pending listing on mcp.so — spot-check when live.

#### MCPRepository (mcprepository.com)

**URL:** [mcprepository.com](https://mcprepository.com) — CLI: [`mcprepository/mcp-index`](https://github.com/mcprepository/mcp-index)

Independent of mcp.so (separate site and index; submitting to one does not list you on the other). Submit a GitHub repo with:

```bash
npx mcp-index https://github.com/ndjordjevic/pinrag
```

This calls MCPRepository’s index API (`POST https://mcprepository.com/api/index`). **Listed** Mar 2026 — [PinRAG on MCPRepository](https://mcprepository.com/ndjordjevic/pinrag).

#### One-Click Install URLs (README)

The PyPI package exposes **`pinrag-mcp`** (not `pinrag`), so the correct invocation is **`uvx --from pinrag pinrag-mcp`**.

**Cursor:**
```
https://cursor.com/en/install-mcp?name=pinrag&config=eyJjb21tYW5kIjoidXZ4IiwiYXJncyI6WyItLWZyb20iLCJwaW5yYWciLCJwaW5yYWctbWNwIl0sImVudiI6eyJPUEVOQUlfQVBJX0tFWSI6IiIsIlBJTlJBR19QRVJTSVNUX0RJUiI6IiJ9fQ
```
Decodes to `{"command":"uvx","args":["--from","pinrag","pinrag-mcp"],"env":{"OPENAI_API_KEY":"","PINRAG_PERSIST_DIR":""}}`.

**VS Code:** GitHub strips custom URL schemes, so the README links to an HTTPS landing page with the `vscode:` button: [`docs/vscode-mcp-install.html`](../docs/vscode-mcp-install.html), served via GitHub Pages at `https://ndjordjevic.github.io/pinrag/vscode-mcp-install.html`.

Raw `vscode:` URL (for local preview / manual paste):
```
vscode:mcp/install?%7B%22name%22%3A%22pinrag%22%2C%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22--from%22%2C%22pinrag%22%2C%22pinrag-mcp%22%5D%2C%22env%22%3A%7B%22OPENAI_API_KEY%22%3A%22%22%2C%22PINRAG_PERSIST_DIR%22%3A%22%22%7D%7D
```

One-click installs pre-fill `OPENAI_API_KEY` and optional `PINRAG_PERSIST_DIR` (empty strings); users paste their key.

#### Manual Install (README)

Users add PinRAG to their MCP client config manually — works in every MCP client (Cursor, VS Code, Claude Code, JetBrains, Windsurf, Zed, OpenCode, Amp). The README Quick Start documents the config for each.

#### Plugin Bundle ([pinrag-plugin](https://github.com/ndjordjevic/pinrag-plugin))

Separate from the PyPI package: a Git repo bundling the same **`uvx --from pinrag pinrag-mcp`** MCP config with a **`use-pinrag`** skill (and a Goose-formatted copy under `pinrag/`). Keeps build concerns out of the main [pinrag](https://github.com/ndjordjevic/pinrag) repo. Published Mar 2026.

| Tool | Install method |
|------|---------------|
| **Cursor** | Cursor Directory Auto-scan or manual `.cursor-plugin/` |
| **Claude Code** | `claude --plugin-dir ./pinrag-plugin` |
| **VS Code Copilot** | *Chat: Install Plugin From Source* → repo URL |
| **Amp** | `amp skill add ndjordjevic/pinrag-plugin/skills/use-pinrag` |
| **Goose** | Local clone; marketplace PR [#18](https://github.com/block/agent-skills/pull/18) pending |

### Not Yet Started or In Progress

#### awesome-mcp-servers

[punkpeye/awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers) (~84k stars). **Mechanism unchanged:** fork → branch → edit root [`README.md`](https://github.com/punkpeye/awesome-mcp-servers/blob/main/README.md) → open PR — see upstream [CONTRIBUTING.md](https://github.com/punkpeye/awesome-mcp-servers/blob/main/CONTRIBUTING.md).

**Status (Mar 2026):** [PR #3834](https://github.com/punkpeye/awesome-mcp-servers/pull/3834) is **open** (adds PinRAG under **🧠 Knowledge & Memory** with Glama score badge). **Pending upstream merge** — after merge, spot-check the list on `main` and mark Phase 2 complete in this doc.

One line under **🧠 Knowledge & Memory** (local-first RAG; fits alongside similar entries). **Alphabetical order by `owner/repo`** — `ndjordjevic/pinrag` belongs **after** `n24q02m/mnemo-mcp` and **before** `nicholasglazer/gnosis-mcp`. Use the **[Glama score badge](https://glama.ai/mcp/servers/ndjordjevic/pinrag/badges/score.svg)** with paths **`ndjordjevic/pinrag`** (no `@` prefix — `@` breaks the SVG URL).

```
- [ndjordjevic/pinrag](https://github.com/ndjordjevic/pinrag) [![ndjordjevic/pinrag MCP server](https://glama.ai/mcp/servers/ndjordjevic/pinrag/badges/score.svg)](https://glama.ai/mcp/servers/ndjordjevic/pinrag) 🐍 🏠 - RAG for PDFs, YouTube, GitHub repos, Discord exports; index documents and query with citations.
```

Optional: [CONTRIBUTING.md](https://github.com/punkpeye/awesome-mcp-servers/blob/main/CONTRIBUTING.md) says automated-agent PRs can append `🤖🤖🤖` to the PR title for fast-track merge. Large PR backlog — expect delay.

#### Windsurf.run

[windsurf.run](https://windsurf.run/) — Windsurf/Codeium MCP directory. Check for "Submit" flow. PinRAG config for Windsurf (`~/.codeium/windsurf/mcp_config.json`) uses Claude Desktop schema.

#### MCP Market (mcpmarket.com)

Submit via web form. 21,700+ servers.

#### MCPCentral (mcpcentral.io)

Submit at [mcpcentral.io/submit-server](https://mcpcentral.io/submit-server). Supports `mcp-publisher` CLI.

#### Cursor Marketplace (official plugin)

Submit pinrag-plugin at [cursor.com/marketplace/publish](https://cursor.com/marketplace/publish). Distinct from cursor.store — this is Cursor's curated marketplace for plugins with skills/rules.

#### Claude Code Marketplace

Submit at [claude.ai/settings/plugins/submit](https://claude.ai/settings/plugins/submit) or [platform.claude.com/plugins/submit](https://platform.claude.com/plugins/submit). Lists pinrag-plugin so Claude Code users can discover and install from inside the tool.

#### VS Code Copilot Marketplace

PR to [github/awesome-copilot](https://github.com/github/awesome-copilot) and/or install-via-Git. See [Agent plugins docs](https://code.visualstudio.com/docs/copilot/customization/agent-plugins).

#### VS Code Extension

TypeScript extension spawning `uvx --from pinrag pinrag-mcp`. Registers via `mcpServerDefinitionProviders`. Makes PinRAG discoverable via `@mcp pinrag` in Extensions view. Effort: 1–2 days. See [vscode-marketplace-investigation.md](vscode-marketplace-investigation.md). Do after other listings — one-click URL + MCP Registry cover most of the value.

#### Smithery (smithery.ai)

2,880+ servers. Hosted gateway. **Blocked:** requires Streamable HTTP transport (PinRAG is stdio-only). Only viable with PinRAG Cloud or adding HTTP transport.

#### Glama (glama.ai)

9,000–19,000+ servers. Directory, scoring, and optional hosted deploy. **Listed Mar 2026** — [PinRAG on Glama](https://glama.ai/mcp/servers/ndjordjevic/pinrag); [score page](https://glama.ai/mcp/servers/ndjordjevic/pinrag/score). Root [`glama.json`](../glama.json) lists maintainers for ownership verification; [`Dockerfile`](../Dockerfile) supports Glama’s build checks. README badge: `badges/score.svg` (compact) or `badges/card.svg` (detailed) — use paths **`/mcp/servers/ndjordjevic/pinrag/...`** (not `@ndjordjevic/...`).

#### CursorMCP.dev ([cursormcp.dev](https://cursormcp.dev/))

Third-party **hand-picked** Cursor MCP directory (featured servers, categories such as Knowledge & Memory, browse/search). **No “add server,” submit form, or documented inclusion process** on the site (checked Mar 2026). **Unknown** how PinRAG could end up there (e.g. editorial curation, scraping registries, or partnerships). Treat as **out of band** until the operator publishes criteria or a submission channel.

#### .well-known/mcp.json

Emerging standard (SEP-1960) for automated server discovery. AI clients (Claude, ChatGPT, Cursor) auto-detect MCP servers at `/.well-known/mcp.json`. Only relevant when PinRAG has a web endpoint (PinRAG Cloud).

---

## 3. Advertising

### 3.1 Repository Optimization

| Action | Status | Details |
|--------|--------|---------|
| One-click install badges (Cursor + VS Code) | **Done** | Top of README Quick Start |
| PyPI badge | **Done** | Already present |
| GitHub Topics | **Done** | `mcp`, `mcp-server`, `rag`, `pdf`, `langchain`, `model-context-protocol`, `chromadb`, `cursor`, `discord`, `github-repos`, `pypi`, `python`, `vscode`, `youtube` |
| Demo GIF / screenshot | Not started | Show: install → index PDF → query → answer with citations |
| Stars / social proof | Ongoing | Encourage early users to star |

### 3.2 Content Marketing

| Channel | Format | Topic Ideas | Status |
|---------|--------|-------------|--------|
| Dev.to / Hashnode | Blog post | "How I Built a RAG MCP Server in Python", "Give Your AI Assistant a Memory for Documents" | Not started |
| YouTube | Demo video (2–3 min) | Install PinRAG → index a PDF → query from Cursor — full flow | Not started |
| Medium | Tutorial | "Index Your PDFs, YouTube Videos, and GitHub Repos for AI Coding Assistants" | Not started |

### 3.3 Community Engagement

| Community | Approach | Status |
|-----------|----------|--------|
| **Reddit** — r/MCP, r/LocalLLaMA, r/langchain, r/cursor | Share PinRAG, explain the use case, answer questions | Not started |
| **Hacker News** — Show HN | "Show HN: PinRAG — MCP server that lets AI assistants query your PDFs, YouTube, GitHub repos" | Not started |
| **Twitter/X** | Post + demo GIF; tag @AnthropicAI, @cursor_ai, @LangChainAI | Not started |
| **LangChain Discord** | Community showcase / show-and-tell | Not started |
| **MCP-focused Discord servers** | Share and discuss | Not started |

### 3.4 Ecosystem Partnerships

| Partner | How | Status |
|---------|-----|--------|
| **LangChain** | Submit to integrations page or community gallery | Not started |
| **Cursor** | Write a "How to use PinRAG with Cursor" blog post or tutorial | Not started |
| **VS Code** | If extension is published, it shows in Extensions view | Blocked (extension not built) |

### 3.5 Origin Story (optional for future marketing)

PinRAG was conceived as an **MCP RAG** where you **index your own sources** — PDFs, YouTube transcripts, GitHub repo contents, Discord channel exports — so you can **study a topic** by asking questions across those resources in the IDE. We have not decided whether to foreground this narrative in public marketing; revisit when writing posts or demos.

---

## 4. Execution Checklist

### Phase 1: Foundation — done

- [x] One-click install URLs in README (Cursor + VS Code)
- [x] GitHub Topics set
- [x] SVG icon — [`docs/pinrag-icon.svg`](../docs/pinrag-icon.svg)

### Phase 2: Primary Listings — in progress

- [x] **Official MCP Registry** — `io.github.ndjordjevic/pinrag`; [`server.json`](../server.json)
- [x] **mcp-marketplace.io** — listed (Mar 2026)
- [x] **Cursor Directory** — submitted Mar 2026 via [cursor.directory](https://cursor.directory); **approved** (listed)
- [ ] **mcp.so** — submitted (Mar 2026) via [web form](https://mcp.so/submit); pending listing / approval
- [x] **MCPRepository** — [listed](https://mcprepository.com/ndjordjevic/pinrag) (Mar 2026); submitted via [`npx mcp-index`](https://github.com/mcprepository/mcp-index)
- [x] **Glama** — [listed](https://glama.ai/mcp/servers/ndjordjevic/pinrag) (Mar 2026); [`glama.json`](../glama.json) + [`Dockerfile`](../Dockerfile) in repo
- [ ] **awesome-mcp-servers** — [PR #3834](https://github.com/punkpeye/awesome-mcp-servers/pull/3834) **open** (pending merge); after merge, confirm line on `main` and check this off

### Phase 3: Plugin Bundle — in progress

- [x] **[pinrag-plugin](https://github.com/ndjordjevic/pinrag-plugin)** published
- [ ] **Goose Agent Skills** — [PR #18](https://github.com/block/agent-skills/pull/18) (pending review)
- [ ] **Cursor Marketplace** (official plugin) — [cursor.com/marketplace/publish](https://cursor.com/marketplace/publish)
- [ ] **Claude Code marketplace** — [claude.ai/settings/plugins/submit](https://claude.ai/settings/plugins/submit)
- [ ] **VS Code Copilot** — PR to [awesome-copilot](https://github.com/github/awesome-copilot); document "Install plugin from source" URL
- [ ] **Cursor Directory** — update listing to point at pinrag-plugin (Auto scan)

### Phase 4: Remaining Directories — not started

- [x] **cursor.store** — [listed](https://www.cursor.store/mcp/ndjordjevic/pinrag) (Mar 2026)
- [ ] **Windsurf.run** — check for submission process
- [ ] **MCP Market** (mcpmarket.com) — submit via web form
- [ ] **MCPCentral** (mcpcentral.io) — submit at [mcpcentral.io/submit-server](https://mcpcentral.io/submit-server)

### Phase 5: Content & Community — not started

- [ ] Create demo GIF/video for README
- [ ] Write first blog post (Dev.to or Hashnode)
- [ ] Post on Reddit (r/MCP, r/langchain)
- [ ] Post on Twitter/X
- [ ] Consider Hacker News Show HN

### Phase 6: Higher Effort — future

- [ ] Build VS Code Extension (TypeScript wrapper)
- [ ] Explore Smithery listing (requires HTTP transport — PinRAG Cloud)
- [ ] Implement `.well-known/mcp.json` (PinRAG Cloud)

---

## 5. Key Takeaways

1. **MCP Registry is the highest-leverage listing.** It cascades into VS Code, GitHub MCP, and potentially Cursor. PinRAG already qualifies via PyPI.
2. **One-click install URLs are the lowest-effort, highest-conversion asset.** Both Cursor and VS Code are live.
3. **Content marketing outweighs directory count.** A single Hacker News Show HN or popular Reddit thread drives more installs than 10 marketplace listings combined.
4. **A demo video/GIF is the highest-ROI content piece.** Reusable across README, blog posts, social media, and every marketplace listing.
5. **Plugin bundle targets a subset of tools.** Cursor, Claude Code, VS Code Copilot, Amp, and Goose; everyone else uses PyPI MCP-only.
6. **Smithery is blocked on HTTP transport.** PinRAG is stdio-only; Smithery listing requires PinRAG Cloud or an added HTTP layer.
7. **awesome-mcp-servers has a massive PR backlog** — [PR #3834](https://github.com/punkpeye/awesome-mcp-servers/pull/3834) for PinRAG is open (Mar 2026); expect a wait for merge.
8. **VS Code Extension is nice-to-have, not urgent.** One-click URL + MCP Registry cover most of the discoverability value.
9. **mcp.so ≠ MCPRepository.** Two separate directories and submission paths; completing one does not list you on the other. `npx mcp-index` only targets MCPRepository.

---

## 6. References

### Official MCP Registry

- [Registry overview](https://modelcontextprotocol.io/registry/about)
- [Quickstart](https://modelcontextprotocol.io/registry/quickstart)
- [Package types (PyPI)](https://modelcontextprotocol.io/registry/package-types)
- [Authentication](https://modelcontextprotocol.io/registry/authentication)
- [GitHub Actions](https://modelcontextprotocol.io/registry/github-actions)
- [FAQ](https://modelcontextprotocol.io/registry/faq)

### Plugin Bundle & Skills

- [ndjordjevic/pinrag-plugin](https://github.com/ndjordjevic/pinrag-plugin) — MCP + skill bundle (Cursor, Claude Code, VS Code Copilot, Amp)
- [block/agent-skills#18](https://github.com/block/agent-skills/pull/18) — Goose Agent Skills PR (pending)

### Plugin Submission URLs

- [Cursor Marketplace — publish](https://cursor.com/marketplace/publish)
- [Claude Code — submit plugin](https://claude.ai/settings/plugins/submit)
- [VS Code — Agent plugins](https://code.visualstudio.com/docs/copilot/customization/agent-plugins)
- [github/awesome-copilot](https://github.com/github/awesome-copilot)

### Directories & Marketplaces

- [PinRAG on cursor.store](https://www.cursor.store/mcp/ndjordjevic/pinrag) — live listing
- [cursor.store/mcp/new](https://www.cursor.store/mcp/new) — submit new listings
- [Cursor Directory](https://cursor.directory) — official Cursor listing ([cursor/mcp-servers](https://github.com/cursor/mcp-servers) is deprecated)
- [mcp-marketplace.io/submit](https://mcp-marketplace.io/submit) — security-scanned marketplace ([docs](https://mcp-marketplace.io/docs), [FAQ](https://mcp-marketplace.io/faq))
- [mcp.so/submit](https://mcp.so/submit) — large public directory (~17,000+ servers); independent of MCPRepository
- [MCPRepository](https://mcprepository.com) — [`mcp-index` CLI](https://github.com/mcprepository/mcp-index) (`POST /api/index`); not mcp.so
- [awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers) — 83.7k stars; PinRAG: [PR #3834](https://github.com/punkpeye/awesome-mcp-servers/pull/3834) (open)
- [Glama — PinRAG](https://glama.ai/mcp/servers/ndjordjevic/pinrag) — directory + [score](https://glama.ai/mcp/servers/ndjordjevic/pinrag/score); badge SVGs under `/badges/score.svg` and `/badges/card.svg` (use `ndjordjevic/pinrag`, not `@ndjordjevic/...`)
- [mcpmarket.com](https://mcpmarket.com/) — 21,700+ servers
- [mcpcentral.io/submit-server](https://mcpcentral.io/submit-server)
- [windsurf.run](https://windsurf.run/) — Windsurf/Codeium directory
- [cursormcp.dev](https://cursormcp.dev/) — hand-picked Cursor MCP catalog; no documented submission path (Mar 2026)

### IDE Integration

- [VS Code MCP Developer Guide](https://code.visualstudio.com/api/extension-guides/mcp)
- [VS Code MCP configuration](https://code.visualstudio.com/docs/copilot/reference/mcp-configuration)
- [Windsurf MCP docs](https://docs.codeium.com/windsurf/mcp)

### Related Notes

- [vscode-marketplace-investigation.md](vscode-marketplace-investigation.md)
- [cursor-mcp-list-investigation.md](cursor-mcp-list-investigation.md)

### CLI Tools

- [mcp-publisher](https://github.com/modelcontextprotocol/registry) — official registry publisher
- [publish-mcp-server](https://pypi.org/project/publish-mcp-server/) — Python helper for registry publishing
- [mcp-index](https://github.com/mcprepository/mcp-index) — submits a GitHub repo to [MCPRepository](https://mcprepository.com) (`POST /api/index`); not mcp.so
