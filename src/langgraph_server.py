"""
LangGraph Agent Server for Local Debugging

This server exposes the Level 3 workflow as a LangGraph-compatible endpoint
that LangGraph Studio can connect to for visual debugging.

Run this separately from Streamlit:
    python src/langgraph_server.py

Then in LangGraph Studio:
    Base URL: http://localhost:8000
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment
load_dotenv()

from level3_multi_agent_workflow_v2 import build_langgraph_workflow
from langchain_core.messages import HumanMessage

# ============================================================================
# LANGGRAPH SERVER SETUP
# ============================================================================

# Build the workflow graph
workflow_graph = build_langgraph_workflow()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    print("[SERVER] LangGraph Agent Server starting...")
    print("[SERVER] Workflow graph loaded")
    yield
    print("[SERVER] LangGraph Agent Server shutdown")

# Create FastAPI app
app = FastAPI(
    title="FactoryOps AI - Level 3 Workflow",
    description="LangGraph Agent Server for multi-agent fault handling workflow",
    version="2.0",
    lifespan=lifespan
)

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "FactoryOps AI Level 3 Workflow",
        "workflow": "fault_analysis -> diagnosis -> request"
    }

# ============================================================================
# WORKFLOW EXECUTION ENDPOINT
# ============================================================================

@app.post("/invoke")
async def invoke_workflow(request: dict):
    """
    Execute the workflow.

    Request body:
    {
        "input": "Machine MX-204 stopped with error E17"
    }

    Returns:
    {
        "output": {
            "fault_analysis": {...},
            "diagnosis": {...},
            "awaiting_approval": true,
            ...
        }
    }
    """
    user_input = request.get("input", "")

    if not user_input:
        return {"error": "Missing 'input' field"}

    try:
        # Execute workflow
        initial_input = {"user_input": user_input, "messages": [HumanMessage(content=user_input)]}
        result = workflow_graph.invoke(initial_input)

        return {
            "status": "success",
            "output": result
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

# ============================================================================
# WORKFLOW INFO ENDPOINT
# ============================================================================

@app.get("/info")
async def workflow_info():
    """Get workflow structure information."""
    return {
        "name": "Level 3 Multi-Agent Fault Handling Workflow",
        "description": "Three sequential agents: Fault Analysis -> Diagnosis -> Request",
        "agents": [
            {
                "name": "Fault Analysis Agent",
                "purpose": "Extract machine_id and error_code from user input",
                "output": "fault_analysis dict with structured data"
            },
            {
                "name": "Maintenance Diagnosis Agent",
                "purpose": "Look up machine specs and error info, determine severity",
                "tools": ["search_machine", "lookup_error_code"],
                "output": "diagnosis dict with severity and recommendation"
            },
            {
                "name": "Maintenance Request Agent",
                "purpose": "Present recommendation and wait for human approval",
                "output": "awaiting_approval flag set to True"
            }
        ],
        "endpoints": {
            "health": "GET /health",
            "invoke": "POST /invoke",
            "info": "GET /info",
            "studio": "LangGraph Studio connects here"
        }
    }

# ============================================================================
# LANGGRAPH STUDIO INTEGRATION
# ============================================================================

# For LangGraph Studio to work, we need to expose the graph in the right format
@app.get("/graphs")
async def list_graphs():
    """List available graphs for LangGraph Studio."""
    return {
        "graphs": [
            {
                "name": "level3_workflow",
                "nodes": [
                    "fault_analysis_agent",
                    "diagnosis_agent",
                    "request_agent"
                ]
            }
        ]
    }

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    print("\n" + "="*70)
    print("[SERVER] Starting LangGraph Agent Server")
    print("="*70)
    print("\nEndpoints:")
    print("  Health:  http://localhost:8000/health")
    print("  Invoke:  http://localhost:8000/invoke (POST)")
    print("  Info:    http://localhost:8000/info")
    print("\nLangGraph Studio Connection:")
    print("  Base URL: http://localhost:8000")
    print("  Status:   Waiting for connections...")
    print("\n" + "="*70 + "\n")

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info"
    )
