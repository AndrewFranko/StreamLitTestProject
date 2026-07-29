"""
LangSmith Configuration and Integration

Enables tracing of RAG pipeline, LangGraph workflows, and tool calls
for visualization in LangSmith Studio.
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def setup_langsmith() -> bool:
    """
    Configure LangSmith tracing.

    Reads LANGSMITH_API_KEY and LANGSMITH_PROJECT from environment.
    Enables tracing if both are configured.

    Returns:
        True if LangSmith is configured and enabled, False otherwise
    """
    api_key = os.getenv("LANGSMITH_API_KEY")
    project = os.getenv("LANGSMITH_PROJECT")
    tracing_enabled = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"

    if not api_key or not project or not tracing_enabled:
        logger.info("LangSmith tracing not fully configured")
        return False

    try:
        # Set environment variables for LangChain
        os.environ["LANGSMITH_API_KEY"] = api_key
        os.environ["LANGSMITH_PROJECT"] = project
        os.environ["LANGCHAIN_TRACING_V2"] = "true"

        logger.info(f"✓ LangSmith configured for project: {project}")
        return True
    except Exception as e:
        logger.error(f"Failed to configure LangSmith: {e}")
        return False


def get_langsmith_status() -> dict:
    """Get current LangSmith configuration status."""
    return {
        "api_key_configured": bool(os.getenv("LANGSMITH_API_KEY")),
        "project_configured": bool(os.getenv("LANGSMITH_PROJECT")),
        "tracing_enabled": os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true",
        "project_name": os.getenv("LANGSMITH_PROJECT", "not_configured"),
        "studio_url": "https://smith.langchain.com/studio" if os.getenv("LANGSMITH_PROJECT") else None
    }


# Configure on module import
LANGSMITH_ENABLED = setup_langsmith()

if LANGSMITH_ENABLED:
    logger.info("LangSmith tracing enabled - traces will appear in Studio")
else:
    logger.debug("LangSmith tracing disabled - configure .env to enable")
