"""
LangSmith Configuration and Integration

Enables tracing of RAG pipeline, LangGraph workflows, and tool calls
for visualization in LangSmith Studio.

Configuration loaded from pyproject.toml [tool.factoryops.langsmith] section.
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def load_langsmith_config() -> dict:
    """
    Load LangSmith configuration from pyproject.toml/pyproject.local.toml.

    Returns:
        dict with langsmith config (api_key, project, endpoint, etc)
    """
    try:
        import tomllib
        from pathlib import Path

        config = {}
        base_path = Path(__file__).parent.parent

        # Load from pyproject.toml
        pyproject_path = base_path / "pyproject.toml"
        if pyproject_path.exists():
            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)
            config = data.get("tool", {}).get("factoryops", {}).get("langsmith", {})

        # Load and merge from pyproject.local.toml (secrets)
        local_path = base_path / "pyproject.local.toml"
        if local_path.exists():
            with open(local_path, "rb") as f:
                local_data = tomllib.load(f)
            local_config = local_data.get("tool", {}).get("factoryops", {}).get("langsmith", {})
            config.update(local_config)

        return config
    except Exception as e:
        logger.debug(f"Could not load LangSmith config: {e}")
        return {}


def setup_langsmith() -> bool:
    """
    Configure LangSmith tracing from pyproject.toml/pyproject.local.toml.

    Sets environment variables that LangChain uses automatically for tracing.

    Returns:
        True if LangSmith is configured and enabled, False otherwise
    """
    config = load_langsmith_config()

    # Get API key from TOML config or environment
    api_key = config.get("api-key", "") or os.getenv("LANGSMITH_API_KEY", "")
    project = config.get("project", "Factory")
    endpoint = config.get("endpoint", "https://eu.api.smith.langchain.com")
    tracing_v2 = config.get("tracing-v2", True)

    if not api_key:
        logger.debug("LangSmith API key not configured - tracing disabled")
        return False

    try:
        # Set environment variables for LangChain automatic tracing
        os.environ["LANGSMITH_API_KEY"] = api_key
        os.environ["LANGSMITH_PROJECT"] = project
        os.environ["LANGSMITH_ENDPOINT"] = endpoint
        os.environ["LANGCHAIN_TRACING_V2"] = "true" if tracing_v2 else "false"
        os.environ["LANGSMITH_BATCH_TIMEOUT_MS"] = str(config.get("batch-timeout-ms", 100))
        os.environ["LANGSMITH_TIMEOUT_MS"] = str(config.get("timeout-ms", 10000))

        logger.info(f"LangSmith configured: project='{project}', endpoint='{endpoint}'")
        return True
    except Exception as e:
        logger.error(f"Failed to configure LangSmith: {e}")
        return False


def get_langsmith_status() -> dict:
    """Get current LangSmith configuration status."""
    api_key = os.getenv("LANGSMITH_API_KEY")
    project = os.getenv("LANGSMITH_PROJECT", "not_configured")
    endpoint = os.getenv("LANGSMITH_ENDPOINT", "")
    tracing_enabled = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"

    return {
        "api_key_configured": bool(api_key),
        "project_configured": project != "not_configured",
        "tracing_enabled": tracing_enabled,
        "project_name": project,
        "endpoint": endpoint,
        "studio_url": f"https://smith.langchain.com/studio?projectName={project}" if project != "not_configured" else None
    }


# Configure on module import
LANGSMITH_ENABLED = setup_langsmith()

if LANGSMITH_ENABLED:
    logger.info("LangSmith tracing enabled - traces will appear in Studio")
else:
    logger.debug("LangSmith tracing not configured (LANGSMITH_API_KEY not set)")
