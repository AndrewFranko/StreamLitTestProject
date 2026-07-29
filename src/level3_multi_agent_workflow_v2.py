"""
Level 3: True Multi-Agent Architecture with RELIABLE RunTree Tracing

Uses explicit LangSmith RunTree for synchronous, reliable tracing.
Each agent uses ChatGoogleGenerativeAI directly (no AgentEngine complexity).
Workflow executes three sequential agents with explicit RunTree wrapping.
"""

import json
import os
from typing import Any, TypedDict
from datetime import datetime
import sys
import logging

logger = logging.getLogger(__name__)

# LangGraph imports
try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
    logger.info("[OK] LangGraph imported successfully")
except ImportError as e:
    LANGGRAPH_AVAILABLE = False
    logger.error(f"[FAIL] LangGraph import failed: {e}")

from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI

# LangSmith imports
try:
    from langsmith import traceable
    LANGSMITH_AVAILABLE = True
except ImportError:
    def traceable(func):
        return func
    LANGSMITH_AVAILABLE = False

# ============================================================================
# STATE DEFINITION
# ============================================================================

class WorkflowState(TypedDict):
    """Shared state for all agents in the workflow."""
    user_input: str
    messages: list  # Message history

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

@traceable(name="Fault Analysis Agent")
def fault_analysis_agent(state: WorkflowState) -> WorkflowState:
    """
    AGENT 1: Fault Analysis

    Extract machine_id, error_code, request_type from user input.
    Uses ChatGoogleGenerativeAI directly for maximum reliability.
    """
    user_input = state["user_input"]
    logger.info(f"[Agent 1] Fault Analysis starting")

    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

        extraction_prompt = f"""Extract machine fault information from this text:
"{user_input}"

Return ONLY a JSON object (no markdown, no code blocks, just raw JSON):
{{
    "machine_id": "extracted machine ID or UNKNOWN",
    "error_code": "extracted error code or UNKNOWN",
    "request_type": "Maintenance Request",
    "missing_fields": []
}}"""

        result = llm.invoke(extraction_prompt)
        response_text = result.content

        # Parse JSON
        try:
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                fault_data = json.loads(json_match.group())
            else:
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

@traceable(name="Diagnosis Agent")
def diagnosis_agent(state: WorkflowState) -> WorkflowState:
    """
    AGENT 2: Maintenance Diagnosis

    Uses fault_analysis data to diagnose issue.
    Looks up machine and error details, provides analysis.
    """
    fault_data = state.get("fault_analysis", {})
    machine_id = fault_data.get("machine_id", "UNKNOWN")
    error_code = fault_data.get("error_code", "UNKNOWN")

    logger.info(f"[Agent 2] Diagnosis starting: {machine_id}/{error_code}")

    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

        # Search tools
        machines = load_machines_data()
        machine_details = next((m for m in machines if m.get("id") == machine_id), {"error": "not found"})

        errors = load_error_codes_data()
        error_details = next((e for e in errors if e.get("code") == error_code), {"error": "not found"})

        # Use Gemini for intelligent diagnosis
        diagnosis_prompt = f"""Based on this machine and error data, provide a detailed diagnosis:

Machine: {json.dumps(machine_details, indent=2)}

Error Code Details: {json.dumps(error_details, indent=2)}

Provide your analysis in JSON format:
{{
    "severity": "low/medium/high/critical",
    "root_cause": "detailed root cause analysis",
    "recommended_action": "specific action to take",
    "estimated_repair_time_minutes": number,
    "required_parts": ["part1", "part2"],
    "safety_concerns": "any safety issues to note"
}}"""

        result = llm.invoke(diagnosis_prompt)
        response_text = result.content

        # Parse diagnosis from Gemini
        try:
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                gemini_diagnosis = json.loads(json_match.group())
            else:
                gemini_diagnosis = {}
        except:
            gemini_diagnosis = {}

        # Build diagnosis with Gemini insights
        severity = gemini_diagnosis.get("severity", error_details.get("severity", "unknown"))
        root_cause = gemini_diagnosis.get("root_cause", error_details.get("symptom", "Unknown"))
        recommended_action = gemini_diagnosis.get("recommended_action", error_details.get("recommended_action", "Contact supervisor"))

        diagnosis_data = {
            "machine_details": machine_details,
            "error_details": error_details,
            "severity": severity,
            "root_cause": root_cause,
            "recommended_action": recommended_action,
            "gemini_analysis": gemini_diagnosis
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

@traceable(name="Request Agent")
def request_agent(state: WorkflowState) -> WorkflowState:
    """
    AGENT 3: Maintenance Request

    Present recommendation and await human approval.
    """
    diagnosis = state.get("diagnosis", {})
    fault_data = state.get("fault_analysis", {})

    machine_id = fault_data.get("machine_id", "UNKNOWN")
    error_code = fault_data.get("error_code", "UNKNOWN")
    severity = diagnosis.get("severity", "unknown")
    recommended_action = diagnosis.get("recommended_action", "Contact supervisor")

    logger.info(f"[Agent 3] Request Agent: awaiting approval")

    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

        # Use Gemini to compose professional ticket summary
        ticket_prompt = f"""Create a professional maintenance ticket summary for approval:

Machine: {machine_id}
Error Code: {error_code}
Severity: {severity.upper()}
Recommended Action: {recommended_action}
Root Cause: {diagnosis.get('root_cause', 'Unknown')}

Generate a clear, concise ticket description that a technician would understand:"""

        result = llm.invoke(ticket_prompt)
        ticket_description = result.content

        messages = state.get("messages", [])
        messages.append(AIMessage(content="Maintenance request ready for approval"))

        output = {
            "awaiting_approval": True,
            "ticket_created": False,
            "ticket_id": "",
            "final_response": f"""
Maintenance Request Ready for Approval
========================================
Machine: {machine_id}
Error Code: {error_code}
Severity: {severity.upper()}

Ticket Description (generated by Gemini):
{ticket_description}

⚠️ APPROVAL REQUIRED
Please review and approve ticket creation before proceeding.
            """,
            "messages": messages,
            "ticket_description": ticket_description
        }

        return output
    except Exception as e:
        logger.error(f"[Agent 3] Error: {e}")
        raise


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

    # Compile workflow
    try:
        compiled_workflow = workflow.compile()
        logger.info("[OK] LangGraph workflow compiled (v2 - true multi-agent)")
    except Exception as e:
        logger.error(f"Failed to compile workflow: {e}")
        raise

    return compiled_workflow


# ============================================================================
# WORKFLOW EXECUTION WITH EXPLICIT RUNTREE TRACING
# ============================================================================

def execute_workflow(user_input: str, config: dict = None) -> dict:
    """Execute multi-agent workflow with RELIABLE explicit RunTree tracing."""
    import os

    logger.info(f"[Workflow] Starting with RUNTREE-based explicit tracing")

    if not LANGGRAPH_AVAILABLE:
        raise ImportError("LangGraph is required. Install: pip install langgraph")

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

    workflow = build_langgraph_workflow()
    if not workflow:
        raise RuntimeError("Failed to build LangGraph workflow")

    if config is None:
        config = {"configurable": {"thread_id": f"fault_{datetime.now().timestamp()}"}}

    # Create explicit LangSmith RunTree for RELIABLE tracing
    try:
        from langsmith.run_trees import RunTree

        api_key = os.getenv('LANGSMITH_API_KEY')
        endpoint = os.getenv('LANGSMITH_ENDPOINT', 'https://eu.api.smith.langchain.com')
        project = os.getenv('LANGSMITH_PROJECT', 'Factory')

        # Create root run
        root_run = RunTree(
            name="Level3_MultiAgent_Workflow",
            run_type="chain",
            inputs={"user_input": user_input},
            project_name=project,
            client_kwargs={"api_key": api_key, "api_url": endpoint}
        )

        logger.info(f"[Workflow] Created RunTree: {root_run.id}")

        try:
            # Execute workflow
            result = workflow.invoke(initial_state, config=config)

            logger.info("[Workflow] Execution completed")
            logger.info(f"  Machine: {result.get('fault_analysis', {}).get('machine_id')}")
            logger.info(f"  Severity: {result.get('diagnosis', {}).get('severity')}")
            logger.info(f"  Awaiting Approval: {result.get('awaiting_approval')}")

            # Update run with results (SYNCHRONOUS)
            root_run.outputs = {
                "fault_analysis": result.get('fault_analysis', {}),
                "diagnosis": result.get('diagnosis', {}),
                "awaiting_approval": result.get('awaiting_approval', False)
            }
            root_run.end_time = datetime.now()

            return result

        finally:
            # CRITICAL: Post the run to LangSmith (SYNCHRONOUS and RELIABLE)
            root_run.post()
            logger.info("[Workflow] ✓ RunTree posted to LangSmith (synchronous)")

    except ImportError:
        logger.warning("[Workflow] RunTree not available, executing without explicit tracing")
        result = workflow.invoke(initial_state, config=config)
        logger.info("[Workflow] Execution completed")
        return result

    except Exception as e:
        logger.error(f"[Workflow] Execution failed: {e}")
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
