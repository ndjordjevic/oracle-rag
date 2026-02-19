# MCP Server Implementation Research

## What is MCP?

**Model Context Protocol (MCP)** is a standardized protocol that allows applications to provide context to LLMs in a consistent way. It separates the concerns of providing context from the actual LLM interaction.

### Key Concepts

MCP servers expose three main primitives:

1. **Tools**: Functions that LLMs can call (like `query_pdf`, `add_pdf`)
2. **Resources**: File-like data (e.g., document metadata, chunk information)
3. **Prompts**: Pre-written templates for specific tasks

### Why MCP for Oracle-RAG?

- **Standardized Interface**: Makes oracle-rag accessible to any MCP-compatible client (Claude Desktop, Cursor, custom apps)
- **Tool Integration**: LLMs can directly call `query_pdf` and `add_pdf` as tools
- **Separation of Concerns**: RAG logic stays in `oracle_rag` package, MCP server is a thin wrapper
- **Future Extensibility**: Easy to add more tools/resources/prompts

## Language Choice: Python vs Other Options

### Available MCP SDKs

The Model Context Protocol provides official SDKs for multiple languages:

| Language | SDK Status | Best For |
|----------|-----------|----------|
| **TypeScript/JavaScript** | Primary, most mature | Node.js ecosystems, web integrations |
| **Python** | Official, well-maintained | ML/AI projects, LangChain integration |
| **Java** | Official | Enterprise Java applications |
| **C#** | Official | .NET ecosystems |
| **Go** | Official | High-performance, concurrent systems |
| **Rust** | Official | Systems programming, performance-critical |
| **Swift** | Official | macOS/iOS applications |
| **Kotlin** | Official | Android, JVM-based projects |
| **Ruby** | Official | Ruby/Rails ecosystems |
| **PHP** | Official | Web applications |

### Why Python for Oracle-RAG?

**✅ Chosen: Python SDK** (`mcp` package)

**Reasons:**

1. **Existing Codebase**: Oracle-RAG is 100% Python:
   - LangChain (Python-native)
   - ChromaDB (Python client)
   - All existing code (`oracle_rag` package) is Python
   - No language boundary overhead

2. **Direct Integration**: 
   - Can directly import and call `get_rag_chain()`, `index_pdf()` without wrappers
   - Same type system, same error handling patterns
   - Shared dependencies (LangChain, OpenAI SDK)

3. **Ecosystem Alignment**:
   - LangChain has excellent Python support
   - Python is the standard for ML/AI tooling
   - Most RAG examples and tutorials are Python

4. **Development Experience**:
   - FastMCP provides simple decorator-based API
   - Python's dynamic typing makes tool definitions straightforward
   - Easy testing with pytest (already in project)

5. **Deployment**:
   - Single runtime environment
   - No need for Node.js or other runtimes
   - Simpler Docker/containerization

### Alternative: TypeScript/JavaScript

**If we were starting fresh or had a JS/TS codebase:**

**Pros:**
- Most mature SDK with comprehensive docs
- Strong type safety with Zod schemas
- Excellent for web/Node.js integrations
- Large community and examples

**Cons:**
- Would require rewriting RAG logic or creating Python→Node bridge
- Additional runtime dependency (Node.js)
- More complex deployment (two languages)
- No direct access to Python LangChain APIs

**Verdict**: Not suitable for Oracle-RAG since the entire codebase is Python.

### Other Languages

**Java/C#/Go/Rust/etc.**: Only relevant if:
- Building a polyglot microservices architecture
- Need specific language features (e.g., Go's concurrency, Rust's safety)
- Integrating with existing codebases in those languages

**For Oracle-RAG**: Python is the clear choice given the existing codebase.

## Implementation Approach

### Option 1: FastMCP (Recommended for MVP)

**FastMCP** is a high-level abstraction that uses decorators:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Oracle-RAG", json_response=True)

@mcp.tool()
def query_pdf(query: str, k: int = 5) -> dict:
    """Query indexed PDFs and return answer with citations"""
    # Call existing get_rag_chain()
    pass

@mcp.tool()
def add_pdf(pdf_path: str) -> dict:
    """Add a PDF to the index"""
    # Call existing index_pdf()
    pass
```

**Pros:**
- Simple, declarative syntax
- Minimal boilerplate
- Good for MVP

**Cons:**
- Less control over error handling
- Less flexibility for advanced features

### Option 2: Low-Level MCP Server API

More control but more boilerplate:

```python
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("Oracle-RAG")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="query_pdf",
            description="Query indexed PDFs",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "k": {"type": "integer", "default": 5}
                }
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "query_pdf":
        # Implementation
        pass
```

**Pros:**
- Full control over behavior
- Better for complex error handling
- More flexibility

**Cons:**
- More boilerplate
- Async/await complexity
- Overkill for MVP

## Recommended Structure

```
oracle-rag/
├── src/
│   └── oracle_rag/
│       └── mcp/                    # New module
│           ├── __init__.py
│           ├── server.py           # FastMCP server definition
│           └── tools.py            # Tool implementations (wrappers)
├── scripts/
│   └── mcp_server.py               # Entry point: `uv run scripts/mcp_server.py`
└── tests/
    └── test_mcp_server.py          # MCP server tests
```

## Tools to Implement

### 1. `query_pdf` Tool

**Purpose**: Query all indexed PDFs and return an answer with citations

**Parameters**:
- `query` (str, required): Natural language question
- `k` (int, optional, default=5): Number of chunks to retrieve
- `persist_dir` (str, optional, default="chroma_db"): Chroma persistence directory
- `collection` (str, optional, default="oracle_rag"): Collection name

**Returns**:
```json
{
  "answer": "The answer text...",
  "sources": [
    {"document_id": "doc1.pdf", "page": 5},
    {"document_id": "doc2.pdf", "page": 12}
  ]
}
```

**Implementation**: Wraps `get_rag_chain()` from `oracle_rag.rag`

### 2. `add_pdf` Tool

**Purpose**: Index a new PDF into the vector store

**Parameters**:
- `pdf_path` (str, required): Path to PDF file
- `persist_dir` (str, optional, default="chroma_db"): Chroma persistence directory
- `collection` (str, optional, default="oracle_rag"): Collection name

**Returns**:
```json
{
  "source_path": "/path/to/file.pdf",
  "total_pages": 42,
  "total_chunks": 156,
  "persist_directory": "chroma_db",
  "collection_name": "oracle_rag"
}
```

**Implementation**: Wraps `index_pdf()` from `oracle_rag.indexing`

## Testing Strategy

### 1. Unit Tests (`tests/test_mcp_server.py`)

- Test tool registration
- Test tool parameter validation
- Mock underlying RAG/indexing functions
- Test error handling

### 2. Integration Testing with MCP Inspector

The MCP Inspector is a testing tool:

```bash
# Install inspector
npx -y @modelcontextprotocol/inspector

# Run oracle-rag MCP server
uv run scripts/mcp_server.py

# In another terminal, connect inspector to server
# Inspector will show available tools and allow testing
```

### 3. Manual Testing

- Test with Cursor's MCP integration (if configured)
- Test with Claude Desktop (if available)
- Verify LangSmith traces still work

## Dependencies

Add to `requirements.txt` or `pyproject.toml`:

```
mcp>=1.26.0  # Requires Python 3.10+
```

## Configuration

MCP server should read from `.env`:
- `OPENAI_API_KEY` (required)
- `LANGSMITH_*` variables (optional, for tracing)
- Default `persist_dir` and `collection` can be configurable

## Transport Options

### stdio (Recommended for MVP)

- Simple, works with most MCP clients
- Server reads from stdin, writes to stdout
- Use stderr for logging

```python
if __name__ == "__main__":
    mcp.run(transport="stdio")
```

### Streamable HTTP (For testing)

- Useful for MCP Inspector
- Runs on `http://localhost:8000/mcp`

```python
if __name__ == "__main__":
    mcp.run(transport="streamable-http")
```

## Error Handling

MCP tools should:
- Validate inputs (file paths exist, query not empty)
- Catch exceptions from underlying functions
- Return structured error messages
- Log errors to stderr (not stdout, to avoid corrupting JSON-RPC)

## Future Enhancements (Phase 2)

- **Resources**: Expose document metadata, chunk information
- **Prompts**: Pre-built prompts for common query types
- **Additional Tools**: `remove_pdf`, `list_pdfs`, `query_specific_pdf`
- **Streaming**: Support streaming responses for long queries

## References

- [MCP Python SDK Docs](https://modelcontextprotocol.github.io/python-sdk/)
- [MCP Specification](https://modelcontextprotocol.io/)
- [FastMCP Guide](https://modelcontextprotocol.github.io/python-sdk/fastmcp/)
- [MCP Inspector](https://github.com/modelcontextprotocol/inspector)
