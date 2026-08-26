"""Tests for SQLAlchemy external relationship mappings."""

from datetime import UTC, datetime
from uuid import uuid7

from app.db.models import (
    Customer,
    CustomerProjectAccess,
    ExternalRelationship,
    ExternalRelationshipType,
    User,
    UserRole,
    UserType,
)
from sqlalchemy.orm import Session


def test_user_has_external_relationship(
    db_session: Session,
    user: User,
    customer: Customer,
) -> None:
    """User.external_relationships must expose related records."""
    relationship = ExternalRelationship(
        id=uuid7(),
        user_id=user.id,
        customer_id=customer.id,
        relationship_type=ExternalRelationshipType.CONTACT,
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
        created_from=user.id,
    )

    db_session.add(relationship)
    db_session.commit()
    db_session.refresh(user)

    assert relationship in user.external_relationships
    assert relationship.user is user


def test_customer_has_external_relationship(
    db_session: Session,
    user: User,
    customer: Customer,
) -> None:
    """Customer.external_relationships must expose related records."""
    relationship = ExternalRelationship(
        id=uuid7(),
        user_id=user.id,
        customer_id=customer.id,
        relationship_type=ExternalRelationshipType.OWNER,
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
        created_from=user.id,
    )

    db_session.add(relationship)
    db_session.commit()
    db_session.refresh(customer)

    assert relationship in customer.external_relationships
    assert relationship.customer is customer


def test_external_relationship_exposes_creator_user(
    db_session: Session,
    user: User,
    customer: Customer,
) -> None:
    """created_from must resolve to the creating User."""
    relationship = ExternalRelationship(
        id=uuid7(),
        user_id=user.id,
        customer_id=customer.id,
        relationship_type=ExternalRelationshipType.CONTACT,
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
        created_from=user.id,
    )

    db_session.add(relationship)
    db_session.commit()
    db_session.refresh(relationship)

    assert relationship.created_from_user is user


def test_project_has_customer_project_access_relationship(
    db_session: Session,
    project,
    user: User,
) -> None:
    """Project.customer_project_accesses must expose related access records."""
    external_user = User(
        login_identifier="relationship-external-user",
        display_name="Relationship External User",
        user_type=UserType.EXTERNAL,
        role=UserRole.CUSTOMER,
        active=True,
    )
    db_session.add(external_user)
    db_session.commit()
    db_session.refresh(external_user)

    access = CustomerProjectAccess(
        project_id=project.id,
        user_id=external_user.id,
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
        active=True,
        created_from=user.id,
    )
    db_session.add(access)
    db_session.commit()

    db_session.refresh(project)

    assert access in project.customer_project_accesses
    assert access.project is project


def test_user_has_customer_project_access_relationship(
    db_session: Session,
    project,
    user: User,
) -> None:
    """User.customer_project_accesses must expose related access records."""
    external_user = User(
        login_identifier="relationship-external-user-2",
        display_name="Relationship External User 2",
        user_type=UserType.EXTERNAL,
        role=UserRole.CUSTOMER,
        active=True,
    )
    db_session.add(external_user)
    db_session.commit()
    db_session.refresh(external_user)

    access = CustomerProjectAccess(
        project_id=project.id,
        user_id=external_user.id,
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
        active=True,
        created_from=user.id,
    )
    db_session.add(access)
    db_session.commit()

    db_session.refresh(external_user)

    assert access in external_user.customer_project_accesses
    assert access.user is external_user
