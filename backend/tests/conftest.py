"""Shared database test fixtures."""

from collections.abc import Generator
from datetime import UTC, datetime
from uuid import uuid7

import pytest
from app.db.models import (
    Base,
    Customer,
    CustomerType,
    Employment,
    Project,
    ProjectAssignment,
    User,
    UserRole,
    UserType,
)
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker


@pytest.fixture
def sqlite_engine() -> Generator[Engine]:
    """Create an isolated in-memory SQLite engine."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(
        dbapi_connection: object,
        _connection_record: object,
    ) -> None:
        """Enable SQLite foreign-key enforcement."""
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
        finally:
            cursor.close()

    Base.metadata.create_all(engine)

    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def db_session(
    sqlite_engine: Engine,
) -> Generator[Session]:
    """Provide an isolated SQLAlchemy session."""
    session_factory = sessionmaker(
        bind=sqlite_engine,
        autoflush=False,
        expire_on_commit=False,
    )

    session = session_factory()

    try:
        yield session
        session.rollback()
    finally:
        session.close()


@pytest.fixture
def user(db_session: Session) -> User:
    """Create a reusable internal test user."""
    entity = User(
        id=uuid7(),
        login_identifier="test-user",
        display_name="Test User",
        email="test@example.com",
        user_type=UserType.INTERNAL,
        role=UserRole.TECHNICIAN,
        active=True,
    )

    db_session.add(entity)
    db_session.commit()
    db_session.refresh(entity)

    return entity


@pytest.fixture
def customer(db_session: Session) -> Customer:
    """Create a reusable test customer."""
    entity = Customer(
        id=uuid7(),
        customer_type=CustomerType.COMPANY,
        name="Test Customer",
        active=True,
    )

    db_session.add(entity)
    db_session.commit()
    db_session.refresh(entity)

    return entity


@pytest.fixture
def project(
    db_session: Session,
    customer: Customer,
) -> Project:
    """Create a reusable test project."""
    entity = Project(
        id=uuid7(),
        customer_id=customer.id,
        name="Test Project",
        status="ACTIVE",
        active=True,
    )

    db_session.add(entity)
    db_session.commit()
    db_session.refresh(entity)

    return entity


@pytest.fixture
def employment(
    db_session: Session,
    user: User,
) -> Employment:
    """Create a reusable employment record."""
    entity = Employment(
        id=uuid7(),
        user_id=user.id,
        hierarchy_level="LEVEL_1",
        employment_status="ACTIVE",
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
    )

    db_session.add(entity)
    db_session.commit()
    db_session.refresh(entity)

    return entity


@pytest.fixture
def assignment(
    db_session: Session,
    user: User,
    project: Project,
) -> ProjectAssignment:
    """Create a reusable project assignment."""
    entity = ProjectAssignment(
        id=uuid7(),
        project_id=project.id,
        user_id=user.id,
        assignment_context="TEST",
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
        active=True,
    )

    db_session.add(entity)
    db_session.commit()
    db_session.refresh(entity)

    return entity
