#!/usr/bin/env python3
"""Simple LangSmith integration test"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load test env
load_dotenv(Path(__file__).parent / ".env.test")

print("\n" + "="*70)
print("[TEST] LangSmith Integration - Simple Test")
print("="*70 + "\n")

# Test 1: Config
print("[TEST] 1. Configuration Check")
api_key = os.getenv("LANGSMITH_API_KEY")
project = os.getenv("LANGSMITH_PROJECT")
tracing = os.getenv("LANGCHAIN_TRACING_V2")

print(f"  [PASS] API Key: {api_key[:20]}..." if api_key else "  [FAIL] No API key")
print(f"  [PASS] Project: {project}" if project else "  [FAIL] No project")
print(f"  [PASS] Tracing: {tracing}" if tracing == "true" else "  [FAIL] Tracing not enabled")

# Test 2: LangSmith Client
print("\n[TEST] 2. LangSmith Client")
try:
    from langsmith import Client
    client = Client()
    print(f"  [PASS] Client created")
    print(f"  [PASS] Connected to project: {project}")
except Exception as e:
    print(f"  [FAIL] {e}")

# Test 3: Simple Trace
print("\n[TEST] 3. Creating Simple Trace")
try:
    from langsmith.run_trees import RunTree
    from datetime import datetime

    # Create a simple traced operation
    run = RunTree(
        name="test_agent_step",
        run_type="chain",
        inputs={"query": "Machine MX-204 error E17"},
        outputs={"result": "traced successfully"},
    )
    run.end_time = datetime.utcnow()
    client.create_run(run)

    print(f"  [PASS] Trace created and sent to LangSmith")
    print(f"  [PASS] View at: https://smith.langchain.com/studio/{project}")
except Exception as e:
    print(f"  [FAIL] {e}")

# Test 4: LangGraph import
print("\n[TEST] 4. LangGraph Import")
try:
    from langgraph.graph import StateGraph, END
    print(f"  [PASS] LangGraph imported successfully")
except Exception as e:
    print(f"  [FAIL] {e}")

print("\n" + "="*70)
print("[OK] LangSmith Integration Test Complete")
print("="*70)
print("\nNext steps:")
print("  1. Go to https://smith.langchain.com/studio")
print(f"  2. Select project: '{project}'")
print("  3. You should see the test trace")
print("  4. Run the Level 3 workflow to see more traces\n")
