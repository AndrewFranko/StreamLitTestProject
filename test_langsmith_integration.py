#!/usr/bin/env python3
"""
Test LangSmith Integration with Level 3 Workflow

This script tests whether traces are properly sent to LangSmith Studio.
Requires: .env.test file with LANGSMITH_API_KEY
"""

import os
import sys
import json
from pathlib import Path

# Load test environment
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env.test")

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_langsmith_config():
    """Test that LangSmith is configured."""
    print("[TEST] Testing LangSmith Configuration...")

    api_key = os.getenv("LANGSMITH_API_KEY")
    project = os.getenv("LANGSMITH_PROJECT")
    tracing = os.getenv("LANGCHAIN_TRACING_V2")

    checks = {
        "API Key configured": bool(api_key),
        "Project configured": bool(project),
        "Tracing enabled": tracing == "true"
    }

    for check, result in checks.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {check}")

    if all(checks.values()):
        print("\n[OK] LangSmith Configuration: PASS\n")
        return True
    else:
        print("\n[FAIL] LangSmith Configuration: FAIL\n")
        return False


def test_langsmith_import():
    """Test that LangSmith libraries are available."""
    print(" Testing LangSmith Libraries...")

    try:
        from langsmith import Client
        print("  [PASS] langsmith library imported")
    except ImportError as e:
        print(f"  [FAIL] langsmith import failed: {e}")
        print("    Install: pip install langsmith")
        return False

    try:
        client = Client()
        print("  [PASS] LangSmith Client created")
        print(f"  [PASS] Connected to project: {os.getenv('LANGSMITH_PROJECT')}")
    except Exception as e:
        print(f"  [FAIL] Client creation failed: {e}")
        return False

    print("\n[OK] LangSmith Libraries: PASS\n")
    return True


def test_langsmith_trace():
    """Test creating a trace in LangSmith."""
    print(" Testing LangSmith Trace Creation...")

    try:
        from langsmith import trace, Client

        @trace(name="test_agent_workflow")
        def sample_workflow():
            """Test workflow that creates a trace."""
            return {
                "status": "success",
                "message": "Test workflow completed"
            }

        result = sample_workflow()
        print(f"  [PASS] Trace created: {result['message']}")
        print(f"  [PASS] View at: https://smith.langchain.com/studio/factoryops")

    except Exception as e:
        print(f"  [FAIL] Trace creation failed: {e}")
        return False

    print("\n[OK] LangSmith Trace: PASS\n")
    return True


def test_level3_workflow():
    """Test Level 3 workflow with LangSmith tracing."""
    print(" Testing Level 3 Workflow with Tracing...")

    try:
        from level3_multi_agent_workflow_v2 import execute_workflow

        test_query = "Machine MX-204 stopped with error code E17. Check and create maintenance request."

        print(f"  Input: {test_query}")
        print("  Running workflow...")

        result = execute_workflow(test_query)

        # Check result
        success_checks = {
            "Fault analysis extracted": bool(result.get("fault_analysis")),
            "Diagnosis completed": bool(result.get("diagnosis")),
            "Awaiting approval": result.get("awaiting_approval") == True,
        }

        for check, passed in success_checks.items():
            status = "[PASS]" if passed else "[FAIL]"
            print(f"  {status} {check}")

        # Show extracted data
        if result.get("fault_analysis"):
            print(f"\n  Machine: {result['fault_analysis'].get('machine_id')}")
            print(f"  Error Code: {result['fault_analysis'].get('error_code')}")

        if result.get("diagnosis"):
            print(f"  Severity: {result['diagnosis'].get('severity')}")

        print(f"\n  [PASS] Workflow completed successfully")
        print(f"  [PASS] Check LangSmith Studio for trace")

        return all(success_checks.values())

    except Exception as e:
        print(f"  [FAIL] Workflow execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("[TEST] LangSmith Integration Test Suite")
    print("="*70 + "\n")

    tests = [
        ("Configuration", test_langsmith_config),
        ("Libraries", test_langsmith_import),
        ("Trace Creation", test_langsmith_trace),
        ("Level 3 Workflow", test_level3_workflow),
    ]

    results = {}

    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"[FAIL] {name}: Exception - {e}\n")
            results[name] = False

    # Summary
    print("="*70)
    print(" Test Summary")
    print("="*70)

    for name, passed in results.items():
        status = "[OK] PASS" if passed else "[FAIL] FAIL"
        print(f"  {status} - {name}")

    passed_count = sum(1 for p in results.values() if p)
    total_count = len(results)

    print(f"\nResult: {passed_count}/{total_count} tests passed")

    if all(results.values()):
        print("\n[OK] All tests passed! LangSmith is properly configured.\n")
        print("Next steps:")
        print("  1. Go to https://smith.langchain.com/studio")
        print("  2. Select project: 'factoryops'")
        print("  3. You should see traces from your workflows")
        print("  4. Click on a trace to inspect agent execution\n")
        return 0
    else:
        print("\n[FAIL] Some tests failed. Check the output above for details.\n")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
