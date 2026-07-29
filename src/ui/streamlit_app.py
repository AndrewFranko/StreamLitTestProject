"""
FactoryOps AI - Level 2 Agent UI
Streamlit interface with role-based chat, tool execution display, and ticket approval workflow.
"""

import os
import streamlit as st
from datetime import datetime
from typing import Optional, Dict, List, Any
import json

# Load Streamlit Cloud secrets - THIS MUST BE FIRST
try:
    os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
except KeyError:
    st.error("Missing GOOGLE_API_KEY! Please add it to your Streamlit Cloud Secrets.")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="FactoryOps AI",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for clean, minimalist design
st.markdown("""
    <style>
    /* Main container */
    .main {
        max-width: 1200px;
        margin: 0 auto;
    }

    /* Chat container */
    .chat-container {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
        max-height: 600px;
        overflow-y: auto;
    }

    /* Tool execution indicator */
    .tool-execution {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
        padding: 12px;
        border-radius: 4px;
        margin: 8px 0;
        font-size: 0.9em;
    }

    /* Ticket details */
    .ticket-details {
        background-color: #fff3e0;
        border: 1px solid #ffb74d;
        padding: 16px;
        border-radius: 6px;
        margin: 12px 0;
    }

    /* Memory indicator */
    .memory-indicator {
        background-color: #f5f5f5;
        padding: 8px 12px;
        border-radius: 4px;
        font-size: 0.85em;
        color: #666;
        display: inline-block;
    }

    /* Action buttons */
    .action-button {
        margin: 4px 4px 4px 0;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def initialize_session_state():
    """Initialize Streamlit session state for chat history and memory."""
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []  # List of {"role": ..., "content": ..., "timestamp": ...}

    if "selected_role" not in st.session_state:
        st.session_state.selected_role = "Operator"

    if "current_conversation_turns" not in st.session_state:
        st.session_state.current_conversation_turns = 0

    if "tool_execution_log" not in st.session_state:
        st.session_state.tool_execution_log = []  # Track tool calls for display

    if "max_memory_turns" not in st.session_state:
        st.session_state.max_memory_turns = 20  # Max conversation turns to keep in memory

    if "pending_approval" not in st.session_state:
        st.session_state.pending_approval = None  # Track pending approvals for agent action

initialize_session_state()

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def add_message(role: str, content: str, message_type: str = "text"):
    """
    Add a message to chat history.

    Args:
        role: "user", "assistant", "system", or "tool"
        content: Message content
        message_type: "text", "tool_execution", "ticket_approval", etc.
    """
    st.session_state.chat_history.append({
        "role": role,
        "content": content,
        "timestamp": datetime.now(),
        "message_type": message_type
    })
    st.session_state.current_conversation_turns += 1

def get_role_system_prompt(role: str) -> str:
    """Get system prompt tailored to user role."""
    prompts = {
        "Operator": """You are a manufacturing assistant for factory floor operators.
- Provide clear, concise answers about machine operation and safety
- Explain error codes in simple terms
- Help with shift procedures and safety checks
- When issues arise, recommend creating maintenance tickets
- Use safety-focused language
- Keep responses brief and actionable""",

        "Engineer": """You are a technical diagnostic assistant for maintenance engineers.
- Provide detailed technical analysis and troubleshooting steps
- Use engineering terminology and reference technical specs
- Help identify root causes of machine failures
- Recommend maintenance procedures and part replacements
- Suggest technician collaboration when needed
- Include references to error codes and diagnostic history""",

        "Supervisor": """You are an operations assistant for production supervisors.
- Provide real-time status summaries and downtime tracking
- Help coordinate between operators and maintenance teams
- Generate shift handover summaries
- Monitor critical machine failures
- Escalate urgent issues appropriately
- Focus on plant-wide visibility and crew coordination""",

        "Plant Manager": """You are a strategic operations assistant for plant managers.
- Provide KPI dashboards and performance metrics
- Analyze trends and provide predictive insights
- Support data-driven executive decision-making
- Calculate business impact and ROI of maintenance actions
- Support multi-plant comparisons and benchmarking
- Frame recommendations in terms of strategic business outcomes"""
    }
    return prompts.get(role, prompts["Operator"])

def get_memory_context() -> str:
    """Generate memory context from recent conversation turns."""
    # Keep only last N turns to manage token usage
    recent_history = st.session_state.chat_history[-st.session_state.max_memory_turns:]

    context = "Recent conversation context:\n"
    for msg in recent_history:
        if msg["message_type"] == "text":
            context += f"\n{msg['role'].upper()}: {msg['content'][:200]}"

    return context

def display_memory_indicator():
    """Display current memory/context window status."""
    total_turns = st.session_state.current_conversation_turns
    memory_turns = min(len(st.session_state.chat_history), st.session_state.max_memory_turns)

    memory_pct = (memory_turns / st.session_state.max_memory_turns) * 100

    st.markdown(
        f'<div class="memory-indicator">📊 Memory: {memory_turns}/{st.session_state.max_memory_turns} turns '
        f'({memory_pct:.0f}%) | Total conversation: {total_turns} turns</div>',
        unsafe_allow_html=True
    )

def display_tool_execution(tool_name: str, tool_input: Dict[str, Any], status: str = "executing"):
    """Display tool execution in progress."""
    status_icon = "⚙️" if status == "executing" else "✅" if status == "success" else "❌"

    with st.container():
        st.markdown(
            f'<div class="tool-execution">'
            f'{status_icon} <strong>{tool_name}</strong> '
            f'({status})</div>',
            unsafe_allow_html=True
        )
        if tool_input:
            with st.expander("Tool Details", expanded=False):
                st.json(tool_input)

def display_ticket_details(ticket: Dict[str, Any]):
    """Display maintenance ticket details for approval."""
    st.markdown(
        '<div class="ticket-details">',
        unsafe_allow_html=True
    )

    st.subheader("📋 Maintenance Ticket Recommendation")

    col1, col2 = st.columns(2)

    with col1:
        st.write(f"**Machine ID**: {ticket.get('machine_id', 'N/A')}")
        st.write(f"**Issue Type**: {ticket.get('issue_type', 'N/A')}")
        st.write(f"**Priority**: {ticket.get('priority', 'Medium')}")

    with col2:
        st.write(f"**Estimated Duration**: {ticket.get('estimated_duration', 'N/A')}")
        st.write(f"**Required Specialty**: {ticket.get('specialty', 'General Maintenance')}")
        st.write(f"**Parts Needed**: {ticket.get('parts', 'None identified')}")

    st.write("**Description**:")
    st.write(ticket.get('description', 'No description provided'))

    st.write("**Recommended Actions**:")
    if ticket.get('recommended_actions'):
        for i, action in enumerate(ticket['recommended_actions'], 1):
            st.write(f"{i}. {action}")

    st.markdown('</div>', unsafe_allow_html=True)

def display_chat_message(message: Dict[str, Any]):
    """Display a single chat message based on its type."""
    timestamp = message.get("timestamp")
    time_str = timestamp.strftime("%H:%M") if timestamp else ""

    if message["message_type"] == "text":
        with st.chat_message(message["role"], avatar="👤" if message["role"] == "user" else "🤖"):
            st.write(message["content"])
            if time_str:
                st.caption(f"_{time_str}_")

    elif message["message_type"] == "tool_execution":
        display_tool_execution(
            message.get("tool_name", "Unknown"),
            message.get("tool_input", {}),
            message.get("status", "executing")
        )

    elif message["message_type"] == "ticket_approval":
        st.write("**Maintenance Ticket Pending Approval:**")
        display_ticket_details(message.get("ticket_data", {}))

# ============================================================================
# ROLE SELECTOR SIDEBAR
# ============================================================================

st.sidebar.title("🏭 FactoryOps AI")
st.sidebar.markdown("---")

selected_role = st.sidebar.selectbox(
    "Select Your Role",
    options=["Operator", "Engineer", "Supervisor", "Plant Manager"],
    index=["Operator", "Engineer", "Supervisor", "Plant Manager"].index(st.session_state.selected_role)
)

if selected_role != st.session_state.selected_role:
    st.session_state.selected_role = selected_role
    st.session_state.chat_history = []
    st.session_state.current_conversation_turns = 0
    st.session_state.tool_execution_log = []
    st.rerun()

st.sidebar.markdown(f"**Current Role**: {selected_role}")

# Role-specific info
role_descriptions = {
    "Operator": "Quick answers on procedures, errors, and safety checks",
    "Engineer": "Diagnostic workflows and technical troubleshooting",
    "Supervisor": "Real-time status, downtime tracking, and shift coordination",
    "Plant Manager": "Strategic insights, KPIs, and executive reporting"
}

st.sidebar.info(f"📌 {role_descriptions.get(selected_role)}")

# Sidebar actions
st.sidebar.markdown("---")
st.sidebar.subheader("Session Actions")

col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("🔄 Clear Chat", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.current_conversation_turns = 0
        st.session_state.tool_execution_log = []
        st.rerun()

with col2:
    if st.button("💾 Export Chat", use_container_width=True):
        # Prepare chat export as JSON
        export_data = {
            "role": selected_role,
            "exported_at": datetime.now().isoformat(),
            "conversation": [
                {
                    "role": msg["role"],
                    "content": msg["content"],
                    "timestamp": msg["timestamp"].isoformat()
                }
                for msg in st.session_state.chat_history
            ]
        }
        st.sidebar.download_button(
            label="Download JSON",
            data=json.dumps(export_data, indent=2),
            file_name=f"factoryops_chat_{selected_role}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

st.sidebar.markdown("---")

# Settings
with st.sidebar.expander("⚙️ Settings"):
    st.session_state.max_memory_turns = st.slider(
        "Memory Window (conversation turns)",
        min_value=5,
        max_value=50,
        value=st.session_state.max_memory_turns,
        step=5
    )

    st.write("**System Prompt**:")
    st.text_area(
        "View role-specific system prompt",
        value=get_role_system_prompt(selected_role),
        height=120,
        disabled=True
    )

# ============================================================================
# MAIN CHAT INTERFACE
# ============================================================================

st.title("🏭 FactoryOps Manufacturing Assistant")
st.markdown(f"**Role**: {selected_role} | **Memory Context**: ")

display_memory_indicator()

st.markdown("---")

# Chat history display
if st.session_state.chat_history:
    st.subheader("Conversation History")
    for message in st.session_state.chat_history:
        display_chat_message(message)
else:
    st.info("👋 Welcome! Start by asking a question or reporting an issue.")

st.markdown("---")

# ============================================================================
# APPROVAL HANDLING (Chat-based, agent creates via MCP on approval)
# ============================================================================

if st.session_state.pending_approval:
    st.info(f"⏳ Awaiting approval for: {st.session_state.pending_approval.get('description', 'Maintenance action')}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Approve", key="approve_chat", use_container_width=True):
            add_message("user", "✅ Approved", "text")
            st.session_state.pending_approval = None
            st.rerun()

    with col2:
        if st.button("❌ Reject", key="reject_chat", use_container_width=True):
            add_message("user", "❌ Rejected - Please modify the request", "text")
            st.session_state.pending_approval = None
            st.rerun()

# ============================================================================
# USER INPUT & MESSAGE SUBMISSION
# ============================================================================
st.subheader("Your Message")

# Input area
user_input = st.text_area(
    label="Ask a question or describe an issue",
    placeholder="E.g., 'Machine MX-204 showing error E17' or 'How do I reset the pump?'",
    height=80,
    label_visibility="collapsed"
)

col1, col2, col3 = st.columns([3, 1, 1])

with col1:
    submit_btn = st.button("📤 Send Message", use_container_width=True, type="primary")

with col2:
    clear_input = st.button("Clear", use_container_width=True)

if clear_input:
    st.rerun()

# ============================================================================
# MESSAGE PROCESSING & AGENT SIMULATION
# ============================================================================

if submit_btn and user_input.strip():
    # Add user message
    add_message("user", user_input, "text")

    # REAL AGENT PROCESSING - Call actual LangChain agent
    with st.spinner("🤖 Agent processing..."):
        try:
            # Import the real agent engine
            from src.agent_engine import AgentEngine
            import traceback
            import logging

            logger = logging.getLogger(__name__)

            # Map UI role names to agent role names (lowercase)
            role_mapping = {
                "Operator": "operator",
                "Engineer": "engineer",
                "Supervisor": "supervisor",
                "Plant Manager": "plant_manager"
            }
            agent_role = role_mapping.get(selected_role, "operator")

            try:
                # Create fresh agent for this query (simplest approach)
                logger.debug(f"Creating agent for role: {agent_role}")
                agent = AgentEngine(agent_role)
                logger.debug("Agent created successfully")

                # Call the REAL agent with the user input
                logger.debug(f"Processing query: {user_input[:100]}")
                result = agent.process_query(user_input)
                logger.debug(f"Query processed, success: {result.get('success')}")

                # Extract response from agent
                agent_response = result.get("response", "Error: No response from agent")
                tool_calls = result.get("intermediate_steps", [])

                # Display tool calls if any
                if tool_calls:
                    for tool_call in tool_calls:
                        display_tool_execution(
                            tool_name=tool_call.get("tool", "unknown"),
                            tool_input=tool_call.get("input", {}),
                            status="success"
                        )

                # Add actual agent response to chat
                add_message("assistant", agent_response, "text")

            except Exception as agent_error:
                logger.error(f"Agent processing error: {type(agent_error).__name__}")
                logger.error(f"Error message: {str(agent_error)}")
                logger.error(f"Full traceback:\n{traceback.format_exc()}")
                raise agent_error

        except Exception as e:
            error_msg = f"Error calling agent: {str(e)}"
            st.error(error_msg)
            add_message("assistant", error_msg, "text")

            # Also log to console for debugging
            import traceback
            st.error(f"Traceback: {traceback.format_exc()}")

    st.rerun()

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #666; font-size: 0.9em; margin-top: 20px;">
    <p>🏭 FactoryOps AI - Level 2 Agent | Single Agent with Tool Calling</p>
    <p>For technical support, contact the FactoryOps AI team via Slack #factoryops-ai</p>
    </div>
    """,
    unsafe_allow_html=True
)
