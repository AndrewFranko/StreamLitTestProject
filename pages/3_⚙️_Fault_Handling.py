"""
Level 3: Fault Handling Workflow
Page for testing and demonstrating the multi-agent fault-handling workflow
"""

import streamlit as st
import sys
import os
import json
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from level3_multi_agent_workflow import execute_workflow

st.set_page_config(
    page_title="Fault Handling",
    page_icon="⚙️",
    layout="wide"
)

st.title("⚙️ Level 3: Fault Handling Workflow")
st.markdown("""
**Multi-Agent Fault Analysis & Ticket Creation**

Describe a machine fault and the system will:
1. **Extract** machine ID and error code
2. **Diagnose** the issue using machine & error data
3. **Create** a maintenance ticket automatically
""")

# Initialize session state
if "fault_workflows" not in st.session_state:
    st.session_state.fault_workflows = []

if "pending_fault_approval" not in st.session_state:
    st.session_state.pending_fault_approval = None

if "approved_fault_result" not in st.session_state:
    st.session_state.approved_fault_result = None

# ============================================================================
# SIDEBAR: Controls
# ============================================================================

with st.sidebar:
    st.header("🔧 Workflow Control")

    example_queries = {
        "E17 on MX-204": "Machine MX-204 stopped with error code E17. Check the issue and create a maintenance request.",
        "E23 on MX-105": "Error E23 on machine MX-105. What should we do?",
        "MX-204 Down": "Machine MX-204 is down. Error code is E17.",
        "Custom": ""
    }

    selected_example = st.selectbox(
        "Select example or enter custom:",
        list(example_queries.keys())
    )

    if selected_example == "Custom":
        user_input = st.text_area(
            "Enter fault description:",
            height=100,
            placeholder="E.g., Machine MX-204 stopped with error E17..."
        )
    else:
        user_input = example_queries[selected_example]
        st.info(f"**Query**: {user_input}")

    col1, col2 = st.columns(2)
    with col1:
        run_button = st.button("▶️ Run Workflow", use_container_width=True)
    with col2:
        clear_button = st.button("🗑️ Clear History", use_container_width=True)

    if clear_button:
        st.session_state.fault_workflows = []
        st.rerun()

# ============================================================================
# MAIN: Workflow Execution
# ============================================================================

if run_button and user_input.strip():
    with st.spinner("Running fault handling workflow..."):
        result = execute_workflow(user_input)

        # ALWAYS ASK FOR APPROVAL - show details first, then approval buttons
        st.session_state.pending_fault_approval = {
            "input": user_input,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }

        # ====================================================================
        # SHOW WORKFLOW DETAILS (for review before approval)
        # ====================================================================
        st.info("📋 REVIEW DETAILS BELOW - Then approve or reject ticket creation")

        # ====================================================================
        # TABS: Show workflow details for human review
        # ====================================================================
        tab1, tab2, tab3, tab4 = st.tabs(
            ["📋 Summary", "🔍 Fault Analysis", "🔧 Diagnosis", "🎫 Ticket"]
        )

        with tab1:
            col1, col2, col3 = st.columns(3)

            with col1:
                # Show status: if ticket created, show success; if awaiting approval, show pending
                if result["ticket_created"]:
                    st.metric("Status", "✅ Created")
                elif result.get("awaiting_approval"):
                    st.metric("Status", "⏳ PENDING APPROVAL")
                else:
                    st.metric("Status", "❌ Failed")

            with col2:
                st.metric(
                    "Ticket ID",
                    result["ticket_id"] if result["ticket_created"] else "Awaiting Approval"
                )

            with col3:
                severity = result.get("diagnosis", {}).get("severity", "unknown")
                st.metric("Severity", severity.upper())

            st.divider()

            # Final Response
            st.subheader("Final Response")
            if result["ticket_created"]:
                st.success(result["final_response"])
            elif result.get("awaiting_approval"):
                st.warning(result["final_response"])
            else:
                st.info(result["final_response"])

            # Error (if any)
            if result.get("error"):
                st.error(f"**Error**: {result['error']}")

        # ====================================================================
        # TAB 2: Fault Analysis Output
        # ====================================================================
        with tab2:
            st.subheader("Fault Analysis Agent Output")
            st.markdown("*Extracted structured information from user input*")

            fault = result["fault_analysis"]
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Machine ID", fault.get("machine_id", "N/A"))
            with col2:
                st.metric("Error Code", fault.get("error_code", "N/A"))
            with col3:
                st.metric("Request Type", fault.get("request_type", "N/A"))
            with col4:
                missing = len(fault.get("missing_fields", []))
                st.metric("Missing Fields", missing)

            st.json(fault, expanded=True)

        # ====================================================================
        # TAB 3: Diagnosis Output
        # ====================================================================
        with tab3:
            st.subheader("Maintenance Diagnosis Agent Output")
            st.markdown("*Machine & error data lookup with severity determination*")

            diagnosis = result["diagnosis"]

            # Machine Details
            st.subheader("Machine Details")
            machine = diagnosis.get("machine_details", {})
            if "error" not in machine:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Machine ID", machine.get("id", "N/A"))
                    st.metric("Type", machine.get("type", "N/A"))
                with col2:
                    st.metric("Name", machine.get("name", "N/A"))
                    st.metric("Location", machine.get("location", "N/A"))
                with col3:
                    st.metric("Status", machine.get("status", "N/A"))
                    st.metric("Temperature", f"{machine.get('temperature', 'N/A')}°C")

                with st.expander("Full Machine Data"):
                    st.json(machine)
            else:
                st.warning(f"Machine not found: {machine['error']}")

            # Error Details
            st.subheader("Error Code Details")
            error = diagnosis.get("error_details", {})
            if "error" not in error:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Error Code", error.get("code", "N/A"))
                    st.metric("Severity", error.get("severity", "N/A").upper())
                with col2:
                    st.metric("Description", error.get("description", "N/A"), label_visibility="collapsed")

                st.markdown("**Symptom**:")
                st.write(error.get("symptom", "N/A"))

                st.markdown("**Recommended Action**:")
                st.write(error.get("recommended_action", "N/A"))

                with st.expander("Full Error Data"):
                    st.json(error)
            else:
                st.warning(f"Error code not found: {error['error']}")

            # Diagnosis Summary
            st.divider()
            st.subheader("Diagnosis Summary")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Root Cause", diagnosis.get("root_cause", "Unknown"))
            with col2:
                st.metric("Severity Level", diagnosis.get("severity", "unknown").upper())

            st.markdown("**Recommended Action**:")
            st.info(diagnosis.get("recommended_action", "No action specified"))

        # ====================================================================
        # TAB 4: Ticket Details
        # ====================================================================
        with tab4:
            st.subheader("Maintenance Ticket Details")

            if result["ticket_created"]:
                st.success("✅ Ticket Successfully Created!")

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Ticket ID", result["ticket_id"])
                with col2:
                    st.metric("Status", "OPEN")
                with col3:
                    st.metric("Created", datetime.now().strftime("%H:%M:%S"))

                st.divider()

                # Ticket Preview
                fault = result["fault_analysis"]
                diagnosis = result["diagnosis"]

                ticket_data = {
                    "ticket_id": result["ticket_id"],
                    "machine_id": fault.get("machine_id"),
                    "machine_name": diagnosis.get("machine_details", {}).get("name"),
                    "error_code": fault.get("error_code"),
                    "severity": diagnosis.get("severity"),
                    "description": diagnosis.get("recommended_action"),
                    "status": "open",
                    "created_at": datetime.now().isoformat(),
                    "assigned_technician": None
                }

                st.json(ticket_data, expanded=False)

                # Verify in storage
                st.divider()
                st.subheader("Ticket Storage")
                tickets_path = "c:/StreamLit/data/maintenance_tickets.json"
                if os.path.exists(tickets_path):
                    with open(tickets_path) as f:
                        tickets = json.load(f)
                    st.success(f"✅ Ticket persisted to {tickets_path}")
                    st.write(f"**Total tickets in system**: {len(tickets)}")
                    st.write(f"**Latest ticket ID**: {tickets[-1].get('ticket_id', 'N/A')}")
                else:
                    st.error("Tickets file not found")

            elif result.get("awaiting_approval"):
                st.warning("⏳ Ticket Awaiting Human Approval")
                st.info("""
                **Ticket will be created with the following details:**

                Once you approve using the buttons below, this ticket will be:
                1. Created in the maintenance system
                2. Assigned to available technicians
                3. Tracked for completion
                """)

                # Preview of what will be created
                fault = result["fault_analysis"]
                diagnosis = result["diagnosis"]

                st.divider()
                st.subheader("Preview (if approved)")
                preview_data = {
                    "ticket_id": f"TICK-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "machine_id": fault.get("machine_id"),
                    "error_code": fault.get("error_code"),
                    "severity": diagnosis.get("severity"),
                    "description": diagnosis.get("recommended_action"),
                    "status": "will be OPEN",
                    "assigned_technician": "will be assigned"
                }
                st.json(preview_data, expanded=False)

            else:
                st.error("❌ Ticket creation failed")
                if result.get("error"):
                    st.write(f"Error: {result['error']}")

        # ====================================================================
        # APPROVAL BUTTONS: Show after details for human review
        # ====================================================================
        st.divider()
        st.warning("⚠️ APPROVAL REQUIRED - Review details above and then approve or reject")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Approve & Create Ticket", use_container_width=True):
                # NOW create the ticket since user approved
                from level3_multi_agent_workflow import create_maintenance_ticket

                approved_result = st.session_state.pending_fault_approval["result"]
                fault_data = approved_result.get("fault_analysis", {})
                diagnosis = approved_result.get("diagnosis", {})

                machine_id = fault_data.get("machine_id", "UNKNOWN")
                error_code = fault_data.get("error_code", "UNKNOWN")
                severity = diagnosis.get("severity", "unknown")
                recommended_action = diagnosis.get("recommended_action", "Contact supervisor")

                # Create the ticket
                ticket_result = create_maintenance_ticket(
                    machine_id=machine_id,
                    error_code=error_code,
                    description=recommended_action,
                    severity=severity
                )

                if ticket_result["success"]:
                    # Update result with ticket info
                    approved_result["ticket_created"] = True
                    approved_result["ticket_id"] = ticket_result["ticket_id"]

                    # Store in history
                    st.session_state.fault_workflows.insert(0, st.session_state.pending_fault_approval)
                    st.session_state.pending_fault_approval = None

                    st.success(f"✅ Ticket Created: {ticket_result['ticket_id']}")
                    st.balloons()
                    st.rerun()
                else:
                    st.error(f"Failed to create ticket: {ticket_result.get('error', 'Unknown error')}")

        with col2:
            if st.button("❌ Reject - Don't Create", use_container_width=True):
                st.info("Action cancelled by user")
                st.session_state.pending_fault_approval = None
                st.rerun()

# ============================================================================
# HISTORY: Previous Workflows
# ============================================================================

if st.session_state.fault_workflows:
    st.divider()
    st.subheader("📜 Workflow History")

    for i, workflow in enumerate(st.session_state.fault_workflows[:5]):
        with st.expander(
            f"Run {i+1}: {workflow['input'][:60]}... ({workflow['result']['ticket_id']})"
        ):
            col1, col2 = st.columns(2)

            with col1:
                st.write("**Input Query:**")
                st.write(workflow["input"])

            with col2:
                st.write("**Result:**")
                result = workflow["result"]
                st.metric("Status", "✅ Success" if result["ticket_created"] else "❌ Failed")
                st.metric(
                    "Machine",
                    result["fault_analysis"].get("machine_id", "Unknown")
                )
                st.metric(
                    "Severity",
                    result["diagnosis"].get("severity", "Unknown")
                )

            st.write("**Extracted Data:**")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.json(result["fault_analysis"])
            with col2:
                st.write("**Diagnosis:**")
                st.write(f"Severity: {result['diagnosis'].get('severity')}")
                st.write(f"Action: {result['diagnosis'].get('recommended_action')[:50]}...")
            with col3:
                st.write("**Ticket:**")
                st.write(f"ID: {result['ticket_id']}")
                st.write(f"Status: {'Created ✅' if result['ticket_created'] else 'Failed ❌'}")

# ============================================================================
# INFO: How It Works
# ============================================================================

with st.expander("ℹ️ How Level 3 Fault Handling Works"):
    st.markdown("""
    ### Three-Agent Workflow

    **Agent 1: Fault Analysis**
    - Extracts structured information from free-text input
    - Identifies: machine_id, error_code, request_type
    - Uses LLM-based text extraction with JSON output
    - Time: ~1.5s

    **Agent 2: Maintenance Diagnosis**
    - Searches machine data (machines.json)
    - Looks up error code details (error_codes.json)
    - Determines severity level
    - Recommends maintenance action
    - Time: <100ms

    **Agent 3: Maintenance Request**
    - Creates persistent maintenance ticket
    - Stores in data/maintenance_tickets.json
    - Generates confirmation response
    - Time: <50ms

    ### Total Latency: ~1.7s (LLM-dominated)

    ### Data Sources
    - **machines.json**: 5 production machines with full specifications
    - **error_codes.json**: 6+ error codes with severity & actions
    - **maintenance_tickets.json**: Persistent ticket storage (JSON list)

    ### Example Flow
    ```
    Input: "Machine MX-204 error E17"

    Agent 1 → machine_id="MX-204", error_code="E17"
    Agent 2 → Machine: Hydraulic Press B (high severity)
    Agent 3 → Ticket TICK-20260728144422 created ✅
    ```
    """)
