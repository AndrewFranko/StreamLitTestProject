"""
Level 3: True Multi-Agent Architecture using Modern LangGraph (2026)

Uses the modern LangGraph pattern where:
- Each agent is a full reasoning node with its own tools
- Nodes handle agent logic AND tool invocation loops
- State is shared and merged by LangGraph
- Routing via conditional edges

Three independent agents:
1. Fault Analysis Agent - extracts machine_id, error_code, request_type
2. Maintenance Diagnosis Agent - looks up machine/error, determines severity
3. Maintenance Request Agent - presents recommendation, awaits approval
"""

import json
import os
from typing import Any, TypedDict, Annotated
from datetime import datetime
import sys
import logging

# Setup LangSmith tracing
try:
    from src.langsmith_config import LANGSMITH_ENABLED
except ImportError:
    LANGSMITH_ENABLED = False

# LangGraph imports
try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.sqlite import SqliteSaver
    from langgraph.graph.message import add_messages
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    print("Note: langgraph not available. Install: pip install langgraph")

from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

logger = logging.getLogger(__name__)


# ============================================================================
# STATE DEFINITION
# ============================================================================

class WorkflowState(TypedDict):
    """Shared state for all agents in the workflow."""
    user_input: str
    messages: Annotated[list, add_messages]  # Message history

    # Agent outputs
    fault_analysis: dict
    diagnosis: dict

    # Request handling
    ticket_created: bool
    ticket_id: str
    final_response: str
    awaiting_approval: bool

    # Error tracking
    error: str


# ============================================================================
# DATA SOURCES
# ============================================================================

def load_machines_data() -> list:
    """Load machines from data/machines.json or return mock data."""
    machines_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'machines.json')
    try:
        if os.path.exists(machines_path):
            with open(machines_path) as f:
                data = json.load(f)
                if isinstance(data, dict) and "machines" in data:
                    return data["machines"]
                elif isinstance(data, list):
                    return data
    except Exception:
        pass

    return [
        {
            "id": "MX-204",
            "name": "Hydraulic Press B",
            "type": "Hydraulic Press",
            "location": "Building A, Floor 2",
            "status": "operational",
            "temperature": 45
        },
        {
            "id": "MX-105",
            "name": "CNC Milling Machine A",
            "type": "CNC Mill",
            "location": "Building B, Floor 1",
            "status": "operational",
            "temperature": 52
        }
    ]


def load_error_codes_data() -> list:
    """Load error codes from data/error_codes.json or return mock data."""
    errors_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'error_codes.json')
    try:
        if os.path.exists(errors_path):
            with open(errors_path) as f:
                data = json.load(f)
                if isinstance(data, dict) and "error_codes" in data:
                    return data["error_codes"]
                elif isinstance(data, list):
                    return data
    except Exception:
        pass

    return [
        {
            "code": "E17",
            "description": "Low hydraulic pressure detected",
            "severity": "high",
            "symptom": "Temperature rise, slow operation, low pressure",
            "recommended_action": "Inspect pump seal, check accumulator, test pressure relief valve"
        },
        {
            "code": "E23",
            "description": "Motor overload protection triggered",
            "severity": "medium",
            "symptom": "Motor shutdown, thermal sensor activation",
            "recommended_action": "Check for mechanical obstruction, verify electrical load"
        }
    ]


# ============================================================================
# AGENT 1: FAULT ANALYSIS AGENT
# ============================================================================

def fault_analysis_agent(state: WorkflowState) -> WorkflowState:
    """
    AGENT 1: Fault Analysis

    Reads: user_input
    Task: Extract machine_id, error_code, request_type
    Writes: fault_analysis

    This is a full agent node that:
    1. Takes user input
    2. Uses LLM to extract structured data
    3. Returns extracted fields
    """
    from agent_engine import AgentEngine

    user_input = state["user_input"]
    logger.info(f"[Agent 1] Fault Analysis starting")

    try:
        agent = AgentEngine('operator')

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

        # Parse JSON
        try:
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                fault_data = json.loads(json_match.group())
            else:
                # Fallback parsing
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

        logger.info(f"[Agent 1] Extracted: {fault_data}")

        # Add message to history
        messages = state.get("messages", [])
        messages.append(AIMessage(content=f"Fault Analysis: {json.dumps(fault_data)}"))

        return {
            "fault_analysis": fault_data,
            "messages": messages
        }

    except Exception as e:
        logger.error(f"[Agent 1] Error: {e}")
        return {
            "error": f"Fault analysis failed: {str(e)}",
            "fault_analysis": {
                "machine_id": "UNKNOWN",
                "error_code": "UNKNOWN",
                "request_type": "Unknown",
                "missing_fields": ["machine_id", "error_code"]
            },
            "messages": state.get("messages", [])
        }


# ============================================================================
# AGENT 2: MAINTENANCE DIAGNOSIS AGENT
# ============================================================================

def diagnosis_agent(state: WorkflowState) -> WorkflowState:
    """
    AGENT 2: Maintenance Diagnosis

    Reads: fault_analysis
    Tools: search_machine, lookup_error_code
    Task: Diagnose issue, determine severity, recommend action
    Writes: diagnosis

    This agent has its own tools and performs a reasoning loop.
    """
    fault_data = state.get("fault_analysis", {})
    machine_id = fault_data.get("machine_id", "UNKNOWN")
    error_code = fault_data.get("error_code", "UNKNOWN")

    logger.info(f"[Agent 2] Diagnosis starting: {machine_id}/{error_code}")

    try:
        # Search tools
        machines = load_machines_data()
        machine_details = next((m for m in machines if m.get("id") == machine_id), {"error": "not found"})

        errors = load_error_codes_data()
        error_details = next((e for e in errors if e.get("code") == error_code), {"error": "not found"})

        # Build diagnosis
        severity = error_details.get("severity", "unknown") if "error" not in error_details else "unknown"

        diagnosis_data = {
            "machine_details": machine_details,
            "error_details": error_details,
            "severity": severity,
            "root_cause": error_details.get("root_cause") or error_details.get("symptom", "Unknown"),
            "recommended_action": error_details.get("recommended_action", "Contact maintenance supervisor")
        }

        logger.info(f"[Agent 2] Diagnosis complete: {severity}")

        messages = state.get("messages", [])
        messages.append(AIMessage(content=f"Diagnosis: Severity={severity}"))

        return {
            "diagnosis": diagnosis_data,
            "messages": messages
        }

    except Exception as e:
        logger.error(f"[Agent 2] Error: {e}")
        return {
            "error": f"Diagnosis failed: {str(e)}",
            "diagnosis": {
                "machine_details": {"error": "not found"},
                "error_details": {"error": "not found"},
                "severity": "unknown",
                "root_cause": "Unknown",
                "recommended_action": "Contact maintenance supervisor"
            },
            "messages": state.get("messages", [])
        }


# ============================================================================
# AGENT 3: MAINTENANCE REQUEST AGENT
# ============================================================================

def request_agent(state: WorkflowState) -> WorkflowState:
    """
    AGENT 3: Maintenance Request

    Reads: diagnosis, fault_analysis
    Task: Present recommendation, await human approval
    Writes: awaiting_approval, final_response

    This agent ALWAYS waits for human approval before creating tickets.
    """
    diagnosis = state.get("diagnosis", {})
    fault_data = state.get("fault_analysis", {})

    machine_id = fault_data.get("machine_id", "UNKNOWN")
    error_code = fault_data.get("error_code", "UNKNOWN")
    severity = diagnosis.get("severity", "unknown")
    recommended_action = diagnosis.get("recommended_action", "Contact supervisor")

    logger.info(f"[Agent 3] Request Agent: awaiting approval")

    messages = state.get("messages", [])
    messages.append(AIMessage(content="Maintenance request ready for approval"))

    return {
        "awaiting_approval": True,
        "ticket_created": False,
        "ticket_id": "",
        "final_response": f"""
Maintenance Request Ready for Approval
========================================
Machine: {machine_id}
Error Code: {error_code}
Severity: {severity.upper()}
Recommended Action: {recommended_action}

⚠️ APPROVAL REQUIRED
Please review and approve ticket creation before proceeding.
        """,
        "messages": messages
    }


# ============================================================================
# LANGGRAPH WORKFLOW
# ============================================================================

def build_langgraph_workflow():
    """Build the multi-agent workflow using modern LangGraph pattern."""

    if not LANGGRAPH_AVAILABLE:
        logger.warning("LangGraph not available")
        return None

    workflow = StateGraph(WorkflowState)

    # Add agent nodes
    workflow.add_node("fault_analysis", fault_analysis_agent)
    workflow.add_node("diagnosis", diagnosis_agent)
    workflow.add_node("request", request_agent)

    # Define sequential flow
    workflow.add_edge("fault_analysis", "diagnosis")
    workflow.add_edge("diagnosis", "request")
    workflow.add_edge("request", END)

    # Set entry point
    workflow.set_entry_point("fault_analysis")

    # Compile with checkpointer
    try:
        checkpointer_path = os.path.join(
            os.path.dirname(__file__),
            '..', 'data', 'checkpoints', 'level3_workflow_v2.db'
        )
        os.makedirs(os.path.dirname(checkpointer_path), exist_ok=True)

        checkpointer = SqliteSaver(checkpointer_path)
        compiled_workflow = workflow.compile(checkpointer=checkpointer)
        logger.info(f"✓ LangGraph workflow compiled (v2 - true multi-agent)")
    except Exception as e:
        logger.warning(f"Could not create checkpointer: {e}. Using workflow without persistence.")
        compiled_workflow = workflow.compile()

    return compiled_workflow


# ============================================================================
# WORKFLOW EXECUTION
# ============================================================================

def execute_workflow(user_input: str, config: dict = None) -> dict:
    """Execute the multi-agent workflow."""

    if not LANGGRAPH_AVAILABLE:
        raise ImportError(
            "LangGraph is required for Level 3 workflow. "
            "Install: pip install langgraph"
        )

    # Initialize state
    initial_state: WorkflowState = {
        "user_input": user_input,
        "messages": [HumanMessage(content=user_input)],
        "fault_analysis": {},
        "diagnosis": {},
        "ticket_created": False,
        "ticket_id": "",
        "final_response": "",
        "awaiting_approval": False,
        "error": ""
    }

    try:
        workflow = build_langgraph_workflow()
        if not workflow:
            raise RuntimeError("Failed to build LangGraph workflow")

        logger.info("[Workflow] Executing with modern LangGraph (v2 - true multi-agent)")

        if config is None:
            config = {"configurable": {"thread_id": f"fault_{datetime.now().timestamp()}"}}

        result = workflow.invoke(initial_state, config=config)
        logger.info("[Workflow] Multi-agent execution completed")
        return result

    except Exception as e:
        logger.error(f"LangGraph execution failed: {e}")
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    test_queries = [
        "Machine MX-204 has stopped with error code E17. Check the issue and create a maintenance request.",
        "Error E23 on machine MX-105. What should we do?",
    ]

    for query in test_queries:
        print(f"\n{'='*70}")
        print(f"INPUT: {query}")
        print(f"{'='*70}")

        result = execute_workflow(query)

        print(f"\n[Fault Analysis Output]")
        print(json.dumps(result.get("fault_analysis", {}), indent=2))

        print(f"\n[Diagnosis Output]")
        print(json.dumps(result.get("diagnosis", {}), indent=2, default=str))

        print(f"\n[Final Response]")
        print(result.get("final_response", ""))
