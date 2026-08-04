import streamlit as st
import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agent_engine import AgentEngine

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
    except Exception as e:
        st.error(f"Failed to save chat history: {str(e)}")


def load_chat_history(role: str) -> list:
    """Load chat history from file."""
    try:
        file_path = get_chat_file_path(role)
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                data = json.load(f)
                return data.get("messages", [])
    except Exception as e:
        st.error(f"Failed to load chat history: {str(e)}")
    return []


def show_chat_page():
    """Display the main chat interface."""
    st.sidebar.title("🏭 FactoryOps AI")

    selected_role = st.sidebar.selectbox(
        "Select Role:",
        options=["Operator", "Engineer", "Supervisor", "Plant Manager"],
        index=["Operator", "Engineer", "Supervisor", "Plant Manager"].index(st.session_state.role)
    )

    if selected_role != st.session_state.role:
        save_chat_history(st.session_state.role, st.session_state.chat_history)
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
            export_data = {
                "role": st.session_state.role,
                "exported_at": datetime.now().isoformat(),
                "messages": st.session_state.chat_history
            }
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

    st.title("🏭 FactoryOps AI – Manufacturing Assistant")
    st.markdown(f"*Role: {st.session_state.role}* | *Memory: {len(st.session_state.chat_history)} messages*")

    st.subheader("💬 Conversation")
    chat_container = st.container(border=True, height=500)

    with chat_container:
        if st.session_state.chat_history:
            for message in st.session_state.chat_history:
                if message["role"] == "user":
                    with st.chat_message("user", avatar="👤"):
                        st.markdown(message['content'])
                else:
                    with st.chat_message("assistant", avatar="🤖"):
                        st.markdown(message['content'])
        else:
            st.info("👋 Welcome! Start by typing a message below.")

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
                st.session_state.chat_history.append({
                    "role": "agent",
                    "content": f"✅ {approval_data.get('summary', 'Action executed successfully')}"
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

    st.divider()
    st.subheader("Chat")

    col1, col2 = st.columns([0.9, 0.1])

    with col1:
        user_input = st.text_input(
            "Ask me anything about manufacturing operations:",
            placeholder="e.g., 'What does error code E17 mean?'",
            key="chat_input",
            max_chars=2000
        )

    with col2:
        send_button = st.button("Send", use_container_width=True, key="send_btn")

    input_error = None
    if send_button:
        if not user_input or not user_input.strip():
            input_error = "Please enter a message before sending"
        elif len(user_input.strip()) < 2:
            input_error = "Message is too short (minimum 2 characters)"

    if input_error:
        st.error(f"Input Error: {input_error}")
    elif send_button and user_input.strip():
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input
        })

        with st.spinner("🤖 Processing..."):
            try:
                role_mapping = {
                    "Operator": "operator",
                    "Engineer": "engineer",
                    "Supervisor": "supervisor",
                    "Plant Manager": "plant_manager"
                }
                agent_role = role_mapping.get(st.session_state.role, "operator")

                if st.session_state.current_role != st.session_state.role or st.session_state.agent is None:
                    agent = AgentEngine(agent_role)
                    st.session_state.agent = agent
                    st.session_state.current_role = st.session_state.role
                else:
                    agent = st.session_state.agent

                result = agent.process_query(user_input)
                response_text = result.get("response", "No response generated.")
                tool_calls = result.get("intermediate_steps", [])

                if not response_text or len(response_text.strip()) == 0:
                    st.warning("Warning: Agent returned empty response")
                    response_text = "I was unable to generate a response. Please try again."

                if tool_calls:
                    with st.expander(f"🔧 Tool Calls ({len(tool_calls)})"):
                        for i, tool_call in enumerate(tool_calls, 1):
                            st.write(f"**Tool {i}: {tool_call.get('tool', 'Unknown')}**")
                            if tool_call.get('input'):
                                st.json(tool_call['input'])

                if any(keyword in response_text.lower() for keyword in ["create ticket", "critical failure"]):
                    st.session_state.pending_approval = {
                        "summary": f"Create ticket for {user_input}",
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

                save_chat_history(st.session_state.role, st.session_state.chat_history)
                st.rerun()

            except Exception as e:
                error_msg = f"Error processing request: {str(e)}"
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


st.set_page_config(
    page_title="FactoryOps AI",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.sidebar.markdown("## 📑 Navigation")
page = st.sidebar.radio(
    "Select Page:",
    options=["💬 Chat", "📊 Conversations"],
    horizontal=False
)
st.sidebar.divider()

if "role" not in st.session_state:
    st.session_state.role = "Operator"

if "chat_history" not in st.session_state:
    st.session_state.chat_history = load_chat_history("Operator")

if "pending_approval" not in st.session_state:
    st.session_state.pending_approval = None

if "approval_key" not in st.session_state:
    st.session_state.approval_key = None

if "agent" not in st.session_state:
    st.session_state.agent = None

if "current_role" not in st.session_state:
    st.session_state.current_role = "Operator"

if page == "💬 Chat":
    show_chat_page()
elif page == "📊 Conversations":
    show_conversations_page()
