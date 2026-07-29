# LangSmith Integration Guide

## Overview
LangSmith is Anthropic's platform for debugging, testing, and monitoring LLM applications. This integration enables visualization of:
- RAG pipeline searches
- LangGraph multi-agent workflows
- Tool invocations and responses
- Token usage and performance metrics

## Setup Steps

### 1. Create LangSmith Account
1. Go to https://smith.langchain.com
2. Sign up for a free account
3. Create a new organization/project

### 2. Get API Key
1. Go to Settings → API Keys
2. Create new API key
3. Copy the key

### 3. Configure Environment

Create/update `.env` file in project root:

```ini
LANGSMITH_API_KEY=<your_api_key_here>
LANGSMITH_PROJECT=<your_project_name>
LANGCHAIN_TRACING_V2=true
```

### 4. Verify Integration

The application will automatically:
- Trace RAG pipeline queries
- Record LangGraph agent executions
- Log all tool calls
- Track token usage

All traces appear in LangSmith Studio dashboard.

## What Gets Traced

### RAG Pipeline
- Ticket description queries
- Vector similarity searches
- Retrieved similar tickets
- Latency and scores

### Level 3 Workflow (LangGraph)
- Fault Analysis Agent execution
- Maintenance Diagnosis Agent operations
- Maintenance Request Agent processing
- State transitions between agents
- Tool calls and outputs

### MCP Ticket Server
- Ticket creation requests
- Search operations
- Update/delete actions

## LangSmith Studio Dashboard

Access at: https://smith.langchain.com/studio

View:
- **Traces**: Complete execution logs
- **Metrics**: Latency, token usage, success rates
- **Runs**: Individual trace details
- **Projects**: Organized by project name

## Example Flow

```
User creates ticket
    ↓
[Trace] MCP create_ticket called
    ├─ [Trace] RAG find_similar_tickets
    │  ├─ Embed query
    │  ├─ Search FAISS index
    │  └─ Return 3 similar tickets
    └─ [Trace] Save ticket to JSON
    
All steps visible in LangSmith Studio
```

## Debugging Tips

1. **Check Traces**: View exact inputs/outputs of each component
2. **Performance**: Identify bottlenecks (RAG search vs LLM vs I/O)
3. **Errors**: Detailed stack traces for failures
4. **Comparison**: Compare different runs and optimizations

## Disable Tracing

To disable LangSmith tracing, remove from `.env` or set:
```ini
LANGCHAIN_TRACING_V2=false
```

## Documentation
- LangSmith Docs: https://docs.smith.langchain.com
- LangChain Tracing: https://python.langchain.com/docs/langsmith/
