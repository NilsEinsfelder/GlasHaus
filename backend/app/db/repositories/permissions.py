"""Persistence operations for permissions."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Permission


class PermissionRepository:
    """Persist and retrieve canonical Permission entities."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, permission_id: UUID) -> Permission | None:
        """Return a permission by ID."""
        return self.session.get(Permission, permission_id)

    def get_by_identifier(self, identifier: str) -> Permission | None:
        """Return a permission by its canonical identifier."""
        statement = select(Permission).where(
            Permission.identifier == identifier,
        )
        return self.session.scalar(statement)

    def list(self) -> list[Permission]:
        """Return all permissions in canonical identifier order."""
        statement = select(Permission).order_by(Permission.identifier)
        return list(self.session.scalars(statement).all())

    def add(self, permission: Permission) -> Permission:
        """Add a permission to the current unit of work."""
        self.session.add(permission)
        self.session.flush()
        return permission
