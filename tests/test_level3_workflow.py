"""
Tests for Level 3: Multi-Agent Workflow

Tests the three-agent fault-handling workflow:
1. Fault Analysis Agent
2. Maintenance Diagnosis Agent
3. Maintenance Request Agent
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from level3_multi_agent_workflow import (
    execute_workflow,
    fault_analysis_agent,
    diagnosis_agent,
    request_agent,
    search_machine,
    lookup_error_code,
    load_machines_data,
    load_error_codes_data,
    WorkflowState
)
import pytest


class TestDataLoading:
    """Test data loading functions."""

    def test_load_machines_data(self):
        """Test loading machines from JSON."""
        machines = load_machines_data()
        assert isinstance(machines, list)
        assert len(machines) > 0
        # Should have expected machines
        machine_ids = [m.get("id") for m in machines]
        assert "MX-204" in machine_ids

    def test_load_error_codes_data(self):
        """Test loading error codes from JSON."""
        errors = load_error_codes_data()
        assert isinstance(errors, list)
        assert len(errors) > 0
        # Should have expected error codes
        error_codes = [e.get("code") for e in errors]
        assert "E17" in error_codes
        assert "E23" in error_codes


class TestToolFunctions:
    """Test individual tool functions."""

    def test_search_machine_found(self):
        """Test searching for existing machine."""
        result = search_machine("MX-204")
        assert "error" not in result
        assert result.get("id") == "MX-204"
        assert result.get("name") == "Hydraulic Press B"

    def test_search_machine_not_found(self):
        """Test searching for non-existent machine."""
        result = search_machine("UNKNOWN-999")
        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_lookup_error_code_found(self):
        """Test looking up existing error code."""
        result = lookup_error_code("E17")
        assert "error" not in result
        assert result.get("code") == "E17"
        assert result.get("severity") == "high"

    def test_lookup_error_code_not_found(self):
        """Test looking up non-existent error code."""
        result = lookup_error_code("E999")
        assert "error" in result
        assert "not found" in result["error"].lower()


class TestFaultAnalysisAgent:
    """Test Fault Analysis Agent."""

    def test_fault_analysis_extracts_machine_and_error(self):
        """Test that fault analysis extracts machine_id and error_code."""
        state: WorkflowState = {
            "user_input": "Machine MX-204 stopped with error code E17. Check and create maintenance request.",
            "fault_analysis": {},
            "diagnosis": {},
            "ticket_created": False,
            "ticket_id": "",
            "final_response": "",
            "error": ""
        }

        result = fault_analysis_agent(state)

        assert "fault_analysis" in result
        assert result["fault_analysis"]["machine_id"] == "MX-204"
        assert result["fault_analysis"]["error_code"] == "E17"

    def test_fault_analysis_handles_different_formats(self):
        """Test fault analysis with different input formats."""
        inputs = [
            "Machine MX-204 error E17",
            "Error E23 on machine MX-105",
            "MX-204 has failed with E17"
        ]

        for user_input in inputs:
            state: WorkflowState = {
                "user_input": user_input,
                "fault_analysis": {},
                "diagnosis": {},
                "ticket_created": False,
                "ticket_id": "",
                "final_response": "",
                "error": ""
            }

            result = fault_analysis_agent(state)
            assert result["fault_analysis"]["machine_id"] != "UNKNOWN"
            assert result["fault_analysis"]["error_code"] != "UNKNOWN"


class TestDiagnosisAgent:
    """Test Maintenance Diagnosis Agent."""

    def test_diagnosis_agent_finds_machine_and_error(self):
        """Test that diagnosis agent retrieves machine and error details."""
        state: WorkflowState = {
            "user_input": "Machine MX-204 error E17",
            "fault_analysis": {
                "machine_id": "MX-204",
                "error_code": "E17",
                "request_type": "Maintenance Request",
                "missing_fields": []
            },
            "diagnosis": {},
            "ticket_created": False,
            "ticket_id": "",
            "final_response": "",
            "error": ""
        }

        result = diagnosis_agent(state)

        assert "diagnosis" in result
        assert "machine_details" in result["diagnosis"]
        assert "error_details" in result["diagnosis"]
        assert result["diagnosis"]["machine_details"].get("id") == "MX-204"
        assert result["diagnosis"]["error_details"].get("code") == "E17"
        assert result["diagnosis"]["severity"] == "high"

    def test_diagnosis_agent_handles_missing_data(self):
        """Test diagnosis agent with non-existent machine/error."""
        state: WorkflowState = {
            "user_input": "Machine XYZ error ABC",
            "fault_analysis": {
                "machine_id": "XYZ-999",
                "error_code": "E999",
                "request_type": "Maintenance Request",
                "missing_fields": []
            },
            "diagnosis": {},
            "ticket_created": False,
            "ticket_id": "",
            "final_response": "",
            "error": ""
        }

        result = diagnosis_agent(state)

        assert "error" in result["diagnosis"]["machine_details"] or "error" in result.get("error", "")


class TestRequestAgent:
    """Test Maintenance Request Agent."""

    def test_request_agent_creates_ticket(self):
        """Test that request agent creates a ticket."""
        state: WorkflowState = {
            "user_input": "Create ticket for MX-204 error E17",
            "fault_analysis": {
                "machine_id": "MX-204",
                "error_code": "E17",
                "request_type": "Maintenance Request",
                "missing_fields": []
            },
            "diagnosis": {
                "machine_details": {"id": "MX-204", "name": "Hydraulic Press B"},
                "error_details": {"code": "E17", "severity": "high"},
                "severity": "high",
                "root_cause": "Pump seal leak",
                "recommended_action": "Inspect hydraulic lines"
            },
            "ticket_created": False,
            "ticket_id": "",
            "final_response": "",
            "error": ""
        }

        result = request_agent(state)

        assert result["ticket_created"] == True
        assert "TICK-" in result["ticket_id"]
        assert "Maintenance Request Created Successfully" in result["final_response"]


class TestCompleteWorkflow:
    """Test complete end-to-end workflow."""

    def test_complete_workflow_e17(self):
        """Test complete workflow for E17 error on MX-204."""
        result = execute_workflow(
            "Machine MX-204 stopped with error code E17. Check the issue and create a maintenance request."
        )

        # Check all stages completed
        assert result["fault_analysis"]["machine_id"] == "MX-204"
        assert result["fault_analysis"]["error_code"] == "E17"

        assert result["diagnosis"]["machine_details"].get("id") == "MX-204"
        assert result["diagnosis"]["error_details"].get("code") == "E17"
        assert result["diagnosis"]["severity"] == "high"

        assert result["ticket_created"] == True
        assert "TICK-" in result["ticket_id"]

    def test_complete_workflow_e23(self):
        """Test complete workflow for E23 error on MX-105."""
        result = execute_workflow(
            "Error E23 on machine MX-105. What should we do?"
        )

        assert result["fault_analysis"]["machine_id"] == "MX-105"
        assert result["fault_analysis"]["error_code"] == "E23"
        assert result["diagnosis"]["severity"] == "medium"

    def test_workflow_state_propagation(self):
        """Test that state propagates through all agents."""
        result = execute_workflow(
            "Machine MX-204 error E17"
        )

        # All stages should have data
        assert len(result["fault_analysis"]) > 0
        assert len(result["diagnosis"]) > 0
        assert result["ticket_id"] != ""
        assert len(result["final_response"]) > 0


class TestErrorHandling:
    """Test error handling in workflow."""

    def test_graceful_degradation_missing_machine(self):
        """Test workflow handles missing machine gracefully."""
        result = execute_workflow(
            "Machine XYZ-999 error E17"
        )

        # Should complete without crashing
        assert isinstance(result, dict)
        # But might have error state
        if "error" in result and result["error"]:
            assert "not found" in result["error"].lower()

    def test_graceful_degradation_missing_error(self):
        """Test workflow handles missing error code gracefully."""
        result = execute_workflow(
            "Machine MX-204 error E999"
        )

        # Should complete without crashing
        assert isinstance(result, dict)


class TestWorkflowMetadata:
    """Test workflow metadata and structure."""

    def test_workflow_state_has_all_fields(self):
        """Test that workflow result has all expected fields."""
        result = execute_workflow("Machine MX-204 error E17")

        required_fields = [
            "user_input",
            "fault_analysis",
            "diagnosis",
            "ticket_created",
            "ticket_id",
            "final_response",
            "error"
        ]

        for field in required_fields:
            assert field in result, f"Missing field: {field}"

    def test_fault_analysis_output_structure(self):
        """Test fault analysis output has expected structure."""
        result = execute_workflow("Machine MX-204 error E17")

        fault = result["fault_analysis"]
        assert "machine_id" in fault
        assert "error_code" in fault
        assert "request_type" in fault
        assert "missing_fields" in fault

    def test_diagnosis_output_structure(self):
        """Test diagnosis output has expected structure."""
        result = execute_workflow("Machine MX-204 error E17")

        diagnosis = result["diagnosis"]
        assert "machine_details" in diagnosis
        assert "error_details" in diagnosis
        assert "severity" in diagnosis
        assert "recommended_action" in diagnosis


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
