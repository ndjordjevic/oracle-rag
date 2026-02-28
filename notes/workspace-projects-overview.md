## Workspace Projects Overview

---

### `langchain-academy` — LangChain Academy: Introduction to LangGraph

Official LangChain Academy course for LangGraph, organized into 7 modules (0–6) of Jupyter notebooks with companion `studio/` directories for LangGraph Studio.

**Module breakdown:**
- **Module 0 (Basics):** Environment setup, chat models, message types, basic model invocation and tool integration (TavilySearch).
- **Module 1 (Building Agents):** `StateGraph`, `MessagesState`, `ToolNode`, conditional edges, the ReAct pattern (tool-calling loop), and memory via `MemorySaver`. Studio files include a simple graph, router, and full ReAct agent.
- **Module 2 (State & Memory):** State schema options (`TypedDict`, `dataclass`, Pydantic), state reducers, conversation summarization, message trimming/filtering, and external memory. Studio includes a chatbot with auto-summarization.
- **Module 3 (Human-in-the-Loop):** Static breakpoints (`interrupt_before`), dynamic interrupts (`NodeInterrupt`), state editing, streaming with interruptions, and time-travel via checkpoints.
- **Module 4 (Multi-Agent & Parallelization):** Fan-out/fan-in parallel execution, sub-graphs for isolated agent states, the `Send` API for dynamic parallelization, map-reduce patterns, and a multi-agent research assistant.
- **Module 5 (Long-Term Memory):** `BaseStore` for persistent key-value storage, user profile and collection memory schemas, `Trustcall` for structured memory extraction, and a full `task_mAIstro` ToDo agent.
- **Module 6 (Deployment):** LangGraph CLI (`langgraph dev`, `langgraph deploy`), connecting via SDK, assistants (versioned/configurable agent instances), thread management, and streaming from deployed agents.

**Key dependencies:** `langgraph`, `langgraph-prebuilt`, `langgraph-sdk`, `langgraph-checkpoint-sqlite`, `langchain-core`, `langchain-openai`, `langchain-tavily`, `langsmith`, `trustcall`.

---

### `lca-lc-foundations` — LangChain Foundations (Python)

Companion repo for the "Introduction to LangChain - Python" course. Teaches core LangChain primitives through three modules with practical projects, using `uv` as the preferred project manager.

**Module breakdown:**
- **Module 1 (Create Agent):** Foundational models, tools (`@tool` decorator), short-term memory, multimodal messages. Project: Personal Chef agent.
- **Module 2 (Advanced Agent):** Model Context Protocol (MCP) with `MultiServerMCPClient`, custom state management, runtime context, multi-agent systems. Project: Wedding Planner. Bonus notebooks on RAG and SQL.
- **Module 3 (Production-Ready Agent):** Middleware patterns, managing long conversations (summarization), HITL with interrupts, dynamic models/prompts/tools. Project: Email Assistant with authentication. Bonus: Agent Chat UI (TypeScript/React).

**Notable utilities:** `env_utils.py` — comprehensive environment verification script that checks Python version, venv activation, installed packages against `pyproject.toml`, API key configuration, and detects env var conflicts. Two `langgraph.json` configs expose the Personal Chef and Email Assistant agents for Studio.

**Key dependencies:** `langchain>=1.1.3`, `langgraph>=1.0.3`, `langchain-openai`, `langchain-anthropic`, `langchain-google-vertexai`, `mcp>=1.21.1`, `langchain-mcp-adapters`, `langchain-tavily`, `pypdf`, `langsmith`. Python >=3.12, <3.14.

---

### `lca-langchainV1-essentials` — LangChain v1 Essentials (Python & JS)

Dual-language tutorial (Python + TypeScript) covering 9 lessons on the LangChain v1 API, centered around `create_agent` and building blocks for agent development. Both sides use a Chinook SQLite database for SQL agent examples.

**Lesson breakdown (same structure in both languages):**
- **L1 (Fast Agent):** Build an SQL agent with `create_agent` in a few lines; runtime context via `RuntimeContext` dataclass.
- **L2 (Messages):** Message types as the unit of context; message flow between components.
- **L3 (Streaming):** `agent.stream()` with `stream_mode="values"` for reduced latency.
- **L4 (Tools):** `@tool` decorator (Python) / `tool()` with Zod schemas (JS); typed arguments and descriptions.
- **L5 (MCP Tools):** `MultiServerMCPClient` connecting to external MCP servers (e.g. `@theo.foobar/mcp-time`).
- **L6 (Memory):** Checkpointing with `MemorySaver` for conversation persistence.
- **L7 (Structured Output):** Producing validated, structured responses from agents.
- **L8 (Dynamic Prompts):** Middleware for runtime prompt modification; `@dynamic_prompt` and `wrap_model_call`.
- **L9 (HITL):** Interrupts for human approval workflows; middleware pattern.

**Studio files:** `sql_agent1.py` (safety-hardened: read-only, LIMIT enforcement, regex SQL validation) and `sql_agent2.py` (minimal checks). JS side mirrors with `sql_agent2.ts`.

**Key dependencies (Python):** `langgraph>=1.0.0`, `langchain>=1.0.0`, `langchain-openai`, `langchain-anthropic`, `langchain-mcp-adapters`. **(JS):** `@langchain/langgraph`, `@langchain/openai`, `@langchain/mcp-adapters`, `zod`, `typeorm`, `better-sqlite3`.

---

### `lca-langgraph-essentials` — LangGraph v1 Essentials (Python & JS)

Focused specifically on LangGraph v1 concepts in both Python and TypeScript, with 6 progressive lessons plus a complete email workflow project. Includes a companion PDF ("LangGraph V1 Essentials.pdf", ~3.2 MB) and visual assets showing graph structure diagrams.

**Python notebooks:**
- **L1 (Nodes):** State schemas with `TypedDict`, node functions, building graphs with `StateGraph`/`START`/`END`.
- **L2 (Edges):** Parallel execution via multiple outgoing edges, state reducers (`operator.add`) for merging parallel results.
- **L3–L4 (Conditional Edges & Memory):** `Command`-based routing from nodes, `add_conditional_edges` with router functions, `InMemorySaver` checkpointer, multi-threaded execution.
- **L5 (Interrupts):** `interrupt()` to pause execution, human review workflows, resuming with `Command(resume=...)`.
- **L6 (Email Agent):** End-to-end email processing: AI classification with structured output, documentation search, bug tracking, response generation, human review for high-urgency cases. Combines all previous concepts.

**JS/TypeScript side (`js/src/`):**
- **L1:** 6 files implementing simple nodes, parallel execution, conditional edges (both Command-based and router-function approaches), memory/checkpointing, and interrupts.
- **L2:** Complete email workflow with 7 nodes (readEmail → classifyIntent → searchDocumentation/bugTracking → writeResponse → humanReview → sendReply), parallel paths, and conditional routing.

**Preview images** in `js/preview/` show rendered graph visualizations for each concept. **Assets** include diagrams for states/nodes, parallel execution, conditional routing, memory, HITL, and the email workflow.

**Key dependencies (Python):** `langgraph>=1.0.0`, `langchain>=1.0.0`, `langchain-openai`, `langchain-anthropic`. **(JS):** `@langchain/langgraph`, `@langchain/openai`, `zod@^4`. Python >=3.11, JS Node >=20.

---

### `rag-from-scratch` — RAG From Scratch (Notebooks)

Educational series that builds RAG from first principles across 18 parts in 5 Jupyter notebooks, accompanying a [YouTube playlist](https://youtube.com/playlist?list=PLfaIDFEXuae2LXbO1_PKyVJiQ23ZztA0x). Focuses on understanding core RAG mechanics without immediately relying on high-level abstractions.

**Notebook breakdown:**
- **Parts 1–4 (`rag_from_scratch_1_to_4.ipynb`):** RAG overview, indexing fundamentals — token counting (~4 chars/token), text embedding models (OpenAI), cosine similarity, document loaders, text splitters (`RecursiveTextSplitter`), and the full document ingestion pipeline.
- **Parts 5–9 (`rag_from_scratch_5_to_9.ipynb`):** Retrieval strategies and generation — different retrieval approaches and how to wire them into generation.
- **Parts 10–11 (`rag_from_scratch_10_and_11.ipynb`):** Routing and query construction — logical routing (function calling for structured output) vs. semantic routing (embedding-based), branching based on datasource selection, and building structured queries with metadata filters.
- **Parts 12–14 (`rag_from_scratch_12_to_14.ipynb`):** Advanced RAG techniques.
- **Parts 15–18 (`rag_from_scratch_15_to_18.ipynb`):** Production patterns and considerations.

**Value for Oracle-RAG:** This project is a conceptual grounding for reasoning about RAG behavior and trade-offs. Especially relevant topics include: indexing strategies (Parts 1–4), retrieval quality and routing (Parts 10–11), metadata filtering and query construction (Part 11), and production patterns (Parts 15–18). Use it as a reference when evaluating new features like hybrid search, re-ranking, query preprocessing, or chunk size tuning.

---

### `langsmith-cookbook` — LangSmith Cookbook (Observability, Evaluation, Feedback)

Official [LangSmith Cookbook](https://github.com/langchain-ai/langsmith-cookbook) — practical recipes for debugging, evaluating, testing, and improving LLM applications with [LangSmith](https://smith.langchain.com/). The repo is **archived** (read-only as of Feb 2026) but remains a strong reference. Most content is Jupyter notebooks plus a few Streamlit/Next.js apps; each recipe is self-contained in a subfolder with optional `requirements.txt` and assets.

**Section breakdown:**

- **Tracing** (`tracing-examples/`) — Instrument apps for LangSmith without locking into LangChain: `@traceable` decorator (Python SDK), REST API for logging runs and nested spans, custom run names for chains/lambdas/agents, tracing nested tool calls via `run_manager.get_child()` and callbacks, and displaying trace links in Streamlit for quick jump-to-trace during development.
- **LangChain Hub** (`hub-examples/`) — Use Hub prompts in pipelines: RetrievalQA chain with hub-loaded prompts, prompt versioning for deployment stability (pin specific versions vs. `latest`), and runnable prompt templates (edit in playground → save → integrate into runnable chains).
- **Testing & Evaluation** (`testing-examples/`) — Dataset-driven evals and regression testing.
  - **RAG:** Q&A correctness (labeled dataset + LLM-as-judge), dynamic data (evaluators that dereference labels), fixed-source RAG eval (evaluate generator with pre-supplied retrieved docs), and **RAGAS** integration (answer correctness, faithfulness, context relevancy, context recall, context precision — both generator and retriever, labeled and reference-free).
  - **Chat:** Simulated-user evals (task-based scoring), single-turn evals within multi-turn conversation datasets.
  - **Extraction / Agents / Multimodal:** Extraction chain (JSON similarity vs. labels), exact match, agent intermediate steps (expected trajectory), tool selection (precision + prompt writer for failures), multimodal (e.g. image classification).
  - **Fundamentals:** Backtesting (production runs → dataset → compare new version), adding metrics to existing test projects (`compute_test_metrics`), naming test projects, exporting tests to CSV (`get_test_results`), downloading feedback and examples for reports.
- **TypeScript testing** (`typescript-testing-examples/`) — Vision-based evals (e.g. GPT-4V for AI-generated UIs), traceable example; fewer examples than Python.
- **Feedback** (`feedback-examples/`) — Capture and automate feedback on runs: Streamlit and Next.js chat apps with tracing and feedback; algorithmic feedback pipeline (batch evaluation of production runs); real-time automated feedback (async callback per run); **real-time RAG chatbot evaluation** (Streamlit) — relevance and faithfulness evaluators via `EvaluatorCallbackHandler`, non-blocking hallucination checks against retrieved docs; LangChain agent with web-search and human feedback.
- **Optimization** (`optimization/`) — Use LangSmith to improve prompts and few-shot sets: prompt bootstrapping (rewrite system prompt from feedback + LLM optimizer), style-transfer example (Elvis-bot), automated few-shot bootstrapping (curate examples by performance, e.g. SCONE), iterative prompt optimization (Streamlit, few-shot + optimizer model), online few-shot (add good examples to dataset from evaluators).
- **Fine-tuning** (`fine-tuning-examples/`) — Export run data for training: export to OpenAI fine-tuning format from LangSmith runs; Lilac-based dataset curation (near-duplicates, PII, etc.).
- **Exploratory data analysis** (`exploratory-data-analysis/`) — ETL for LLM runs and feedback (export for analytics); Lilac to enrich, label, and organize datasets.
- **Introduction** (`introduction/`) — High-level LangSmith intro, summarization, and online evaluation notebooks.

**Key dependencies:** Per-recipe; commonly `langsmith`, `langchain`, `langchain-openai`, `langchain-anthropic`, Chroma (RAG examples), Streamlit/Next.js for apps; RAGAS recipes use `ragas`; fine-tuning/EDA use `lilac` where applicable.

**Value for Oracle-RAG:** Use the cookbook when adding observability and evaluation: (1) **Tracing** — add `@traceable` or LangChain callbacks so MCP and RAG runs appear in LangSmith. (2) **RAG evaluation** — adopt the Q&A correctness or RAGAS patterns (faithfulness, context relevancy/recall/precision) and run them on a small dataset before/after retrieval or prompt changes. (3) **Real-time RAG feedback** — adapt the Streamlit real-time feedback example (relevance + faithfulness evaluators, `EvaluatorCallbackHandler`) to monitor production oracle-rag answers against retrieved chunks. (4) **Backtesting** — turn production MCP traces into a dataset and compare new chain versions. (5) **Prompt versioning** — if prompts move to LangChain Hub, use versioned fetches for stable deployments.

---

### `cookbooks` — LangChain Cookbooks (LangGraph + LangSmith patterns)

Official [LangChain Cookbooks](https://github.com/langchain-ai/cookbooks) repo: curated code snippets and examples for **LangGraph** and **LangSmith** — design patterns, persistence, streaming, observability, and auth. Structure is **python/** (and **javascript/** placeholder). MIT licensed; actively maintained.

**LangGraph (`python/langgraph/`):**

- **Agents** — **basic-RAG**: stateless RAG agent with LangGraph + Chroma. **assistants-demo**: ReAct agent and supervisor/multi-agent with configuration, notebooks. **ecommerce-hierarchical-system**: top-level supervisor routing to BU supervisors (billing & payments, order management, promotions & loyalty), each with sub-agents and tools; `uv sync`, LangSmith tracing, `langgraph dev`; good reference for hierarchical routing. **arxiv-researcher**: multi-agent flow (high-level summary, detailed summary, application agent).
- **Human-in-the-loop** — Examples for human interaction in graphs (folder present; see repo for current contents).
- **MCP** — **mcp-auth-demo**: full user-auth flow for agents that call MCP with user credentials: Supabase auth → Supabase Vault for secrets → custom LangGraph auth middleware → MCP server authenticated with user-scoped GitHub PAT; tests for vault retrieval, MCP connection, middleware, and agent flow; aligns with [LangGraph Agent Authentication](https://langchain-ai.github.io/langgraph/how-tos/auth/). Relevant if oracle-rag or MCP servers ever need per-user or per-tenant credentials.
- **Persistence** — **fault-tolerance**: two patterns — (1) **Partial failure / pending writes**: parallel nodes where some fail; successful node outputs saved as pending writes, only failed nodes retry, reducers merge state, checkpointing preserves work. (2) **Retry + fallbacks**: progressive retry (direct retry → simplified input → default result), graceful degradation. Uses SQLite checkpointer, `merge_dicts` and `add_messages` reducers. Useful for robust RAG/agent pipelines.
- **Streaming** — **custom-streaming/log-analysis**: custom streaming example (log analysis).

**LangSmith (`python/langsmith/`):**

- **Observability** — **tracing/data-privacy/trace-content-redaction**: redact system prompts (or other content) in traces for privacy/compliance; notebook + `utils.py`. **tracing/otel**: OpenTelemetry tracing with Bedrock agents (`tracing_bedrock_agents_otel.ipynb`).
- **evaluation/** and **prompt-engineering/** — Placeholders (`.gitkeep`); richer evaluation and prompt patterns live in `langsmith-cookbook`.

**Key dependencies:** Per-example; commonly `langgraph`, `langchain`, `langchain-openai`, Chroma (basic-RAG), `uv` (ecommerce), Supabase (mcp-auth-demo). LangSmith/OTEL examples use `langsmith` and OpenTelemetry packages.

**Value for Oracle-RAG:** (1) **RAG agent structure** — basic-RAG shows a minimal LangGraph + Chroma RAG agent; use as a template if you move oracle-rag into a graph. (2) **Fault tolerance** — persistence/fault-tolerance patterns (pending writes, retries + fallbacks) for retrieval or LLM steps that can fail. (3) **MCP auth** — if you add per-user or per-tenant MCP access, mcp-auth-demo shows Supabase + Vault + LangGraph auth middleware. (4) **Trace privacy** — data-privacy redaction example if you need to redact prompts or PII in LangSmith traces. (5) **Hierarchical routing** — ecommerce-hierarchical-system as a reference for routing to multiple “BU”-style sub-graphs (e.g. by document type or tag).
