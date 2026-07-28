import streamlit as st
import sys
import os

# Add src directory to path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Debug: Write all output to file
DEBUG_FILE = "c:/StreamLit/debug_trace.txt"
def debug_log(msg):
    with open(DEBUG_FILE, "a", encoding="utf-8") as f:
        import datetime
        f.write(f"[{datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]}] {msg}\n")
    print(msg)

from agent_engine import AgentEngine
from mcp_ticket_server import create_ticket as mcp_create_ticket, ticket_summary
import json
from datetime import datetime
import uuid
import re

# Chat history persistence
CHAT_HISTORY_DIR = "c:/StreamLit/chat_history"
os.makedirs(CHAT_HISTORY_DIR, exist_ok=True)

def get_role_chat_dir(role: str) -> str:
    """Get the directory for a role's chats."""
    role_dir = os.path.join(CHAT_HISTORY_DIR, role.lower().replace(' ', '_'))
    os.makedirs(role_dir, exist_ok=True)
    return role_dir

def get_all_chats_for_role(role: str) -> list:
    """Get all saved chats for a role."""
    role_dir = get_role_chat_dir(role)
    chats = []

    for file in os.listdir(role_dir):
        if file.endswith(".json") and file != "metadata.json":
            file_path = os.path.join(role_dir, file)
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    chats.append({
                        "id": file.replace(".json", ""),
                        "name": data.get("name", "Untitled"),
                        "created": data.get("created", "N/A"),
                        "last_updated": data.get("last_updated", "N/A"),
                        "message_count": len(data.get("messages", [])),
                        "path": file_path
                    })
            except Exception as e:
                debug_log(f"[ERROR] Failed to load chat {file}: {str(e)}")

    return sorted(chats, key=lambda x: x["last_updated"], reverse=True)

def save_chat(role: str, chat_id: str, chat_name: str, messages: list):
    """Save a chat to file."""
    try:
        role_dir = get_role_chat_dir(role)
        file_path = os.path.join(role_dir, f"{chat_id}.json")

        chat_data = {
            "id": chat_id,
            "name": chat_name,
            "role": role,
            "created": st.session_state.get(f"{chat_id}_created", datetime.now().isoformat()),
            "last_updated": datetime.now().isoformat(),
            "messages": messages
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(chat_data, f, indent=2, ensure_ascii=False)
        debug_log(f"[SAVE] Chat saved: {chat_id} ({len(messages)} messages)")
    except Exception as e:
        debug_log(f"[ERROR] Failed to save chat: {str(e)}")

def load_chat(role: str, chat_id: str) -> dict:
    """Load a specific chat."""
    try:
        role_dir = get_role_chat_dir(role)
        file_path = os.path.join(role_dir, f"{chat_id}.json")

        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                data = json.load(f)
                debug_log(f"[LOAD] Chat loaded: {chat_id} ({len(data.get('messages', []))} messages)")
                return data
    except Exception as e:
        debug_log(f"[ERROR] Failed to load chat: {str(e)}")

    return None

def create_new_chat(role: str, chat_name: str = None) -> str:
    """Create a new chat and return its ID."""
    chat_id = str(uuid.uuid4())[:8]
    if chat_name is None:
        chat_name = f"Chat - {datetime.now().strftime('%Y-%m-%d %H:%M')}"

    st.session_state[f"{chat_id}_created"] = datetime.now().isoformat()
    save_chat(role, chat_id, chat_name, [])
    debug_log(f"[NEW CHAT] Created: {chat_id}")
    return chat_id

def delete_chat(role: str, chat_id: str):
    """Delete a chat file."""
    try:
        role_dir = get_role_chat_dir(role)
        file_path = os.path.join(role_dir, f"{chat_id}.json")
        if os.path.exists(file_path):
            os.remove(file_path)
            debug_log(f"[DELETE] Chat deleted: {chat_id}")
            return True
    except Exception as e:
        debug_log(f"[ERROR] Failed to delete chat: {str(e)}")
    return False

def rename_chat(role: str, chat_id: str, new_name: str):
    """Rename a chat."""
    try:
        chat_data = load_chat(role, chat_id)
        if chat_data:
            chat_data["name"] = new_name
            role_dir = get_role_chat_dir(role)
            file_path = os.path.join(role_dir, f"{chat_id}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(chat_data, f, indent=2, ensure_ascii=False)
            debug_log(f"[RENAME] Chat renamed: {chat_id} -> {new_name}")
            return True
    except Exception as e:
        debug_log(f"[ERROR] Failed to rename chat: {str(e)}")
    return False

# Page configuration
st.set_page_config(
    page_title="FactoryOps AI - Chat",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "role" not in st.session_state:
    st.session_state.role = "Operator"

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

if "current_chat_name" not in st.session_state:
    st.session_state.current_chat_name = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "agent" not in st.session_state:
    st.session_state.agent = None

if "pending_approval" not in st.session_state:
    st.session_state.pending_approval = None

if "approval_key" not in st.session_state:
    st.session_state.approval_key = None

if "show_chat_list" not in st.session_state:
    st.session_state.show_chat_list = False


# Sidebar: Role selection
st.sidebar.title("🏭 FactoryOps AI")

selected_role = st.sidebar.selectbox(
    "Select Role:",
    options=["Operator", "Engineer", "Supervisor", "Plant Manager"],
    index=["Operator", "Engineer", "Supervisor", "Plant Manager"].index(st.session_state.role)
)

# Update role if changed
if selected_role != st.session_state.role:
    if st.session_state.current_chat_id and st.session_state.chat_history:
        save_chat(st.session_state.role, st.session_state.current_chat_id,
                 st.session_state.current_chat_name, st.session_state.chat_history)

    st.session_state.role = selected_role
    st.session_state.current_chat_id = None
    st.session_state.current_chat_name = None
    st.session_state.chat_history = []
    st.rerun()

st.sidebar.markdown(f"**Current Role:** {st.session_state.role}")
st.sidebar.divider()

# Chat selection and management
st.sidebar.markdown("### 💬 Chats")

# Get all chats for current role
all_chats = get_all_chats_for_role(st.session_state.role)

# New chat button
if st.sidebar.button("➕ New Chat", use_container_width=True):
    new_chat_id = create_new_chat(st.session_state.role)
    st.session_state.current_chat_id = new_chat_id
    st.session_state.current_chat_name = f"Chat - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    st.session_state.chat_history = []
    st.rerun()

# Display chat list
if all_chats:
    st.sidebar.markdown(f"**Saved Chats ({len(all_chats)})**")

    for chat in all_chats:
        col1, col2, col3 = st.sidebar.columns([3, 1, 1])

        with col1:
            # Button to load chat
            chat_label = f"{chat['name'][:20]}... ({chat['message_count']} msgs)" if len(chat['name']) > 20 else f"{chat['name']} ({chat['message_count']} msgs)"

            if st.button(chat_label, key=f"load_{chat['id']}", use_container_width=True):
                # Save current chat if any
                if st.session_state.current_chat_id and st.session_state.chat_history:
                    save_chat(st.session_state.role, st.session_state.current_chat_id,
                             st.session_state.current_chat_name, st.session_state.chat_history)

                # Load selected chat
                chat_data = load_chat(st.session_state.role, chat['id'])
                if chat_data:
                    st.session_state.current_chat_id = chat['id']
                    st.session_state.current_chat_name = chat['name']
                    st.session_state.chat_history = chat_data.get('messages', [])
                    st.rerun()

        with col2:
            if st.button("✏️", key=f"rename_{chat['id']}", use_container_width=True):
                st.session_state[f"rename_{chat['id']}"] = True

        with col3:
            if st.button("🗑️", key=f"delete_{chat['id']}", use_container_width=True):
                if delete_chat(st.session_state.role, chat['id']):
                    if st.session_state.current_chat_id == chat['id']:
                        st.session_state.current_chat_id = None
                        st.session_state.current_chat_name = None
                        st.session_state.chat_history = []
                    st.rerun()

        # Rename input
        if st.session_state.get(f"rename_{chat['id']}"):
            new_name = st.sidebar.text_input(f"Rename '{chat['name']}':", value=chat['name'], key=f"rename_input_{chat['id']}")
            col1, col2 = st.sidebar.columns(2)
            with col1:
                if st.button("✅", key=f"rename_confirm_{chat['id']}"):
                    if rename_chat(st.session_state.role, chat['id'], new_name):
                        st.session_state[f"rename_{chat['id']}"] = False
                        if st.session_state.current_chat_id == chat['id']:
                            st.session_state.current_chat_name = new_name
                        st.rerun()
            with col2:
                if st.button("❌", key=f"rename_cancel_{chat['id']}"):
                    st.session_state[f"rename_{chat['id']}"] = False
                    st.rerun()

st.sidebar.divider()

col1, col2 = st.sidebar.columns(2)

with col1:
    if st.button("🗑️ Clear Chat", use_container_width=True):
        if st.session_state.current_chat_id:
            st.session_state.chat_history = []
            save_chat(st.session_state.role, st.session_state.current_chat_id,
                     st.session_state.current_chat_name, [])
            st.rerun()

with col2:
    if st.button("💾 Export", use_container_width=True):
        if st.session_state.current_chat_id:
            export_data = {
                "role": st.session_state.role,
                "chat_name": st.session_state.current_chat_name,
                "exported_at": datetime.now().isoformat(),
                "messages": st.session_state.chat_history
            }
            st.session_state["export_json"] = json.dumps(export_data, indent=2)

st.sidebar.divider()
st.sidebar.markdown("**About**")
st.sidebar.markdown(
    "AI-powered manufacturing assistant for machine operators, maintenance engineers, "
    "supervisors, and plant managers."
)

# Main chat area
st.title("🏭 FactoryOps AI – Manufacturing Assistant")

if not st.session_state.current_chat_id:
    st.info("👈 Select or create a chat from the sidebar to get started!")
else:
    st.markdown(f"*Role: {st.session_state.role}* | *Chat: {st.session_state.current_chat_name}* | *Memory: {len(st.session_state.chat_history)} messages*")

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
    if st.session_state.pending_approval and st.session_state.pending_approval.get("awaiting_approval"):
        st.divider()
        st.warning("⚠️ Action Requires Approval")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("✅ Approve", key=f"approve_{st.session_state.approval_key}", use_container_width=True):
                debug_log("[APPROVAL] User approved action - Processing with agent...")

                # Add approval message to history
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": "✅ Approved"
                })

                # Process approval with agent (agent will call create_maintenance_ticket via MCP)
                try:
                    approval_message = "✅ Approved"
                    debug_log(f"[APPROVAL] Sending '{approval_message}' to agent")

                    role_mapping = {
                        "Operator": "operator",
                        "Engineer": "engineer",
                        "Supervisor": "supervisor",
                        "Plant Manager": "plant_manager"
                    }
                    agent_role = role_mapping.get(st.session_state.role, "operator")
                    agent = st.session_state.agent or AgentEngine(agent_role)

                    result = agent.process_query(approval_message)
                    response_text = result.get("response", "Ticket created successfully.")

                    debug_log(f"[APPROVAL] Agent response: {response_text[:100]}")

                    # Add agent response to chat
                    st.session_state.chat_history.append({
                        "role": "agent",
                        "content": response_text
                    })

                except Exception as e:
                    error_msg = f"Error processing approval: {str(e)}"
                    debug_log(f"[APPROVAL ERROR] {error_msg}")
                    st.session_state.chat_history.append({
                        "role": "agent",
                        "content": error_msg
                    })

                # Clear approval state
                st.session_state.pending_approval = None
                st.session_state.approval_key = None

                # Save and rerun
                if st.session_state.current_chat_id:
                    save_chat(st.session_state.role, st.session_state.current_chat_id,
                             st.session_state.current_chat_name, st.session_state.chat_history)
                st.rerun()

        with col2:
            if st.button("❌ Reject", key=f"reject_{st.session_state.approval_key}", use_container_width=True):
                debug_log("[APPROVAL] User rejected action - Processing with agent...")

                # Add rejection message to history
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": "❌ Rejected"
                })

                # Process rejection with agent (agent will handle the rejection)
                try:
                    rejection_message = "❌ Rejected"
                    debug_log(f"[APPROVAL] Sending '{rejection_message}' to agent")

                    role_mapping = {
                        "Operator": "operator",
                        "Engineer": "engineer",
                        "Supervisor": "supervisor",
                        "Plant Manager": "plant_manager"
                    }
                    agent_role = role_mapping.get(st.session_state.role, "operator")
                    agent = st.session_state.agent or AgentEngine(agent_role)

                    result = agent.process_query(rejection_message)
                    response_text = result.get("response", "Action cancelled.")

                    debug_log(f"[APPROVAL] Agent response: {response_text[:100]}")

                    # Add agent response to chat
                    st.session_state.chat_history.append({
                        "role": "agent",
                        "content": response_text
                    })

                except Exception as e:
                    error_msg = f"Error processing rejection: {str(e)}"
                    debug_log(f"[APPROVAL ERROR] {error_msg}")
                    st.session_state.chat_history.append({
                        "role": "agent",
                        "content": error_msg
                    })

                # Clear approval state
                st.session_state.pending_approval = None
                st.session_state.approval_key = None

                # Save and rerun
                if st.session_state.current_chat_id:
                    save_chat(st.session_state.role, st.session_state.current_chat_id,
                             st.session_state.current_chat_name, st.session_state.chat_history)
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

                debug_log(f"[UI] Creating agent for role: {agent_role}")
                debug_log(f"[UI] User input: {user_input}")

                # Create fresh agent for each query
                debug_log(f"[UI] Creating NEW agent for role: {agent_role}")
                agent = AgentEngine(agent_role)
                st.session_state.agent = agent

                debug_log(f"[UI] Agent ready successfully")

                result = agent.process_query(user_input)
                debug_log(f"[UI] Agent result received: {type(result)}")
                debug_log(f"[UI] Result success: {result.get('success')}")

                response_text = result.get("response", "No response generated.")
                tool_calls = result.get("intermediate_steps", [])

                # Ensure response_text is a string, not a dict or JSON
                if isinstance(response_text, dict):
                    response_text = str(response_text.get("content", str(response_text)))

                response_text = str(response_text).strip()

                debug_log(f"[UI] Extracted response: {response_text[:100]}")
                debug_log(f"[UI] Tool calls: {len(tool_calls)}")

                if not response_text or len(response_text.strip()) == 0:
                    debug_log(f"[UI] WARNING: Response is empty!")
                    st.warning("Warning: Agent returned empty response")
                    response_text = "I was unable to generate a response. Please try again."

                # Check if request_approval tool was called
                has_approval_request = any(
                    tc.get('tool') == 'request_approval'
                    for tc in tool_calls
                )

                if tool_calls:
                    with st.expander(f"🔧 Tool Calls ({len(tool_calls)})"):
                        for i, tool_call in enumerate(tool_calls, 1):
                            st.write(f"**Tool {i}: {tool_call.get('tool', 'Unknown')}**")
                            if tool_call.get('input'):
                                st.json(tool_call['input'])
                            if tool_call.get('output'):
                                st.caption(f"Result: {str(tool_call['output'])[:200]}")

                # If agent called request_approval, show approval buttons
                if has_approval_request:
                    st.session_state.pending_approval = {
                        "response": response_text,
                        "awaiting_approval": True
                    }
                    st.session_state.approval_key = len(st.session_state.chat_history)

                    st.session_state.chat_history.append({
                        "role": "agent",
                        "content": response_text + "\n\n⏳ *Awaiting your approval to proceed...*"
                    })
                else:
                    st.session_state.chat_history.append({
                        "role": "agent",
                        "content": response_text
                    })

                # Auto-save chat
                if st.session_state.current_chat_id:
                    save_chat(st.session_state.role, st.session_state.current_chat_id,
                             st.session_state.current_chat_name, st.session_state.chat_history)
                debug_log(f"[AUTO-SAVE] Chat auto-saved")

                st.rerun()

            except Exception as e:
                error_msg = f"Error processing request: {str(e)}"
                debug_log(f"[UI] EXCEPTION CAUGHT: {type(e).__name__}")
                debug_log(f"[UI] Error message: {str(e)}")
                import traceback
                debug_log(f"[UI] Traceback:\n{traceback.format_exc()}")

                st.session_state.chat_history.append({
                    "role": "agent",
                    "content": error_msg
                })
                st.error(error_msg)
                st.rerun()

# Show export button if export data is ready
if "export_json" in st.session_state:
    st.divider()
    st.download_button(
        label="📥 Download Chat as JSON",
        data=st.session_state["export_json"],
        file_name=f"chat_{st.session_state.role}_{st.session_state.current_chat_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )
    if st.button("Close Export"):
        del st.session_state["export_json"]
        st.rerun()
