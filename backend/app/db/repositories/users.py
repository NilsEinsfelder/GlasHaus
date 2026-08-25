"""Persistence operations for users."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import User


class UserRepository:
    """Persist and retrieve User entities."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, user_id: UUID) -> User | None:
        """Return a user by ID."""
        return self.session.get(User, user_id)

    def get_by_login_identifier(
        self,
        login_identifier: str,
    ) -> User | None:
        """Return a user by its unique login identifier."""
        statement = select(User).where(
            User.login_identifier == login_identifier,
        )
        return self.session.scalar(statement)

    def list(
        self,
        *,
        active_only: bool = False,
    ) -> list[User]:
        """Return users."""
        statement = select(User).order_by(User.display_name)

        if active_only:
            statement = statement.where(User.active.is_(True))

        return list(self.session.scalars(statement).all())

    def add(self, user: User) -> User:
        """Add a user to the current unit of work."""
        self.session.add(user)
        self.session.flush()
        return user

    def deactivate(self, user: User) -> User:
        """Deactivate a user without deleting historical data."""
        user.active = False
        self.session.flush()
        return user
