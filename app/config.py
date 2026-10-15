from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables or .env file.
    """
    app_name: str = "bingeWatch 2.0"
    app_version: str = "0.1.0"
    app_env: str = "development"
    debug: bool = False

    # Server binding
    host: str = "0.0.0.0"
    port: int = 8000

    # AI & Media API Keys
    sarvam_api_key: Optional[str] = None
    tmdb_api_key: Optional[str] = None

    # Default region code for TMDB streaming lookup (e.g., 'US', 'IN', 'GB')
    default_region: str = "US"

    # Optional webhook authentication token
    webhook_secret: Optional[str] = None

    # Gmail Integration for BookMyShow Ticket Automation
    gmail_user: Optional[str] = None
    gmail_app_password: Optional[str] = None
    gmail_imap_server: str = "imap.gmail.com"
    gmail_imap_port: int = 993
    gmail_check_interval: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
