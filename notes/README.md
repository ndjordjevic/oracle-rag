# Notes

This directory contains documentation about the learning process, design decisions, and implementation details for Oracle-RAG.

## Overview

These notes document:
- **Design decisions** and rationale for technology choices
- **Implementation challenges** and solutions
- **Key learnings** from LangChain, LangGraph, and MCP
- **Architecture choices** and trade-offs
- **Setup guides** for development tools
- **Research** and evaluation processes

## Documentation Index

### Planning & Decision Documents

- **[implementation-checklist.md](implementation-checklist.md)** - Master implementation checklist tracking all phases (MVP → Enhanced → Advanced → Production)
- **[requirements-checklist.md](requirements-checklist.md)** - Requirements tracking aligned with implementation phases
- **[langchain-rationale.md](langchain-rationale.md)** - Why LangChain was chosen for Phase 1 MVP
- **[langgraph-rationale.md](langgraph-rationale.md)** - LangGraph evaluation and future migration plans

### Technology Decisions

- **[vector-database-decision.md](vector-database-decision.md)** - Vector database selection (Chroma chosen)
- **[embedding-provider-decision.md](embedding-provider-decision.md)** - Embedding model selection (OpenAI API)
- **[pdf-parsing-library-analysis.md](pdf-parsing-library-analysis.md)** - PDF library evaluation (pypdf chosen)
- **[package-manager-decision.md](package-manager-decision.md)** - Package manager choice (uv)

### Implementation Guides

- **[langsmith-setup.md](langsmith-setup.md)** - LangSmith observability setup and troubleshooting
- **[mcp-server-research.md](mcp-server-research.md)** - MCP server implementation research and patterns
- **[langchain-features-used.md](langchain-features-used.md)** - LangChain features actively used in the project

## Quick Navigation

**Getting Started:**
1. Read [implementation-checklist.md](implementation-checklist.md) to understand project phases
2. Review [langsmith-setup.md](langsmith-setup.md) for observability setup
3. Check [mcp-server-research.md](mcp-server-research.md) for MCP integration details

**Understanding Decisions:**
- See decision documents for rationale behind technology choices
- Review rationale documents for framework selection reasoning

**Implementation:**
- Follow checklists for step-by-step implementation tracking
- Reference feature documentation for LangChain usage patterns

## Contributing

When adding new notes:
- Use descriptive filenames (e.g., `feature-name.md`, `decision-topic.md`)
- Link to related documents for cross-referencing
- Update this README when adding significant documentation
- Keep decision documents focused on rationale and trade-offs
