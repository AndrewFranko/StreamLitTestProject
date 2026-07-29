#!/usr/bin/env python3
"""
Run LangGraph Studio with the Level 3 workflow

This script uses LangGraph's built-in server instead of our custom FastAPI.

Usage:
    python run_langgraph_studio.py

Then open: http://localhost:8030 (or the URL shown in console)
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Import the workflow
from level3_multi_agent_workflow_v2 import build_langgraph_workflow

# Create the workflow
workflow = build_langgraph_workflow()

# Export for LangGraph Studio
graph = workflow

if __name__ == "__main__":
    print("\n" + "="*70)
    print("LangGraph Studio Server")
    print("="*70)
    print("\nWorkflow loaded: level3_workflow")
    print("Ready for LangGraph Studio connection")
    print("\nTo run LangGraph Studio:")
    print("  python -m langgraph_runtime.main")
    print("\n" + "="*70 + "\n")
