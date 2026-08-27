"""Tests for workspace persistence."""

from uuid import uuid7

import pytest
from app.db.models import User, Workspace, WorkspaceType
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


@pytest.mark.parametrize(
    "workspace_type",
    [
        WorkspaceType.INTERNAL,
        WorkspaceType.CUSTOMER,
    ],
)
def test_workspace_roundtrip(
    db_session: Session,
    user: User,
    project,
    workspace_type: WorkspaceType,
) -> None:
    """Supported workspace types must persist all model fields."""
    workspace = Workspace(
        id=uuid7(),
        project_id=project.id,
        workspace_type=workspace_type,
        created_from=user.id,
    )

    db_session.add(workspace)
    db_session.commit()
    db_session.refresh(workspace)

    assert workspace.project_id == project.id
    assert workspace.workspace_type is workspace_type
    assert workspace.created_from == user.id
    assert workspace.created_at is not None
    assert workspace.updated_at is not None


def test_project_can_have_internal_and_customer_workspace(
    db_session: Session,
    user: User,
    project,
) -> None:
    """A project must support one workspace of each primary type."""
    internal_workspace = Workspace(
        id=uuid7(),
        project_id=project.id,
        workspace_type=WorkspaceType.INTERNAL,
        created_from=user.id,
    )
    customer_workspace = Workspace(
        id=uuid7(),
        project_id=project.id,
        workspace_type=WorkspaceType.CUSTOMER,
        created_from=user.id,
    )

    db_session.add_all(
        [
            internal_workspace,
            customer_workspace,
        ],
    )
    db_session.commit()

    assert sorted(workspace.workspace_type for workspace in project.workspaces) == [
        WorkspaceType.CUSTOMER,
        WorkspaceType.INTERNAL,
    ]


def test_project_cannot_have_two_workspaces_of_same_type(
    db_session: Session,
    user: User,
    project,
) -> None:
    """The database must enforce one workspace per project and type."""
    first = Workspace(
        id=uuid7(),
        project_id=project.id,
        workspace_type=WorkspaceType.INTERNAL,
        created_from=user.id,
    )
    second = Workspace(
        id=uuid7(),
        project_id=project.id,
        workspace_type=WorkspaceType.INTERNAL,
        created_from=user.id,
    )

    db_session.add_all([first, second])

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_workspace_type_constraint_rejects_invalid_value(
    db_session: Session,
    user: User,
    project,
) -> None:
    """Unsupported workspace types must be rejected by the database."""
    workspace = Workspace(
        id=uuid7(),
        project_id=project.id,
        workspace_type="INVALID",
        created_from=user.id,
    )

    db_session.add(workspace)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_workspace_requires_existing_project(
    db_session: Session,
    user: User,
) -> None:
    """project_id must reference an existing project."""
    workspace = Workspace(
        id=uuid7(),
        project_id=uuid7(),
        workspace_type=WorkspaceType.INTERNAL,
        created_from=user.id,
    )

    db_session.add(workspace)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_workspace_requires_existing_creator(
    db_session: Session,
    project,
) -> None:
    """created_from must reference an existing user."""
    workspace = Workspace(
        id=uuid7(),
        project_id=project.id,
        workspace_type=WorkspaceType.INTERNAL,
        created_from=uuid7(),
    )

    db_session.add(workspace)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_workspace_exposes_project_relationship(
    db_session: Session,
    user: User,
    project,
) -> None:
    """Workspace.project must resolve to the owning project."""
    workspace = Workspace(
        id=uuid7(),
        project_id=project.id,
        workspace_type=WorkspaceType.CUSTOMER,
        created_from=user.id,
    )

    db_session.add(workspace)
    db_session.commit()
    db_session.refresh(workspace)

    assert workspace.project is project


def test_workspace_exposes_creator_relationship(
    db_session: Session,
    user: User,
    project,
) -> None:
    """Workspace.created_from_user must resolve to the creating user."""
    workspace = Workspace(
        id=uuid7(),
        project_id=project.id,
        workspace_type=WorkspaceType.INTERNAL,
        created_from=user.id,
    )

    db_session.add(workspace)
    db_session.commit()
    db_session.refresh(workspace)

    assert workspace.created_from_user is user
