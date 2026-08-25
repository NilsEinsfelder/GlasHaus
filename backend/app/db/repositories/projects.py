"""Persistence operations for projects."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Project


class ProjectRepository:
    """Persist and retrieve Project entities."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, project_id: UUID) -> Project | None:
        """Return a project by ID."""
        return self.session.get(Project, project_id)

    def list(
        self,
        *,
        customer_id: UUID | None = None,
        active_only: bool = False,
    ) -> list[Project]:
        """Return projects with optional customer and lifecycle filters."""
        statement = select(Project).order_by(Project.name)

        if customer_id is not None:
            statement = statement.where(
                Project.customer_id == customer_id,
            )

        if active_only:
            statement = statement.where(Project.active.is_(True))

        return list(self.session.scalars(statement).all())

    def add(self, project: Project) -> Project:
        """Add a project to the current unit of work."""
        self.session.add(project)
        self.session.flush()
        return project

    def deactivate(self, project: Project) -> Project:
        """Deactivate a project without deleting historical data."""
        project.active = False
        self.session.flush()
        return project
