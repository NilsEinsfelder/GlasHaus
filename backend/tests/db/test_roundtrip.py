"""Persistence roundtrip tests."""

from datetime import UTC, datetime

from app.db.models import (
    Customer,
    Employment,
    ExternalRelationship,
    ExternalRelationshipType,
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


def test_external_relationship_roundtrip(
    db_session: Session,
    user: User,
    customer: Customer,
) -> None:
    """An ExternalRelationship must survive a database roundtrip."""
    valid_from = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    valid_until = datetime(2026, 12, 31, 12, 0, tzinfo=UTC)

    relationship = ExternalRelationship(
        user_id=user.id,
        customer_id=customer.id,
        relationship_type=ExternalRelationshipType.OWNER,
        valid_from=valid_from,
        valid_until=valid_until,
        active=True,
        created_from=user.id,
    )

    db_session.add(relationship)
    db_session.commit()

    relationship_id = relationship.id

    db_session.expire_all()

    stored = db_session.get(
        ExternalRelationship,
        relationship_id,
    )

    assert stored is not None
    assert stored.user_id == user.id
    assert stored.customer_id == customer.id
    assert stored.created_from == user.id
    assert stored.relationship_type is ExternalRelationshipType.OWNER
    assert stored.active is True

    assert stored.valid_from.replace(tzinfo=UTC) == valid_from
    assert stored.valid_until is not None
    assert stored.valid_until.replace(tzinfo=UTC) == valid_until

    assert stored.created_at is not None
    assert stored.updated_at is not None
