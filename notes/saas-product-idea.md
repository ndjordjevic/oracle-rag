# Oracle-RAG Cloud: MCP-Native RAG-as-a-Service

*Product idea — revisit after Phase 4 is complete.*

---

## One-Liner

The RAG backend for AI agents. Upload documents, get MCP tools instantly — no pipelines, no vector DB ops, no infrastructure.

## The Problem

Developers building AI agents (in Cursor, Claude, ChatGPT, custom apps) need their agents to query private documents. Today they either:

1. **Build a full RAG pipeline** — chunking, embeddings, vector DB, retrieval, prompt engineering. Weeks of work, ongoing maintenance.
2. **Use a generic RAG SaaS** (Vectara, Pinecone + orchestration, Ailog) — REST-first APIs that weren't designed for the agent/MCP world. Require glue code to expose as agent tools.
3. **Skip RAG** and stuff documents into context windows — works until it doesn't (cost, token limits, quality).

None of these are optimized for the emerging MCP-native agent ecosystem.

## The Solution

Oracle-RAG Cloud: a hosted service where developers upload PDFs (and later other doc types), and immediately get MCP-compatible tools (`query_pdf`, `add_pdf`, `list_pdfs`, `ask_about_documents`) that any MCP host can call. Also exposed as a REST API for non-MCP clients.

**Developer experience:**
1. Sign up, get an API key.
2. Upload documents via dashboard or API.
3. Point your agent's MCP config at `https://api.oracle-rag.com/mcp/{your-key}`.
4. Your agent can now query your documents. Done.

## Why MCP-Native Is the Differentiator

- MCP is the emerging standard: Anthropic (Nov 2024), OpenAI, Google Cloud (Dec 2025) all support it.
- Developers building agents in Cursor, Claude Desktop, ChatGPT, and custom LangGraph/LangChain apps need MCP-compatible tools.
- **No one owns "MCP-native RAG cloud" for the indie/SMB developer segment.** Contextual AI has an enterprise MCP RAG server, but nothing targets the $29–$99/mo developer market.
- The MCP angle makes oracle-rag a *tool the agent discovers and uses*, not just an API the developer manually integrates.

## Cursor Integration

Cursor supports MCP in two ways: **Marketplace** (one-click install for listed servers, OAuth) and **custom servers** via a JSON config file. Cloud oracle-rag is added as a **custom** server — users do not need a Marketplace listing.

**Config file:** `~/.cursor/mcp.json` (or project-level `mcp.json`). Same file as today; users add a new entry under `mcpServers`.

**Format for remote (cloud) MCP:** Cursor’s docs specify a **Remote Server** shape: `url` (HTTP or SSE endpoint) plus optional `headers` (e.g. API key). No local `command`/`args` — Cursor connects to the cloud URL.

**Example — cloud oracle-rag in `mcp.json`:**

```json
"oracle-rag-cloud": {
  "url": "https://api.oracle-rag.com/mcp",
  "headers": {
    "Authorization": "Bearer YOUR_API_KEY"
  }
}
```

(Exact header name depends on our auth design: `Authorization: Bearer ...`, `X-API-Key`, etc.)

**Summary:** Users add cloud oracle-rag by editing `mcp.json` with the Remote Server entry above. One-click from the Marketplace would require publishing there later; until then, we provide this snippet in docs and the dashboard.

Ref: Cursor Docs → [Model Context Protocol (MCP)](https://cursor.com/docs/mcp) → “Using mcp.json” → Remote Server.

## Target Audience

**Primary:** Solo developers and small teams building AI agents who need document-grounded answers but don't want to manage RAG infrastructure.

**Specific personas:**
- Developer using Cursor with MCP tools, querying project docs / specs / manuals.
- Startup building a customer-facing AI agent that needs to answer from their knowledge base.
- Consultant / freelancer building AI agents for clients, needs a managed doc backend per client.

**Not targeting (initially):** Large enterprises (compliance, SOC2 — leave that to Vectara/Coveo).

## Competitive Landscape

### MCP-Native RAG Competitors (can be added to Cursor/Claude today)

These are the **direct competitors** — cloud RAG services that already expose an MCP server, usable from Cursor, Claude Desktop, etc.

| Player | MCP transport | Pricing | Docs/PDF support | What they do well | Gap vs Oracle-RAG Cloud |
|--------|--------------|---------|-------------------|-------------------|------------------------|
| **Ragie** | Native HTTP streaming (hosted URL per partition) | Free (1k docs) / $100 (Starter) / $500 (Pro) / Enterprise | PDF, Google Drive, Notion, JIRA, audio/video | Hybrid + hierarchical search, reranking, entity extraction, multi-language, partitions for data isolation | Expensive ($100/mo minimum paid); aimed at teams, not solo devs; no $29 tier |
| **CustomGPT.ai** | Hosted SSE (`mcp.customgpt.ai`) | Included with existing plans (no free tier listed) | PDF, Google Drive, Notion, Confluence, web scraping | #1 ranked RAG accuracy (independent benchmark), SOC2, fully managed, zero-infra | Enterprise-oriented; pricing opaque; overkill for a developer who just needs "query my PDFs from Cursor" |
| **R2R / SciPhi** | MCP server (Claude Desktop documented) | Free (300 RAG req/mo, 100 files) / $25/mo (Dev) / Enterprise | 40+ formats incl. PDF, spreadsheets, audio | Vector + graph + web search, knowledge graphs, agentic RAG | Dev tier is cheap ($25) but limited (1k files, 3k RAG/mo); knowledge graph complexity may be overkill for simple doc Q&A |
| **Inkeep** | MCP via OpenAI-compatible API | $600–$750/mo (Growth) / Enterprise | Docs, help centers, knowledge bases, Notion, Confluence | Polished support/docs search; AI reports on content gaps; auto-reply bots | Very expensive; targets support teams, not individual developers; no PDF upload — focused on public docs/help centers |
| **RAGFlow** | Self-hosted MCP (Docker) | Self-hosted only (open source) | PDF (DeepDoc), Office, images | Strong PDF parsing (DeepDoc), hybrid search, open source | No cloud-hosted option — user must run their own server; not a SaaS competitor but a self-host alternative |
| **Contextual AI** | Hosted MCP server | Enterprise | Domain-specific Q&A with citations | Enterprise agentic RAG | Enterprise-only; not indie/SMB market |

### Non-MCP RAG-as-a-Service (REST only)

| Player | Pricing | Gap |
|--------|---------|-----|
| **Vectara** | Enterprise | No MCP, not indie-friendly |
| **Pinecone** | Usage-based | Vector DB only, BYO orchestration, no MCP |
| **Ailog** (France) | Free – €99/mo | REST only, no MCP; closest on pricing |
| **Ragapi.tech** | $7–$464/mo | REST only, no MCP |
| **Nuclia** | Enterprise | Acquired by Progress Software |
| **Coveo** | Enterprise | Not developer/indie market |

### Local/Self-Hosted MCP RAG (not cloud competitors, but alternatives users consider)

| Player | Notes |
|--------|-------|
| **pdf-rag-mcp-server** (GitHub: hyson666) | Open-source, runs locally on `localhost:7800`, semantic search over PDFs. User must self-host. |
| **DocsMCP** | Local docs access from files or URLs. Not a cloud service. |
| **local-rag** (your current MCP) | npx-based, reads local files. No cloud, no vector DB. |
| **pdfrag** (your current MCP) | Local Python MCP, Chroma-backed. No cloud. |

### Indirect Competitors

| Player | Why developers use them instead | Gap |
|--------|-------------------------------|-----|
| **LangChain/LlamaIndex** | DIY RAG with full control | Not hosted — oracle-rag removes the ops burden |
| **Supabase + pgvector** | Database they already use | BYO chunking, embedding, prompt — not turnkey |
| **OpenAI Assistants API** | Built-in file search | Locked to OpenAI models, limited retrieval tuning, no MCP |

### Cursor Marketplace Status

The Cursor Marketplace currently lists ~15 MCP plugins (Slack, Figma, Vercel, Linear, Notion, Stripe, etc.). **No dedicated "RAG / document Q&A" plugin exists in the Marketplace.** RAG MCP servers (Ragie, CustomGPT, R2R) are added via `mcp.json`, not the Marketplace. This means:
- Getting listed in the Cursor Marketplace early (if they open it to more submissions) would be a strong distribution channel.
- Until then, the install path is: copy JSON snippet → paste into `mcp.json`.

### Key Insight (Updated)

MCP-native RAG cloud exists but splits into:
- **Expensive / enterprise:** Ragie ($100+), CustomGPT (opaque), Inkeep ($600+), Contextual AI (enterprise).
- **Cheap but limited:** R2R/SciPhi ($25/mo, 300 free RAG req/mo, small file limits).
- **Self-hosted only:** RAGFlow, pdf-rag-mcp-server.

**The gap:** A simple, developer-friendly, MCP-native RAG cloud at **$29–$79/mo** focused on **PDF document Q&A from Cursor/Claude/agents**. Not a knowledge graph platform. Not an enterprise compliance suite. Just: upload PDFs → get MCP tools → your agent queries them. R2R/SciPhi is the closest on price, but oracle-rag could differentiate on simplicity, PDF focus, and Cursor-first DX.

## Pricing Model (Draft)

| Tier | Price | Includes |
|------|-------|----------|
| **Free** | $0/mo | 5 documents, 100 queries/mo, 1 MCP endpoint |
| **Developer** | $29/mo | 100 documents, 5,000 queries/mo, 3 MCP endpoints, REST API |
| **Pro** | $79/mo | 1,000 documents, 50,000 queries/mo, unlimited endpoints, priority support |
| **Team** | $199/mo | 10,000 documents, 200,000 queries/mo, team access, custom models |

**Cost structure to watch:** LLM API calls (embedding + generation) dominate costs. At $29/mo with 5,000 queries, need to keep per-query cost under $0.005. Strategies: use smaller embedding models, cache frequent queries, batch embeddings, use cheaper LLMs for generation (or let the user bring their own LLM key).

## Unit Economics (Rough)

Per query cost breakdown (estimates):
- Embedding the query: ~$0.0001 (text-embedding-3-small)
- Vector search: ~$0.0001 (managed DB cost amortized)
- LLM generation (if included): ~$0.002–$0.01 (depends on model)
- **Total per query: ~$0.003–$0.01**

At $29/mo with 5,000 queries: revenue $29, cost ~$15–$50. **Margin is tight if generation is included.** Options:
1. **BYOK (Bring Your Own Key):** User provides their LLM API key — oracle-rag handles only retrieval. Dramatically improves margins.
2. **Retrieval-only tier:** Return ranked chunks + metadata, let the user's agent handle generation. Most MCP/agent use cases work this way naturally.
3. **Generation included at higher tiers** with markup.

BYOK + retrieval-focus is the most viable path for a solo founder.

## What Needs to Be Built (Beyond Current State)

### Must-Have for Launch

| Component | Current State | Work Needed |
|-----------|--------------|-------------|
| Multi-tenant auth & isolation | None | API keys, per-tenant collections, rate limiting |
| Remote MCP server (SSE transport) | stdio only | Implement MCP SSE/Streamable HTTP transport |
| REST API | None | FastAPI wrapper around core functions |
| Managed vector DB | Local Chroma | Migrate to hosted solution (Chroma Cloud, Qdrant Cloud, or Pinecone) |
| Document upload & management | Local filesystem | Cloud storage (S3/GCS) + upload API |
| Usage metering & billing | None | Track queries/docs per tenant, integrate Stripe |
| Dashboard / onboarding UI | None | Minimal web UI: upload docs, see usage, get MCP config |
| Retrieval quality | In progress (Phase 4) | Must be competitive (>70% correctness) before launch |
| Deployment | Local dev | Docker → cloud (Railway, Fly.io, or AWS) |

### Nice-to-Have for Launch

- Embeddable chat widget (like Ailog)
- Multiple embedding model choices
- Webhook notifications
- Team/organization management
- Custom system prompts per endpoint

### Timeline Estimate (Solo, Full-Time)

| Phase | Duration | Deliverable |
|-------|----------|------------|
| Finish Phase 4 (retrieval quality) | 2–4 weeks | Competitive retrieval |
| Multi-tenant + auth + remote MCP | 3–4 weeks | Core cloud architecture |
| REST API + billing + dashboard | 3–4 weeks | Launchable product |
| Deploy + landing page + docs | 1–2 weeks | Public launch |
| **Total** | **~3–4 months** | **Beta launch** |

## Distribution Channels

### Priority Order

**1. Cursor Marketplace** ⭐ (highest value for target audience)
- Submit at: `cursor.com/marketplace/publish`
- Plugins are Git repositories; manually reviewed by the Cursor team before listing.
- Once approved: "Add to Cursor" one-click install — the premium discovery channel.
- Bundle includes: MCP server + rules/skills/docs.
- **No RAG/document Q&A plugin exists in the Marketplace yet. First-mover advantage.**

**2. Anthropic Connectors Directory** ⭐ (Claude Desktop / Claude.ai / Claude Code)
- Submit at: `clau.de/mcp-directory-submission` (remote MCPs)
- Covers Claude Desktop, Claude.ai, Claude Mobile, Claude Code.
- Requirements: OAuth 2.0 auth, privacy policy, documentation, test credentials, tool annotations.
- ~2 week review time.
- Also supports `.mcpb` Desktop Extensions for one-click install in Claude Desktop.

**3. Anthropic Official MCP Registry**
- `registry.modelcontextprotocol.io` — canonical Anthropic-maintained registry.
- Listed servers appear in tooling that auto-discovers MCP servers.

**4. Community Directories** (submit immediately, no review lag, build SEO + early users)

| Directory | Size | Cost | Link |
|-----------|------|------|------|
| **mcpservers.org** | 300+ | Free (or $39 fast-track + Official badge) | `mcpservers.org/submit` |
| **mcp.so** | Active | Free | Form / API |
| **mcp-awesome.com** | 1,200+ | Free | PR / form |
| **awesomemcp.io** | 789+ | Free | PR |
| **mcpserve.com** | Active | Free / GitHub PR | `mcpserve.com/submit.html` |
| **TensorBlock/awesome-mcp-servers** (GitHub) | 7,260+ | Free | Pull request |
| **punkpeye/awesome-mcp-servers** (GitHub) | Widely linked | Free | Pull request |

### Recommended Launch Sequence
1. **Pre-launch:** Submit to community directories (free, instant SEO, early signups).
2. **At launch:** Submit to Anthropic MCP Registry + Connectors Directory (2-week turnaround).
3. **Post-launch:** Apply to Cursor Marketplace once the product is stable (manual review, biggest prize).

## Validation Plan (Before Building)

1. **Landing page** — "MCP-native RAG cloud for AI agents. Upload docs, your agent queries them." Email signup.
2. **Talk to 20 developers** building AI agents. Ask: "How do you handle document retrieval in your agents today? What's painful?" Don't pitch — listen.
3. **Post in communities** — r/LocalLLaMA, r/LangChain, Indie Hackers, Cursor forums, MCP Discord. Gauge interest.
4. **Target: 100 email signups or 5 "I'd pay for this" conversations** before committing to the cloud build.

## Risks

| Risk | Mitigation |
|------|-----------|
| MCP doesn't become dominant standard | Also offer REST API; MCP is branding/positioning, not the only interface |
| OpenAI/Anthropic build this in (Assistants API already has file search) | They optimize for their own models; oracle-rag is model-agnostic and tunable |
| Margin compression at low price points | BYOK model, retrieval-only pricing, optimize embedding costs |
| Solo founder capacity | Focus on one persona, one feature, ship weekly |
| Retrieval quality not competitive | Finish Phase 4 first — don't launch until quality is there |

## Lessons from the Market

- **Chatbase** started as "Chat with PDF" → hit $64K MRR → had to pivot to "B2B AI agent platform" to escape commoditization. The simple RAG product became a feature, not a business. **Implication:** Build for agents, not for "chat with PDF."
- **Ailog** carved a niche with GDPR + French market + 5-min deploy. **Implication:** Geographic or regulatory niches can work.
- **BoltAI** makes $15–30K/mo as a solo dev with perpetual licensing for an AI client. **Implication:** Solo AI SaaS can be very profitable at modest scale.
- **Ragapi** prices at $7/mo. **Implication:** Race-to-bottom pricing exists; differentiate on DX and MCP-native, not on price.

## Summary

| Question | Answer |
|----------|--------|
| Is the market real? | Yes — $92M in 2025, growing 13.6% CAGR |
| Is it crowded? | Yes for generic RAG-as-a-service. No for MCP-native agent-focused RAG |
| Is it feasible to build? | Yes — 3–4 months to beta as a solo developer |
| Is it rational? | Only if differentiated (MCP-native + agent-focused + BYOK). Not as a generic RAG API |
| What to do first? | Finish Phase 4 retrieval quality, then validate demand before building cloud infra |

---

*Next steps: revisit this doc after Phase 4. If retrieval quality is competitive, run the validation plan. If 100+ signups or 5+ "I'd pay" conversations, proceed to cloud architecture.*
