"""PostgreSQL migration integration tests."""

import os
from datetime import UTC, datetime

import pytest
from alembic import command
from alembic.config import Config
from app.db.models.customer import Customer
from app.db.models.employment import Employment
from app.db.models.project import Project
from app.db.models.project_assignment import ProjectAssignment
from app.db.models.user import User
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

pytestmark = pytest.mark.postgresql


def _database_url() -> str:
    """Return the PostgreSQL test database URL."""
    database_url = os.environ.get("GLASHAUS_TEST_DATABASE_URL")

    if not database_url:
        pytest.skip(
            "GLASHAUS_TEST_DATABASE_URL is not configured",
        )

    return database_url


def _alembic_config(database_url: str) -> Config:
    """Create an Alembic configuration for the test database."""
    config = Config("alembic.ini")
    config.set_main_option(
        "sqlalchemy.url",
        database_url,
    )

    return config


def test_postgresql_migration_reaches_head() -> None:
    """The complete Alembic migration chain must work on PostgreSQL."""
    database_url = _database_url()
    engine = create_engine(database_url)

    try:
        config = _alembic_config(database_url)

        command.upgrade(config, "head")

        inspector = inspect(engine)
        tables = set(inspector.get_table_names())

        assert {
            "alembic_version",
            "devices",
            "sync_states",
            "users",
            "employments",
            "customers",
            "projects",
            "project_assignments",
        } <= tables

    finally:
        engine.dispose()


def test_postgresql_domain_roundtrip() -> None:
    """The core domain graph must persist and reload on PostgreSQL."""
    database_url = _database_url()
    engine = create_engine(database_url)

    try:
        config = _alembic_config(database_url)
        command.upgrade(config, "head")

        with Session(engine) as session:
            user = User(
                login_identifier="postgres-roundtrip-user",
            )

            customer = Customer(
                name="PostgreSQL Test Customer",
                customer_type="customer",
            )

            session.add_all([user, customer])
            session.flush()

            employment = Employment(
                user_id=user.id,
                valid_from=datetime(
                    2026,
                    1,
                    1,
                    tzinfo=UTC,
                ),
            )

            project = Project(
                customer_id=customer.id,
                name="PostgreSQL Test Project",
            )

            session.add_all([employment, project])
            session.flush()

            assignment = ProjectAssignment(
                project_id=project.id,
                user_id=user.id,
            )

            session.add(assignment)
            session.commit()

            session.expire_all()

            stored_user = session.get(
                User,
                user.id,
            )
            stored_customer = session.get(
                Customer,
                customer.id,
            )
            stored_employment = session.get(
                Employment,
                employment.id,
            )
            stored_project = session.get(
                Project,
                project.id,
            )
            stored_assignment = session.get(
                ProjectAssignment,
                assignment.id,
            )

            assert stored_user is not None
            assert stored_customer is not None
            assert stored_employment is not None
            assert stored_project is not None
            assert stored_assignment is not None

            assert stored_employment.user_id == stored_user.id
            assert stored_project.customer_id == stored_customer.id
            assert stored_assignment.user_id == stored_user.id
            assert stored_assignment.project_id == stored_project.id

            assert stored_employment.valid_from == datetime(
                2026,
                1,
                1,
            )

    finally:
        engine.dispose()


def test_postgresql_migration_can_downgrade() -> None:
    """The Sprint-B migration must be reversible on PostgreSQL."""
    database_url = _database_url()
    engine = create_engine(database_url)

    try:
        config = _alembic_config(database_url)

        command.upgrade(config, "head")
        command.downgrade(config, "0001_initial_schema")

        inspector = inspect(engine)
        tables = set(inspector.get_table_names())

        assert "users" not in tables
        assert "employments" not in tables
        assert "customers" not in tables
        assert "projects" not in tables
        assert "project_assignments" not in tables

        assert "devices" in tables
        assert "sync_states" in tables

    finally:
        engine.dispose()
