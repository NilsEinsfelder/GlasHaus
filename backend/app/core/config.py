"""Application configuration for the GlasHaus backend."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "GlasHaus Backend"
    environment: Literal["development", "test", "production"] = "development"
    database_url: str = Field(
        default="sqlite:///./glashaus.db",
        description="SQLAlchemy database URL.",
    )
    sql_echo: bool = False


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings instance."""
    return Settings()
