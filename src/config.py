"""
Configuration module for FactoryOps AI.
Loads environment variables and provides settings for the application.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Application settings loaded from .env file.
    Uses Pydantic v2 BaseSettings for environment variable management.
    """

    # Gemini API Configuration
    google_api_key: str

    # Application Settings
    app_env: str = "development"  # development, staging, production
    app_name: str = "FactoryOps AI"
    log_level: str = "INFO"

    # LLM Configuration
    model_name: str = "gemini-3.1-flash-lite"
    temperature: float = 0.7
    max_tokens: int = 2048

    # Memory Configuration
    max_conversation_length: int = 100
    conversation_buffer_type: str = "buffer"  # buffer, summary, etc.

    # Agent Configuration
    agent_max_iterations: int = 10
    agent_timeout: float = 30.0

    # Data Paths
    machines_data_path: str = "data/machines.json"
    error_codes_data_path: str = "data/error_codes.json"
    technicians_data_path: str = "data/technicians.json"
    tickets_data_path: str = "data/maintenance_tickets.json"

    # Session & Security
    session_timeout_minutes: int = 30

    # Monitoring
    enable_logging: bool = True
    log_file: str = "logs/factoryops.log"

    class Config:
        """Pydantic v2 configuration."""
        env_file = ".env"
        case_sensitive = False
        extra = "allow"  # Allow extra fields from .env


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Retrieve cached settings instance.
    Uses LRU cache to ensure only one Settings instance is created.

    Returns:
        Settings: Application configuration object

    Raises:
        ValueError: If GOOGLE_API_KEY is not set in .env
    """
    try:
        settings = Settings()
        if not settings.google_api_key:
            raise ValueError(
                "GOOGLE_API_KEY must be set in .env file. "
                "Copy .env.example to .env and add your Gemini API key."
            )
        logger.info(
            f"Configuration loaded: {settings.app_name} "
            f"({settings.app_env}) - Model: {settings.model_name}"
        )
        return settings
    except Exception as e:
        logger.error(f"Failed to load configuration: {str(e)}")
        raise


# Global settings instance
settings = get_settings()
