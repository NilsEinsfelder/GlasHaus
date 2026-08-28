"""Tests for permission grant persistence and repository operations."""

from datetime import UTC, datetime
from uuid import UUID, uuid7

import pytest
from app.db.models import (
    Permission,
    PermissionGrant,
    PermissionGrantConstraintType,
    PermissionGrantEffect,
    PermissionGrantScopeType,
    User,
    UserRole,
    UserType,
)
from app.db.repositories.permission_grants import PermissionGrantRepository
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


def _user(login_identifier: str) -> User:
    """Create a test user entity."""
    return User(
        id=uuid7(),
        login_identifier=login_identifier,
        display_name=login_identifier,
        email=f"{login_identifier}@example.com",
        user_type=UserType.INTERNAL,
        role=UserRole.TECHNICIAN,
        active=True,
    )


def _permission(identifier: str) -> Permission:
    """Create a test permission entity."""
    return Permission(
        id=uuid7(),
        identifier=identifier,
    )


def _grant(
    *,
    user_id: UUID,
    permission_id: UUID,
    granted_by_user_id: UUID,
    effect: PermissionGrantEffect = PermissionGrantEffect.ALLOW,
    scope_type: PermissionGrantScopeType = PermissionGrantScopeType.GLOBAL,
    scope_id: UUID | None = None,
    constraint_type: PermissionGrantConstraintType | None = None,
    constraint_value: dict[str, str] | None = None,
    valid_from: datetime = datetime(2026, 1, 1, tzinfo=UTC),
    valid_until: datetime | None = None,
    active: bool = True,
) -> PermissionGrant:
    """Create a permission grant entity for testing."""
    return PermissionGrant(
        id=uuid7(),
        user_id=user_id,
        permission_id=permission_id,
        effect=effect,
        scope_type=scope_type,
        scope_id=scope_id,
        constraint_type=constraint_type,
        constraint_value=constraint_value,
        valid_from=valid_from,
        valid_until=valid_until,
        active=active,
        granted_by_user_id=granted_by_user_id,
    )


def test_permission_grant_can_be_persisted(
    db_session: Session,
) -> None:
    """A basic permission grant can be persisted and retrieved."""
    user = _user("grant-user")
    grantor = _user("grantor-user")
    permission = _permission("project.read")

    db_session.add_all([user, grantor, permission])
    db_session.flush()

    grant = _grant(
        user_id=user.id,
        permission_id=permission.id,
        granted_by_user_id=grantor.id,
    )

    db_session.add(grant)
    db_session.commit()

    persisted = db_session.get(PermissionGrant, grant.id)

    assert persisted is not None
    assert persisted.id == grant.id
    assert persisted.user_id == user.id
    assert persisted.permission_id == permission.id
    assert persisted.effect == PermissionGrantEffect.ALLOW
    assert persisted.scope_type == PermissionGrantScopeType.GLOBAL
    assert persisted.scope_id is None
    assert persisted.active is True


def test_permission_grant_supports_purchase_limit_constraint(
    db_session: Session,
) -> None:
    """A purchase limit supports a structured JSON constraint value."""
    user = _user("purchase-limit-user")
    grantor = _user("purchase-limit-grantor")
    permission = _permission("purchase.create")

    db_session.add_all([user, grantor, permission])
    db_session.flush()

    constraint_value = {
        "amount": "2000.50",
        "currency": "EUR",
    }

    grant = _grant(
        user_id=user.id,
        permission_id=permission.id,
        granted_by_user_id=grantor.id,
        scope_type=PermissionGrantScopeType.PROJECT,
        scope_id=user.id,
        constraint_type=PermissionGrantConstraintType.PURCHASE_LIMIT,
        constraint_value=constraint_value,
    )

    db_session.add(grant)
    db_session.commit()

    persisted = db_session.get(PermissionGrant, grant.id)

    assert persisted is not None
    assert persisted.constraint_type == PermissionGrantConstraintType.PURCHASE_LIMIT
    assert persisted.constraint_value == constraint_value
    assert persisted.constraint_value["amount"] == "2000.50"
    assert persisted.constraint_value["currency"] == "EUR"


def test_permission_grant_supports_global_scope_without_scope_id(
    db_session: Session,
) -> None:
    """A global permission grant must not have a scope ID."""
    user = _user("global-user")
    grantor = _user("global-grantor")
    permission = _permission("project.read")

    db_session.add_all([user, grantor, permission])
    db_session.flush()

    grant = _grant(
        user_id=user.id,
        permission_id=permission.id,
        granted_by_user_id=grantor.id,
        scope_type=PermissionGrantScopeType.GLOBAL,
        scope_id=None,
    )

    db_session.add(grant)
    db_session.commit()

    persisted = db_session.get(PermissionGrant, grant.id)

    assert persisted is not None
    assert persisted.scope_type == PermissionGrantScopeType.GLOBAL
    assert persisted.scope_id is None


def test_permission_grant_requires_scope_id_for_project_scope(
    db_session: Session,
) -> None:
    """A non-global permission grant requires a scope ID."""
    user = _user("project-scope-user")
    grantor = _user("project-scope-grantor")
    permission = _permission("project.read")

    db_session.add_all([user, grantor, permission])
    db_session.flush()

    grant = _grant(
        user_id=user.id,
        permission_id=permission.id,
        granted_by_user_id=grantor.id,
        scope_type=PermissionGrantScopeType.PROJECT,
        scope_id=None,
    )

    db_session.add(grant)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_permission_grant_rejects_invalid_valid_range(
    db_session: Session,
) -> None:
    """A grant cannot expire before or at its valid-from timestamp."""
    user = _user("range-user")
    grantor = _user("range-grantor")
    permission = _permission("project.read")

    db_session.add_all([user, grantor, permission])
    db_session.flush()

    grant = _grant(
        user_id=user.id,
        permission_id=permission.id,
        granted_by_user_id=grantor.id,
        valid_from=datetime(2026, 2, 1, tzinfo=UTC),
        valid_until=datetime(2026, 1, 1, tzinfo=UTC),
    )

    db_session.add(grant)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_permission_grant_allows_open_ended_validity(
    db_session: Session,
) -> None:
    """A grant may have no valid-until timestamp."""
    user = _user("open-ended-user")
    grantor = _user("open-ended-grantor")
    permission = _permission("project.read")

    db_session.add_all([user, grantor, permission])
    db_session.flush()

    grant = _grant(
        user_id=user.id,
        permission_id=permission.id,
        granted_by_user_id=grantor.id,
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
        valid_until=None,
    )

    db_session.add(grant)
    db_session.commit()

    persisted = db_session.get(PermissionGrant, grant.id)

    assert persisted is not None
    assert persisted.valid_until is None


def test_permission_grant_allows_constraint_type_without_value_at_python_level(
    db_session: Session,
) -> None:
    """Constraint validation is not performed by the SQLAlchemy JSON type."""
    user = _user("constraint-user")
    grantor = _user("constraint-grantor")
    permission = _permission("purchase.create")

    db_session.add_all([user, grantor, permission])
    db_session.flush()

    grant = _grant(
        user_id=user.id,
        permission_id=permission.id,
        granted_by_user_id=grantor.id,
        constraint_type=PermissionGrantConstraintType.PURCHASE_LIMIT,
        constraint_value=None,
    )

    db_session.add(grant)
    db_session.commit()

    persisted = db_session.get(PermissionGrant, grant.id)

    assert persisted is not None
    assert persisted.constraint_type == PermissionGrantConstraintType.PURCHASE_LIMIT
    assert persisted.constraint_value is None


def test_permission_grant_allows_json_value_at_python_level(
    db_session: Session,
) -> None:
    """A JSON constraint value is persisted as structured data."""
    user = _user("json-user")
    grantor = _user("json-grantor")
    permission = _permission("purchase.create")

    db_session.add_all([user, grantor, permission])
    db_session.flush()

    constraint_value = {
        "amount": "500.00",
        "currency": "EUR",
    }

    grant = _grant(
        user_id=user.id,
        permission_id=permission.id,
        granted_by_user_id=grantor.id,
        constraint_type=None,
        constraint_value=constraint_value,
    )

    db_session.add(grant)
    db_session.commit()

    persisted = db_session.get(PermissionGrant, grant.id)

    assert persisted is not None
    assert persisted.constraint_value == constraint_value


def test_permission_grant_repository_get(
    db_session: Session,
) -> None:
    """The repository can retrieve a grant by ID."""
    user = _user("repository-get-user")
    grantor = _user("repository-get-grantor")
    permission = _permission("project.read")

    db_session.add_all([user, grantor, permission])
    db_session.flush()

    grant = _grant(
        user_id=user.id,
        permission_id=permission.id,
        granted_by_user_id=grantor.id,
    )

    db_session.add(grant)
    db_session.commit()

    repository = PermissionGrantRepository(db_session)

    result = repository.get(grant.id)

    assert result is not None
    assert result.id == grant.id


def test_permission_grant_repository_get_returns_none_for_unknown_id(
    db_session: Session,
) -> None:
    """The repository returns None when the grant does not exist."""
    repository = PermissionGrantRepository(db_session)

    result = repository.get(uuid7())

    assert result is None


def test_permission_grant_repository_list_for_user(
    db_session: Session,
) -> None:
    """The repository lists all grants belonging to a user."""
    user = _user("list-user")
    grantor = _user("list-grantor")
    permission = _permission("project.read")

    db_session.add_all([user, grantor, permission])
    db_session.flush()

    first = _grant(
        user_id=user.id,
        permission_id=permission.id,
        granted_by_user_id=grantor.id,
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
    )

    second = _grant(
        user_id=user.id,
        permission_id=permission.id,
        granted_by_user_id=grantor.id,
        valid_from=datetime(2026, 2, 1, tzinfo=UTC),
    )

    other_user = _user("other-list-user")
    db_session.add(other_user)
    db_session.flush()

    other = _grant(
        user_id=other_user.id,
        permission_id=permission.id,
        granted_by_user_id=grantor.id,
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
    )

    db_session.add_all([first, second, other])
    db_session.commit()

    repository = PermissionGrantRepository(db_session)

    grants = repository.list_for_user(user.id)

    assert [grant.id for grant in grants] == [first.id, second.id]


def test_permission_grant_repository_list_active_for_user(
    db_session: Session,
) -> None:
    """The repository lists only currently active and temporally valid grants."""
    user = _user("active-list-user")
    grantor = _user("active-list-grantor")
    permission = _permission("project.read")

    db_session.add_all([user, grantor, permission])
    db_session.flush()

    active_grant = _grant(
        user_id=user.id,
        permission_id=permission.id,
        granted_by_user_id=grantor.id,
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
        active=True,
    )

    inactive_grant = _grant(
        user_id=user.id,
        permission_id=permission.id,
        granted_by_user_id=grantor.id,
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
        active=False,
    )

    expired_grant = _grant(
        user_id=user.id,
        permission_id=permission.id,
        granted_by_user_id=grantor.id,
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
        valid_until=datetime(2026, 2, 1, tzinfo=UTC),
        active=True,
    )

    future_grant = _grant(
        user_id=user.id,
        permission_id=permission.id,
        granted_by_user_id=grantor.id,
        valid_from=datetime(2030, 1, 1, tzinfo=UTC),
        active=True,
    )

    db_session.add_all(
        [
            active_grant,
            inactive_grant,
            expired_grant,
            future_grant,
        ]
    )
    db_session.commit()

    repository = PermissionGrantRepository(db_session)

    grants = repository.list_active_for_user(
        user.id,
        at=datetime(2026, 8, 28, tzinfo=UTC),
    )

    assert [grant.id for grant in grants] == [active_grant.id]


def test_permission_grant_repository_add(
    db_session: Session,
) -> None:
    """The repository adds and flushes a permission grant."""
    user = _user("repository-add-user")
    grantor = _user("repository-add-grantor")
    permission = _permission("project.read")

    db_session.add_all([user, grantor, permission])
    db_session.flush()

    grant = _grant(
        user_id=user.id,
        permission_id=permission.id,
        granted_by_user_id=grantor.id,
    )

    repository = PermissionGrantRepository(db_session)

    result = repository.add(grant)

    assert result is grant
    assert result.id is not None
    assert db_session.get(PermissionGrant, grant.id) is grant


def test_permission_grant_repository_deactivate(
    db_session: Session,
) -> None:
    """The repository can deactivate a permission grant."""
    user = _user("deactivate-user")
    grantor = _user("deactivate-grantor")
    permission = _permission("project.read")

    db_session.add_all([user, grantor, permission])
    db_session.flush()

    grant = _grant(
        user_id=user.id,
        permission_id=permission.id,
        granted_by_user_id=grantor.id,
        active=True,
    )

    db_session.add(grant)
    db_session.commit()

    repository = PermissionGrantRepository(db_session)

    result = repository.deactivate(grant)

    assert result is grant
    assert result.active is False

    db_session.commit()

    persisted = db_session.get(PermissionGrant, grant.id)

    assert persisted is not None
    assert persisted.active is False


def test_permission_grant_rollback_does_not_persist(
    db_session: Session,
) -> None:
    """Rolling back a grant transaction removes the uncommitted grant."""
    user = _user("transaction-user")
    grantor = _user("transaction-grantor")
    permission = Permission(
        id=uuid7(),
        identifier="project.read",
    )

    db_session.add_all([user, grantor, permission])
    db_session.flush()

    grant = PermissionGrant(
        user_id=user.id,
        permission_id=permission.id,
        effect=PermissionGrantEffect.ALLOW,
        scope_type=PermissionGrantScopeType.GLOBAL,
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
        active=True,
        granted_by_user_id=grantor.id,
    )

    db_session.add(grant)
    db_session.flush()

    grant_id = grant.id

    assert db_session.get(PermissionGrant, grant_id) is not None

    db_session.rollback()

    assert db_session.get(PermissionGrant, grant_id) is None
