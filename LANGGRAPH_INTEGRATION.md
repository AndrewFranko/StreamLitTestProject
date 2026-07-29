# LangGraph Integration - Detailed Breakdown

## Where LangGraph is Used

### 1. IMPORT STATEMENTS (Lines 21-28)

```python
# LangGraph imports
try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.sqlite import SqliteSaver
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    print("Note: langgraph not available. Will use sequential execution.")
```

**Location**: `src/level3_multi_agent_workflow.py`, lines 21-28

**What it does**:
- Imports `StateGraph` - creates the workflow graph structure
- Imports `END` - marks the final node in the workflow
- Imports `SqliteSaver` - checkpointer for persisting state
- Graceful degradation if langgraph not installed

---

### 2. STATE DEFINITION (Lines 67-83)

```python
class WorkflowState(TypedDict):
    """Shared state across all agents in the workflow"""
    user_input: str
    
    # Output from Fault Analysis Agent
    fault_analysis: dict
    
    # Output from Diagnosis Agent
    diagnosis: dict
    
    # Output from Request Agent
    ticket_created: bool
    ticket_id: str
    final_response: str
    
    # Error handling
    error: str
```

**Location**: `src/level3_multi_agent_workflow.py`, lines 67-83

**What it does**:
- Defines the LangGraph state structure
- TypedDict ensures type safety across all agents
- Each agent reads and writes to this shared state
- State flows through the workflow: user_input → fault_analysis → diagnosis → ticket_id

**Flow Diagram**:
```
WorkflowState
├── user_input (input)
│   ↓ [Agent 1]
├── fault_analysis (output from agent 1)
│   ↓ [Agent 2]
├── diagnosis (output from agent 2)
│   ↓ [Agent 3]
├── ticket_created (output from agent 3)
├── ticket_id (output from agent 3)
├── final_response (output from agent 3)
└── error (error handling)
```

---

### 3. AGENT NODE DEFINITIONS (Lines 280-410)

#### Agent Node 1: Fault Analysis (Lines 280-340)

```python
def fault_analysis_agent(state: WorkflowState) -> WorkflowState:
    """
    Agent 1: Extracts machine_id, error_code, request_type from user input
    Uses the agent_engine to perform LLM-based extraction
    """
    from agent_engine import AgentEngine

    user_input = state["user_input"]
    logger.info(f"[Fault Analysis] Processing: {user_input}")

    try:
        agent = AgentEngine('operator')
        
        # ... extraction logic ...
        
        state["fault_analysis"] = fault_data
        logger.info(f"[Fault Analysis] Extracted: {fault_data}")

    except Exception as e:
        logger.error(f"[Fault Analysis] Error: {e}")
        state["error"] = f"Fault analysis failed: {str(e)}"
        # ... error handling ...

    return state
```

**Location**: `src/level3_multi_agent_workflow.py`, lines 280-340

**What it does**:
- Takes `WorkflowState` as input
- Reads: `state["user_input"]`
- Writes: `state["fault_analysis"]` with extracted machine_id, error_code
- Returns modified `state` to next agent
- This is a **LangGraph node**

---

#### Agent Node 2: Diagnosis (Lines 343-410)

```python
def diagnosis_agent(state: WorkflowState) -> WorkflowState:
    """
    Agent 2: Searches machine and error data, determines severity and recommendation
    """
    fault_data = state.get("fault_analysis", {})
    machine_id = fault_data.get("machine_id", "UNKNOWN")
    error_code = fault_data.get("error_code", "UNKNOWN")

    logger.info(f"[Diagnosis] Analyzing: {machine_id} / {error_code}")

    try:
        # Call tools
        machine_details = search_machine(machine_id)
        error_details = lookup_error_code(error_code)

        # Determine severity
        severity = error_details.get("severity", "unknown")

        # Build diagnosis
        diagnosis_data = {
            "machine_details": machine_details,
            "error_details": error_details,
            "severity": severity,
            # ...
        }

        state["diagnosis"] = diagnosis_data

    except Exception as e:
        logger.error(f"[Diagnosis] Error: {e}")
        state["error"] = f"Diagnosis failed: {str(e)}"
        # ... error handling ...

    return state
```

**Location**: `src/level3_multi_agent_workflow.py`, lines 343-410

**What it does**:
- Takes `WorkflowState` from Agent 1
- Reads: `state["fault_analysis"]` (output from Agent 1)
- Calls tools: `search_machine()`, `lookup_error_code()`
- Writes: `state["diagnosis"]` with severity and action
- Returns modified `state` to next agent
- This is a **LangGraph node**

---

#### Agent Node 3: Request (Lines 413-465)

```python
def request_agent(state: WorkflowState) -> WorkflowState:
    """
    Agent 3: Presents recommendation and creates maintenance ticket
    """
    diagnosis = state.get("diagnosis", {})
    fault_data = state.get("fault_analysis", {})

    machine_id = fault_data.get("machine_id", "UNKNOWN")
    error_code = fault_data.get("error_code", "UNKNOWN")
    severity = diagnosis.get("severity", "unknown")

    logger.info(f"[Request] Creating ticket for {machine_id}/{error_code}")

    try:
        # Create ticket using tool
        ticket_result = create_maintenance_ticket(
            machine_id=machine_id,
            error_code=error_code,
            description=recommended_action,
            severity=severity
        )

        if ticket_result["success"]:
            state["ticket_created"] = True
            state["ticket_id"] = ticket_result["ticket_id"]
            state["final_response"] = f"Maintenance Request Created Successfully..."
        else:
            state["ticket_created"] = False
            state["error"] = ticket_result.get("error", "Unknown error")

    except Exception as e:
        logger.error(f"[Request] Error: {e}")
        state["error"] = str(e)
        state["final_response"] = f"Error creating ticket: {str(e)}"
        state["ticket_created"] = False

    return state
```

**Location**: `src/level3_multi_agent_workflow.py`, lines 413-465

**What it does**:
- Takes `WorkflowState` from Agent 2
- Reads: `state["diagnosis"]` and `state["fault_analysis"]`
- Calls tool: `create_maintenance_ticket()`
- Writes: `state["ticket_created"]`, `state["ticket_id"]`, `state["final_response"]`
- Returns final `state` to workflow end
- This is a **LangGraph node**

---

### 4. LANGGRAPH WORKFLOW BUILDER (Lines 417-455)

```python
def build_langgraph_workflow():
    """Build the multi-agent workflow using LangGraph"""

    if not LANGGRAPH_AVAILABLE:
        logger.warning("LangGraph not available - using sequential workflow only")
        return None

    # Create state graph
    workflow = StateGraph(WorkflowState)

    # Add nodes
    workflow.add_node("fault_analysis", fault_analysis_agent)
    workflow.add_node("diagnosis", diagnosis_agent)
    workflow.add_node("request", request_agent)

    # Add edges (sequential flow)
    workflow.add_edge("fault_analysis", "diagnosis")
    workflow.add_edge("diagnosis", "request")
    workflow.add_edge("request", END)

    # Set entry point
    workflow.set_entry_point("fault_analysis")

    # Compile with checkpointer for persistence
    try:
        checkpointer_path = os.path.join(
            os.path.dirname(__file__),
            '..', 'data', 'checkpoints', 'level3_workflow.db'
        )
        os.makedirs(os.path.dirname(checkpointer_path), exist_ok=True)

        checkpointer = SqliteSaver(checkpointer_path)
        compiled_workflow = workflow.compile(checkpointer=checkpointer)
        logger.info(f"✓ LangGraph workflow compiled with checkpointer at {checkpointer_path}")
    except Exception as e:
        logger.warning(f"Could not create checkpointer: {e}. Using workflow without persistence.")
        compiled_workflow = workflow.compile()

    return compiled_workflow
```

**Location**: `src/level3_multi_agent_workflow.py`, lines 417-455

**What it does**:

#### 4a. StateGraph Creation (Line 425)
```python
workflow = StateGraph(WorkflowState)
```
- Creates a graph that manages `WorkflowState`
- Defines the structure for all agents to share state

#### 4b. Add Nodes (Lines 428-430)
```python
workflow.add_node("fault_analysis", fault_analysis_agent)
workflow.add_node("diagnosis", diagnosis_agent)
workflow.add_node("request", request_agent)
```
- Registers 3 agent functions as **nodes** in the graph
- Each node is a Python function that takes `WorkflowState` and returns modified `WorkflowState`

#### 4c. Add Edges (Lines 433-435)
```python
workflow.add_edge("fault_analysis", "diagnosis")
workflow.add_edge("diagnosis", "request")
workflow.add_edge("request", END)
```
- Connects nodes in sequence
- Defines the flow: Agent1 → Agent2 → Agent3 → END
- This is the **orchestration** - LangGraph manages the flow

#### 4d. Set Entry Point (Line 438)
```python
workflow.set_entry_point("fault_analysis")
```
- Marks "fault_analysis" as the first node to run

#### 4e. Compile with Checkpointer (Lines 441-453)
```python
checkpointer = SqliteSaver(checkpointer_path)
compiled_workflow = workflow.compile(checkpointer=checkpointer)
```
- **LangGraph checkpointing**: Saves workflow state to SQLite
- Path: `data/checkpoints/level3_workflow.db`
- Allows resuming workflows from any node

---

### 5. WORKFLOW EXECUTION (Lines 468-508)

```python
def execute_workflow(user_input: str, config: dict = None) -> dict:
    """
    Execute the multi-agent workflow

    Args:
        user_input: User message about machine fault
        config: Optional LangGraph config (for resuming from checkpoint)

    Returns:
        Workflow state with results from all three agents
    """

    # Initialize state
    initial_state: WorkflowState = {
        "user_input": user_input,
        "fault_analysis": {},
        "diagnosis": {},
        "ticket_created": False,
        "ticket_id": "",
        "final_response": "",
        "error": ""
    }

    # Try LangGraph execution
    if LANGGRAPH_AVAILABLE:
        try:
            workflow = build_langgraph_workflow()
            if workflow:
                logger.info("[Workflow] Executing with LangGraph")

                if config is None:
                    config = {"configurable": {"thread_id": f"fault_{datetime.now().timestamp()}"}}

                result = workflow.invoke(initial_state, config=config)
                logger.info("[Workflow] LangGraph execution completed")
                return result
        except Exception as e:
            logger.warning(f"LangGraph execution failed, falling back to sequential: {e}")

    # Fallback: Sequential execution
    logger.info("[Workflow] Executing sequentially (no LangGraph)")
    state = initial_state
    state = fault_analysis_agent(state)
    state = diagnosis_agent(state)
    state = request_agent(state)

    return state
```

**Location**: `src/level3_multi_agent_workflow.py`, lines 468-508

**What it does**:

#### 5a. Initialize State (Lines 473-481)
```python
initial_state: WorkflowState = {
    "user_input": user_input,
    "fault_analysis": {},
    "diagnosis": {},
    "ticket_created": False,
    "ticket_id": "",
    "final_response": "",
    "error": ""
}
```
- Creates the initial `WorkflowState` with user input

#### 5b. LangGraph Execution (Lines 483-497)
```python
if LANGGRAPH_AVAILABLE:
    workflow = build_langgraph_workflow()
    config = {"configurable": {"thread_id": f"fault_{datetime.now().timestamp()}"}}
    result = workflow.invoke(initial_state, config=config)
```
- **`workflow.invoke()`** - LangGraph method to run the entire workflow
- **`config`** with `thread_id` - enables resumable execution (checkpointing)
- Each execution gets a unique thread_id for checkpoint recovery

#### 5c. Graceful Fallback (Lines 501-506)
```python
# Fallback: Sequential execution
state = initial_state
state = fault_analysis_agent(state)
state = diagnosis_agent(state)
state = request_agent(state)
```
- If LangGraph not available, runs agents sequentially
- Same agent functions work either way
- **100% compatible fallback**

---

## Visual Architecture

### LangGraph Structure
```
StateGraph(WorkflowState)
│
├─── Node: fault_analysis_agent
│    ├─ Input: state["user_input"]
│    └─ Output: state["fault_analysis"] = {machine_id, error_code}
│
├─── Edge: fault_analysis → diagnosis
│
├─── Node: diagnosis_agent
│    ├─ Input: state["fault_analysis"]
│    └─ Output: state["diagnosis"] = {severity, recommended_action}
│
├─── Edge: diagnosis → request
│
├─── Node: request_agent
│    ├─ Input: state["diagnosis"]
│    └─ Output: state["ticket_id"]
│
├─── Edge: request → END
│
└─── Checkpointer: SqliteSaver
     └─ Path: data/checkpoints/level3_workflow.db
```

### Execution Flow with LangGraph
```
User Input
    ↓
workflow.invoke(initial_state, config=config)
    ↓
[LangGraph Orchestration]
    ├─ Checkpoint initial state
    ├─ Run fault_analysis_agent (node 1)
    ├─ Checkpoint state after agent 1
    ├─ Run diagnosis_agent (node 2)
    ├─ Checkpoint state after agent 2
    ├─ Run request_agent (node 3)
    ├─ Checkpoint final state
    └─ Return complete state
    ↓
Final Response with ticket_id
```

---

## Key LangGraph Features Used

| Feature | Location | Purpose |
|---------|----------|---------|
| **StateGraph** | Line 425 | Graph structure for workflow |
| **add_node()** | Lines 428-430 | Register agent nodes |
| **add_edge()** | Lines 433-435 | Connect nodes in sequence |
| **set_entry_point()** | Line 438 | First node to run |
| **workflow.invoke()** | Line 495 | Execute the workflow |
| **SqliteSaver** | Line 448 | Checkpoint persistence |
| **config (thread_id)** | Line 492 | Resume from checkpoints |
| **END** | Line 435 | Workflow termination marker |

---

## Why LangGraph?

✅ **Structured Orchestration**: Define multi-agent flows explicitly  
✅ **State Management**: TypedDict ensures type-safe state passing  
✅ **Checkpointing**: Save/resume workflow at any node  
✅ **Composability**: Easy to add/remove agents  
✅ **Traceability**: Each node execution is logged  
✅ **Production Ready**: Built for real-world multi-agent systems  

---

## Files

**Main Implementation**:
- `src/level3_multi_agent_workflow.py` (Lines 21-508)

**Uses LangGraph for**:
- StateGraph definition (Line 67-83, 425)
- Agent node registration (Lines 428-430)
- Workflow orchestration (Lines 433-438)
- State checkpointing (Line 448)
- Execution management (Line 495)

**Testing**:
- `tests/test_level3_workflow.py` - Tests work with/without langgraph
- `test_pdf_requirements.py` - Verifies workflow output (langgraph or sequential)

---

## Summary

**LangGraph is used in 5 key places**:

1. ✅ **Imports** (lines 22-28) - Import StateGraph, END, SqliteSaver
2. ✅ **State Definition** (lines 67-83) - WorkflowState TypedDict
3. ✅ **Agent Nodes** (lines 280-465) - 3 agent functions as nodes
4. ✅ **Workflow Builder** (lines 417-455) - Build StateGraph with edges
5. ✅ **Execution** (lines 468-508) - workflow.invoke() to run all agents

**Result**: Production-grade multi-agent workflow with checkpointing, graceful degradation, and full type safety.
