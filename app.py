"""
FactoryOps AI - Manufacturing Assistant
Multi-page Streamlit app with Chat and Conversations
"""

import streamlit as st

st.set_page_config(
    page_title="FactoryOps AI",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🏭 FactoryOps Manufacturing Assistant")
st.markdown("Welcome! Select a page from the sidebar to get started.")

st.info("""
### 📑 Available Pages:
- **💬 Chat** - Main chat interface with AI assistant
- **📊 Conversations** - View and manage saved conversations

Choose a page from the sidebar →
""")
