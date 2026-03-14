# Workspace Projects Overview

Reference projects from `Langchain.code-workspace` (9 folders; pinrag and pinrag-cloud are not listed here). Consult the relevant "Value for PinRAG" section first when looking for example patterns, then use the module/path details to locate code.

---

### `langchain-academy` — LangChain Academy: Introduction to LangGraph

**Value for PinRAG:** Core LangGraph primitives: `StateGraph`, `ToolNode`, `MemorySaver`, conditional edges, ReAct pattern (Module 1); state reducers, message management, summarization (Module 2); HITL breakpoints and time-travel (Module 3); multi-agent fan-out, `Send` API, map-reduce (Module 4); `BaseStore` for persistent memory (Module 5); deployment with `langgraph dev` / SDK (Module 6).

Official LangChain Academy LangGraph course, 7 modules (0–6) of Jupyter notebooks with companion `studio/` directories.

**Module breakdown:**
- **Module 0:** Environment setup, chat models, message types, basic tool integration (TavilySearch).
- **Module 1:** `StateGraph`, `MessagesState`, `ToolNode`, conditional edges, ReAct pattern, `MemorySaver`.
- **Module 2:** State schemas (`TypedDict`, `dataclass`, Pydantic), reducers, conversation summarization, message trimming/filtering, external memory.
- **Module 3:** Static breakpoints (`interrupt_before`), dynamic interrupts (`NodeInterrupt`), state editing, streaming, time-travel via checkpoints.
- **Module 4:** Fan-out/fan-in parallel execution, sub-graphs, `Send` API, map-reduce, multi-agent research assistant.
- **Module 5:** `BaseStore` for persistent key-value storage, user profile/collection memory schemas, `Trustcall` for structured extraction, full `task_mAIstro` ToDo agent.
- **Module 6:** LangGraph CLI (`langgraph dev`, `langgraph deploy`), SDK, assistants, thread management, streaming from deployed agents.

**Key dependencies:** `langgraph`, `langgraph-prebuilt`, `langgraph-sdk`, `langgraph-checkpoint-sqlite`, `langchain-core`, `langchain-openai`, `langchain-tavily`, `langsmith`, `trustcall`.

---

### `lca-lc-foundations` — LangChain Foundations (Python)

**Value for PinRAG:** `MultiServerMCPClient` integration (Module 2); middleware patterns, long-conversation management, HITL interrupts (Module 3); `env_utils.py` for environment verification.

Companion repo for "Introduction to LangChain - Python". Three modules with practical projects; uses `uv`.

**Module breakdown:**
- **Module 1:** Models, `@tool` decorator, short-term memory, multimodal messages. Project: Personal Chef agent.
- **Module 2:** `MultiServerMCPClient`, custom state, runtime context, multi-agent. Project: Wedding Planner. Bonus: RAG and SQL notebooks.
- **Module 3:** Middleware, long-conversation summarization, HITL interrupts, dynamic models/prompts/tools. Project: Email Assistant. Bonus: Agent Chat UI (TypeScript/React).

**Notable:** `env_utils.py` — checks Python version, venv, installed packages vs. `pyproject.toml`, API keys, env var conflicts.

**Key dependencies:** `langchain>=1.1.3`, `langgraph>=1.0.3`, `langchain-openai`, `langchain-anthropic`, `langchain-google-vertexai`, `mcp>=1.21.1`, `langchain-mcp-adapters`, `langchain-tavily`, `pypdf`, `langsmith`. Python >=3.12, <3.14.

---

### `lca-langchainV1-essentials` — LangChain v1 Essentials (Python & JS)

**Value for PinRAG:** `create_agent` patterns (L1); typed `@tool` / Zod schemas (L4); `MultiServerMCPClient` with external MCP servers (L5); checkpointing (L6); structured output (L7); dynamic prompts / middleware (L8); HITL interrupts (L9). Safety-hardened SQL agent (`sql_agent1.py`) as a reference for tool guardrails.

Dual-language tutorial (Python + TypeScript) covering 9 lessons on LangChain v1 API. Uses a Chinook SQLite database for SQL agent examples.

**Lesson breakdown:**
- **L1:** `create_agent` fast-start; `RuntimeContext` for runtime config.
- **L2:** Message types as unit of context.
- **L3:** `agent.stream()` with `stream_mode="values"`.
- **L4:** `@tool` (Python) / `tool()` with Zod schemas (JS); typed args.
- **L5:** `MultiServerMCPClient` connecting to external MCP servers.
- **L6:** `MemorySaver` checkpointing.
- **L7:** Structured output from agents.
- **L8:** Middleware for runtime prompt modification; `@dynamic_prompt`.
- **L9:** Interrupts for human approval workflows.

**Key dependencies (Python):** `langgraph>=1.0.0`, `langchain>=1.0.0`, `langchain-openai`, `langchain-anthropic`, `langchain-mcp-adapters`. **(JS):** `@langchain/langgraph`, `@langchain/openai`, `@langchain/mcp-adapters`, `zod`, `typeorm`, `better-sqlite3`.

---

### `lca-langgraph-essentials` — LangGraph v1 Essentials (Python & JS)

**Value for PinRAG:** `Command`-based routing, parallel node execution, `InMemorySaver` checkpointer (L3–L4); `interrupt()` for human review (L5); end-to-end email agent combining structured output, parallel paths, and HITL (L6 — good template for a doc-processing graph).

6 progressive lessons plus a complete email workflow project in both Python and TypeScript. Includes a companion PDF and graph-structure visual assets.

**Python notebooks:**
- **L1:** `TypedDict` state, node functions, `StateGraph`/`START`/`END`.
- **L2:** Parallel execution via multiple outgoing edges, `operator.add` reducers.
- **L3–L4:** `Command`-based routing, `add_conditional_edges`, `InMemorySaver`, multi-threaded execution.
- **L5:** `interrupt()`, human review workflows, `Command(resume=...)`.
- **L6:** End-to-end email agent: AI classification, doc search, bug tracking, response generation, HITL for high-urgency cases.

**JS side (`js/src/`):** mirrors Python; L2 implements the full 7-node email workflow. `js/preview/` has rendered graph visualizations.

**Key dependencies (Python):** `langgraph>=1.0.0`, `langchain>=1.0.0`, `langchain-openai`, `langchain-anthropic`. **(JS):** `@langchain/langgraph`, `@langchain/openai`, `zod@^4`. Python >=3.11, JS Node >=20.

---

### `rag-from-scratch` — RAG From Scratch (Notebooks)

**Value for PinRAG:** Conceptual grounding for RAG trade-offs. Key topics: indexing strategies (Parts 1–4), retrieval quality (Parts 5–9), routing and query construction with metadata filters (Parts 10–11), advanced techniques (Parts 12–14), production patterns (Parts 15–18). Reference when evaluating hybrid search, re-ranking, query preprocessing, or chunk-size tuning.

18-part educational series in 5 Jupyter notebooks, accompanying a [YouTube playlist](https://youtube.com/playlist?list=PLfaIDFEXuae2LXbO1_PKyVJiQ23ZztA0x). Builds RAG from first principles.

**Notebook breakdown:**
- **Parts 1–4:** RAG overview, indexing fundamentals — token counting, OpenAI embeddings, cosine similarity, document loaders, `RecursiveTextSplitter`, ingestion pipeline.
- **Parts 5–9:** Retrieval strategies and generation.
- **Parts 10–11:** Routing and query construction — logical routing (function calling) vs. semantic routing (embedding-based); structured queries with metadata filters.
- **Parts 12–14:** Advanced RAG techniques.
- **Parts 15–18:** Production patterns and considerations.

---

### `langsmith-cookbook` — LangSmith Cookbook (Observability, Evaluation, Feedback)

**Value for PinRAG:** (1) **Tracing** — `@traceable` / callbacks to surface MCP and RAG runs in LangSmith. (2) **RAG evaluation** — Q&A correctness and RAGAS patterns (faithfulness, context relevancy/recall/precision) to run on a dataset before/after retrieval or prompt changes. (3) **Real-time RAG feedback** — `EvaluatorCallbackHandler` for live relevance + faithfulness checks against retrieved chunks. (4) **Backtesting** — turn production MCP traces into a dataset and compare chain versions. (5) **Prompt versioning** — versioned Hub fetches for stable deployments.

Official [LangSmith Cookbook](https://github.com/langchain-ai/langsmith-cookbook). **Archived** (read-only as of Feb 2026) but still a strong reference. Self-contained recipes in subfolders.

**Section breakdown:**
- **Tracing** (`tracing-examples/`) — `@traceable`, REST API spans, custom run names, nested tool call tracing, Streamlit trace links.
- **LangChain Hub** (`hub-examples/`) — Hub prompts in pipelines, prompt versioning, runnable prompt templates.
- **Testing & Evaluation** (`testing-examples/`) — RAG: Q&A correctness (LLM-as-judge), dynamic data, RAGAS integration. Chat: simulated-user evals, single-turn evals in multi-turn datasets. Extraction/Agents/Multimodal: exact match, agent trajectory, tool selection, multimodal. Fundamentals: backtesting, metrics on existing projects, CSV export.
- **TypeScript testing** (`typescript-testing-examples/`) — Vision-based evals (GPT-4V), traceable examples.
- **Feedback** (`feedback-examples/`) — Streamlit/Next.js chat apps with tracing and feedback; algorithmic feedback pipeline; real-time RAG chatbot evaluation with `EvaluatorCallbackHandler`.
- **Optimization** (`optimization/`) — Prompt bootstrapping from feedback, automated few-shot curation, iterative prompt optimization, online few-shot selection.
- **Fine-tuning** (`fine-tuning-examples/`) — Export runs to OpenAI fine-tuning format; Lilac-based dataset curation.
- **EDA** (`exploratory-data-analysis/`) — ETL for LLM runs and feedback; Lilac for enrichment and labeling.

**Key dependencies:** `langsmith`, `langchain`, `langchain-openai`, `langchain-anthropic`, Chroma (RAG), Streamlit/Next.js (apps), `ragas`, `lilac` (where applicable).

---

### `cookbooks` — LangChain Cookbooks (LangGraph + LangSmith patterns)

**Value for PinRAG:** (1) **RAG agent structure** — `basic-RAG` (minimal LangGraph + Chroma) as a template if pinrag moves into a graph. (2) **Fault tolerance** — pending-writes and retry+fallback patterns for retrieval or LLM steps. (3) **MCP auth** — `mcp-auth-demo` (Supabase + Vault + LangGraph auth middleware) for per-user or per-tenant MCP credentials. (4) **Trace privacy** — content redaction for prompts or PII in LangSmith. (5) **Hierarchical routing** — `ecommerce-hierarchical-system` as a reference for routing to multiple sub-graphs by document type or tag.

Official [LangChain Cookbooks](https://github.com/langchain-ai/cookbooks). Curated patterns for LangGraph and LangSmith. Actively maintained; MIT licensed.

**LangGraph (`python/langgraph/`):**
- **Agents** — `basic-RAG`: stateless RAG with LangGraph + Chroma. `assistants-demo`: ReAct + supervisor/multi-agent. `ecommerce-hierarchical-system`: top-level supervisor → BU supervisors (billing, orders, promotions) → sub-agents. `arxiv-researcher`: multi-agent flow.
- **Human-in-the-loop** — Human interaction examples.
- **MCP** — `mcp-auth-demo`: Supabase auth → Vault → LangGraph auth middleware → MCP server with user-scoped GitHub PAT.
- **Persistence** — `fault-tolerance`: (1) partial failure/pending writes with parallel nodes; (2) retry + fallbacks with graceful degradation. SQLite checkpointer, `merge_dicts`/`add_messages` reducers.
- **Streaming** — `custom-streaming/log-analysis`.

**LangSmith (`python/langsmith/`):**
- **Observability** — `tracing/data-privacy/trace-content-redaction`: redact system prompts for compliance. `tracing/otel`: OpenTelemetry with Bedrock agents.
- **evaluation/** and **prompt-engineering/** — Placeholders; richer patterns in `langsmith-cookbook`.

**Key dependencies:** `langgraph`, `langchain`, `langchain-openai`, Chroma (`basic-RAG`), `uv` (ecommerce), Supabase (`mcp-auth-demo`), `langsmith` + OpenTelemetry (OTEL examples).

---

### `deep_research_from_scratch` — Deep Research From Scratch (LangGraph)

**Value for PinRAG:** (1) **MCP integration** — `MultiServerMCPClient` / MCP adapters: client spawns server, gets tools, binds to model. (2) **Structured output** — Pydantic schemas for clarification and delegation; applicable to query analysis or tool routing. (3) **Supervisor / multi-step workflows** — context isolation and "sub-agent as tool" pattern for multi-step reasoning over docs. (4) **Per-component evaluation** — LangSmith datasets + LLM-as-judge + mock scenarios before composing stages; directly applicable when adding new RAG or agent steps. (5) **LangGraph Studio** — `langgraph.json` exposing multiple graphs as a model for multi-workflow repos.

Tutorial repo and LangChain Academy course building a deep research agent: **Scope** → **Research** → **Write**. Five notebooks + Python package; uses `uv`, LangGraph state graphs, MCP adapters, multi-agent supervisor.

**Notebook breakdown:**
- **1. Scoping** — Structured output for user clarification; brief generation; state schemas; conditional routing; LangSmith eval (criteria captured? no hallucination?).
- **2. Research agent with tools** — LLM + tools loop with termination; think tool (Anthropic-style) to avoid spin-out; search budgets (2–3 simple, up to 5 complex); webpage summarization inside tool; context compression at end; LangSmith eval (should continue vs. stop).
- **3. Research agent with MCP** — MCP as protocol: agent spawns server (stdio/HTTP), adapter converts tools to LangChain; async execution; filesystem MCP server example.
- **4. Research supervisor** — Multi-agent: context isolation across subtopics; `asyncio.gather()` for parallel sub-agents; `ConductResearch` as tool returning `compressed_research`; LangSmith eval (expect parallelization or not).
- **5. Full system** — Connect scope → supervisor → write; report writer with `max_tokens`; `langgraph dev` for Studio.

**Package layout:** `src/deep_research_from_scratch/` — state schemas, prompts, research agents (basic/MCP/full), `multi_agent_supervisor.py`, utils. **langgraph.json** exposes 5 graphs.

**Key dependencies:** `langgraph>=1.0.0`, `langchain>=1.0.0`, `langchain-openai`, `langchain-anthropic`, `langchain_community`, `langchain_tavily`, `langchain_mcp_adapters`, `pydantic>=2`, `tavily-python`, `rich`, `jupyter`. Python >=3.11, <3.14.

---

### `intro-to-langsmith` — Intro to LangSmith (LangSmith Academy)

**Value for PinRAG:** (1) **Tracing** — `@traceable` on RAG steps with `run_type` (retriever/chain/llm); conversational thread tracking for multi-turn chat. (2) **Evaluation framework** — create a dataset (Q&A or relevance pairs), run experiments, use custom or LLM-as-judge evaluators; directly applicable before adding multi-query, re-ranking, or other retrieval changes. (3) **Prompt iteration** — Playground + dataset + experiments for RAG prompt tuning. (4) **Feedback and production** — publish feedback on runs from MCP clients; online evaluators and `list_runs` filtering for production monitoring.

LangSmith fundamentals course: observability, prompt engineering, evaluation, feedback, production monitoring. Uses a single running RAG app over LangSmith docs (SitemapLoader, SKLearnVectorStore, OpenAI) throughout.

**Module breakdown:**
- **Module 0:** Set up course RAG app: sitemap indexing, `RecursiveCharacterTextSplitter`, SKLearnVectorStore (parquet), OpenAI answers.
- **Module 1 (Tracing):** `@traceable`, run types (LLM/Retriever/Tool/Chain), conversational threads, alternative tracing methods.
- **Module 2 (Evaluations):** Custom evaluators, LLM-as-judge (reference-free and reference-based), dataset upload, experiments, summary evaluators, pairwise comparison.
- **Module 3 (Prompt engineering):** Playground experiments, prompt engineering lifecycle, LangChain Hub integration.
- **Module 4 (Feedback):** Programmatic feedback on runs via SDK (`run_id`).
- **Module 5 (Production monitoring):** Online evaluators per production run; `list_runs` / `/runs/query` filtering and export.

**Key dependencies:** `langsmith>=0.2.0`, `langchain`, `langgraph`, `langgraph-sdk`, `langchain-community`, `langchain-core`, `langchain-openai`, `langchain-text-splitters`, `scikit-learn`, `pandas`, `pyarrow`, `lxml`. Python >=3.11.
