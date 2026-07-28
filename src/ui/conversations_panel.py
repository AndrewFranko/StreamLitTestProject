"""
Conversations Management Panel
View, search, and analyze all saved conversations
"""

import streamlit as st
import json
import os
from datetime import datetime
from pathlib import Path

CHAT_HISTORY_DIR = "c:/StreamLit/chat_history"

def get_all_conversations():
    """Get all saved conversations."""
    conversations = []

    if not os.path.exists(CHAT_HISTORY_DIR):
        return conversations

    for file in os.listdir(CHAT_HISTORY_DIR):
        if file.endswith(".json"):
            file_path = os.path.join(CHAT_HISTORY_DIR, file)
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    conversations.append({
                        "file": file,
                        "path": file_path,
                        "role": data.get("role", "Unknown"),
                        "last_updated": data.get("last_updated", "N/A"),
                        "message_count": len(data.get("messages", [])),
                        "messages": data.get("messages", [])
                    })
            except Exception as e:
                st.warning(f"Error loading {file}: {str(e)}")

    return sorted(conversations, key=lambda x: x["last_updated"], reverse=True)

def display_conversation(conv):
    """Display a full conversation."""
    st.subheader(f"💬 {conv['role']} - {conv['message_count']} messages")
    st.caption(f"Last updated: {conv['last_updated']}")

    if conv['messages']:
        for msg in conv['messages']:
            if msg.get("role") == "user":
                with st.chat_message("user", avatar="👤"):
                    st.markdown(msg.get("content", ""))
            else:
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(msg.get("content", ""))
    else:
        st.info("No messages in this conversation")

def delete_conversation(file_path):
    """Delete a conversation file."""
    try:
        os.remove(file_path)
        st.success("Conversation deleted!")
        st.rerun()
    except Exception as e:
        st.error(f"Error deleting conversation: {str(e)}")

def export_conversation(conv):
    """Export conversation as JSON."""
    return json.dumps(conv, indent=2)

def main():
    st.set_page_config(
        page_title="Conversations Panel",
        page_icon="📊",
        layout="wide"
    )

    st.title("📊 Conversations Management Panel")
    st.markdown("View, analyze, and manage all saved conversations")
    st.divider()

    # Get all conversations
    conversations = get_all_conversations()

    if not conversations:
        st.info("No conversations saved yet. Start chatting to see them here!")
        return

    # Summary stats
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Conversations", len(conversations))

    with col2:
        total_messages = sum(c["message_count"] for c in conversations)
        st.metric("Total Messages", total_messages)

    with col3:
        roles = set(c["role"] for c in conversations)
        st.metric("Roles Used", len(roles))

    with col4:
        st.metric("Latest Update", conversations[0]["last_updated"][:10] if conversations else "N/A")

    st.divider()

    # Filter and view options
    col1, col2, col3 = st.columns(3)

    with col1:
        search_term = st.text_input("🔍 Search in conversations")

    with col2:
        selected_roles = st.multiselect(
            "Filter by role",
            options=sorted(set(c["role"] for c in conversations)),
            default=sorted(set(c["role"] for c in conversations))
        )

    with col3:
        sort_by = st.selectbox("Sort by", ["Last Updated", "Message Count", "Role"])

    # Filter conversations
    filtered = conversations

    if selected_roles:
        filtered = [c for c in filtered if c["role"] in selected_roles]

    if search_term:
        filtered = [
            c for c in filtered
            if any(search_term.lower() in msg.get("content", "").lower()
                   for msg in c.get("messages", []))
        ]

    # Sort conversations
    if sort_by == "Message Count":
        filtered = sorted(filtered, key=lambda x: x["message_count"], reverse=True)
    elif sort_by == "Role":
        filtered = sorted(filtered, key=lambda x: x["role"])

    st.divider()

    if not filtered:
        st.warning("No conversations match your filters")
        return

    st.subheader(f"📋 Conversations ({len(filtered)})")

    # Display conversations in expandable sections
    for i, conv in enumerate(filtered):
        with st.expander(
            f"**{conv['role']}** - {conv['message_count']} messages - {conv['last_updated'][:19]}",
            expanded=False
        ):
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                if st.button("📖 View Full", key=f"view_{i}"):
                    st.session_state[f"show_conv_{i}"] = True

            with col2:
                csv_data = json.dumps(conv, indent=2)
                st.download_button(
                    "💾 Export",
                    data=csv_data,
                    file_name=f"conversation_{conv['role']}_{conv['last_updated'][:10]}.json",
                    mime="application/json",
                    key=f"download_{i}"
                )

            with col3:
                if st.button("🗑️ Delete", key=f"delete_{i}"):
                    delete_conversation(conv["path"])

            # Show preview
            st.markdown("**Preview:**")
            preview_messages = conv['messages'][-3:] if conv['messages'] else []
            for msg in preview_messages:
                role = "👤 User" if msg.get("role") == "user" else "🤖 Agent"
                content = msg.get("content", "")[:100]
                st.caption(f"{role}: {content}...")

        # Show full conversation if requested
        if st.session_state.get(f"show_conv_{i}"):
            with st.container(border=True):
                display_conversation(conv)

    st.divider()
    st.markdown("""
    ### 📊 About This Panel
    - All conversations are automatically saved after each message
    - Each role has its own conversation history
    - Use the search and filter options to find specific conversations
    - Export conversations as JSON for backup or analysis
    - Delete conversations to clean up old data
    """)

if __name__ == "__main__":
    main()
