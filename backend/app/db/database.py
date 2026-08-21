from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import Base

DATABASE_URL = "sqlite:///glashaus.db"

engine = create_engine(
    DATABASE_URL,
    future=True,
)

SessionFactory = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


def initialize_database(database_engine: Engine = engine) -> None:
    """Create all database tables for local development and tests."""
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
