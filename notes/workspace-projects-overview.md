## Workspace Projects Overview

### `/Users/nenaddjordjevic/PythonProjects/langchain-academy/` – LangChain Academy: Introduction to LangGraph

This repo is the official LangChain Academy course for LangGraph. It is organized into numbered modules (0–6), each containing Jupyter notebooks and a `studio/` subdirectory with LangGraph graphs and `langgraph.json` configs. The early modules teach PDF processing, chunking, embeddings, vector stores, and simple RAG pipelines; later modules layer on LangGraph concepts like stateful graphs, parallelization, subgraphs, memory, and deployment. This project is your primary reference for how the LangChain team currently recommends structuring LangGraph graphs, running LangGraph Studio locally, and wiring LangSmith tracing around real-world examples.

### `/Users/nenaddjordjevic/PythonProjects/lca-lc-foundations/` – LangChain Foundations (Python)

This course repo introduces core LangChain primitives in Python: models, tools, prompts, memory, evaluation, and LangSmith. It uses `uv` as the preferred project manager, a `.env`-driven configuration pattern, and notebooks grouped into modules that walk from basic LLM calls through tools, agents, and production-oriented patterns. It is especially useful as a reference for “vanilla” LangChain usage without LangGraph: how to structure environments, manage API keys, run notebooks, and integrate LangSmith tracing and Tavily into a LangChain codebase. When designing non-graph pieces of Oracle-RAG (e.g., configuration, env management), this repo shows the idiomatic LangChain way to do it.

### `/Users/nenaddjordjevic/PythonProjects/lca-langchainV1-essentials/` – LangChain v1 Essentials (Python & JS)

This repo is the companion to the LangChain V1 Essentials course, with both `python/` and `js/` directories. The Python side contains a sequence of notebooks (L1–L9) that cover fast agents, message abstractions, streaming, tools (including MCP tools), memory, structured output, dynamic prompts, and human-in-the-loop patterns. The JS side mirrors many of the same lessons for TypeScript users, including an MCP-enabled SQL agent and a LangGraph setup for Node. Together, these projects are your cross-language reference for how the LangChain team expects agents, tools, and RAG-like workflows to be built in the v1 API across Python and JS.

### `/Users/nenaddjordjevic/PythonProjects/lca-langgraph-essentials/` – LangGraph v1 Essentials

This repo focuses specifically on LangGraph v1 concepts in both Python and JS. The Python notebooks (L1–L6) walk through building nodes, edges, conditional routing, memory, interrupts, and a more complete email-agent workflow, while the JS `src/` directory contains TypeScript implementations of the same ideas with preview assets and example graphs. It is a practical catalog of LangGraph patterns—simple node graphs, parallel execution, conditional edges, memory management, and HITL—implemented in both ecosystems. When you later move Oracle-RAG toward LangGraph-based orchestration (Phase 3), this repo is your template for structuring `StateGraph`s, conditional flows, and Studio integration.

### `/Users/nenaddjordjevic/PythonProjects/oracle-rag/` – Oracle-RAG (Your Product)

This is your own RAG product: a LangChain-based PDF RAG system packaged as a Python library and MCP server. It implements PDF ingestion (via `pypdf`), chunking with heading-awareness and character offsets, Chroma-based vector storage, and a plain-Python `run_rag()` chain instrumented with LangSmith. On top of that, it exposes a FastMCP server with tools to add/remove/list/query PDFs, including richer metadata (upload timestamps, document size stats, section labels) and metadata-based filtering (by document, page range, and tag). The project is production-oriented: versioned with PyPI publishing, GitHub releases, tests across indexing/RAG/MCP, and editor-agnostic MCP configuration (Cursor, VS Code, JetBrains IDEs). This is the main codebase you are evolving and hardening based on patterns from the other learning repos.

### `/Users/nenaddjordjevic/PythonProjects/rag-from-scratch/` – RAG From Scratch (Notebooks)

This repo is a focused educational resource that walks through Retrieval-Augmented Generation from first principles via a set of Jupyter notebooks (`rag_from_scratch_1_to_4.ipynb`, `..._5_to_9.ipynb`, etc.). It emphasizes understanding core RAG components—indexing, retrieval, generation, and evaluation—without immediately relying on high-level LangChain abstractions. The notebooks accompany a YouTube playlist and are useful as a conceptual grounding: they show how to reason about RAG behavior, trade-offs (e.g., fine-tuning vs retrieval), and architecture before layering on LangChain or LangGraph. You can use this project as a sanity check or inspiration when considering new features for Oracle-RAG, especially around evaluation, retrieval strategies, and chunking behavior.

