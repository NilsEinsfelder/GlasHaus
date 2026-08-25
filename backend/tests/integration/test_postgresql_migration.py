"""PostgreSQL integration tests for the Alembic migration workflow."""

import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from app.db.models import (
    Customer,
    CustomerType,
    Employment,
    Project,
    ProjectAssignment,
    User,
    UserRole,
    UserType,
)
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

BACKEND_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_CONFIG_PATH = BACKEND_ROOT / "alembic.ini"


def _database_url() -> str:
    """Return the PostgreSQL test database URL or skip the test."""
    database_url = os.getenv("GLASHAUS_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("GLASHAUS_TEST_DATABASE_URL is not configured")
    return database_url


def _alembic_config(database_url: str) -> Config:
    """Build an Alembic configuration for the test database."""
    config = Config(str(ALEMBIC_CONFIG_PATH))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def test_postgresql_migration_reaches_head() -> None:
    """The complete migration chain must reach the current head."""
    database_url = _database_url()
    config = _alembic_config(database_url)

    command.upgrade(config, "head")

    engine = create_engine(database_url)
    try:
        inspector = inspect(engine)

        assert set(inspector.get_table_names()) == {
            "alembic_version",
            "devices",
            "sync_states",
            "users",
            "employments",
            "customers",
            "projects",
            "project_assignments",
        }
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
                display_name="PostgreSQL Roundtrip User",
                user_type=UserType.INTERNAL,
                role=UserRole.TECHNICIAN,
            )
            customer = Customer(
                name="PostgreSQL Test Customer",
                customer_type=CustomerType.COMPANY,
            )
            session.add_all([user, customer])
            session.flush()

            employment = Employment(
                user_id=user.id,
                hierarchy_level="LEVEL_1",
                employment_status="ACTIVE",
                valid_from=user.created_at,
            )
            project = Project(
                customer_id=customer.id,
                name="PostgreSQL Test Project",
                status="ACTIVE",
            )
            session.add_all([employment, project])
            session.flush()

            assignment = ProjectAssignment(
                user_id=user.id,
                project_id=project.id,
                assignment_context="PostgreSQL roundtrip",
                valid_from=project.created_at,
            )
            session.add(assignment)
            session.commit()

            persisted_user_id = user.id
            persisted_customer_id = customer.id
            persisted_project_id = project.id
            persisted_assignment_id = assignment.id

        with Session(engine) as session:
            loaded_user = session.get(User, persisted_user_id)
            loaded_customer = session.get(Customer, persisted_customer_id)
            loaded_project = session.get(Project, persisted_project_id)
            loaded_assignment = session.get(
                ProjectAssignment,
                persisted_assignment_id,
            )

            assert loaded_user is not None
            assert loaded_user.login_identifier == "postgres-roundtrip-user"
            assert loaded_user.display_name == "PostgreSQL Roundtrip User"
            assert loaded_user.user_type is UserType.INTERNAL
            assert loaded_user.role is UserRole.TECHNICIAN

            assert loaded_customer is not None
            assert loaded_customer.customer_type is CustomerType.COMPANY

            assert loaded_project is not None
            assert loaded_project.customer_id == persisted_customer_id

            assert loaded_assignment is not None
            assert loaded_assignment.user_id == persisted_user_id
            assert loaded_assignment.project_id == persisted_project_id
    finally:
        engine.dispose()


def test_postgresql_migration_can_downgrade() -> None:
    """The PostgreSQL database must be able to downgrade to base."""
    database_url = _database_url()
    config = _alembic_config(database_url)

    command.upgrade(config, "head")
    command.downgrade(config, "base")

    engine = create_engine(database_url)
    try:
        assert inspect(engine).get_table_names() == ["alembic_version"]
    finally:
        engine.dispose()
