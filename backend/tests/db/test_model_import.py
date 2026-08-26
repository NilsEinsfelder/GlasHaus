"""Tests for SQLAlchemy model registration."""

from app.db.models import (
    Base,
    Customer,
    Employment,
    ExternalRelationship,
    Project,
    ProjectAssignment,
    User,
)


def test_core_domain_models_are_registered() -> None:
    """All core domain models must be registered in Base.metadata."""
    expected_tables = {
        User.__tablename__,
        Employment.__tablename__,
        Customer.__tablename__,
        Project.__tablename__,
        ProjectAssignment.__tablename__,
        ExternalRelationship.__tablename__,
    }

    registered_tables = set(Base.metadata.tables)

    assert expected_tables <= registered_tables


def test_core_domain_models_have_expected_table_names() -> None:
    """Core domain models must expose the expected database table names."""
    assert User.__tablename__ == "users"
    assert Employment.__tablename__ == "employments"
    assert Customer.__tablename__ == "customers"
    assert Project.__tablename__ == "projects"
    assert ProjectAssignment.__tablename__ == "project_assignments"
    assert ExternalRelationship.__tablename__ == "external_relationships"
