"""Application configuration using pydantic-settings."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = True
    api_version: str = "v1"
    app_name: str = "Bookmark Manager API"

    # Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Database
    database_url: str = (
        "postgresql+asyncpg://bookmark_user:bookmark_secret@localhost:5432/bookmark_db"
    )

    @property
    def async_database_url(self) -> str:
        """Get database URL with asyncpg driver for SQLAlchemy async support.
        Cloud providers like Render use 'postgres://' but SQLAlchemy async needs 'postgresql+asyncpg://'.
        """
        url = self.database_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    # JWT Security
    secret_key: str = "development-secret-key"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # URL Metadata Fetching
    metadata_fetch_timeout: int = 5  # seconds
    metadata_fetch_enabled: bool = True  # Enable/disable auto-fetch

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
