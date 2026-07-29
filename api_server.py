"""
LangServe API Server - Exposes agents as REST endpoints for LangSmith Studio

Run this alongside the Streamlit app:
    python api_server.py

Then in LangSmith Studio:
    - Connect to: http://localhost:8000
    - Or use the API directly at: http://localhost:8000/docs
"""

import sys
import logging
from pathlib import Path

# Setup
sys.path.insert(0, str(Path(__file__).parent / "src"))
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from langserve import add_routes
    from agent_engine import AgentEngine
    import uvicorn
except ImportError as e:
    logger.error(f"Missing dependency: {e}")
    logger.info("Install with: pip install langserve uvicorn")
    sys.exit(1)

# Initialize FastAPI app
app = FastAPI(
    title="FactoryOps AI - Agent Server",
    description="REST API for FactoryOps manufacturing agents",
    version="1.0"
)

# Enable CORS for LangSmith Studio
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agents for each role
logger.info("Initializing agents...")
agents = {
    "operator": AgentEngine("operator"),
    "engineer": AgentEngine("engineer"),
    "supervisor": AgentEngine("supervisor"),
    "plant_manager": AgentEngine("plant_manager"),
}
logger.info(f"✓ Initialized {len(agents)} agents")

# Create runnables from agents
def create_agent_runnable(agent):
    """Wrap agent in a runnable interface for LangServe"""
    from langchain_core.runnables import RunnablePassthrough, RunnableLambda

    def invoke_agent(input_dict):
        query = input_dict.get("query", "")
        result = agent.process_query(query)
        return {
            "response": result.get("response", ""),
            "success": result.get("success", False),
            "tool_calls": result.get("intermediate_steps", []),
        }

    return RunnableLambda(invoke_agent)

# Expose agents as API endpoints
logger.info("Setting up API routes...")

add_routes(
    app,
    create_agent_runnable(agents["operator"]),
    path="/agents/operator",
)
add_routes(
    app,
    create_agent_runnable(agents["engineer"]),
    path="/agents/engineer",
)
add_routes(
    app,
    create_agent_runnable(agents["supervisor"]),
    path="/agents/supervisor",
)
add_routes(
    app,
    create_agent_runnable(agents["plant_manager"]),
    path="/agents/plant_manager",
)

# Health check
@app.get("/health")
async def health():
    return {"status": "healthy", "agents": list(agents.keys())}

# Root endpoint
@app.get("/")
async def root():
    return {
        "name": "FactoryOps AI Agent Server",
        "agents": list(agents.keys()),
        "docs": "http://localhost:8000/docs",
        "langsmith_studio": "https://smith.langchain.com/studio?projectName=Factory",
    }

if __name__ == "__main__":
    logger.info("\n" + "="*70)
    logger.info("Starting FactoryOps AI Agent Server")
    logger.info("="*70)
    logger.info(f"API: http://localhost:8000")
    logger.info(f"Docs: http://localhost:8000/docs")
    logger.info(f"LangSmith Studio: https://smith.langchain.com/studio?projectName=Factory")
    logger.info("="*70 + "\n")

    uvicorn.run(app, host="localhost", port=8000, log_level="info")
