"""
LangGraph Studio Compatible Application

This exports the workflow in the format LangGraph Studio expects.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
load_dotenv()

from level3_multi_agent_workflow_v2 import build_langgraph_workflow

# Build the workflow
graph = build_langgraph_workflow()

# Export for LangGraph Studio
__all__ = ["graph"]

if __name__ == "__main__":
    print("LangGraph app loaded")
    print(f"Graph type: {type(graph)}")
    print(f"Graph name: level3_workflow")
