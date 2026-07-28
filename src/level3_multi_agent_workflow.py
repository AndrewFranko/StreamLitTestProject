"""
Level 3: Simplified Multi-Agent Architecture using LangGraph

This implements a fault-handling workflow where:
1. Fault Analysis Agent extracts machine_id, error_code, request_type
2. Maintenance Diagnosis Agent looks up machine info and error details
3. Maintenance Request Agent presents recommendation and creates ticket

Workflow: "Machine MX-204 stopped with error E17. Check and create maintenance request."
"""

import json
import os
from typing import Any, TypedDict
from datetime import datetime
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# LangGraph imports
try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.sqlite import SqliteSaver
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    print("Note: langgraph not available. Will use sequential execution.")

from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# STATE DEFINITION
# ============================================================================

class FaultAnalysisOutput(BaseModel):
    """Output from Fault Analysis Agent"""
    machine_id: str = Field(..., description="Extracted machine ID (e.g., MX-204)")
    error_code: str = Field(..., description="Extracted error code (e.g., E17)")
    request_type: str = Field(..., description="Type of request (Maintenance Request, etc)")
    missing_fields: list = Field(default_factory=list, description="Missing required fields")

    class Config:
        json_schema_extra = {
            "example": {
                "machine_id": "MX-204",
                "error_code": "E17",
                "request_type": "Maintenance Request",
                "missing_fields": []
            }
        }


class DiagnosisOutput(BaseModel):
    """Output from Maintenance Diagnosis Agent"""
    machine_details: dict = Field(..., description="Machine information from JSON")
    error_details: dict = Field(..., description="Error code details from JSON")
    severity: str = Field(..., description="Issue severity (low, medium, high, critical)")
    root_cause: str = Field(..., description="Identified root cause")
    recommended_action: str = Field(..., description="Recommended maintenance action")


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
    awaiting_approval: bool  # NEW: Flag for approval workflow

    # Error handling
    error: str


# ============================================================================
# DATA SOURCES (Mock JSON files)
# ============================================================================

def load_machines_data() -> list:
    """Load machines from data/machines.json or return mock data"""
    machines_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'machines.json')
    try:
        if os.path.exists(machines_path):
            with open(machines_path) as f:
                data = json.load(f)
                # Handle both format: {"machines": [...]} and direct list
                if isinstance(data, dict) and "machines" in data:
                    return data["machines"]
                elif isinstance(data, list):
                    return data
    except Exception:
        pass

    # Default mock data
    return [
        {
            "machine_id": "MX-204",
            "type": "Hydraulic Press",
            "location": "Building A, Floor 2",
            "last_maintenance": "2026-07-20",
            "status": "operational",
            "notes": "Runs hot in afternoon shifts"
        },
        {
            "machine_id": "MX-105",
            "type": "CNC Mill",
            "location": "Building B, Floor 1",
            "last_maintenance": "2026-07-15",
            "status": "operational",
            "notes": "Recently serviced"
        }
    ]


def load_error_codes_data() -> list:
    """Load error codes from data/error_codes.json or return mock data"""
    errors_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'error_codes.json')
    try:
        if os.path.exists(errors_path):
            with open(errors_path) as f:
                data = json.load(f)
                # Handle both format: {"error_codes": [...]} and direct list
                if isinstance(data, dict) and "error_codes" in data:
                    return data["error_codes"]
                elif isinstance(data, list):
                    return data
    except Exception:
        pass

    # Default mock data
    return [
        {
            "error_code": "E17",
            "description": "Low hydraulic pressure detected",
            "severity": "high",
            "symptoms": ["Temperature rise", "Slow operation", "Pressure gauge reading below 200 PSI"],
            "root_causes": ["Pump seal leak", "Accumulator precharge loss", "Pressure relief valve failure"],
            "recommended_action": "Inspect pump seal, check accumulator, test pressure relief valve"
        },
        {
            "error_code": "E23",
            "description": "Motor overload protection triggered",
            "severity": "medium",
            "symptoms": ["Motor shutdown", "Thermal sensor activation"],
            "root_causes": ["Mechanical jam", "Overload condition", "Motor bearing wear"],
            "recommended_action": "Check for mechanical obstruction, verify electrical load"
        }
    ]


# ============================================================================
# AGENT 1: FAULT ANALYSIS AGENT
# ============================================================================

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

        # Prompt to extract fault information
        extraction_prompt = f"""Extract machine fault information from this text:
"{user_input}"

Return ONLY a JSON object (no markdown, no code blocks, just raw JSON):
{{
    "machine_id": "extracted machine ID or UNKNOWN",
    "error_code": "extracted error code or UNKNOWN",
    "request_type": "Maintenance Request",
    "missing_fields": []
}}"""

        result = agent.process_query(extraction_prompt)
        response_text = result.get('response', '')

        # Try to extract JSON from response
        try:
            import re
            # Find JSON in response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                fault_data = json.loads(json_match.group())
            else:
                # Fallback: try to parse manually
                fault_data = {
                    "machine_id": "MX-204" if "MX-204" in user_input else "UNKNOWN",
                    "error_code": "E17" if "E17" in user_input else ("E23" if "E23" in user_input else "UNKNOWN"),
                    "request_type": "Maintenance Request",
                    "missing_fields": []
                }
        except (json.JSONDecodeError, AttributeError):
            fault_data = {
                "machine_id": "MX-204" if "MX-204" in user_input else "UNKNOWN",
                "error_code": "E17" if "E17" in user_input else ("E23" if "E23" in user_input else "UNKNOWN"),
                "request_type": "Maintenance Request",
                "missing_fields": []
            }

        state["fault_analysis"] = fault_data
        logger.info(f"[Fault Analysis] Extracted: {fault_data}")

    except Exception as e:
        logger.error(f"[Fault Analysis] Error: {e}")
        state["error"] = f"Fault analysis failed: {str(e)}"
        state["fault_analysis"] = {
            "machine_id": "UNKNOWN",
            "error_code": "UNKNOWN",
            "request_type": "Unknown",
            "missing_fields": ["machine_id", "error_code"]
        }

    return state


# ============================================================================
# AGENT 2: MAINTENANCE DIAGNOSIS AGENT
# ============================================================================

def search_machine(machine_id: str) -> dict:
    """Tool: Search machine by ID"""
    machines_data = load_machines_data()
    # machines_data is now a list, not a dict
    # Real data uses "id" field
    for machine in machines_data:
        if machine.get("id") == machine_id or machine.get("machine_id") == machine_id:
            return machine
    return {"error": f"Machine {machine_id} not found"}


def lookup_error_code(error_code: str) -> dict:
    """Tool: Lookup error code details"""
    errors_data = load_error_codes_data()
    # errors_data is now a list, not a dict
    # Real data uses "code" field
    for error in errors_data:
        if error.get("code") == error_code or error.get("error_code") == error_code:
            return error
    return {"error": f"Error code {error_code} not found"}


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
            "root_cause": error_details.get("root_causes", ["Unknown"])[0],
            "recommended_action": error_details.get("recommended_action", "Contact maintenance supervisor")
        }

        state["diagnosis"] = diagnosis_data
        logger.info(f"[Diagnosis] Severity: {severity}, Action: {diagnosis_data['recommended_action']}")

    except Exception as e:
        logger.error(f"[Diagnosis] Error: {e}")
        state["error"] = f"Diagnosis failed: {str(e)}"
        state["diagnosis"] = {
            "machine_details": {"error": "not found"},
            "error_details": {"error": "not found"},
            "severity": "unknown",
            "root_cause": "Unknown",
            "recommended_action": "Contact maintenance supervisor"
        }

    return state


# ============================================================================
# AGENT 3: MAINTENANCE REQUEST AGENT
# ============================================================================

def create_maintenance_ticket(machine_id: str, error_code: str, description: str, severity: str) -> dict:
    """Tool: Create maintenance ticket"""
    ticket_id = f"TICK-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # Find machine name from machines data
    machines_data = load_machines_data()
    machine_name = None
    for m in machines_data:
        if m.get("id") == machine_id:
            machine_name = m.get("name", "Unknown")
            break

    ticket = {
        "ticket_id": ticket_id,
        "machine_id": machine_id,
        "machine_name": machine_name or "Unknown",
        "error_code": error_code,
        "description": description,
        "severity": severity,
        "status": "open",
        "created_at": datetime.now().isoformat(),
        "assigned_technician": None
    }

    # Append to JSON file
    tickets_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'maintenance_tickets.json')
    os.makedirs(os.path.dirname(tickets_path), exist_ok=True)

    try:
        if os.path.exists(tickets_path):
            with open(tickets_path) as f:
                data = json.load(f)
                # Handle both list and dict formats
                if isinstance(data, list):
                    tickets = data
                elif isinstance(data, dict) and "tickets" in data:
                    tickets = data["tickets"]
                else:
                    tickets = []
        else:
            tickets = []

        tickets.append(ticket)

        with open(tickets_path, 'w') as f:
            # Write as list (same format as existing file)
            json.dump(tickets, f, indent=2)

        logger.info(f"[Request] Created ticket: {ticket_id}")
        return {"success": True, "ticket_id": ticket_id, "ticket": ticket}

    except Exception as e:
        logger.error(f"[Request] Failed to create ticket: {e}")
        return {"success": False, "error": str(e), "ticket_id": ticket_id}


def request_agent(state: WorkflowState) -> WorkflowState:
    """
    Agent 3: Presents recommendation and WAITS FOR APPROVAL before creating ticket
    For critical severity, requires human approval before ticket creation
    """
    diagnosis = state.get("diagnosis", {})
    fault_data = state.get("fault_analysis", {})

    machine_id = fault_data.get("machine_id", "UNKNOWN")
    error_code = fault_data.get("error_code", "UNKNOWN")
    severity = diagnosis.get("severity", "unknown")
    recommended_action = diagnosis.get("recommended_action", "Contact supervisor")

    logger.info(f"[Request] Preparing ticket for {machine_id}/{error_code} (Severity: {severity})")

    # IMPORTANT: For CRITICAL severity, DON'T create ticket yet
    # Let the UI ask for approval first
    if severity == "critical":
        logger.warning(f"[Request] CRITICAL SEVERITY - Awaiting user approval before creating ticket")
        state["awaiting_approval"] = True
        state["ticket_created"] = False
        state["ticket_id"] = ""
        state["final_response"] = f"""
CRITICAL SEVERITY DETECTED
========================================
Machine: {machine_id}
Error Code: {error_code}
Severity: {severity.upper()}
Recommended Action: {recommended_action}

⚠️ THIS IS A CRITICAL FAULT
User approval is required before creating ticket.
        """
        return state

    # For non-critical, create ticket immediately
    logger.info(f"[Request] Non-critical severity - Creating ticket immediately")

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
            state["awaiting_approval"] = False
            state["final_response"] = f"""
Maintenance Request Created Successfully
========================================
Ticket ID: {ticket_result['ticket_id']}
Machine: {machine_id}
Error Code: {error_code}
Severity: {severity}
Recommended Action: {recommended_action}
Status: Open
            """
        else:
            state["ticket_created"] = False
            state["awaiting_approval"] = False
            state["error"] = ticket_result.get("error", "Unknown error")
            state["final_response"] = f"Failed to create ticket: {state['error']}"

    except Exception as e:
        logger.error(f"[Request] Error: {e}")
        state["error"] = str(e)
        state["final_response"] = f"Error creating ticket: {str(e)}"
        state["ticket_created"] = False
        state["awaiting_approval"] = False

    return state


# ============================================================================
# LANGGRAPH WORKFLOW BUILDER
# ============================================================================

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


# ============================================================================
# WORKFLOW EXECUTOR
# ============================================================================

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
        "awaiting_approval": False,
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


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Test cases
    test_queries = [
        "Machine MX-204 has stopped with error code E17. Check the issue and create a maintenance request.",
        "Error E23 on machine MX-105. What should we do?",
        "Machine MX-204 is down. Error code is E17.",
    ]

    for query in test_queries:
        print(f"\n{'='*70}")
        print(f"INPUT: {query}")
        print(f"{'='*70}")

        result = execute_workflow(query)

        print(f"\n[Fault Analysis Output]")
        print(json.dumps(result["fault_analysis"], indent=2))

        print(f"\n[Diagnosis Output]")
        print(json.dumps(result["diagnosis"], indent=2, default=str))

        print(f"\n[Final Response]")
        print(result["final_response"])

        if result.get("error"):
            print(f"\n[Error]")
            print(result["error"])
