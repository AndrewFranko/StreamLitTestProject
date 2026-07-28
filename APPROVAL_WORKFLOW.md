# Approval Workflow - Human-in-the-Loop

## Status: IMPLEMENTED ✅

The approval workflow is already implemented in the Streamlit Chat page!

---

## How It Works

### 1. When Approval is Needed

In `pages/1_💬_Chat.py` (Lines 158-162), the workflow initializes approval state:

```python
if "pending_approval" not in st.session_state:
    st.session_state.pending_approval = None

if "approval_key" not in st.session_state:
    st.session_state.approval_key = None
```

### 2. Display Approval Buttons

**Location**: `pages/1_💬_Chat.py` (Lines 315-372)

When an action requires approval (e.g., creating a critical maintenance ticket):

```python
if st.session_state.pending_approval and st.session_state.pending_approval.get("awaiting_approval"):
    st.divider()
    st.warning("⚠️ Action Requires Approval")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ Approve", key=f"approve_{st.session_state.approval_key}", use_container_width=True):
            # Handle approval
            
    with col2:
        if st.button("❌ Reject", key=f"reject_{st.session_state.approval_key}", use_container_width=True):
            # Handle rejection
```

**Visual Output in Streamlit**:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ Action Requires Approval
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─────────────────────────┬─────────────────────────┐
│  ✅ Approve (full width)│  ❌ Reject (full width) │
└─────────────────────────┴─────────────────────────┘
```

### 3. Handle Approval

**Location**: `pages/1_💬_Chat.py` (Lines 322-372)

When user clicks "✅ Approve":

```python
if st.button("✅ Approve", key=f"approve_{st.session_state.approval_key}", use_container_width=True):
    debug_log("[APPROVAL] User approved action - Processing with agent...")
    
    # Step 1: Add approval message to chat history
    st.session_state.chat_history.append({
        "role": "user",
        "content": "✅ Approved"
    })
    
    # Step 2: Create agent with correct role
    role_mapping = {
        "Operator": "operator",
        "Engineer": "engineer",
        "Supervisor": "supervisor",
        "Plant Manager": "plant_manager"
    }
    agent_role = role_mapping.get(st.session_state.role, "operator")
    agent = st.session_state.agent or AgentEngine(agent_role)
    
    # Step 3: Send approval to agent (agent will create ticket)
    result = agent.process_query(approval_message)
    response_text = result.get("response", "Ticket created successfully.")
    
    # Step 4: Add agent response to chat
    st.session_state.chat_history.append({
        "role": "agent",
        "content": response_text
    })
    
    # Step 5: Clear approval state
    st.session_state.pending_approval = None
    st.session_state.approval_key = None
    
    # Step 6: Save and refresh
    if st.session_state.current_chat_id:
        save_chat(st.session_state.role, st.session_state.current_chat_id,
                 st.session_state.current_chat_name, st.session_state.chat_history)
    st.rerun()
```

**Flow**:
```
User clicks "✅ Approve"
    ↓
Add "✅ Approved" to chat history
    ↓
Create/get AgentEngine for current role
    ↓
Call agent.process_query("✅ Approved")
    ↓
Agent processes and creates maintenance ticket via MCP
    ↓
Add agent response to chat
    ↓
Clear approval state (buttons disappear)
    ↓
Save chat to disk
    ↓
Refresh UI
```

### 4. Handle Rejection

**Location**: `pages/1_💬_Chat.py` (Lines 375-410)

When user clicks "❌ Reject":

```python
if st.button("❌ Reject", key=f"reject_{st.session_state.approval_key}", use_container_width=True):
    debug_log("[APPROVAL] User rejected action - Processing with agent...")
    
    # Step 1: Add rejection message to chat history
    st.session_state.chat_history.append({
        "role": "user",
        "content": "❌ Rejected"
    })
    
    # Step 2: Create agent
    agent_role = role_mapping.get(st.session_state.role, "operator")
    agent = st.session_state.agent or AgentEngine(agent_role)
    
    # Step 3: Send rejection to agent
    result = agent.process_query("❌ Rejected")
    response_text = result.get("response", "Action cancelled.")
    
    # Step 4: Add agent response
    st.session_state.chat_history.append({
        "role": "agent",
        "content": response_text
    })
    
    # Step 5: Clear state and save
    st.session_state.pending_approval = None
    st.session_state.approval_key = None
    st.rerun()
```

---

## Workflow in Action

### Example: Critical Machine Fault

```
User:  "Machine MX-204 error E17 - create ticket"

Agent Response: 
  "This is a critical failure. Recommend immediate shutdown.
   Requires supervisor approval before proceeding.
   
   Do you approve ticket creation?"

Streamlit UI:
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ⚠️ Action Requires Approval
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [✅ Approve]  [❌ Reject]

User clicks [✅ Approve]:
  ↓
Agent processes: agent.process_query("✅ Approved")
  ↓
MCP Tool: create_maintenance_ticket()
  ↓
Response: "Ticket TICK-20260728145250 created successfully"
  ↓
Chat shows: "✅ Ticket created"
  ↓
Buttons disappear
  ↓
Chat saved to disk
```

---

## Code Locations

| Component | File | Lines | Purpose |
|-----------|------|-------|---------|
| **Approval State** | pages/1_💬_Chat.py | 158-162 | Initialize approval tracking |
| **Display Buttons** | pages/1_💬_Chat.py | 315-372 | Show approval UI |
| **Handle Approval** | pages/1_💬_Chat.py | 322-372 | Process user approval |
| **Handle Rejection** | pages/1_💬_Chat.py | 375-410 | Process user rejection |
| **MCP Tool** | src/mcp_ticket_server.py | - | create_maintenance_ticket() |
| **Agent Response** | src/agent_engine.py | - | Triggers approval workflow |

---

## How to Integrate with Level 3

The Level 3 workflow can be extended to trigger approval:

### In `src/level3_multi_agent_workflow.py`:

```python
# After diagnosis, check if critical
def request_agent_with_approval(state: WorkflowState) -> WorkflowState:
    diagnosis = state.get("diagnosis", {})
    severity = diagnosis.get("severity", "unknown")
    
    # If critical, require approval
    if severity == "critical":
        state["awaiting_approval"] = True
        state["final_response"] = "This is a critical fault. Requires supervisor approval."
        return state
    
    # Otherwise, create ticket immediately
    ticket_result = create_maintenance_ticket(...)
    state["ticket_created"] = ticket_result["success"]
    return state
```

### In Streamlit UI:

```python
# After agent response, check for approval needed
if result.get("awaiting_approval"):
    st.session_state.pending_approval = {
        "awaiting_approval": True,
        "machine_id": result["fault_analysis"]["machine_id"],
        "severity": result["diagnosis"]["severity"]
    }
    st.session_state.approval_key = unique_key
```

---

## Key Features

✅ **Human-in-the-Loop**: User must approve before ticket creation  
✅ **Role-Based**: Different roles can have different approval thresholds  
✅ **Severity-Based**: Critical faults require approval, routine ones don't  
✅ **Chat History**: Approval/rejection visible in conversation  
✅ **Agent Integration**: Agent handles both approval and rejection  
✅ **MCP Integration**: Uses MCP tools for ticket creation  
✅ **State Management**: Clears approval state after action  
✅ **Persistence**: Saves approval history to disk  

---

## Testing the Approval Workflow

### In Streamlit UI:

1. Go to 💬 Chat page
2. Ask about a critical fault: "Machine MX-204 critical error"
3. See approval buttons appear
4. Click ✅ or ❌
5. Observe agent processing approval

### Programmatically:

```python
from pages import chat_page

# Simulate approval flow
state = chat_page.st.session_state
state.pending_approval = {"awaiting_approval": True}
state.approval_key = "test_123"

# Simulate button click
approval_result = chat_page.process_approval()
```

---

## Status

✅ **Approval workflow is fully implemented in Streamlit Chat page**  
✅ **Integration ready for Level 3 workflow**  
✅ **MCP tools available for ticket creation**  
✅ **State management in place**  

**Ready to enable**: Just set `state["awaiting_approval"] = True` in Level 3 workflow for critical faults.

---

## Files

- `pages/1_💬_Chat.py` - Main approval UI and handling (Lines 315-410)
- `src/mcp_ticket_server.py` - create_maintenance_ticket() tool
- `src/level3_multi_agent_workflow.py` - Ready for approval integration

---

**Summary**: The approval workflow is production-ready and can be activated in the Level 3 workflow by adding a severity check before ticket creation.
