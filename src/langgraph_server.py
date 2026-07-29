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
import json
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment
from dotenv import load_dotenv
load_dotenv()

try:
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    import uvicorn
    from langchain_core.messages import HumanMessage
    from level3_multi_agent_workflow_v2 import build_langgraph_workflow

    logger.info("[OK] All imports successful")
except ImportError as e:
    logger.error(f"[FAIL] Import error: {e}")
    sys.exit(1)

# ============================================================================
# BUILD WORKFLOW
# ============================================================================

logger.info("[STARTUP] Building workflow graph...")
try:
    workflow_graph = build_langgraph_workflow()
    logger.info("[OK] Workflow graph built successfully")
except Exception as e:
    logger.error(f"[FAIL] Could not build workflow: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================================================
# CREATE FASTAPI APP
# ============================================================================

app = FastAPI(
    title="FactoryOps AI - Level 3 Workflow",
    description="LangGraph Agent Server for multi-agent fault handling workflow",
    version="2.0"
)

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return JSONResponse({
        "status": "ok",
        "service": "FactoryOps AI Level 3 Workflow",
        "workflow": "fault_analysis -> diagnosis -> request"
    })

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
        "status": "success",
        "output": {...}
    }
    """
    try:
        user_input = request.get("input", "")

        if not user_input:
            return JSONResponse({"error": "Missing 'input' field"}, status_code=400)

        logger.info(f"[INVOKE] Processing: {user_input}")

        # Execute workflow
        initial_input = {
            "user_input": user_input,
            "messages": [HumanMessage(content=user_input)]
        }

        result = workflow_graph.invoke(initial_input)
        logger.info("[OK] Workflow execution completed")

        return JSONResponse({
            "status": "success",
            "output": {
                "user_input": result.get("user_input"),
                "fault_analysis": result.get("fault_analysis"),
                "diagnosis": result.get("diagnosis"),
                "awaiting_approval": result.get("awaiting_approval"),
                "ticket_created": result.get("ticket_created"),
                "error": result.get("error")
            }
        })
    except Exception as e:
        logger.error(f"[ERROR] Workflow execution failed: {e}")
        import traceback
        tb = traceback.format_exc()
        logger.error(tb)
        print(f"\n[SERVER ERROR]\n{tb}\n")
        return JSONResponse(
            {"status": "error", "error": str(e), "traceback": tb},
            status_code=500
        )

# ============================================================================
# WORKFLOW INFO ENDPOINT
# ============================================================================

@app.get("/info")
async def workflow_info():
    """Get workflow structure information."""
    return JSONResponse({
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
        ]
    })

# ============================================================================
# STARTUP/SHUTDOWN EVENTS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Handle startup."""
    logger.info("[STARTUP] FastAPI application started")

@app.on_event("shutdown")
async def shutdown_event():
    """Handle shutdown."""
    logger.info("[SHUTDOWN] FastAPI application stopping")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    port = 8888

    print("\n" + "="*70)
    print("[SERVER] Starting LangGraph Agent Server")
    print("="*70)
    print(f"\nServer Configuration:")
    print(f"  Host: 127.0.0.1")
    print(f"  Port: {port}")
    print(f"  Endpoint: http://127.0.0.1:{port}")
    print(f"\nAvailable Endpoints:")
    print(f"  Health: GET  http://localhost:{port}/health")
    print(f"  Invoke: POST http://localhost:{port}/invoke")
    print(f"  Info:   GET  http://localhost:{port}/info")
    print(f"\nLangGraph Studio Connection:")
    print(f"  Base URL: http://localhost:{port}")
    print(f"  Status:   Starting server...")
    print("\n" + "="*70 + "\n")

    try:
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=port,
            log_level="info"
        )
    except OSError as e:
        if "10048" in str(e) or "already in use" in str(e).lower():
            logger.error(f"\n[ERROR] Port {port} is already in use!")
            logger.error("\nTrying alternate port 9000...")
            print(f"\nLangGraph Studio Connection (alternate):")
            print(f"  Base URL: http://localhost:9000")
            print("\n" + "="*70 + "\n")
            try:
                uvicorn.run(
                    app,
                    host="127.0.0.1",
                    port=9000,
                    log_level="info"
                )
            except Exception as e2:
                logger.error(f"Failed on port 9000 too: {e2}")
                sys.exit(1)
        else:
            raise
