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
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
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

# Enable CORS for LangGraph Studio
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*", "GET", "POST", "OPTIONS"],
    allow_headers=["*", "Content-Type", "Authorization"],
    expose_headers=["*"],
    max_age=600,
)

# ============================================================================
# ROOT ENDPOINT (for LangGraph Studio compatibility)
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint for LangGraph Studio."""
    return JSONResponse({
        "status": "ok",
        "server": "FactoryOps AI Level 3 Workflow Server",
        "version": "2.0",
        "streamlit_app": "http://localhost:8501",
        "langgraph_studio": "http://localhost:3000",
        "langsmith_studio": "https://eu.smith.langchain.com/studio"
    })

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/ok")
async def ok():
    """LangGraph Studio health check endpoint."""
    return JSONResponse({"ok": True})

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

@app.api_route("/threads/{thread_id}/runs/stream", methods=["POST", "GET", "OPTIONS"])
async def stream_run(thread_id: str, req: Request):
    """Stream run output (LangGraph Studio compatible execution)."""
    import uuid
    from langchain_core.messages import HumanMessage

    try:
        body = await req.json()
    except:
        body = {}

    user_input = body.get("input", "")
    if isinstance(user_input, dict):
        user_input = user_input.get("text", str(user_input))

    if not user_input:
        return JSONResponse({"error": "Missing input"}, status_code=400)

    try:
        initial_input = {
            "user_input": str(user_input),
            "messages": [HumanMessage(content=str(user_input))]
        }

        # Execute with streaming
        result = workflow_graph.invoke(initial_input)

        return JSONResponse({
            "run_id": str(uuid.uuid4()),
            "status": "completed",
            "output": {
                "user_input": result.get("user_input"),
                "fault_analysis": result.get("fault_analysis"),
                "diagnosis": result.get("diagnosis"),
                "awaiting_approval": result.get("awaiting_approval"),
                "ticket_created": result.get("ticket_created")
            }
        })
    except Exception as e:
        logger.error(f"Stream execution failed: {e}")
        return JSONResponse(
            {"status": "error", "error": str(e)},
            status_code=500
        )

@app.post("/invoke")
async def invoke_workflow(data: dict):
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
        user_input = data.get("input", "") if data else ""

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
# LANGGRAPH API ENDPOINTS (required by LangGraph Studio)
# ============================================================================

@app.api_route("/api/runs", methods=["GET", "POST", "OPTIONS"])
async def list_runs():
    """List all runs."""
    return JSONResponse([])

@app.api_route("/api/threads", methods=["GET", "POST", "OPTIONS"])
async def list_threads():
    """List all threads."""
    return JSONResponse([])

@app.post("/assistants/search")
async def search_assistants(req: Request):
    """Search assistants - implements LangGraph Server API protocol (2026)."""
    import uuid
    from datetime import datetime

    # Try to parse body, but accept empty
    try:
        body = await req.json()
    except:
        body = {}

    # LangGraph Server API response format (2026 spec)
    assistants = {
        "assistants": [
            {
                "assistant_id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "level3_workflow")),
                "graph_id": "level3_workflow",
                "name": "Level 3 Multi-Agent Workflow",
                "description": "Multi-agent fault handling: Fault Analysis → Diagnosis → Request",
                "config": {
                    "tags": ["multi-agent", "manufacturing", "fault-handling"],
                    "recursion_limit": 25,
                    "configurable": {}
                },
                "created_at": datetime.utcnow().isoformat() + "Z",
                "updated_at": datetime.utcnow().isoformat() + "Z",
                "metadata": {
                    "type": "multi_agent",
                    "nodes": ["fault_analysis", "diagnosis", "request"],
                    "agents": 3,
                    "flow": "sequential"
                }
            }
        ],
        "pagination": {
            "limit": 10,
            "offset": 0,
            "total": 1
        }
    }

    return JSONResponse(assistants)

@app.api_route("/api/assistants", methods=["GET", "POST", "OPTIONS"])
async def list_assistants():
    """List all assistants in LangGraph format (legacy)."""
    import uuid
    from datetime import datetime

    assistants = [{
        "assistant_id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "level3_workflow")),
        "graph_id": "level3_workflow",
        "name": "Level 3 Multi-Agent Workflow",
        "description": "Fault Analysis -> Diagnosis -> Request",
        "context": {
            "agents": 3,
            "flow": "sequential"
        },
        "metadata": {
            "type": "multi_agent",
            "nodes": ["fault_analysis", "diagnosis", "request"]
        },
        "created_at": datetime.utcnow().isoformat() + "+00:00",
        "updated_at": datetime.utcnow().isoformat() + "+00:00"
    }]

    return JSONResponse(assistants)

@app.get("/openapi.json")
async def openapi():
    """OpenAPI specification."""
    return JSONResponse({
        "openapi": "3.0.0",
        "info": {
            "title": "FactoryOps AI Level 3 Workflow",
            "version": "2.0"
        },
        "paths": {
            "/ok": {"get": {"summary": "Health check"}},
            "/api/runs": {"get": {"summary": "List runs"}},
            "/api/threads": {"get": {"summary": "List threads"}},
            "/api/assistants": {"get": {"summary": "List assistants"}}
        }
    })

# ============================================================================
# LANGGRAPH STUDIO COMPATIBILITY ENDPOINTS
# ============================================================================

@app.get("/runs")
async def list_runs():
    """List runs (for LangGraph Studio compatibility)."""
    return JSONResponse([])

@app.post("/runs")
async def create_run(data: dict):
    """Create a run (for LangGraph Studio compatibility)."""
    return JSONResponse({"run_id": "default", "status": "created"})

@app.get("/runs/{run_id}")
async def get_run(run_id: str):
    """Get run details (for LangGraph Studio compatibility)."""
    return JSONResponse({
        "run_id": run_id,
        "status": "completed",
        "output": {}
    })

@app.post("/runs/{run_id}/stream")
async def stream_run(run_id: str, data: dict):
    """Stream run output (for LangGraph Studio compatibility)."""
    return JSONResponse({"status": "streaming"})

@app.get("/assistants/{assistant_id}/subgraphs")
async def get_assistant_subgraphs(assistant_id: str, recurse: bool = True):
    """Get subgraphs for nested visualization (required for Studio)."""
    return JSONResponse({
        "subgraphs": [
            {
                "id": "fault_analysis",
                "namespace": ["fault_analysis"],
                "schema": {
                    "type": "object",
                    "properties": {
                        "machine_id": {"type": "string"},
                        "error_code": {"type": "string"}
                    }
                }
            },
            {
                "id": "diagnosis",
                "namespace": ["diagnosis"],
                "schema": {
                    "type": "object",
                    "properties": {
                        "severity": {"type": "string"},
                        "recommended_action": {"type": "string"}
                    }
                }
            },
            {
                "id": "request",
                "namespace": ["request"],
                "schema": {
                    "type": "object",
                    "properties": {
                        "awaiting_approval": {"type": "boolean"}
                    }
                }
            }
        ]
    })

@app.get("/assistants/{assistant_id}/schemas")
async def get_assistant_schemas(assistant_id: str):
    """Get input/output schemas for graph introspection (LangGraph Studio)."""
    return JSONResponse({
        "input_schema": {
            "type": "object",
            "properties": {
                "user_input": {
                    "type": "string",
                    "description": "User query about machine fault or error"
                },
                "messages": {
                    "type": "array",
                    "description": "Chat message history"
                }
            },
            "required": ["user_input"]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "user_input": {"type": "string"},
                "fault_analysis": {
                    "type": "object",
                    "description": "Extracted fault information"
                },
                "diagnosis": {
                    "type": "object",
                    "description": "Diagnostic analysis from maintenance agent"
                },
                "awaiting_approval": {
                    "type": "boolean",
                    "description": "Waiting for human approval"
                },
                "ticket_created": {
                    "type": "boolean",
                    "description": "Maintenance ticket successfully created"
                }
            }
        },
        "state_schema": {
            "type": "object",
            "properties": {
                "user_input": {"type": "string"},
                "messages": {"type": "array"},
                "fault_analysis": {"type": "object"},
                "diagnosis": {"type": "object"},
                "awaiting_approval": {"type": "boolean"},
                "ticket_created": {"type": "boolean"},
                "error": {"type": "string"}
            }
        }
    })

@app.get("/assistants/{assistant_id}/nodes/{node_id}")
async def get_node_schema(assistant_id: str, node_id: str):
    """Get schema for individual node (required for Studio node inspection)."""
    node_schemas = {
        "fault_analysis": {
            "id": "fault_analysis",
            "label": "Fault Analysis Agent",
            "type": "agent",
            "description": "Extracts machine_id and error_code from user input",
            "input_schema": {
                "type": "object",
                "properties": {"user_input": {"type": "string"}},
                "required": ["user_input"]
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "machine_id": {"type": "string"},
                    "error_code": {"type": "string"}
                }
            }
        },
        "diagnosis": {
            "id": "diagnosis",
            "label": "Diagnosis Agent",
            "type": "agent",
            "description": "Looks up machine specs and error info",
            "input_schema": {
                "type": "object",
                "properties": {
                    "machine_id": {"type": "string"},
                    "error_code": {"type": "string"}
                }
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "severity": {"type": "string"},
                    "recommended_action": {"type": "string"}
                }
            }
        },
        "request": {
            "id": "request",
            "label": "Request Agent",
            "type": "agent",
            "description": "Presents recommendation and awaits approval",
            "input_schema": {
                "type": "object",
                "properties": {
                    "diagnosis": {"type": "object"},
                    "fault_analysis": {"type": "object"}
                }
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "awaiting_approval": {"type": "boolean"},
                    "ticket_created": {"type": "boolean"}
                }
            }
        }
    }

    schema = node_schemas.get(node_id)
    if schema:
        return JSONResponse(schema)
    return JSONResponse({"error": f"Node {node_id} not found"}, status_code=404)

@app.get("/assistants/{assistant_id}/graph")
async def get_assistant_graph(assistant_id: str):
    """Get graph topology for visualization (LangGraph Studio)."""
    try:
        # Get the actual graph from compiled workflow
        graph = workflow_graph.get_graph()

        # Extract node and edge information
        nodes = []
        edges = []

        # Get graph structure
        if hasattr(graph, 'nodes'):
            for node_id, node in graph.nodes.items():
                nodes.append({
                    "id": str(node_id),
                    "label": str(node_id).replace("_", " ").title(),
                    "type": "agent"
                })

        if hasattr(graph, 'edges'):
            for source, target in graph.edges:
                edges.append({
                    "source": str(source),
                    "target": str(target)
                })

        # If we got nodes, return the graph structure
        if nodes:
            return JSONResponse({
                "id": "level3_workflow",
                "name": "Level 3 Workflow",
                "description": "Multi-Agent Fault Handling Workflow",
                "nodes": nodes,
                "edges": edges
            })
    except Exception as e:
        logger.warning(f"Could not extract graph schema: {e}")

    # Fallback to manual structure if extraction fails
    return JSONResponse({
        "id": "level3_workflow",
        "name": "Level 3 Workflow",
        "description": "Multi-Agent Fault Handling Workflow",
        "nodes": [
            {"id": "fault_analysis", "label": "Fault Analysis Agent", "type": "agent"},
            {"id": "diagnosis", "label": "Diagnosis Agent", "type": "agent"},
            {"id": "request", "label": "Request Agent", "type": "agent"}
        ],
        "edges": [
            {"source": "fault_analysis", "target": "diagnosis"},
            {"source": "diagnosis", "target": "request"}
        ]
    })

@app.get("/graph/mermaid")
async def get_graph_mermaid():
    """Get Mermaid diagram of the workflow (for visualization)."""
    try:
        graph = workflow_graph.get_graph()
        mermaid_str = graph.draw_mermaid()
        return JSONResponse({
            "format": "mermaid",
            "diagram": mermaid_str,
            "description": "Multi-agent workflow: fault_analysis → diagnosis → request"
        })
    except Exception as e:
        logger.warning(f"Could not generate mermaid: {e}")
        return JSONResponse({
            "format": "mermaid",
            "diagram": "graph LR\n  A[Fault Analysis] --> B[Diagnosis]\n  B --> C[Request]\n",
            "description": "Fallback diagram"
        })

@app.get("/graphs")
async def get_graphs():
    """Get available graphs with full topology (for LangGraph Studio visualization)."""
    return JSONResponse({
        "graphs": [
            {
                "id": "level3_workflow",
                "name": "Level 3 Workflow",
                "description": "Multi-Agent Fault Handling Workflow",
                "type": "compiled_state_graph",
                "nodes": [
                    {
                        "id": "fault_analysis",
                        "label": "Fault Analysis Agent",
                        "type": "agent",
                        "position": {"x": 0, "y": 0}
                    },
                    {
                        "id": "diagnosis",
                        "label": "Diagnosis Agent",
                        "type": "agent",
                        "position": {"x": 400, "y": 0}
                    },
                    {
                        "id": "request",
                        "label": "Request Agent",
                        "type": "agent",
                        "position": {"x": 800, "y": 0}
                    }
                ],
                "edges": [
                    {
                        "source": "fault_analysis",
                        "target": "diagnosis",
                        "label": "fault_analysis"
                    },
                    {
                        "source": "diagnosis",
                        "target": "request",
                        "label": "diagnosis"
                    }
                ],
                "entry_point": "fault_analysis",
                "exit_point": "request"
            }
        ]
    })

# ============================================================================
# CATCH-ALL CORS PREFLIGHT (DISABLED - was blocking /assistants/* routes)
# ============================================================================
# Commented out because FastAPI CORS middleware handles preflight automatically
# @app.api_route("/{full_path:path}", methods=["OPTIONS"])
# async def preflight_handler(full_path: str):
#     """Handle CORS preflight requests - catch-all for undefined routes."""
#     return JSONResponse({"ok": True})

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
    port = 5555  # Use 5555 (different from previous attempts)

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
