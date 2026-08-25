"""Tests for domain foreign-key integrity."""

from datetime import UTC, datetime
from uuid import uuid7

import pytest
from app.db.models import (
    Employment,
    Project,
    ProjectAssignment,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


def test_employment_requires_existing_user(
    db_session: Session,
) -> None:
    """Employment.user_id must reference an existing user."""
    employment = Employment(
        id=uuid7(),
        user_id=uuid7(),
        hierarchy_level="LEVEL_1",
        employment_status="ACTIVE",
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
    )

    db_session.add(employment)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_project_requires_existing_customer(
    db_session: Session,
) -> None:
    """Project.customer_id must reference an existing customer."""
    project = Project(
        id=uuid7(),
        customer_id=uuid7(),
        name="Invalid Project",
        status="ACTIVE",
    )

    db_session.add(project)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_assignment_requires_existing_user_and_project(
    db_session: Session,
) -> None:
    """ProjectAssignment must reference existing user and project."""
    assignment = ProjectAssignment(
        id=uuid7(),
        user_id=uuid7(),
        project_id=uuid7(),
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
    )

    db_session.add(assignment)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()
