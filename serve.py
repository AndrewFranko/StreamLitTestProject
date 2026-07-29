"""
LangServe - Expose agents as interactive runnables for LangSmith Studio

Run: python serve.py

Then in LangSmith Studio Connect tab:
  Base URL: http://localhost:8000
"""

import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langserve import add_routes
from langchain_core.runnables import RunnableLambda
from agent_engine import AgentEngine

# Initialize agents
logger.info("Initializing agents...")
operators = {
    "operator": AgentEngine("operator"),
    "engineer": AgentEngine("engineer"),
    "supervisor": AgentEngine("supervisor"),
    "plant_manager": AgentEngine("plant_manager"),
}

# Create FastAPI app
app = FastAPI(
    title="FactoryOps AI Agents",
    description="Manufacturing AI agents for Factory operations",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Wrap agents as runnables
def create_runnable(agent, role_name):
    def invoke(text: str):
        result = agent.process_query(text)
        return {
            "response": result.get("response", ""),
            "success": result.get("success", False),
        }

    return RunnableLambda(invoke).with_config({
        "run_name": f"{role_name.capitalize()} Agent",
        "description": f"Manufacturing assistant for {role_name}",
    })

# Expose as routes
add_routes(
    app,
    create_runnable(operators["operator"], "operator"),
    path="/operator",
    playground_type="chat",
)

add_routes(
    app,
    create_runnable(operators["engineer"], "engineer"),
    path="/engineer",
    playground_type="chat",
)

add_routes(
    app,
    create_runnable(operators["supervisor"], "supervisor"),
    path="/supervisor",
    playground_type="chat",
)

add_routes(
    app,
    create_runnable(operators["plant_manager"], "plant_manager"),
    path="/plant_manager",
    playground_type="chat",
)

# Health check
@app.get("/health")
def health():
    return {"status": "ok", "agents": list(operators.keys())}

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*70)
    print("FactoryOps AI - Agent Server")
    print("="*70)
    print(f"\n✓ Server: http://localhost:8000")
    print(f"✓ API Docs: http://localhost:8000/docs")
    print(f"\nIn LangSmith Studio Connect tab:")
    print(f"  Base URL: http://localhost:8000")
    print("\nAgents exposed:")
    for role in operators:
        print(f"  • /{role}")
    print("\n" + "="*70 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8000)
