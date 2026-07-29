"""
Streamlit Cloud Secrets Helper
Simple utility to load secrets from Streamlit Cloud into environment variables.

Usage in your Streamlit app:
```python
from src.streamlit_secrets_helper import setup_secrets

# Call this early in your app
setup_secrets()

# Now use your secrets
from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro")
```
"""

import os
import streamlit as st


def setup_secrets(required_keys=None):
    """
    Load secrets from Streamlit Cloud secrets into environment variables.

    Args:
        required_keys: List of required secret keys.
                      If any are missing, raises KeyError and shows Streamlit error.
                      Default: ["GOOGLE_API_KEY"]

    Raises:
        KeyError: If any required secrets are missing
    """
    if required_keys is None:
        required_keys = ["GOOGLE_API_KEY"]

    # Try to load secrets
    try:
        for key in required_keys:
            if key not in st.secrets:
                st.error(f"Missing required secret: {key}")
                st.stop()
            os.environ[key] = st.secrets[key]

    except Exception as e:
        st.error(f"Error loading secrets: {e}")
        st.stop()


def load_optional_secrets(keys):
    """
    Load optional secrets that may or may not exist.

    Args:
        keys: List of optional secret keys to load
    """
    for key in keys:
        try:
            if key in st.secrets:
                os.environ[key] = st.secrets[key]
        except Exception:
            pass  # Optional, so just skip if not available
