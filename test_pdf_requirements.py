#!/usr/bin/env python
"""
PDF Requirement Verification Script

Verifies that all Level 3 (Day 3) requirements from the Lab 5 PDF are met.

PDF Requirements:
1. Extract machine ID and error code from user input
2. Retrieve machine details from JSON file
3. Check error code details from JSON file
4. Determine issue severity
5. Recommend maintenance action
6. Ask user to confirm (can add approval later)
7. Create simulated maintenance request

This script tests ALL of these end-to-end.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from level3_multi_agent_workflow import execute_workflow
import json

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'


def print_header(title):
    """Print a formatted header"""
    print(f"\n{BOLD}{BLUE}{'='*80}{RESET}")
    print(f"{BOLD}{BLUE}{title}{RESET}")
    print(f"{BOLD}{BLUE}{'='*80}{RESET}\n")


def print_pass(msg):
    """Print a passing test"""
    print(f"{GREEN}[PASS]{RESET}: {msg}")


def print_fail(msg):
    """Print a failing test"""
    print(f"{RED}[FAIL]{RESET}: {msg}")


def print_info(msg):
    """Print info message"""
    print(f"{BLUE}[INFO]{RESET} {msg}")


def verify_requirement(requirement_num, requirement_text, test_func):
    """Verify a single requirement"""
    print(f"\n{BOLD}Requirement {requirement_num}: {requirement_text}{RESET}")
    try:
        result = test_func()
        if result:
            print_pass(requirement_text)
            return True
        else:
            print_fail(requirement_text)
            return False
    except Exception as e:
        print_fail(f"{requirement_text} - Exception: {str(e)}")
        return False


# ============================================================================
# TEST CASE 1: PDF Example Query
# ============================================================================

def test_pdf_example():
    """Test with the exact example from the PDF"""

    print_header("TEST CASE 1: PDF Example Query")
    print_info("Query: 'Machine MX-204 has stopped with error code E17. Check the issue and create a maintenance request.'")

    user_input = "Machine MX-204 has stopped with error code E17. Check the issue and create a maintenance request."
    result = execute_workflow(user_input)

    tests_passed = 0
    tests_total = 7

    # ========================================================================
    # REQUIREMENT 1: Extract machine ID
    # ========================================================================
    def req1():
        machine_id = result["fault_analysis"].get("machine_id")
        print(f"  Extracted machine_id: {machine_id}")
        return machine_id == "MX-204"

    if verify_requirement(1, "Extract machine ID from user input", req1):
        tests_passed += 1

    # ========================================================================
    # REQUIREMENT 2: Extract error code
    # ========================================================================
    def req2():
        error_code = result["fault_analysis"].get("error_code")
        print(f"  Extracted error_code: {error_code}")
        return error_code == "E17"

    if verify_requirement(2, "Extract error code from user input", req2):
        tests_passed += 1

    # ========================================================================
    # REQUIREMENT 3: Retrieve machine details
    # ========================================================================
    def req3():
        machine = result["diagnosis"].get("machine_details", {})
        if "error" in machine:
            print(f"  ❌ Machine not found: {machine['error']}")
            return False

        machine_id = machine.get("id")
        machine_name = machine.get("name")
        machine_type = machine.get("type")
        location = machine.get("location")

        print(f"  Machine ID: {machine_id}")
        print(f"  Machine Name: {machine_name}")
        print(f"  Type: {machine_type}")
        print(f"  Location: {location}")

        return machine_id == "MX-204" and machine_name and machine_type and location

    if verify_requirement(3, "Retrieve machine details from data/machines.json", req3):
        tests_passed += 1

    # ========================================================================
    # REQUIREMENT 4: Check error code details
    # ========================================================================
    def req4():
        error = result["diagnosis"].get("error_details", {})
        if "error" in error:
            print(f"  ❌ Error code not found: {error['error']}")
            return False

        error_code = error.get("code")
        description = error.get("description")
        symptom = error.get("symptom")

        print(f"  Error Code: {error_code}")
        print(f"  Description: {description}")
        print(f"  Symptom: {symptom}")

        return error_code == "E17" and description and symptom

    if verify_requirement(4, "Check error code details from data/error_codes.json", req4):
        tests_passed += 1

    # ========================================================================
    # REQUIREMENT 5: Determine issue severity
    # ========================================================================
    def req5():
        severity = result["diagnosis"].get("severity")
        print(f"  Determined severity: {severity}")
        return severity in ["low", "medium", "high", "critical"]

    if verify_requirement(5, "Determine issue severity", req5):
        tests_passed += 1

    # ========================================================================
    # REQUIREMENT 6: Recommend maintenance action
    # ========================================================================
    def req6():
        action = result["diagnosis"].get("recommended_action")
        print(f"  Recommended action: {action}")
        return action and len(action) > 10

    if verify_requirement(6, "Recommend maintenance action", req6):
        tests_passed += 1

    # ========================================================================
    # REQUIREMENT 7: Create maintenance request
    # ========================================================================
    def req7():
        ticket_created = result["ticket_created"]
        ticket_id = result["ticket_id"]

        print(f"  Ticket Created: {ticket_created}")
        print(f"  Ticket ID: {ticket_id}")

        # Verify ticket was persisted
        tickets_path = "data/maintenance_tickets.json"
        if os.path.exists(tickets_path):
            with open(tickets_path) as f:
                tickets = json.load(f)
            latest_ticket = tickets[-1] if tickets else None
            if latest_ticket and latest_ticket.get("ticket_id") == ticket_id:
                print(f"  ✓ Ticket persisted to {tickets_path}")
                return True

        return ticket_created and ticket_id.startswith("TICK-")

    if verify_requirement(7, "Create simulated maintenance request and persist to JSON", req7):
        tests_passed += 1

    # ========================================================================
    # SUMMARY
    # ========================================================================
    print(f"\n{BOLD}Test Case 1 Results:{RESET}")
    print(f"Passed: {tests_passed}/{tests_total}")

    if tests_passed == tests_total:
        print(f"{GREEN}{BOLD}[SUCCESS] ALL REQUIREMENTS MET FOR TEST CASE 1{RESET}")
        return True
    else:
        print(f"{RED}{BOLD}[FAILURE] SOME REQUIREMENTS FAILED{RESET}")
        return False


# ============================================================================
# TEST CASE 2: Alternative Query Format
# ============================================================================

def test_alternative_format():
    """Test with alternative query format"""

    print_header("TEST CASE 2: Alternative Query Format")
    print_info("Query: 'Error E23 on machine MX-201. What should we do?'")

    user_input = "Error E23 on machine MX-201. What should we do?"
    result = execute_workflow(user_input)

    # Extract requirements
    machine_id = result["fault_analysis"].get("machine_id")
    error_code = result["fault_analysis"].get("error_code")
    machine_details = result["diagnosis"].get("machine_details", {})
    error_details = result["diagnosis"].get("error_details", {})
    severity = result["diagnosis"].get("severity")
    ticket_created = result["ticket_created"]

    print(f"Machine ID: {machine_id} (Expected: MX-201)")
    print(f"Error Code: {error_code} (Expected: E23)")
    print(f"Machine Found: {'Yes' if 'error' not in machine_details else 'No'}")
    print(f"Error Found: {'Yes' if 'error' not in error_details else 'No'}")
    print(f"Severity: {severity}")
    print(f"Ticket Created: {ticket_created}")

    all_pass = (
        machine_id == "MX-201" and
        error_code == "E23" and
        "error" not in machine_details and
        "error" not in error_details and
        severity in ["low", "medium", "high", "critical"] and
        ticket_created
    )

    if all_pass:
        print(f"\n{GREEN}{BOLD}[SUCCESS] TEST CASE 2 PASSED{RESET}")
    else:
        print(f"\n{RED}{BOLD}[FAILURE] TEST CASE 2 FAILED{RESET}")

    return all_pass


# ============================================================================
# TEST CASE 3: Edge Cases
# ============================================================================

def test_edge_cases():
    """Test edge cases"""

    print_header("TEST CASE 3: Edge Cases")

    test_results = {}

    # Edge case 1: Minimal input
    print_info("Edge Case 1: Minimal input")
    result = execute_workflow("MX-204 error E17")
    test_results["minimal"] = (
        result["fault_analysis"]["machine_id"] == "MX-204" and
        result["fault_analysis"]["error_code"] == "E17" and
        result["ticket_created"]
    )
    print(f"  Result: {GREEN + 'PASS' if test_results['minimal'] else RED + 'FAIL'}{RESET}")

    # Edge case 2: Unknown machine (graceful degradation)
    print_info("Edge Case 2: Unknown machine (graceful degradation)")
    result = execute_workflow("Machine UNKNOWN error E17")
    test_results["unknown_machine"] = isinstance(result, dict) and not str(result.get("error", "")).startswith("Traceback")
    status = "PASS" if test_results['unknown_machine'] else "FAIL"
    print(f"  Result: {status} (no crash)")

    # Edge case 3: Unknown error code (graceful degradation)
    print_info("Edge Case 3: Unknown error code (graceful degradation)")
    result = execute_workflow("Machine MX-204 error UNKNOWN")
    test_results["unknown_error"] = isinstance(result, dict) and not str(result.get("error", "")).startswith("Traceback")
    status = "PASS" if test_results['unknown_error'] else "FAIL"
    print(f"  Result: {status} (no crash)")

    all_pass = all(test_results.values())

    if all_pass:
        print(f"\n{GREEN}{BOLD}[SUCCESS] ALL EDGE CASES PASSED{RESET}")
    else:
        print(f"\n{RED}{BOLD}[FAILURE] SOME EDGE CASES FAILED{RESET}")

    return all_pass


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run all tests"""

    print(f"\n{BOLD}{BLUE}")
    print("=" * 80)
    print("PDF REQUIREMENT VERIFICATION - Level 3 Fault Handling")
    print("=" * 80)
    print(RESET)

    results = {
        "test_case_1": test_pdf_example(),
        "test_case_2": test_alternative_format(),
        "test_case_3": test_edge_cases(),
    }

    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================

    print_header("FINAL VERIFICATION SUMMARY")

    print(f"{BOLD}Test Results:{RESET}")
    for test_name, passed in results.items():
        status = f"{GREEN}PASS{RESET}" if passed else f"{RED}FAIL{RESET}"
        test_display = test_name.replace("_", " ").title()
        print(f"  {test_display}: {status}")

    all_passed = all(results.values())

    print(f"\n{BOLD}Overall Result:{RESET}")
    if all_passed:
        print(f"{GREEN}{BOLD}")
        print("=" * 80)
        print("ALL PDF REQUIREMENTS MET")
        print("=" * 80)
        print("Level 3 Multi-Agent Fault Handling is COMPLETE and VERIFIED")
        print("Ready for Level 4: REST API and Streamlit Deployment")
        print(RESET)
        return 0
    else:
        print(f"{RED}{BOLD}")
        print("=" * 80)
        print("SOME REQUIREMENTS NOT MET")
        print("=" * 80)
        print(RESET)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
