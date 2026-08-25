"""Persistence operations for project assignments."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ProjectAssignment


class ProjectAssignmentRepository:
    """Persist and retrieve ProjectAssignment entities."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(
        self,
        assignment_id: UUID,
    ) -> ProjectAssignment | None:
        """Return an assignment by ID."""
        return self.session.get(ProjectAssignment, assignment_id)

    def list_for_user(
        self,
        user_id: UUID,
        *,
        active_only: bool = False,
    ) -> list[ProjectAssignment]:
        """Return assignments for a user."""
        statement = (
            select(ProjectAssignment)
            .where(ProjectAssignment.user_id == user_id)
            .order_by(ProjectAssignment.valid_from)
        )

        if active_only:
            statement = statement.where(
                ProjectAssignment.active.is_(True),
            )

        return list(self.session.scalars(statement).all())

    def list_for_project(
        self,
        project_id: UUID,
        *,
        active_only: bool = False,
    ) -> list[ProjectAssignment]:
        """Return assignments for a project."""
        statement = (
            select(ProjectAssignment)
            .where(ProjectAssignment.project_id == project_id)
            .order_by(ProjectAssignment.valid_from)
        )

        if active_only:
            statement = statement.where(
                ProjectAssignment.active.is_(True),
            )

        return list(self.session.scalars(statement).all())

    def add(
        self,
        assignment: ProjectAssignment,
    ) -> ProjectAssignment:
        """Add an assignment to the current unit of work."""
        self.session.add(assignment)
        self.session.flush()
        return assignment

    def deactivate(
        self,
        assignment: ProjectAssignment,
    ) -> ProjectAssignment:
        """Deactivate an assignment without deleting history."""
        assignment.active = False
        self.session.flush()
        return assignment
