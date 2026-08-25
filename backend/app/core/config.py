"""Application configuration for the GlasHaus backend."""

from functools import lru_cache
from typing import Literal, Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


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
    log_level: LogLevel = "INFO"

    @model_validator(mode="after")
    def validate_environment(self) -> Self:
        """Validate settings against environment-specific requirements."""
        if self.environment == "production" and not self.database_url.startswith(
            ("postgresql://", "postgresql+psycopg://")
        ):
            raise ValueError(
                "Production environment requires a PostgreSQL database URL."
            )

        return self


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings instance."""
    return Settings()
