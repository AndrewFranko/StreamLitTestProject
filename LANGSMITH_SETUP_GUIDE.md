# LangSmith + LangGraph Proper Setup Guide

## Problem Identified
- Custom `AgentEngine` class does NOT send traces to LangSmith automatically
- Only LangChain runnables (chat models, tools, chains) create automatic traces
- Setting env vars alone is NOT enough - code must use LangChain's instrumented classes

## Solution: Use LangChain Directly

### Environment Setup (Already Done ✓)
```
LANGCHAIN_TRACING_V2=true
LANGSMITH_API_KEY=lsv2_pt_...
LANGSMITH_PROJECT=Factory
LANGSMITH_ENDPOINT=https://eu.api.smith.langchain.com
```

### Code Changes Required

Instead of:
```python
from agent_engine import AgentEngine
agent = AgentEngine('operator')
result = agent.process_query(prompt)
```

Use:
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)
prompt = ChatPromptTemplate.from_template("...")
chain = prompt | llm

result = chain.invoke({"input": "..."})
```

## Why This Works

1. `ChatGoogleGenerativeAI` is a LangChain Runnable
2. When `LANGCHAIN_TRACING_V2=true`, LangChain automatically creates traces
3. Traces appear in LangSmith immediately after execution
4. No manual `@traceable` needed
5. Works inside LangGraph nodes

## Implementation Steps

1. Replace AgentEngine with ChatGoogleGenerativeAI in all 3 agents
2. Use ChatPromptTemplate for prompts
3. Keep LangGraph structure (StateGraph, nodes, edges)
4. Traces will appear automatically

Sources:
- https://docs.langchain.com/langsmith/trace-with-langgraph
- https://medium.com/ravjot03/langsmith-for-agent-observability-tracing-langgraph-tool-calling-end-to-end-2a97d0024dfb
