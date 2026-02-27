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
