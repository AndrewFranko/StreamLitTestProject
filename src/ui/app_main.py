"""
FactoryOps AI - Main App with Multi-Page Support
"""

import streamlit as st

# Page config
st.set_page_config(
    page_title="FactoryOps AI",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for page
if "page" not in st.session_state:
    st.session_state.page = "Chat"

# Sidebar navigation
st.sidebar.title("🏭 FactoryOps AI")
st.sidebar.divider()

st.sidebar.markdown("## 📑 Navigation")
selected_page = st.sidebar.radio(
    "Select Page:",
    options=["💬 Chat", "📊 Conversations"],
    key="page_selector"
)

st.sidebar.divider()

# Import and display the appropriate page
if selected_page == "💬 Chat":
    # Import chat app
    from chat_interface import show_chat_app
    show_chat_app()
elif selected_page == "📊 Conversations":
    # Import conversations panel
    from conversations_panel import main as show_conversations
    show_conversations()
