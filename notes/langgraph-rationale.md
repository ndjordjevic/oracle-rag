# Rationale: Using LangGraph for Oracle-RAG

## Overview

LangGraph provides a graph-based approach to building AI applications with explicit state management, conditional routing, and complex control flow. It's ideal for applications that need more than simple linear processing.

## Why LangGraph for PDF RAG?

### ✅ Advantages

1. **Explicit State Management**
   - Clear state schema definition
   - Easy to track conversation history, retrieved documents, intermediate results
   - State persists across nodes, enabling complex workflows
   - Perfect for maintaining context across multiple queries

2. **Flexible Control Flow**
   - Conditional edges: route based on query type, retrieval quality, or user intent
   - Easy to add retry logic: "if retrieval quality is low, try different strategy"
   - Support for loops and iterative refinement
   - Can branch: "if question is about code, use code-specific retrieval"

3. **Complex Workflow Support**
   - Multi-step reasoning: retrieve → evaluate → refine → retrieve again
   - Parallel processing: retrieve from multiple sources simultaneously
   - Human-in-the-loop: pause for feedback before final answer
   - Agent-like behavior: tool calling, decision making

4. **Better for Advanced Features**
   - Easy to add query classification (factual vs. analytical)
   - Can implement retrieval quality checks and fallbacks
   - Support for multi-document synthesis
   - Enables iterative refinement of answers

5. **Future-Proof Architecture**
   - Easy to extend with new nodes (e.g., re-ranking, summarization)
   - Can add sub-graphs for complex operations
   - Supports streaming and interruption
   - Better foundation for agent capabilities later

6. **MCP Server Advantages**
   - Can expose multiple tools (query, refine, stream)
   - Better state management for conversation history
   - Can implement more sophisticated MCP patterns

### ❌ Limitations

1. **Higher Complexity**
   - Need to design graph structure and state schema
   - More boilerplate code initially
   - Steeper learning curve
   - More concepts to understand (nodes, edges, state)

2. **Overkill for Simple Use Cases**
   - If we only need linear RAG, graph structure adds unnecessary complexity
   - More setup time for basic functionality
   - Harder to debug initially

3. **More Abstraction**
   - State management can be confusing at first
   - Need to understand graph execution model
   - More moving parts to maintain

## Example Pattern

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

class RAGState(TypedDict):
    question: str
    documents: list
    answer: str
    retrieval_quality: float

def retrieve_node(state: RAGState):
    # Retrieve documents
    docs = retriever.invoke(state["question"])
    return {"documents": docs}

def generate_node(state: RAGState):
    # Generate answer
    answer = llm.invoke(format_prompt(state["question"], state["documents"]))
    return {"answer": answer}

def should_refine(state: RAGState) -> str:
    # Conditional routing
    if state["retrieval_quality"] < 0.7:
        return "retry_retrieval"
    return "end"

graph = StateGraph(RAGState)
graph.add_node("retrieve", retrieve_node)
graph.add_node("generate", generate_node)
graph.add_conditional_edges("retrieve", should_refine)
graph.add_edge("generate", END)
```

## When to Choose LangGraph

- ✅ Need conditional logic or routing
- ✅ Want to implement advanced RAG features (re-ranking, multi-step, refinement)
- ✅ Planning to add agent-like capabilities
- ✅ Need state persistence across queries
- ✅ Want to support streaming, interruption, or human feedback
- ✅ Building for extensibility and future features

## Decision Criteria for Oracle-RAG

**Choose LangGraph if:**
- We want to build a more sophisticated PDF RAG system
- We plan to add features like query classification, retrieval quality checks, or answer refinement
- We want better state management for conversation history
- We're building for the long term and want extensibility
- We want to expose multiple MCP tools with different capabilities
- We might add agent-like behavior later (e.g., "search web if PDF doesn't have answer")
