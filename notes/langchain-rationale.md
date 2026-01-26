# Rationale: Using LangChain for Oracle-RAG

## Overview

LangChain provides a straightforward, chain-based approach to building RAG applications. It's ideal for linear, predictable workflows where data flows sequentially through well-defined steps.

## Why LangChain for PDF RAG?

### ✅ Advantages

1. **Simplicity & Clarity**
   - Linear chain structure: `retriever → formatter → prompt → LLM → output`
   - Easy to understand and debug
   - Minimal boilerplate code
   - Perfect for straightforward RAG: retrieve documents, format context, generate answer

2. **Mature RAG Patterns**
   - Well-established patterns for RAG applications
   - Extensive documentation and examples
   - `RunnablePassthrough` and `RunnableSequence` make chaining intuitive
   - Built-in support for document retrieval and formatting

3. **Lower Complexity**
   - No need to define state schemas
   - No graph structure to design
   - Faster to prototype and iterate
   - Less cognitive overhead for simple use cases

4. **Sufficient for Basic PDF RAG**
   - PDF RAG typically follows: load → chunk → embed → retrieve → generate
   - This is a linear flow that chains handle perfectly
   - No complex routing or state management needed initially

5. **Easier MCP Integration**
   - Simpler to wrap a chain as an MCP tool
   - Chain execution is straightforward: input → output
   - Less state to manage when exposing via MCP

### ❌ Limitations

1. **Limited Control Flow**
   - Hard to add conditional logic (e.g., "if retrieval fails, try different strategy")
   - No easy way to loop or retry
   - Difficult to branch based on query type

2. **State Management**
   - No built-in state persistence between steps
   - Harder to track conversation history
   - Limited ability to modify flow based on intermediate results

3. **Complex Workflows**
   - If we later need multi-step reasoning, tool calling, or agent behavior, chains become cumbersome
   - Hard to add parallel processing or conditional routing

## Example Pattern

```python
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)
```

## When to Choose LangChain

- ✅ Building a simple PDF RAG: query → retrieve → answer
- ✅ No need for complex routing or state management
- ✅ Want to get started quickly
- ✅ Linear workflow is sufficient
- ✅ Planning to wrap as a simple MCP tool (input → output)

## Decision Criteria for Oracle-RAG

**Choose LangChain if:**
- We want to start simple and iterate
- The PDF RAG workflow is straightforward: load PDFs, query, get answers
- We don't need complex routing or multi-step reasoning
- We want faster initial development
- MCP integration should be simple (single tool: query → answer)
