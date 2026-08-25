"""Tests for SQLAlchemy domain relationships."""

from app.db.models import (
    Customer,
    Employment,
    Project,
    ProjectAssignment,
    User,
)
from sqlalchemy.orm import Session


def test_user_has_employment_relationship(
    db_session: Session,
    user: User,
    employment: Employment,
) -> None:
    """User.employments must expose related employment records."""
    db_session.refresh(user)

    assert employment in user.employments
    assert employment.user is user


def test_customer_has_project_relationship(
    db_session: Session,
    customer: Customer,
    project: Project,
) -> None:
    """Customer.projects must expose related projects."""
    db_session.refresh(customer)

    assert project in customer.projects
    assert project.customer is customer


def test_project_has_assignment_relationship(
    db_session: Session,
    project: Project,
    assignment: ProjectAssignment,
) -> None:
    """Project.assignments must expose related assignments."""
    db_session.refresh(project)

    assert assignment in project.assignments
    assert assignment.project is project


def test_user_has_assignment_relationship(
    db_session: Session,
    user: User,
    assignment: ProjectAssignment,
) -> None:
    """User.project_assignments must expose related assignments."""
    db_session.refresh(user)

    assert assignment in user.project_assignments
    assert assignment.user is user
