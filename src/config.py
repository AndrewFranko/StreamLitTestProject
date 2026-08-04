"""
Configuration module for FactoryOps AI.
Loads settings from:
1. Streamlit Cloud secrets (st.secrets) - highest priority
2. Environment variables
3. pyproject.local.toml
4. pyproject.toml
Uses Pydantic BaseSettings for flexible configuration management.
"""

import os
import sys
from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache
import logging

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

logger = logging.getLogger(__name__)


def load_streamlit_secrets():
    """
    Load secrets from Streamlit Cloud secrets.
    This should be called early in the app initialization.
    """
    try:
        import streamlit as st

        # List of secrets to load from Streamlit
        secret_keys = [
            "GOOGLE_API_KEY",
            "LANGSMITH_API_KEY",
            "LANGSMITH_PROJECT",
            "LANGSMITH_ENDPOINT",
            "APP_ENV",
        ]

        for key in secret_keys:
            try:
                if key in st.secrets:
                    os.environ[key] = st.secrets[key]
                    logger.debug(f"Loaded {key} from Streamlit Cloud secrets")
            except KeyError:
                pass  # Key not in secrets, that's ok

    except ImportError:
        logger.debug("Streamlit not available - running locally")
    except Exception as e:
        logger.debug(f"Could not load Streamlit secrets: {e}")


def load_pyproject_config() -> dict:
    """Load configuration from pyproject.toml and pyproject.local.toml."""
    config = {}
    base_path = Path(__file__).parent.parent.parent

    # Load base config from pyproject.toml
    pyproject_path = base_path / "pyproject.toml"
    if pyproject_path.exists():
        try:
            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)
            config = data.get("tool", {}).get("factoryops", {})
            logger.debug(f"Loaded configuration from {pyproject_path}")
        except Exception as e:
            logger.warning(f"Failed to load pyproject.toml: {e}")

    # Load local secrets from pyproject.local.toml (overrides base)
    local_path = base_path / "pyproject.local.toml"
    if local_path.exists():
        try:
            with open(local_path, "rb") as f:
                local_data = tomllib.load(f)
            local_config = local_data.get("tool", {}).get("factoryops", {})
            _deep_merge(config, local_config)
            logger.debug(f"Merged local config from {local_path}")
        except Exception as e:
            logger.warning(f"Failed to load pyproject.local.toml: {e}")

    return config


def _deep_merge(base: dict, override: dict) -> None:
    """Recursively merge override dict into base dict."""
    for key, value in override.items():
        if isinstance(value, dict) and key in base and isinstance(base[key], dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


class Settings(BaseSettings):
    """
    Application settings loaded from pyproject.toml, pyproject.local.toml, and environment variables.
    Priority: Environment Variables > pyproject.local.toml > pyproject.toml > Defaults
    """

    # Gemini API Configuration
    google_api_key: str = ""

    # Application Settings
    app_env: str = "development"
    app_name: str = "FactoryOps AI"
    log_level: str = "INFO"

    # LLM Configuration
    model_name: str = "gemini-3.1-flash-lite"
    temperature: float = 0.7
    max_tokens: int = 2048

    # Memory Configuration
    max_conversation_length: int = 100
    conversation_buffer_type: str = "buffer"

    # Agent Configuration
    agent_max_iterations: int = 10
    agent_timeout: float = 30.0

    # Data Paths
    machines_data_path: str = "src/data/machines.json"
    error_codes_data_path: str = "src/data/error_codes.json"
    technicians_data_path: str = "src/data/technicians.json"
    tickets_data_path: str = "src/data/maintenance_tickets.json"

    # Session & Security
    session_timeout_minutes: int = 30

    # API Integration URLs
    mes_api_url: str = "http://mes-internal.factoryops.com/api"
    maintenance_api_url: str = "http://maintenance.factoryops.com/api"
    inventory_api_url: str = "http://inventory.factoryops.com/api"

    # Database Configuration
    database_url: str = "sqlite:///./data/factory_ops.db"

    # Monitoring & Logging
    enable_logging: bool = True
    log_file: str = "logs/factoryops.log"

    # LangSmith Configuration (for Studio monitoring)
    langsmith_api_key: str = ""
    langsmith_project: str = "Factory"
    langsmith_endpoint: str = "https://eu.api.smith.langchain.com"
    langsmith_batch_timeout_ms: int = 100
    langsmith_timeout_ms: int = 10000
    langsmith_tracing_v2: bool = True
    langsmith_tracing: bool = True
    langsmith_callbacks_background: bool = False

    class Config:
        """Pydantic v2 configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "allow"


def _merge_all_settings():
    """
    Merge settings from multiple sources into environment variables for Pydantic.
    Priority: Streamlit secrets > Environment vars > pyproject.local.toml > pyproject.toml
    """
    # 1. Load Streamlit Cloud secrets FIRST (highest priority)
    load_streamlit_secrets()

    # 2. Load TOML configs
    toml_config = load_pyproject_config()

    # Convert kebab-case to snake_case and flatten nested dicts
    def flatten_dict(d, parent_key="", sep="_"):
        """Recursively flatten nested dicts, converting kebab-case to snake_case."""
        items = []
        for k, v in d.items():
            # Convert kebab-case to snake_case
            k_snake = k.replace("-", "_")
            new_key = f"{parent_key}{sep}{k_snake}".upper() if parent_key else k_snake.upper()

            if isinstance(v, dict):
                items.extend(flatten_dict(v, new_key, sep=sep).items())
            elif v is not None:  # Only set if value is not None
                # Don't override existing environment variables (set by Streamlit secrets)
                if not os.getenv(new_key):
                    os.environ[new_key] = str(v)
                    logger.debug(f"Set {new_key} from TOML config")
                items.append((new_key, v))
        return dict(items)

    # Flatten and merge TOML config (only if not already set by Streamlit)
    if toml_config:
        flatten_dict(toml_config)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Retrieve cached settings instance.
    Priority: Streamlit secrets > Environment Variables > pyproject.local.toml > pyproject.toml > Defaults

    Returns:
        Settings: Application configuration object

    Raises:
        ValueError: If GOOGLE_API_KEY is not set
    """
    try:
        _merge_all_settings()
        settings = Settings()

        if not settings.google_api_key:
            raise ValueError(
                "GOOGLE_API_KEY is required. Set it via:\n"
                "  1. Environment variable: GOOGLE_API_KEY=your_key\n"
                "  2. pyproject.local.toml: [tool.factoryops.api] google-api-key = 'your_key'\n"
                "  3. .env file: GOOGLE_API_KEY=your_key"
            )

        logger.info(
            f"✓ Configuration loaded: {settings.app_name} "
            f"({settings.app_env}) - Model: {settings.model_name}"
        )
        logger.debug(
            f"  Database: {settings.database_url}\n"
            f"  LangSmith: {settings.langsmith_project}\n"
            f"  Data paths: {settings.machines_data_path}"
        )
        return settings
    except Exception as e:
        logger.error(f"Failed to load configuration: {str(e)}")
        raise


# Global settings instance
settings = get_settings()
