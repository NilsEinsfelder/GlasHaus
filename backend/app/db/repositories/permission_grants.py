"""Persistence operations for permission grants."""

from __future__ import annotations

import builtins
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import PermissionGrant


class PermissionGrantRepository:
    """Persist and retrieve PermissionGrant entities."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, grant_id: UUID) -> PermissionGrant | None:
        """Return a permission grant by ID."""
        return self.session.get(PermissionGrant, grant_id)

    def list(self) -> builtins.list[PermissionGrant]:
        """Return all permission grants in deterministic order."""
        statement = select(PermissionGrant).order_by(
            PermissionGrant.id,
        )
        return list(self.session.scalars(statement).all())

    def list_for_user(
        self,
        user_id: UUID,
    ) -> builtins.list[PermissionGrant]:
        """Return all permission grants belonging to a user."""
        statement = (
            select(PermissionGrant)
            .where(PermissionGrant.user_id == user_id)
            .order_by(
                PermissionGrant.valid_from,
                PermissionGrant.id,
            )
        )
        return list(self.session.scalars(statement).all())

    def list_active_for_user(
        self,
        user_id: UUID,
        *,
        at: datetime | None = None,
    ) -> builtins.list[PermissionGrant]:
        """Return grants active for a user at a given point in time."""
        timestamp = at if at is not None else datetime.now(UTC)

        statement = (
            select(PermissionGrant)
            .where(
                PermissionGrant.user_id == user_id,
                PermissionGrant.active.is_(True),
                PermissionGrant.valid_from <= timestamp,
                (
                    PermissionGrant.valid_until.is_(None)
                    | (PermissionGrant.valid_until > timestamp)
                ),
            )
            .order_by(
                PermissionGrant.valid_from,
                PermissionGrant.id,
            )
        )

        return list(self.session.scalars(statement).all())

    def add(self, grant: PermissionGrant) -> PermissionGrant:
        """Add a permission grant to the current unit of work."""
        self.session.add(grant)
        self.session.flush()
        return grant

    def deactivate(self, grant: PermissionGrant) -> PermissionGrant:
        """Deactivate a permission grant."""
        grant.active = False
        self.session.flush()
        return grant
