"""Persistence operations for permission grants."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import PermissionGrant


class PermissionGrantRepository:
    """Persist and retrieve explicit PermissionGrant entities."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, grant_id: UUID) -> PermissionGrant | None:
        """Return a permission grant by ID."""
        return self.session.get(PermissionGrant, grant_id)

    def list_for_user(
        self,
        user_id: UUID,
    ) -> list[PermissionGrant]:
        """Return all permission grants for a user."""
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
        at: datetime,
    ) -> list[PermissionGrant]:
        """Return grants active and temporally valid for a user."""
        statement = (
            select(PermissionGrant)
            .where(
                PermissionGrant.user_id == user_id,
                PermissionGrant.active.is_(True),
                PermissionGrant.valid_from <= at,
                (
                    PermissionGrant.valid_until.is_(None)
                    | (PermissionGrant.valid_until > at)
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
        """Deactivate a permission grant without deleting its history."""
        grant.active = False
        self.session.flush()
        return grant
