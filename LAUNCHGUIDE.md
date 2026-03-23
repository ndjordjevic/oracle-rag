# PinRAG

## Tagline
MCP RAG server: index PDFs, GitHub Repos, YouTube, Discord, Plain Text; query with citations.

## Description
PinRAG is a retrieval-augmented generation (RAG) MCP server built with LangChain and Chroma. Index PDFs, plain text, Discord exports, YouTube transcripts, and GitHub repositories, then ask questions in Cursor, VS Code (Copilot), or any MCP-capable client. Answers include citations (pages, timestamps, paths). Install via PyPI (`pipx`, `uv tool`, or `uvx --from pinrag pinrag-mcp`). Configure API keys in your editor’s MCP `env` block.

## Setup Requirements

`pinrag-mcp` validates API keys at startup (`require_api_keys_for_server`): it requires a non-empty key for the **embedding** provider (`PINRAG_EMBEDDING_PROVIDER`, default `openai`) and for the **LLM** provider (`PINRAG_LLM_PROVIDER`, default `anthropic`).

**Required — default stack (OpenAI embeddings + Anthropic chat):** set both keys in MCP `env`.
- `OPENAI_API_KEY` — [OpenAI API keys](https://platform.openai.com/api-keys)
- `ANTHROPIC_API_KEY` — [Anthropic console](https://console.anthropic.com/)

**Required — other combinations:** If `PINRAG_LLM_PROVIDER=openai`, only `OPENAI_API_KEY` is needed for both chat and default OpenAI embeddings. If `PINRAG_EMBEDDING_PROVIDER=cohere`, set `COHERE_API_KEY` — [Cohere API keys](https://dashboard.cohere.com/api-keys). The chat key must match `PINRAG_LLM_PROVIDER` (`ANTHROPIC_API_KEY` or `OPENAI_API_KEY`).

**Optional:**
- `PINRAG_PERSIST_DIR` — Absolute path to the Chroma data directory (default: `chroma_db` next to the process cwd; a stable path is recommended)
- `PINRAG_LLM_PROVIDER` — `anthropic` (default) or `openai`
- `PINRAG_EMBEDDING_PROVIDER` — `openai` (default) or `cohere`
- `GITHUB_TOKEN` — Private repos or higher GitHub API rate limits when indexing — [GitHub tokens](https://github.com/settings/tokens)

## Category
Developer Tools

## Use Cases
Coding assistants, documentation Q&A, research, onboarding, technical support, content analysis

## Features
- Index PDFs, directories, plain text, Discord exports, YouTube (URL/playlist/ID), GitHub repos
- Query with source citations and optional metadata filters (tags, doc type, page range, paths)
- MCP tools: add documents, add URL, query, list, remove
- MCP resources and `use_pinrag` prompt for guided workflows
- Configurable LLM (Anthropic/OpenAI) and embeddings (OpenAI/Cohere)

## Getting Started
- "Index the PDFs in ./docs and summarize the deployment steps."
- "What does this repo say about authentication?" (after indexing a GitHub URL)
- Tool: `query_tool` — Ask questions over indexed documents with citations
- Tool: `add_document_tool` — Index files, folders, or supported URLs
- Tool: `list_documents_tool` — See what is indexed

## Tags
rag, mcp, langchain, chromadb, pdf, github, youtube, embeddings, anthropic, openai, cursor, vscode, retrieval, citations

## Documentation URL
https://github.com/ndjordjevic/pinrag#readme

## Health Check URL
Not applicable — stdio MCP (local `uvx` / `pipx`); no hosted HTTP endpoint.
