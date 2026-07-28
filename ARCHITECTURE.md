# FactoryOps AI - System Architecture

## Overview

FactoryOps AI is a **multi-phase, role-based manufacturing assistant** built with:
- **LLM**: Google Gemini API via LangChain
- **Backend**: LangChain agent with tool calling
- **Frontend**: Streamlit multi-page UI
- **Persistence**: JSON files (tickets, chat history) + SQLite (memory, checkpointing)

**Current Level**: MVP (Level 1) + Tool Calling Infrastructure (Level 2)

---

## System Architecture

### Frontend Layer (Streamlit)
- **Main**: app.py (navigation, role selector)
- **Chat Page**: pages/1_💬_Chat.py (569 lines, message history, role-specific context)
- **Conversations**: pages/2_📊_Conversations.py (chat management)
- **Tickets**: pages/3_📋_Tickets.py (ticket viewer)

### Agent Engine (LangChain)
- **AgentEngine**: Role-based agents (operator, engineer, supervisor, plant_manager)
- **Memory**: 3-tier system
  - Session: ConversationMemory (50 messages, ephemeral)
  - Long-term: SqliteStore per-role (data/memory/long_term_memory_{role}.db)
  - State: SqliteSaver per-role (data/checkpoints/agent_state_{role}.db)
- **Model**: ChatGoogleGenerativeAI (Gemini API)
- **Tools**: 12 tools with Pydantic validation

### Guardrails Middleware
- **InputValidationMiddleware**: Length (2-2000 chars), dangerous pattern blocking
- **ToolInputValidationMiddleware**: machine_id, priority, description validation
- **OutputValidationMiddleware**: Response length, safe content check
- **Factory**: create_agent_with_middleware() applies all middleware at agent creation

### Data Persistence
- **Chat History**: chat_history/{role}/*.json
- **Maintenance Tickets**: data/maintenance_tickets.json (MCP)
- **Memory**: data/memory/long_term_memory_{role}.db (per-role)
- **Checkpoints**: data/checkpoints/agent_state_{role}.db (per-role)
- **Mock Data**: machines.json, error_codes.json, technicians.json

---

## Role-Based Customization

| Aspect | Operator | Engineer | Supervisor | Plant Manager |
|--------|----------|----------|------------|---------------|
| **Focus** | Safety, procedures | Diagnostics, repair | Shift coordination | Strategic KPIs |
| **Tool Set** | Status, errors | Diagnostics, plans | Summary, technicians | Analytics, trends |
| **Memory** | `long_term_memory_operator.db` | `long_term_memory_engineer.db` | `long_term_memory_supervisor.db` | `long_term_memory_plant_manager.db` |
| **Response Style** | Simple, actionable | Technical, detailed | Overview, metrics | Financial, strategic |

---

## Data Flow: Query → Response

```
User Input (Streamlit Chat)
    ↓
[InputValidationMiddleware] ← Guardrails check length, patterns
    ↓
AgentEngine.process_query()
    ├─ Retrieve session memory (ConversationMemory)
    ├─ Retrieve long-term memory (SqliteStore per-role)
    └─ Pass to LLM with system prompt
    ↓
ChatGoogleGenerativeAI (Gemini LLM)
    ├─ Decide: Invoke tool or just respond?
    └─ If tool call:
        ↓
    [Tool Execution]
        ├─ [ToolInputValidationMiddleware] ← Pydantic validation
        ├─ Execute tool (read machines.json, error_codes.json, etc.)
        └─ Return result
    ↓
[OutputValidationMiddleware] ← Guardrails check response quality
    ↓
Response to User (Streamlit)
    └─ Save to chat_history/{role}/{chat_id}.json
```

---

## Tools (12 Available)

All tools have Pydantic input schemas and are validated by ToolInputValidationMiddleware:

1. **check_machine_status(machine_id)** — Get current machine state
2. **lookup_error_code(error_code)** — Explain fault codes (E17, E23, etc.)
3. **request_approval(machine_id, description, priority)** — Trigger approval workflow
4. **create_maintenance_ticket(machine_id, description, priority)** — Create MCP ticket
5. **check_technician_availability(specialty)** — Find available staff
6. **generate_shift_summary(shift_id)** — End-of-shift report
7. **escalate_critical_failure(machine_id, reason)** — Alert supervisors
8. **search_knowledge_base(query)** — Search machine documentation
9. **get_machine_specs(machine_id)** — Retrieve machine details
10. **get_production_targets(machine_id)** — Production goals
11. **estimate_downtime(machine_id, issue)** — Calculate loss impact
12. **generate_maintenance_plan(machine_id)** — Recommend service schedule

---

## Memory Architecture

### Session Memory (ConversationMemory)
- **Scope**: Per-session, ephemeral
- **Capacity**: 50 messages
- **Lifetime**: Duration of Streamlit session
- **Use**: Recent context for LLM attention

### Long-Term Memory (SqliteStore)
- **Scope**: Per-role, permanent
- **Capacity**: Unlimited
- **Location**: `data/memory/long_term_memory_{role}.db`
- **Methods**:
  - `store_memory(key, value, tags)` → bool
  - `retrieve_memory(key)` → str | None
  - `search_memory(query)` → List[Dict]
- **Use**: Store facts, patterns, preferences across sessions

### State Checkpointing (SqliteSaver)
- **Scope**: Per-role, permanent
- **Capacity**: Full agent graph state
- **Location**: `data/checkpoints/agent_state_{role}.db`
- **Use**: Resume agent execution mid-conversation
- **Status**: Awaiting langgraph installation

---

## Key Implementation Details

### Guardrails Factory Pattern (src/guardrails_middleware_layer.py)

```python
agent = create_agent_with_middleware(
    model=ChatGoogleGenerativeAI(...),
    tools=tools,
    system_prompt="You are a manufacturing assistant",
    middleware=[
        InputValidationMiddleware(GuardrailsStrategy.BLOCK),
        ToolInputValidationMiddleware(GuardrailsStrategy.BLOCK),
        OutputValidationMiddleware(GuardrailsStrategy.BLOCK)
    ],
    checkpointer=checkpointer,      # Per-role state persistence
    store=store                     # Per-role long-term facts
)
```

**Applied at**: Agent creation time (not query-time)  
**Pattern**: Middleware stack intercepted via BaseCallbackHandler  
**Interception Points**: on_tool_start(), on_llm_end()

### Role-Scoped Memory Isolation

```python
operator_agent = AgentEngine('operator')
engineer_agent = AgentEngine('engineer')

# Each role has SEPARATE databases:
# operator: data/memory/long_term_memory_operator.db
# engineer: data/memory/long_term_memory_engineer.db

operator_agent.store_memory('key', 'value', ['tag'])
engineer_agent.retrieve_memory('key')  # Not found (different role)
```

### Chat Interface with Role Switching (pages/1_💬_Chat.py)

```
Sidebar: Role Selector
├─ Operator / Engineer / Supervisor / Plant Manager
├─ Creates AgentEngine(role) on role change
├─ Saves current chat to chat_history/{old_role}/
└─ Loads chat from chat_history/{new_role}/

Chat Area:
├─ Multiple chats per role
├─ Rename / Delete / Export
├─ Message history with timestamps
├─ Approval buttons for critical actions
└─ Saves automatically to JSON
```

---

## Files & Lines of Code

| File | Lines | Purpose |
|------|-------|---------|
| src/agent_engine.py | ~600 | AgentEngine class, memory, guardrails integration |
| pages/1_💬_Chat.py | 569 | Main Streamlit chat interface |
| src/guardrails_middleware_layer.py | 288 | Middleware definitions + factory |
| src/tools.py | ~400 | 12 tools with Pydantic validation |
| src/mcp_ticket_server.py | ~200 | Ticket persistence via MCP |
| pages/2_📊_Conversations.py | ~150 | Chat management UI |
| pages/3_📋_Tickets.py | ~100 | Ticket viewer |
| app.py | 25 | Main entry point |

---

## Testing Strategy

**Unit Tests**:
- Tool Pydantic schemas block invalid inputs
- Memory isolation per role (separate .db files)
- Guardrails block dangerous patterns

**Integration Tests**:
- End-to-end: user query → LLM → tool → response
- Chat history persistence and loading
- Role switching preserves separate histories

**Manual Testing**:
- Run Streamlit app
- Switch roles, verify separate chat histories
- Ask questions, verify role-appropriate responses
- Create tickets, verify JSON persistence

---

## Dependencies

**Required**:
- langchain==0.2.8
- langchain-google-genai==4.3.2
- google-generativeai==0.5.4
- streamlit==1.35.0
- pydantic==2.7.1

**Optional (not installed yet)**:
- langgraph — For checkpointing and graph execution
- sqlalchemy — For future database ORM
- fastapi — For future REST API

---

## Status & Next Steps

**✅ Implemented**:
- Level 1: Conversational assistant with role-based responses
- Tool definitions and Pydantic validation
- Guardrails middleware factory pattern
- Role-scoped memory architecture
- Streamlit multi-page UI with chat management

**🔄 In Progress**:
- Level 2: Validate tool calling works end-to-end
- Approval workflow integration

**📋 Planned**:
- Level 3: Multi-agent orchestration
- Level 4: FastAPI backend, PostgreSQL, Docker deployment

---

**Architecture Version**: 1.0  
**Last Updated**: 2026-07-28  
**Current Status**: MVP Complete (Level 1), Level 2 Infrastructure Ready
