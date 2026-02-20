# LangSmith Integration Guide

LangSmith provides observability, debugging, and monitoring for your RAG chain. It works **automatically** with LCEL chains - no code changes needed!

## Quick Setup

### 1. Get Your LangSmith API Key

1. Sign up at https://smith.langchain.com (free tier available)
2. Go to Settings → API Keys
3. Create a new API key
4. Copy the key

### 2. Configure Environment Variables

Add these to your `.env` file:

```bash
# LangSmith tracing
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://eu.api.smith.langchain.com
LANGSMITH_API_KEY=your-api-key-here
LANGSMITH_PROJECT=oracle-rag
```

> **Important**: The `LANGSMITH_ENDPOINT` must match your LangSmith data region.
> - **US Central** (default): `https://api.smith.langchain.com` (can be omitted)
> - **EU West**: `https://eu.api.smith.langchain.com` (must be set explicitly)
>
> You can see your region in the LangSmith URL: `eu.smith.langchain.com` = EU, `smith.langchain.com` = US.

**Alternative variable names** (also supported):
- `LANGCHAIN_API_KEY` (instead of `LANGSMITH_API_KEY`)
- `LANGCHAIN_TRACING_V2=true` (instead of `LANGSMITH_TRACING=true`)

### 3. That's It!

Your LCEL chain will automatically send traces to LangSmith. No code changes needed!

## What You'll See in LangSmith

When you run `rag_cli.py`, LangSmith will automatically capture:

1. **Full Chain Execution**
   - Input query
   - Retrieval step (documents fetched)
   - Context formatting
   - LLM invocation (prompt, response)
   - Source formatting

2. **Timing Information**
   - How long each step takes
   - Total chain execution time

3. **Inputs/Outputs**
   - Query text
   - Retrieved documents
   - Formatted context
   - LLM prompt and response
   - Final answer and sources

4. **Metadata**
   - Model used
   - Token counts
   - Cost estimates

## Viewing Traces

1. Go to your LangSmith dashboard (US: https://smith.langchain.com, EU: https://eu.smith.langchain.com)
2. Navigate to "Tracing" in the left sidebar
3. Select your project (`oracle-rag`)
4. Click on any trace to see the full execution flow

## Advanced Configuration

### Custom Project Names

You can organize traces by environment:

```bash
# Development
LANGSMITH_PROJECT=oracle-rag-dev

# Production
LANGSMITH_PROJECT=oracle-rag-prod

# Testing
LANGSMITH_PROJECT=oracle-rag-test
```

### Disable Tracing Temporarily

Set `LANGSMITH_TRACING=false` or remove the variable to disable tracing without removing the API key.

### Programmatic Configuration (Alternative)

If you prefer not to use environment variables, you can configure tracing in code:

```python
from langsmith import traceable

@traceable(name="rag_chain")
def get_rag_chain(...):
    # Your chain code
    pass
```

However, environment variables are simpler and work automatically with LCEL.

## Benefits for Your RAG System

1. **Debugging**: See exactly what documents were retrieved and why
2. **Performance**: Identify bottlenecks (slow retrieval, LLM calls)
3. **Quality**: Review LLM responses and improve prompts
4. **Cost Tracking**: Monitor API usage and costs
5. **Evaluation**: Compare different queries and chain configurations

## Example Trace Structure

When you run a query, LangSmith captures:

```
Trace: RAG Chain Execution
├── Input: {"query": "What is...", "k": 5}
├── Run: retrieve (RunnablePassthrough.assign)
│   └── Output: [Document(...), Document(...), ...]
├── Run: format_docs (RunnablePassthrough.assign)
│   └── Output: "[1] (doc: file.pdf, p. 1)\n..."
├── Run: LLM Call (RAG_PROMPT | llm | StrOutputParser)
│   ├── Input: System + Human messages
│   ├── Model: gpt-4o-mini
│   ├── Tokens: 150 input, 200 output
│   └── Output: "Based on the context..."
└── Run: format_sources (RunnableLambda)
    └── Output: [{"document_id": "...", "page": 1}, ...]
```

## Troubleshooting

**403 Forbidden errors?**
- **Most common cause**: Wrong API endpoint for your region. If your LangSmith URL starts with `eu.smith.langchain.com`, you **must** set `LANGSMITH_ENDPOINT=https://eu.api.smith.langchain.com`
- If using an org-scoped API key with multiple workspaces, set `LANGSMITH_WORKSPACE_ID`
- Ensure the `.env` does NOT use `export` prefix (correct: `KEY=value`, wrong: `export KEY=value`)

**No traces appearing?**
- Check `LANGSMITH_API_KEY` is set correctly
- Verify `LANGSMITH_TRACING=true`
- Ensure you're loading `.env` with `load_dotenv()`

**Traces work from CLI but not when calling MCP tools (e.g. add_pdf_tool)?**
- MCP tools run in the **MCP server process**. That process must have LangSmith env vars set.
- **Option A (implemented)**: The MCP entrypoint (`scripts/mcp_server.py`) loads `.env` from the **project root** (directory containing `pyproject.toml`), so it does not depend on process cwd. Add the LangSmith vars to your project's `.env` (see step 2 above); then restart the MCP server (or Cursor). Traces from tool calls should then appear in LangSmith.
- **Alternative**: To avoid using project `.env`, set `LANGSMITH_TRACING`, `LANGSMITH_API_KEY`, and `LANGSMITH_PROJECT` in Cursor's MCP server env for Oracle-RAG.
- Tool calls are wrapped with LangSmith's `@traceable` (`add_pdf`, `query_pdf`), so you'll see a top-level run per tool call when tracing is on.

**Wrong project name?**
- Set `LANGSMITH_PROJECT` explicitly
- Or create the project manually in LangSmith UI

**Performance impact?**
- LangSmith tracing is async and non-blocking
- Minimal performance overhead (< 10ms typically)

## References

- LangSmith Docs: https://docs.langchain.com/langsmith/
- Observability Guide: https://docs.langchain.com/langsmith/observability-concepts
- API Reference: https://api.smith.langchain.com/
