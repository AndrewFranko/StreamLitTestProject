import streamlit as st
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Debug: Write all output to file
DEBUG_FILE = "c:/StreamLit/debug_trace.txt"
def debug_log(msg):
    with open(DEBUG_FILE, "a") as f:
        import datetime
        f.write(f"[{datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]}] {msg}\n")
    print(msg)

from agent_engine import AgentEngine
import json
import os
from datetime import datetime

# Chat history persistence
CHAT_HISTORY_DIR = "c:/StreamLit/chat_history"
os.makedirs(CHAT_HISTORY_DIR, exist_ok=True)

def get_chat_file_path(role: str) -> str:
    """Get the file path for saving chat history by role."""
    return os.path.join(CHAT_HISTORY_DIR, f"chat_{role.lower().replace(' ', '_')}.json")

def save_chat_history(role: str, chat_history: list):
    """Auto-save chat history to file."""
    try:
        file_path = get_chat_file_path(role)
        chat_data = {
            "role": role,
            "last_updated": datetime.now().isoformat(),
            "messages": chat_history
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(chat_data, f, indent=2, ensure_ascii=False)
        debug_log(f"[SAVE] Chat history saved for {role} ({len(chat_history)} messages)")
    except Exception as e:
        debug_log(f"[ERROR] Failed to save chat history: {str(e)}")

def load_chat_history(role: str) -> list:
    """Load chat history from file."""
    try:
        file_path = get_chat_file_path(role)
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                data = json.load(f)
                messages = data.get("messages", [])
                debug_log(f"[LOAD] Chat history loaded for {role} ({len(messages)} messages)")
                return messages
    except Exception as e:
        debug_log(f"[ERROR] Failed to load chat history: {str(e)}")
    return []

# Page configuration
st.set_page_config(
    page_title="FactoryOps AI",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Page navigation in sidebar
st.sidebar.markdown("## 📑 Navigation")
page = st.sidebar.radio(
    "Select Page:",
    options=["💬 Chat", "📊 Conversations"],
    horizontal=False
)
st.sidebar.divider()

# Initialize session state
if "role" not in st.session_state:
    st.session_state.role = "Operator"

if "chat_history" not in st.session_state:
    # Load saved chat history if it exists
    st.session_state.chat_history = load_chat_history("Operator")

if "pending_approval" not in st.session_state:
    st.session_state.pending_approval = None

if "approval_key" not in st.session_state:
    st.session_state.approval_key = None

if "agent" not in st.session_state:
    st.session_state.agent = None

if "current_role" not in st.session_state:
    st.session_state.current_role = "Operator"


def show_chat_page():
    """Display the main chat interface."""
    # Sidebar: Role selection and controls
    st.sidebar.title("🏭 FactoryOps AI")

selected_role = st.sidebar.selectbox(
    "Select Role:",
    options=["Operator", "Engineer", "Supervisor", "Plant Manager"],
    index=["Operator", "Engineer", "Supervisor", "Plant Manager"].index(st.session_state.role)
)

# Update role if changed
if selected_role != st.session_state.role:
    # Save current chat history before switching
    save_chat_history(st.session_state.role, st.session_state.chat_history)

    # Load chat history for new role
    st.session_state.role = selected_role
    st.session_state.chat_history = load_chat_history(selected_role)
    st.session_state.pending_approval = None
    st.rerun()

st.sidebar.markdown(f"**Current Role:** {st.session_state.role}")
st.sidebar.divider()

col1, col2 = st.sidebar.columns(2)

with col1:
    if st.button("🗑️ Clear", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.pending_approval = None
        save_chat_history(st.session_state.role, st.session_state.chat_history)
        st.rerun()

with col2:
    if st.button("💾 Save", use_container_width=True):
        import json
        from datetime import datetime

        # Prepare chat for export
        export_data = {
            "role": st.session_state.role,
            "exported_at": datetime.now().isoformat(),
            "messages": st.session_state.chat_history
        }

        # Create download button
        json_str = json.dumps(export_data, indent=2)
        st.download_button(
            label="Download JSON",
            data=json_str,
            file_name=f"chat_{st.session_state.role}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            key=f"download_{datetime.now().timestamp()}"
        )

st.sidebar.divider()
st.sidebar.markdown("**About**")
st.sidebar.markdown(
    "AI-powered manufacturing assistant for machine operators, maintenance engineers, "
    "supervisors, and plant managers."
)


# Main chat area
st.title("🏭 FactoryOps AI – Manufacturing Assistant")
st.markdown(f"*Role: {st.session_state.role}* | *Memory: {len(st.session_state.chat_history)} messages*")

# Display chat history with better styling
st.subheader("💬 Conversation")
chat_container = st.container(border=True, height=500)

with chat_container:
    if st.session_state.chat_history:
        for i, message in enumerate(st.session_state.chat_history):
            if message["role"] == "user":
                with st.chat_message("user", avatar="👤"):
                    st.markdown(message['content'])
            else:
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(message['content'])
    else:
        st.info("👋 Welcome! Start by typing a message below.")


# Approval flow for critical actions
if st.session_state.pending_approval:
    st.divider()
    st.warning("⚠️ Action Requires Approval")

    approval_data = st.session_state.pending_approval

    st.markdown("**Summary:**")
    st.info(approval_data.get("summary", "Action pending approval"))

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Approve", key=f"approve_{st.session_state.approval_key}", use_container_width=True):
            st.session_state.pending_approval = None
            st.session_state.approval_key = None

            st.session_state.chat_history.append({
                "role": "user",
                "content": f"[APPROVED] {approval_data.get('action_summary', 'Action approved')}"
            })

            action_result = f"✅ {approval_data.get('summary', 'Action executed successfully')}"
            st.session_state.chat_history.append({
                "role": "agent",
                "content": action_result
            })

            st.rerun()

    with col2:
        if st.button("❌ Cancel", key=f"cancel_{st.session_state.approval_key}", use_container_width=True):
            st.session_state.pending_approval = None
            st.session_state.approval_key = None

            st.session_state.chat_history.append({
                "role": "agent",
                "content": "Action cancelled."
            })

            st.rerun()


# Input area
st.divider()
st.subheader("Chat")

col1, col2 = st.columns([0.9, 0.1])

with col1:
    user_input = st.text_input(
        "Ask me anything about manufacturing operations:",
        placeholder="e.g., 'What does error code E17 mean?' or 'Create a maintenance ticket for machine MX-204'",
        key="chat_input",
        max_chars=2000
    )

with col2:
    send_button = st.button("Send", use_container_width=True, key="send_btn")


# Validate input before processing
input_error = None
if send_button:
    if not user_input or not user_input.strip():
        input_error = "Please enter a message before sending"
    elif len(user_input.strip()) < 2:
        input_error = "Message is too short (minimum 2 characters)"
    elif len(user_input) > 2000:
        input_error = "Message is too long (maximum 2000 characters)"

if input_error:
    st.error(f"Input Error: {input_error}")
elif send_button and user_input.strip():
    # Add user message to chat history
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_input
    })

    # Get agent response
    with st.spinner("🤖 Processing..."):
        try:
            # Map UI role names to agent role names (lowercase)
            role_mapping = {
                "Operator": "operator",
                "Engineer": "engineer",
                "Supervisor": "supervisor",
                "Plant Manager": "plant_manager"
            }
            agent_role = role_mapping.get(selected_role, "operator")

            # Debug: Log before agent call
            debug_log(f"[UI] Creating agent for role: {agent_role}")
            debug_log(f"[UI] User input: {user_input}")

            # Reuse agent if same role, otherwise create new one
            if st.session_state.current_role != selected_role or st.session_state.agent is None:
                debug_log(f"[UI] Creating NEW agent for role: {agent_role}")
                agent = AgentEngine(agent_role)
                st.session_state.agent = agent
                st.session_state.current_role = selected_role
            else:
                debug_log(f"[UI] Reusing existing agent for role: {agent_role}")
                agent = st.session_state.agent

            debug_log(f"[UI] Agent ready successfully")

            result = agent.process_query(user_input)
            debug_log(f"[UI] Agent result received: {type(result)}")
            debug_log(f"[UI] Result success: {result.get('success')}")
            debug_log(f"[UI] Response type: {type(result.get('response'))}")
            debug_log(f"[UI] Response length: {len(str(result.get('response', '')))}")

            # Extract response and tool calls
            response_text = result.get("response", "No response generated.")
            tool_calls = result.get("intermediate_steps", [])

            debug_log(f"[UI] Extracted response: {response_text[:100]}")
            debug_log(f"[UI] Tool calls: {len(tool_calls)}")

            # Debug: Check if response is empty
            if not response_text or len(response_text.strip()) == 0:
                debug_log(f"[UI] WARNING: Response is empty!")
                st.warning("Warning: Agent returned empty response")
                response_text = "I was unable to generate a response. Please try again."

            debug_log(f"[UI] About to display tool calls...")

            # Display tool execution info if tools were used
            if tool_calls:
                with st.expander(f"🔧 Tool Calls ({len(tool_calls)})"):
                    for i, tool_call in enumerate(tool_calls, 1):
                        st.write(f"**Tool {i}: {tool_call.get('tool', 'Unknown')}**")
                        if tool_call.get('input'):
                            st.json(tool_call['input'])
                        if tool_call.get('output'):
                            st.caption(f"Result: {str(tool_call['output'])[:200]}")

            # Check for critical actions that need approval
            if any(keyword in response_text.lower() for keyword in ["create ticket", "create maintenance", "critical failure", "escalate"]):
                # Extract action summary for approval
                approval_summary = f"Create ticket for {user_input}"
                if "mx-" in response_text.lower():
                    import re
                    match = re.search(r'(mx-\d+)', response_text.lower())
                    if match:
                        approval_summary = f"Create ticket for {match.group(0).upper()}: {user_input}"

                st.session_state.pending_approval = {
                    "summary": approval_summary,
                    "action_summary": user_input,
                    "response": response_text
                }
                st.session_state.approval_key = len(st.session_state.chat_history)

                st.session_state.chat_history.append({
                    "role": "agent",
                    "content": response_text + "\n\n*⏳ Action pending your approval below.*"
                })
            else:
                st.session_state.chat_history.append({
                    "role": "agent",
                    "content": response_text
                })

            # Auto-save chat history after each message
            save_chat_history(st.session_state.role, st.session_state.chat_history)
            debug_log(f"[AUTO-SAVE] Chat history auto-saved for {st.session_state.role}")

            st.rerun()

        except Exception as e:
            error_msg = f"Error processing request: {str(e)}"
            debug_log(f"[UI] EXCEPTION CAUGHT: {type(e).__name__}")
            debug_log(f"[UI] Error message: {str(e)}")
            debug_log(f"[UI] Full exception: {repr(e)}")
            import traceback
            debug_log(f"[UI] Traceback:\n{traceback.format_exc()}")

            st.session_state.chat_history.append({
                "role": "agent",
                "content": error_msg
            })
            st.error(error_msg)
            st.rerun()


def show_conversations_page():
    """Display saved conversations."""
    st.title("📊 Saved Conversations")
    st.markdown("View and manage your saved chat conversations.")

    st.info("Conversations are automatically saved by role. Switch roles in the Chat page to view conversations for different roles.")


# Show different pages based on selection
if page == "💬 Chat":
    show_chat_page()
elif page == "📊 Conversations":
    show_conversations_page()
