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

JSONValue = dict[str, "JSONValue"] | list["JSONValue"] | str | int | float | bool | None


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
    constraint_value: JSONValue = None,
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


def _persist_dependencies(
    db_session: Session,
    *,
    user_identifier: str,
    grantor_identifier: str,
    permission_identifier: str,
) -> tuple[User, User, Permission]:
    """Persist the entities required by a PermissionGrant."""
    user = _user(user_identifier)
    grantor = _user(grantor_identifier)
    permission = _permission(permission_identifier)

    db_session.add_all([user, grantor, permission])
    db_session.flush()

    return user, grantor, permission


def _commit_grant(
    db_session: Session,
    grant: PermissionGrant,
) -> PermissionGrant:
    """Persist a grant and return it."""
    db_session.add(grant)
    db_session.commit()
    return grant


def test_permission_grant_can_be_persisted(
    db_session: Session,
) -> None:
    """A basic permission grant can be persisted and retrieved."""
    user, grantor, permission = _persist_dependencies(
        db_session,
        user_identifier="grant-user",
        grantor_identifier="grantor-user",
        permission_identifier="project.read",
    )

    grant = _commit_grant(
        db_session,
        _grant(
            user_id=user.id,
            permission_id=permission.id,
            granted_by_user_id=grantor.id,
        ),
    )

    persisted = db_session.get(PermissionGrant, grant.id)

    assert persisted is not None
    assert persisted.id == grant.id
    assert persisted.user_id == user.id
    assert persisted.permission_id == permission.id
    assert persisted.granted_by_user_id == grantor.id
    assert persisted.effect is PermissionGrantEffect.ALLOW
    assert persisted.scope_type is PermissionGrantScopeType.GLOBAL
    assert persisted.scope_id is None
    assert persisted.constraint_type is None
    assert persisted.constraint_value is None
    assert persisted.active is True


@pytest.mark.parametrize(
    "scope_type",
    [
        PermissionGrantScopeType.GLOBAL,
        PermissionGrantScopeType.PROJECT,
        PermissionGrantScopeType.WORKSPACE,
        PermissionGrantScopeType.CUSTOMER,
        PermissionGrantScopeType.USER,
    ],
)
def test_permission_grant_supports_all_documented_scopes(
    db_session: Session,
    scope_type: PermissionGrantScopeType,
) -> None:
    """All approved PermissionGrant scope types can be persisted."""
    user, grantor, permission = _persist_dependencies(
        db_session,
        user_identifier=f"scope-user-{scope_type.value.lower()}",
        grantor_identifier=f"scope-grantor-{scope_type.value.lower()}",
        permission_identifier=f"scope.test.{scope_type.value.lower()}",
    )

    scope_id = None if scope_type is PermissionGrantScopeType.GLOBAL else uuid7()

    grant = _commit_grant(
        db_session,
        _grant(
            user_id=user.id,
            permission_id=permission.id,
            granted_by_user_id=grantor.id,
            scope_type=scope_type,
            scope_id=scope_id,
        ),
    )

    persisted = db_session.get(PermissionGrant, grant.id)

    assert persisted is not None
    assert persisted.scope_type is scope_type
    assert persisted.scope_id == scope_id


def test_permission_grant_global_scope_requires_null_scope_id(
    db_session: Session,
) -> None:
    """GLOBAL grants must not contain a scope identifier."""
    user, grantor, permission = _persist_dependencies(
        db_session,
        user_identifier="global-scope-user",
        grantor_identifier="global-scope-grantor",
        permission_identifier="global.scope",
    )

    grant = _grant(
        user_id=user.id,
        permission_id=permission.id,
        granted_by_user_id=grantor.id,
        scope_type=PermissionGrantScopeType.GLOBAL,
        scope_id=uuid7(),
    )

    db_session.add(grant)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


@pytest.mark.parametrize(
    "scope_type",
    [
        PermissionGrantScopeType.PROJECT,
        PermissionGrantScopeType.WORKSPACE,
        PermissionGrantScopeType.CUSTOMER,
        PermissionGrantScopeType.USER,
    ],
)
def test_permission_grant_non_global_scope_requires_scope_id(
    db_session: Session,
    scope_type: PermissionGrantScopeType,
) -> None:
    """Every non-global scope requires a scope identifier."""
    user, grantor, permission = _persist_dependencies(
        db_session,
        user_identifier=f"missing-scope-user-{scope_type.value.lower()}",
        grantor_identifier=f"missing-scope-grantor-{scope_type.value.lower()}",
        permission_identifier=f"missing.scope.{scope_type.value.lower()}",
    )

    grant = _grant(
        user_id=user.id,
        permission_id=permission.id,
        granted_by_user_id=grantor.id,
        scope_type=scope_type,
        scope_id=None,
    )

    db_session.add(grant)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


@pytest.mark.parametrize(
    "effect",
    [
        PermissionGrantEffect.ALLOW,
        PermissionGrantEffect.DENY,
    ],
)
def test_permission_grant_supports_both_effects(
    db_session: Session,
    effect: PermissionGrantEffect,
) -> None:
    """Both ALLOW and DENY grants can be persisted."""
    user, grantor, permission = _persist_dependencies(
        db_session,
        user_identifier=f"effect-user-{effect.value.lower()}",
        grantor_identifier=f"effect-grantor-{effect.value.lower()}",
        permission_identifier=f"effect.test.{effect.value.lower()}",
    )

    grant = _commit_grant(
        db_session,
        _grant(
            user_id=user.id,
            permission_id=permission.id,
            granted_by_user_id=grantor.id,
            effect=effect,
        ),
    )

    persisted = db_session.get(PermissionGrant, grant.id)

    assert persisted is not None
    assert persisted.effect is effect


def test_permission_grant_supports_purchase_limit_json(
    db_session: Session,
) -> None:
    """A purchase limit can use a structured JSON value."""
    user, grantor, permission = _persist_dependencies(
        db_session,
        user_identifier="purchase-limit-json-user",
        grantor_identifier="purchase-limit-json-grantor",
        permission_identifier="purchase.create.json",
    )

    constraint_value: JSONValue = {
        "amount": "2000.50",
        "currency": "EUR",
        "metadata": {
            "approval_required": True,
            "allowed_categories": ["material", "equipment"],
        },
    }

    grant = _commit_grant(
        db_session,
        _grant(
            user_id=user.id,
            permission_id=permission.id,
            granted_by_user_id=grantor.id,
            scope_type=PermissionGrantScopeType.PROJECT,
            scope_id=uuid7(),
            constraint_type=PermissionGrantConstraintType.PURCHASE_LIMIT,
            constraint_value=constraint_value,
        ),
    )

    persisted = db_session.get(PermissionGrant, grant.id)

    assert persisted is not None
    assert persisted.constraint_type is PermissionGrantConstraintType.PURCHASE_LIMIT
    assert persisted.constraint_value == constraint_value


def test_permission_grant_supports_nested_json_values(
    db_session: Session,
) -> None:
    """Constraint values may contain arbitrary nested JSON."""
    user, grantor, permission = _persist_dependencies(
        db_session,
        user_identifier="nested-json-user",
        grantor_identifier="nested-json-grantor",
        permission_identifier="purchase.create.nested",
    )

    constraint_value: JSONValue = {
        "limits": [
            {"amount": "100.00", "currency": "EUR"},
            {"amount": "250.00", "currency": "USD"},
        ],
        "rules": {
            "categories": ["material", "equipment"],
            "requires_approval": True,
            "max_items": 10,
        },
    }

    grant = _commit_grant(
        db_session,
        _grant(
            user_id=user.id,
            permission_id=permission.id,
            granted_by_user_id=grantor.id,
            constraint_type=PermissionGrantConstraintType.PURCHASE_LIMIT,
            constraint_value=constraint_value,
        ),
    )

    persisted = db_session.get(PermissionGrant, grant.id)

    assert persisted is not None
    assert persisted.constraint_value == constraint_value


@pytest.mark.parametrize(
    "constraint_value",
    [
        {},
        {"enabled": True},
        {"amount": 2000},
        {"amount": 2000.50},
        ["material", "equipment"],
        [{"limit": 100}, {"limit": 200}],
        "future-constraint-value",
        42,
        12.5,
        True,
    ],
)
def test_permission_grant_accepts_json_constraint_values(
    db_session: Session,
    constraint_value: JSONValue,
) -> None:
    """constraint_value remains a generic JSON container."""
    user, grantor, permission = _persist_dependencies(
        db_session,
        user_identifier=f"generic-json-user-{uuid7()}",
        grantor_identifier=f"generic-json-grantor-{uuid7()}",
        permission_identifier=f"generic.json.{uuid7()}",
    )

    grant = _commit_grant(
        db_session,
        _grant(
            user_id=user.id,
            permission_id=permission.id,
            granted_by_user_id=grantor.id,
            constraint_type=PermissionGrantConstraintType.PURCHASE_LIMIT,
            constraint_value=constraint_value,
        ),
    )

    persisted = db_session.get(PermissionGrant, grant.id)

    assert persisted is not None
    assert persisted.constraint_value == constraint_value


def test_permission_grant_purchase_limit_allows_null_value(
    db_session: Session,
) -> None:
    """A purchase limit may intentionally have no value."""
    user, grantor, permission = _persist_dependencies(
        db_session,
        user_identifier="unlimited-purchase-user",
        grantor_identifier="unlimited-purchase-grantor",
        permission_identifier="purchase.create.unlimited",
    )

    grant = _commit_grant(
        db_session,
        _grant(
            user_id=user.id,
            permission_id=permission.id,
            granted_by_user_id=grantor.id,
            constraint_type=PermissionGrantConstraintType.PURCHASE_LIMIT,
            constraint_value=None,
        ),
    )

    persisted = db_session.get(PermissionGrant, grant.id)

    assert persisted is not None
    assert persisted.constraint_type is PermissionGrantConstraintType.PURCHASE_LIMIT
    assert persisted.constraint_value is None


def test_permission_grant_without_constraint_type_allows_null_value(
    db_session: Session,
) -> None:
    """A grant without a constraint type has no constraint value."""
    user, grantor, permission = _persist_dependencies(
        db_session,
        user_identifier="no-constraint-user",
        grantor_identifier="no-constraint-grantor",
        permission_identifier="no.constraint",
    )

    grant = _commit_grant(
        db_session,
        _grant(
            user_id=user.id,
            permission_id=permission.id,
            granted_by_user_id=grantor.id,
            constraint_type=None,
            constraint_value=None,
        ),
    )

    persisted = db_session.get(PermissionGrant, grant.id)

    assert persisted is not None
    assert persisted.constraint_type is None
    assert persisted.constraint_value is None


def test_permission_grant_without_constraint_type_rejects_value(
    db_session: Session,
) -> None:
    """A constraint value is invalid when no constraint type is present."""
    user, grantor, permission = _persist_dependencies(
        db_session,
        user_identifier="invalid-constraint-user",
        grantor_identifier="invalid-constraint-grantor",
        permission_identifier="invalid.constraint",
    )

    grant = _grant(
        user_id=user.id,
        permission_id=permission.id,
        granted_by_user_id=grantor.id,
        constraint_type=None,
        constraint_value={"unexpected": True},
    )

    db_session.add(grant)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_permission_grant_rejects_invalid_valid_range(
    db_session: Session,
) -> None:
    """A grant cannot expire before or at its valid-from timestamp."""
    user, grantor, permission = _persist_dependencies(
        db_session,
        user_identifier="range-user",
        grantor_identifier="range-grantor",
        permission_identifier="range.test",
    )

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


def test_permission_grant_rejects_equal_valid_range(
    db_session: Session,
) -> None:
    """A grant cannot expire exactly at its valid-from timestamp."""
    user, grantor, permission = _persist_dependencies(
        db_session,
        user_identifier="equal-range-user",
        grantor_identifier="equal-range-grantor",
        permission_identifier="equal.range",
    )

    timestamp = datetime(2026, 1, 1, tzinfo=UTC)

    grant = _grant(
        user_id=user.id,
        permission_id=permission.id,
        granted_by_user_id=grantor.id,
        valid_from=timestamp,
        valid_until=timestamp,
    )

    db_session.add(grant)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_permission_grant_allows_open_ended_validity(
    db_session: Session,
) -> None:
    """A grant may have no valid-until timestamp."""
    user, grantor, permission = _persist_dependencies(
        db_session,
        user_identifier="open-ended-user",
        grantor_identifier="open-ended-grantor",
        permission_identifier="open.ended",
    )

    grant = _commit_grant(
        db_session,
        _grant(
            user_id=user.id,
            permission_id=permission.id,
            granted_by_user_id=grantor.id,
            valid_until=None,
        ),
    )

    persisted = db_session.get(PermissionGrant, grant.id)

    assert persisted is not None
    assert persisted.valid_until is None


def test_permission_grant_repository_get(
    db_session: Session,
) -> None:
    """The repository retrieves a grant by ID."""
    user, grantor, permission = _persist_dependencies(
        db_session,
        user_identifier="repository-get-user",
        grantor_identifier="repository-get-grantor",
        permission_identifier="repository.get",
    )

    grant = _commit_grant(
        db_session,
        _grant(
            user_id=user.id,
            permission_id=permission.id,
            granted_by_user_id=grantor.id,
        ),
    )

    repository = PermissionGrantRepository(db_session)

    result = repository.get(grant.id)

    assert result is not None
    assert result.id == grant.id


def test_permission_grant_repository_get_returns_none_for_unknown_id(
    db_session: Session,
) -> None:
    """The repository returns None for an unknown grant."""
    repository = PermissionGrantRepository(db_session)

    assert repository.get(uuid7()) is None


def test_permission_grant_repository_list_for_user(
    db_session: Session,
) -> None:
    """The repository lists grants belonging to the requested user."""
    user, grantor, permission = _persist_dependencies(
        db_session,
        user_identifier="list-user",
        grantor_identifier="list-grantor",
        permission_identifier="list.permission",
    )

    other_user = _user("other-list-user")
    db_session.add(other_user)
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
    """Only active and temporally valid grants are returned."""
    user, grantor, permission = _persist_dependencies(
        db_session,
        user_identifier="active-list-user",
        grantor_identifier="active-list-grantor",
        permission_identifier="active.list",
    )

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
    user, grantor, permission = _persist_dependencies(
        db_session,
        user_identifier="repository-add-user",
        grantor_identifier="repository-add-grantor",
        permission_identifier="repository.add",
    )

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
    user, grantor, permission = _persist_dependencies(
        db_session,
        user_identifier="deactivate-user",
        grantor_identifier="deactivate-grantor",
        permission_identifier="deactivate.permission",
    )

    grant = _commit_grant(
        db_session,
        _grant(
            user_id=user.id,
            permission_id=permission.id,
            granted_by_user_id=grantor.id,
            active=True,
        ),
    )

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
    user, grantor, permission = _persist_dependencies(
        db_session,
        user_identifier="transaction-user",
        grantor_identifier="transaction-grantor",
        permission_identifier="transaction.permission",
    )

    grant = _grant(
        user_id=user.id,
        permission_id=permission.id,
        granted_by_user_id=grantor.id,
    )

    db_session.add(grant)
    db_session.flush()

    grant_id = grant.id

    assert db_session.get(PermissionGrant, grant_id) is not None

    db_session.rollback()

    assert db_session.get(PermissionGrant, grant_id) is None
