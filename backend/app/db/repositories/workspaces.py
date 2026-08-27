"""Persistence operations for workspaces."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Workspace, WorkspaceType


class WorkspaceRepository:
    """Persist and retrieve Workspace entities."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, workspace_id: UUID) -> Workspace | None:
        """Return a workspace by ID."""
        return self.session.get(Workspace, workspace_id)

    def get_for_project(
        self,
        project_id: UUID,
        workspace_type: WorkspaceType,
    ) -> Workspace | None:
        """Return the workspace of a project for the requested type."""
        statement = select(Workspace).where(
            Workspace.project_id == project_id,
            Workspace.workspace_type == workspace_type,
        )

        return self.session.scalar(statement)

    def list_for_project(
        self,
        project_id: UUID,
    ) -> list[Workspace]:
        """Return all workspaces belonging to a project."""
        statement = (
            select(Workspace)
            .where(Workspace.project_id == project_id)
            .order_by(Workspace.workspace_type)
        )

        return list(self.session.scalars(statement).all())

    def add(self, workspace: Workspace) -> Workspace:
        """Add a workspace to the current unit of work."""
        self.session.add(workspace)
        self.session.flush()
        return workspace
