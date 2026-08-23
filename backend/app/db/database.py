"""Database engine and session management."""

from collections.abc import Generator
from typing import Any

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.db.models import Base

settings = get_settings()


def _engine_kwargs(database_url: str) -> dict[str, Any]:
    """Build engine options appropriate for the configured database."""
    kwargs: dict[str, Any] = {
        "future": True,
        "pool_pre_ping": True,
    }

    if database_url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}

    return kwargs


engine: Engine = create_engine(
    settings.database_url,
    echo=settings.sql_echo,
    **_engine_kwargs(settings.database_url),
)

SessionFactory = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


def initialize_database(database_engine: Engine = engine) -> None:
    """Create database tables for isolated development or test environments."""
    Base.metadata.create_all(bind=database_engine)


def get_session(
    session_factory: sessionmaker[Session] = SessionFactory,
) -> Generator[Session]:
    """Provide a database session and close it after use."""
    session = session_factory()

    try:
        yield session
    finally:
        session.close()
