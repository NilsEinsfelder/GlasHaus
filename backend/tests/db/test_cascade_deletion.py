"""Tests for non-destructive delete behaviour."""

import pytest
from app.db.models import (
    Customer,
    Employment,
    Project,
    ProjectAssignment,
    User,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


def test_user_delete_is_restricted_when_employment_exists(
    db_session: Session,
    user: User,
    employment: Employment,
) -> None:
    """A user with employment history must not be deleted."""
    db_session.delete(user)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_customer_delete_is_restricted_when_project_exists(
    db_session: Session,
    customer: Customer,
    project: Project,
) -> None:
    """A customer with projects must not be deleted."""
    db_session.delete(customer)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_project_delete_is_restricted_when_assignment_exists(
    db_session: Session,
    project: Project,
    assignment: ProjectAssignment,
) -> None:
    """A project with assignments must not be deleted."""
    db_session.delete(project)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_deactivation_preserves_user(
    db_session: Session,
    user: User,
) -> None:
    """Deactivation must preserve the database record."""
    user.active = False
    db_session.commit()

    db_session.expire_all()

    stored = db_session.get(User, user.id)

    assert stored is not None
    assert stored.active is False
