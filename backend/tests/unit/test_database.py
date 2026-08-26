"""Unit tests for database infrastructure."""

from app.db.database import _engine_kwargs, get_session, initialize_database
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session, sessionmaker


def test_initialize_database_creates_all_registered_tables() -> None:
    """Initialize a test database and create all registered tables."""
    engine = create_engine("sqlite:///:memory:")

    try:
        initialize_database(engine)

        table_names = set(inspect(engine).get_table_names())

        assert table_names == {
            "devices",
            "sync_states",
            "users",
            "employments",
            "customers",
            "projects",
            "project_assignments",
            "external_relationships",
            "customer_project_accesses",
        }
    finally:
        engine.dispose()


def test_get_session_yields_and_closes_session() -> None:
    """Provide a usable database session."""
    engine = create_engine("sqlite:///:memory:")
    session_factory = sessionmaker(bind=engine)

    try:
        generator = get_session(session_factory)
        session = next(generator)

        assert isinstance(session, Session)

        generator.close()
    finally:
        engine.dispose()


def test_engine_kwargs_for_non_sqlite_database() -> None:
    """Do not add SQLite-specific connection arguments for other databases."""
    kwargs = _engine_kwargs("postgresql://user:password@localhost/test")

    assert kwargs == {
        "future": True,
        "pool_pre_ping": True,
    }
