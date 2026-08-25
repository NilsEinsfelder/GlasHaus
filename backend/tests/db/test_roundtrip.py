"""Persistence roundtrip tests."""

from datetime import UTC, datetime

from app.db.models import (
    Customer,
    Employment,
    Project,
    ProjectAssignment,
    User,
)
from sqlalchemy.orm import Session


def test_domain_graph_roundtrip(
    db_session: Session,
    user: User,
    customer: Customer,
    project: Project,
    employment: Employment,
    assignment: ProjectAssignment,
) -> None:
    """A complete domain graph must survive a DB roundtrip."""
    db_session.expire_all()

    stored_user = db_session.get(User, user.id)
    stored_customer = db_session.get(Customer, customer.id)
    stored_project = db_session.get(Project, project.id)
    stored_employment = db_session.get(
        Employment,
        employment.id,
    )
    stored_assignment = db_session.get(
        ProjectAssignment,
        assignment.id,
    )

    assert stored_user is not None
    assert stored_customer is not None
    assert stored_project is not None
    assert stored_employment is not None
    assert stored_assignment is not None

    assert stored_employment.user_id == stored_user.id
    assert stored_project.customer_id == stored_customer.id
    assert stored_assignment.user_id == stored_user.id
    assert stored_assignment.project_id == stored_project.id

    assert stored_employment.valid_from.replace(
        tzinfo=UTC,
    ) == datetime(
        2026,
        1,
        1,
        tzinfo=UTC,
    )

    assert stored_assignment.valid_from.replace(
        tzinfo=UTC,
    ) == datetime(
        2026,
        1,
        1,
        tzinfo=UTC,
    )
