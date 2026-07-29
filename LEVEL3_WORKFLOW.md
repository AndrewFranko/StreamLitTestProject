# Level 3: Simplified Multi-Agent Architecture with LangGraph

**Status**: ✅ Fully Functional  
**Implementation**: 3-Agent Sequential Workflow  
**Data**: Machine & Error Code Lookup  
**Output**: Maintenance Ticket Creation

---

## Architecture Overview

### Three-Agent Workflow

```
User Input
    ↓
[Agent 1: Fault Analysis]
    → Extract: machine_id, error_code, request_type
    ↓
[Agent 2: Maintenance Diagnosis]
    → Tool: search_machine(machine_id)
    → Tool: lookup_error_code(error_code)
    → Output: severity, root_cause, recommended_action
    ↓
[Agent 3: Maintenance Request]
    → Tool: create_maintenance_ticket(...)
    → Output: Ticket ID, Confirmation
    ↓
Maintenance Ticket Created
```

### Workflow State (LangGraph)

```python
WorkflowState = TypedDict({
    "user_input": str,                  # Input query
    "fault_analysis": dict,             # Agent 1 output
    "diagnosis": dict,                  # Agent 2 output
    "ticket_created": bool,             # Success flag
    "ticket_id": str,                   # Generated ticket ID
    "final_response": str,              # User-facing response
    "error": str                        # Error message if failed
})
```

---

## Agent Details

### Agent 1: Fault Analysis Agent

**Responsibility**: Extract structured information from natural language

**Extracts**:
- `machine_id`: Machine identifier (e.g., "MX-204")
- `error_code`: Error code (e.g., "E17")
- `request_type`: Action requested (e.g., "Maintenance Request")
- `missing_fields`: Required fields not provided

**Output Structure**:
```json
{
  "machine_id": "MX-204",
  "error_code": "E17",
  "request_type": "Maintenance Request",
  "missing_fields": []
}
```

**Example Input**:
```
"Machine MX-204 stopped with error code E17. Check the issue and create a maintenance request."
```

**Implementation**: Uses AgentEngine LLM with JSON extraction prompt

---

### Agent 2: Maintenance Diagnosis Agent

**Responsibility**: Analyze machine & error data, determine severity & recommended action

**Tools**:
- `search_machine(machine_id)` → Returns machine details from data/machines.json
- `lookup_error_code(error_code)` → Returns error details from data/error_codes.json

**Output Structure**:
```json
{
  "machine_details": {
    "id": "MX-204",
    "name": "Hydraulic Press B",
    "type": "Hydraulic Press",
    "location": "Plant 1 - Bay B",
    "status": "error",
    "temperature": 85,
    "runtime_hours": 8920,
    "last_maintenance": "2026-06-20",
    "maintenance_interval_days": 30
  },
  "error_details": {
    "code": "E17",
    "severity": "high",
    "description": "Hydraulic pressure loss in main cylinder",
    "symptom": "Machine unable to generate full clamping force",
    "recommended_action": "Inspect hydraulic lines, check pump pressure, possible seal replacement"
  },
  "severity": "high",
  "root_cause": "Pump seal leak",
  "recommended_action": "Inspect hydraulic lines, check pump pressure, possible seal replacement"
}
```

**Logic**:
1. Search machines.json for machine_id
2. Search error_codes.json for error_code
3. Extract severity from error details
4. Combine into diagnostic report

---

### Agent 3: Maintenance Request Agent

**Responsibility**: Create maintenance ticket and present confirmation

**Tool**:
- `create_maintenance_ticket(machine_id, error_code, description, severity)` → Appends to data/maintenance_tickets.json

**Output Structure**:
```
Maintenance Request Created Successfully
========================================
Ticket ID: TICK-20260728144422
Machine: MX-204
Error Code: E17
Severity: high
Recommended Action: Inspect hydraulic lines, check pump pressure, possible seal replacement
Status: Open
```

**Ticket Structure** (saved to JSON):
```json
{
  "ticket_id": "TICK-20260728144422",
  "machine_id": "MX-204",
  "machine_name": "Hydraulic Press B",
  "error_code": "E17",
  "description": "Inspect hydraulic lines, check pump pressure, possible seal replacement",
  "severity": "high",
  "status": "open",
  "created_at": "2026-07-28T14:44:22.123456",
  "assigned_technician": null
}
```

---

## Data Sources

### machines.json
Location: `data/machines.json`

Fields per machine:
- `id`: Machine identifier (e.g., "MX-204")
- `name`: Display name (e.g., "Hydraulic Press B")
- `type`: Machine type (e.g., "Hydraulic Press")
- `location`: Physical location
- `status`: Current status (operational, error, idle)
- `temperature`: Current temperature
- `runtime_hours`: Total runtime
- `last_maintenance`: Last maintenance date
- `maintenance_interval_days`: Days between maintenance

### error_codes.json
Location: `data/error_codes.json`

Fields per error code:
- `code`: Error code (e.g., "E17")
- `severity`: Severity level (low, medium, high, critical)
- `description`: Error description
- `symptom`: User-observable symptom
- `recommended_action`: Recommended maintenance action

### maintenance_tickets.json
Location: `data/maintenance_tickets.json`

Stores created tickets as a list of ticket objects.

---

## Implementation Details

### File Structure
```
src/
  ├── level3_multi_agent_workflow.py       # Main workflow implementation
  ├── agent_engine.py                      # Underlying LLM agent
  └── guardrails_middleware_layer.py       # Input/output validation

data/
  ├── machines.json                        # Machine catalog
  ├── error_codes.json                     # Error code reference
  └── maintenance_tickets.json             # Ticket storage
  └── checkpoints/
      └── level3_workflow.db              # LangGraph state checkpoint
```

### Core Functions

**`execute_workflow(user_input: str, config: dict = None) -> dict`**
- Main entry point
- Initializes WorkflowState
- Invokes agents sequentially (or via LangGraph if available)
- Returns final state with results

**`build_langgraph_workflow() -> StateGraph`**
- Constructs LangGraph workflow
- Creates nodes for each agent
- Defines edges (sequential flow)
- Compiles with SqliteSaver checkpointer for persistence

**`fault_analysis_agent(state) -> state`**
- Uses AgentEngine to extract structured data
- Parses LLM response as JSON
- Populates `state["fault_analysis"]`

**`diagnosis_agent(state) -> state`**
- Calls `search_machine()` and `lookup_error_code()` tools
- Determines severity
- Populates `state["diagnosis"]`

**`request_agent(state) -> state`**
- Calls `create_maintenance_ticket()` tool
- Generates user-facing confirmation
- Sets `ticket_created` flag

---

## LangGraph Integration

### State Graph Structure
```python
workflow = StateGraph(WorkflowState)

# Add nodes
workflow.add_node("fault_analysis", fault_analysis_agent)
workflow.add_node("diagnosis", diagnosis_agent)
workflow.add_node("request", request_agent)

# Add edges (sequential: 1 → 2 → 3 → END)
workflow.add_edge("fault_analysis", "diagnosis")
workflow.add_edge("diagnosis", "request")
workflow.add_edge("request", END)

# Compile with checkpointer
checkpointer = SqliteSaver("data/checkpoints/level3_workflow.db")
compiled = workflow.compile(checkpointer=checkpointer)
```

### Checkpointing
- **Path**: `data/checkpoints/level3_workflow.db`
- **Purpose**: Persist workflow state between runs
- **Thread ID**: Generated per workflow execution
- **Resumable**: Can resume from any agent node

---

## Usage Examples

### Basic Workflow Execution
```python
from level3_multi_agent_workflow import execute_workflow

# Single query
result = execute_workflow(
    "Machine MX-204 stopped with error E17. Create maintenance request."
)

print(f"Ticket ID: {result['ticket_id']}")
print(f"Success: {result['ticket_created']}")
print(f"Response: {result['final_response']}")
```

### With LangGraph Config (Resume)
```python
config = {
    "configurable": {
        "thread_id": "fault_20260728_session_1"
    }
}

result = execute_workflow(
    "Machine MX-204 stopped with error E17. Create maintenance request.",
    config=config
)
# Can resume from same thread_id later
```

### Test Cases
```bash
# Run all test cases
python src/level3_multi_agent_workflow.py

# Expected output for each test:
# [Fault Analysis Output] - Extracted machine_id, error_code
# [Diagnosis Output] - Machine details, error details, severity
# [Final Response] - Ticket created successfully
```

---

## Validation & Error Handling

### Input Validation (Agent 1)
- Extract structured data from free-text input
- Identify missing required fields
- Return JSON with structured output

### Tool Validation (Agent 2)
- Machine lookup: Returns empty object if not found
- Error code lookup: Returns empty object if not found
- Fallback to sensible defaults (severity: "unknown")

### Ticket Validation (Agent 3)
- Check JSON file format before appending
- Handle both list and dict formats
- Catch exceptions and return error status

### Error Propagation
```python
if error:
    state["error"] = f"Agent X failed: {error}"
    state["final_response"] = f"Error: {state['error']}"
    return state
```

---

## Performance Characteristics

| Component | Latency | Notes |
|-----------|---------|-------|
| Fault Analysis | ~1.5s | Single LLM call + JSON parsing |
| Diagnosis | ~0.1s | Local JSON lookups only |
| Ticket Creation | ~0.05s | File I/O |
| **Total** | **~1.7s** | Dominated by LLM latency |

---

## Testing

### Unit Tests
```bash
# Run workflow tests
pytest tests/ -v -k level3

# Run individual agents
python src/level3_multi_agent_workflow.py
```

### Integration Tests
```python
# Test complete workflow
result = execute_workflow("Machine MX-204 error E17")
assert result['ticket_created'] == True
assert 'TICK-' in result['ticket_id']
assert result['fault_analysis']['machine_id'] == 'MX-204'
assert result['diagnosis']['severity'] in ['low', 'medium', 'high', 'critical']
```

### Manual Testing
```bash
# 1. Start Streamlit app
streamlit run app.py

# 2. Select Supervisor role
# 3. Ask: "Machine MX-204 stopped with error E17. Create maintenance request."
# 4. Verify: Ticket appears in 📋 Tickets tab
# 5. Check: data/maintenance_tickets.json updated
```

---

## Stretch Goals / Future Enhancements

### Level 3.5: Human-in-the-Loop Approval
```python
# Before creating critical tickets, ask for approval
if severity == "critical":
    await get_user_approval()
    # Only create ticket if approved
```

### Level 4: REST API Integration
```python
# Currently: local JSON files
# Future: POST /api/tickets to MES
# Future: GET /api/machines from MES API
```

### Parallel Agents (Coming Soon)
```python
# Instead of sequential 1→2→3
# Run diagnosis in parallel with other analysis
# Combine results before request creation
```

---

## Troubleshooting

### Issue: LangGraph Not Available
```
Note: langgraph not available. Will use sequential execution.
```
**Solution**: `pip install langgraph`  
**Impact**: Workflow still works, just without checkpoint persistence

### Issue: Machine Not Found
```json
"machine_details": {"error": "Machine XYZ not found"}
```
**Solution**: Add machine to data/machines.json  
**Check**: Ensure machine `id` matches user input

### Issue: Error Code Not Recognized
```json
"error_details": {"error": "Error code ABC not found"}
```
**Solution**: Add error code to data/error_codes.json  
**Check**: Ensure error `code` field matches user input

### Issue: Ticket Not Created
```
"ticket_created": false,
"error": "list indices must be integers..."
```
**Solution**: Verify data/maintenance_tickets.json format (should be list `[...]`)  
**Check**: File permissions for write access

---

## Summary

**Level 3 (Day 3)** delivers a production-ready multi-agent fault-handling workflow:

✅ Fault Analysis Agent - LLM-based structured extraction  
✅ Maintenance Diagnosis Agent - Tool-based machine & error lookup  
✅ Maintenance Request Agent - Automated ticket creation  
✅ LangGraph Integration - State management & checkpointing  
✅ Error Handling - Graceful degradation & validation  
✅ Testing - Unit, integration, and manual test support  

**Ready for**: User testing, deployment, and Level 4 REST API integration

---

**Last Updated**: 2026-07-28  
**Version**: 1.0  
**Status**: Production-Ready
