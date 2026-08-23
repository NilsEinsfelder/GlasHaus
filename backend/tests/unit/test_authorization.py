"""Unit tests for the GlasHaus identity and authorization model."""

from uuid import uuid7

import pytest
from app.security.authorization import (
    Action,
    AuthorizationDecision,
    CustomerRole,
    CustomerUserPrincipal,
    InternalRole,
    InternalUserPrincipal,
    Project,
    Workspace,
    authorize,
)


def test_internal_user_can_read_assigned_project() -> None:
    """An assigned internal user may read the project."""
    project = Project(id=uuid7(), customer_id=uuid7())
    user = InternalUserPrincipal(
        id=uuid7(),
        role=InternalRole.TECHNICIAN,
        assigned_project_ids=frozenset({project.id}),
    )

    decision = authorize(user, Action.PROJECT_READ, project)

    assert decision == AuthorizationDecision.ALLOW


def test_internal_user_cannot_read_unassigned_project() -> None:
    """An internal user must not access an unassigned project."""
    assigned_project = Project(id=uuid7(), customer_id=uuid7())
    requested_project = Project(id=uuid7(), customer_id=uuid7())

    user = InternalUserPrincipal(
        id=uuid7(),
        role=InternalRole.TECHNICIAN,
        assigned_project_ids=frozenset({assigned_project.id}),
    )

    decision = authorize(user, Action.PROJECT_READ, requested_project)

    assert decision == AuthorizationDecision.DENY


def test_internal_user_has_no_address_only_fallback_for_unassigned_project() -> None:
    """Unassigned projects must not have an emergency address exception."""
    assigned_project = Project(id=uuid7(), customer_id=uuid7())
    requested_project = Project(id=uuid7(), customer_id=uuid7())

    user = InternalUserPrincipal(
        id=uuid7(),
        role=InternalRole.TECHNICIAN,
        assigned_project_ids=frozenset({assigned_project.id}),
    )

    decision = authorize(
        user,
        Action.PROJECT_ADDRESS_READ,
        requested_project,
    )

    assert decision == AuthorizationDecision.DENY


def test_inactive_internal_user_is_denied() -> None:
    """An inactive internal user must not access any project."""
    project = Project(id=uuid7(), customer_id=uuid7())

    user = InternalUserPrincipal(
        id=uuid7(),
        role=InternalRole.TECHNICIAN,
        assigned_project_ids=frozenset({project.id}),
        active=False,
    )

    decision = authorize(user, Action.PROJECT_READ, project)

    assert decision == AuthorizationDecision.DENY


def test_internal_user_can_access_internal_workspace_of_assigned_project() -> None:
    """Assigned internal users may access the internal workspace."""
    project = Project(id=uuid7(), customer_id=uuid7())
    user = InternalUserPrincipal(
        id=uuid7(),
        role=InternalRole.TECHNICIAN,
        assigned_project_ids=frozenset({project.id}),
    )

    decision = authorize(
        user,
        Action.WORKSPACE_READ,
        project,
        workspace=Workspace.INTERNAL,
    )

    assert decision == AuthorizationDecision.ALLOW


def test_internal_user_can_access_customer_workspace_of_assigned_project() -> None:
    """Assigned internal users may access the customer workspace."""
    project = Project(id=uuid7(), customer_id=uuid7())
    user = InternalUserPrincipal(
        id=uuid7(),
        role=InternalRole.PROJECT_MANAGER,
        assigned_project_ids=frozenset({project.id}),
    )

    decision = authorize(
        user,
        Action.WORKSPACE_READ,
        project,
        workspace=Workspace.CUSTOMER,
    )

    assert decision == AuthorizationDecision.ALLOW


def test_customer_user_can_read_own_project() -> None:
    """A customer user may read a project belonging to their customer."""
    customer_id = uuid7()
    project = Project(id=uuid7(), customer_id=customer_id)

    user = CustomerUserPrincipal(
        id=uuid7(),
        customer_id=customer_id,
        role=CustomerRole.CUSTOMER,
        accessible_project_ids=frozenset({project.id}),
    )

    decision = authorize(user, Action.PROJECT_READ, project)

    assert decision == AuthorizationDecision.ALLOW


def test_customer_user_cannot_read_project_of_another_customer() -> None:
    """A customer user must not access another customer's project."""
    own_customer_id = uuid7()
    other_customer_id = uuid7()

    own_project = Project(id=uuid7(), customer_id=own_customer_id)
    other_project = Project(id=uuid7(), customer_id=other_customer_id)

    user = CustomerUserPrincipal(
        id=uuid7(),
        customer_id=own_customer_id,
        role=CustomerRole.CUSTOMER,
        accessible_project_ids=frozenset({own_project.id}),
    )

    decision = authorize(user, Action.PROJECT_READ, other_project)

    assert decision == AuthorizationDecision.DENY


def test_customer_user_cannot_read_unassigned_customer_project() -> None:
    """Customer membership alone must not grant access to every project."""
    customer_id = uuid7()

    assigned_project = Project(id=uuid7(), customer_id=customer_id)
    unassigned_project = Project(id=uuid7(), customer_id=customer_id)

    user = CustomerUserPrincipal(
        id=uuid7(),
        customer_id=customer_id,
        role=CustomerRole.CUSTOMER,
        accessible_project_ids=frozenset({assigned_project.id}),
    )

    decision = authorize(user, Action.PROJECT_READ, unassigned_project)

    assert decision == AuthorizationDecision.DENY


def test_customer_user_can_read_customer_workspace() -> None:
    """A customer user may access the customer workspace."""
    customer_id = uuid7()
    project = Project(id=uuid7(), customer_id=customer_id)

    user = CustomerUserPrincipal(
        id=uuid7(),
        customer_id=customer_id,
        role=CustomerRole.CUSTOMER,
        accessible_project_ids=frozenset({project.id}),
    )

    decision = authorize(
        user,
        Action.WORKSPACE_READ,
        project,
        workspace=Workspace.CUSTOMER,
    )

    assert decision == AuthorizationDecision.ALLOW


def test_customer_user_cannot_read_internal_workspace() -> None:
    """Customer users must never access the internal workspace."""
    customer_id = uuid7()
    project = Project(id=uuid7(), customer_id=customer_id)

    user = CustomerUserPrincipal(
        id=uuid7(),
        customer_id=customer_id,
        role=CustomerRole.CUSTOMER,
        accessible_project_ids=frozenset({project.id}),
    )

    decision = authorize(
        user,
        Action.WORKSPACE_READ,
        project,
        workspace=Workspace.INTERNAL,
    )

    assert decision == AuthorizationDecision.DENY


def test_customer_user_can_download_customer_file() -> None:
    """Customer users may download files from the customer workspace."""
    customer_id = uuid7()
    project = Project(id=uuid7(), customer_id=customer_id)

    user = CustomerUserPrincipal(
        id=uuid7(),
        customer_id=customer_id,
        role=CustomerRole.CUSTOMER,
        accessible_project_ids=frozenset({project.id}),
    )

    decision = authorize(
        user,
        Action.CUSTOMER_FILE_DOWNLOAD,
        project,
        workspace=Workspace.CUSTOMER,
    )

    assert decision == AuthorizationDecision.ALLOW


def test_customer_user_cannot_download_from_internal_workspace() -> None:
    """Customer users cannot use customer permissions against internal data."""
    customer_id = uuid7()
    project = Project(id=uuid7(), customer_id=customer_id)

    user = CustomerUserPrincipal(
        id=uuid7(),
        customer_id=customer_id,
        role=CustomerRole.CUSTOMER,
        accessible_project_ids=frozenset({project.id}),
    )

    decision = authorize(
        user,
        Action.CUSTOMER_FILE_DOWNLOAD,
        project,
        workspace=Workspace.INTERNAL,
    )

    assert decision == AuthorizationDecision.DENY


def test_customer_user_cannot_use_internal_document_permission() -> None:
    """Customer roles must not inherit internal document permissions."""
    customer_id = uuid7()
    project = Project(id=uuid7(), customer_id=customer_id)

    user = CustomerUserPrincipal(
        id=uuid7(),
        customer_id=customer_id,
        role=CustomerRole.CUSTOMER,
        accessible_project_ids=frozenset({project.id}),
    )

    decision = authorize(
        user,
        Action.DOCUMENT_UPDATE,
        project,
        workspace=Workspace.CUSTOMER,
    )

    assert decision == AuthorizationDecision.DENY


def test_customer_manager_can_create_customer_files() -> None:
    """A customer manager may create content in the customer workspace."""
    customer_id = uuid7()
    project = Project(id=uuid7(), customer_id=customer_id)

    user = CustomerUserPrincipal(
        id=uuid7(),
        customer_id=customer_id,
        role=CustomerRole.CUSTOMER_MANAGER,
        accessible_project_ids=frozenset({project.id}),
    )

    decision = authorize(
        user,
        Action.CUSTOMER_FILE_CREATE,
        project,
        workspace=Workspace.CUSTOMER,
    )

    assert decision == AuthorizationDecision.ALLOW


def test_inactive_customer_user_is_denied() -> None:
    """An inactive customer user must not access any project."""
    customer_id = uuid7()
    project = Project(id=uuid7(), customer_id=customer_id)

    user = CustomerUserPrincipal(
        id=uuid7(),
        customer_id=customer_id,
        role=CustomerRole.CUSTOMER,
        accessible_project_ids=frozenset({project.id}),
        active=False,
    )

    decision = authorize(user, Action.PROJECT_READ, project)

    assert decision == AuthorizationDecision.DENY


@pytest.mark.parametrize(
    "principal",
    [
        InternalUserPrincipal(
            id=uuid7(),
            role=InternalRole.TECHNICIAN,
            assigned_project_ids=frozenset(),
        ),
        CustomerUserPrincipal(
            id=uuid7(),
            customer_id=uuid7(),
            role=CustomerRole.CUSTOMER,
            accessible_project_ids=frozenset(),
        ),
    ],
)
def test_unassigned_project_access_is_denied(
    principal: InternalUserPrincipal | CustomerUserPrincipal,
) -> None:
    """No local principal may bypass project assignment."""
    project = Project(id=uuid7(), customer_id=uuid7())

    decision = authorize(
        principal,
        Action.PROJECT_READ,
        project,
    )

    assert decision == AuthorizationDecision.DENY


def test_customer_user_cannot_access_project_only_by_knowing_project_id() -> None:
    """Knowledge of a project ID must never grant customer access."""
    customer_id = uuid7()
    project = Project(id=uuid7(), customer_id=customer_id)

    user = CustomerUserPrincipal(
        id=uuid7(),
        customer_id=customer_id,
        role=CustomerRole.CUSTOMER,
        accessible_project_ids=frozenset(),
    )

    decision = authorize(user, Action.PROJECT_READ, project)

    assert decision == AuthorizationDecision.DENY


def test_internal_user_cannot_access_project_only_by_knowing_project_id() -> None:
    """Knowledge of a project ID must never bypass assignment."""
    project = Project(id=uuid7(), customer_id=uuid7())

    user = InternalUserPrincipal(
        id=uuid7(),
        role=InternalRole.TECHNICIAN,
        assigned_project_ids=frozenset(),
    )

    decision = authorize(user, Action.PROJECT_READ, project)

    assert decision == AuthorizationDecision.DENY
