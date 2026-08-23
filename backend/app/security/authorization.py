"""Authorization policy for the GlasHaus backend."""

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class AuthorizationDecision(StrEnum):
    """Result of an authorization decision."""

    ALLOW = "allow"
    DENY = "deny"


class PrincipalType(StrEnum):
    """Types of principals supported by GlasHaus."""

    INTERNAL_USER = "internal_user"
    CUSTOMER_USER = "customer_user"
    FEDERATION_PEER = "federation_peer"


class InternalRole(StrEnum):
    """Roles available to internal users."""

    ADMIN = "admin"
    OFFICE = "office"
    PROJECT_MANAGER = "project_manager"
    TECHNICIAN = "technician"
    VIEWER = "viewer"


class CustomerRole(StrEnum):
    """Roles available to customer users."""

    CUSTOMER = "customer"
    CUSTOMER_MANAGER = "customer_manager"


class Workspace(StrEnum):
    """Project workspaces."""

    INTERNAL = "internal"
    CUSTOMER = "customer"


class Action(StrEnum):
    """Actions that can be authorized by the policy."""

    PROJECT_READ = "project:read"
    PROJECT_ADDRESS_READ = "project:address:read"

    WORKSPACE_READ = "workspace:read"

    DOCUMENT_READ = "document:read"
    DOCUMENT_UPDATE = "document:update"

    CUSTOMER_FILE_DOWNLOAD = "customer:file:download"
    CUSTOMER_FILE_CREATE = "customer:file:create"


@dataclass(frozen=True, slots=True)
class Project:
    """Minimal project representation required by authorization."""

    id: UUID
    customer_id: UUID


@dataclass(frozen=True, slots=True)
class InternalUserPrincipal:
    """Authenticated internal GlasHaus user."""

    id: UUID
    role: InternalRole
    assigned_project_ids: frozenset[UUID]
    active: bool = True

    @property
    def principal_type(self) -> PrincipalType:
        """Return the principal type."""
        return PrincipalType.INTERNAL_USER


@dataclass(frozen=True, slots=True)
class CustomerUserPrincipal:
    """Authenticated external customer user."""

    id: UUID
    customer_id: UUID
    role: CustomerRole
    accessible_project_ids: frozenset[UUID]
    active: bool = True

    @property
    def principal_type(self) -> PrincipalType:
        """Return the principal type."""
        return PrincipalType.CUSTOMER_USER


@dataclass(frozen=True, slots=True)
class FederationPeerPrincipal:
    """Future authenticated GlasHaus federation peer."""

    id: UUID
    active: bool = True

    @property
    def principal_type(self) -> PrincipalType:
        """Return the principal type."""
        return PrincipalType.FEDERATION_PEER


Principal = InternalUserPrincipal | CustomerUserPrincipal | FederationPeerPrincipal


_INTERNAL_PERMISSIONS: dict[InternalRole, frozenset[Action]] = {
    InternalRole.ADMIN: frozenset(
        {
            Action.PROJECT_READ,
            Action.PROJECT_ADDRESS_READ,
            Action.WORKSPACE_READ,
            Action.DOCUMENT_READ,
            Action.DOCUMENT_UPDATE,
        }
    ),
    InternalRole.OFFICE: frozenset(
        {
            Action.PROJECT_READ,
            Action.PROJECT_ADDRESS_READ,
            Action.WORKSPACE_READ,
            Action.DOCUMENT_READ,
            Action.DOCUMENT_UPDATE,
        }
    ),
    InternalRole.PROJECT_MANAGER: frozenset(
        {
            Action.PROJECT_READ,
            Action.PROJECT_ADDRESS_READ,
            Action.WORKSPACE_READ,
            Action.DOCUMENT_READ,
            Action.DOCUMENT_UPDATE,
        }
    ),
    InternalRole.TECHNICIAN: frozenset(
        {
            Action.PROJECT_READ,
            Action.PROJECT_ADDRESS_READ,
            Action.WORKSPACE_READ,
            Action.DOCUMENT_READ,
        }
    ),
    InternalRole.VIEWER: frozenset(
        {
            Action.PROJECT_READ,
            Action.PROJECT_ADDRESS_READ,
            Action.WORKSPACE_READ,
            Action.DOCUMENT_READ,
        }
    ),
}


_CUSTOMER_PERMISSIONS: dict[CustomerRole, frozenset[Action]] = {
    CustomerRole.CUSTOMER: frozenset(
        {
            Action.PROJECT_READ,
            Action.WORKSPACE_READ,
            Action.CUSTOMER_FILE_DOWNLOAD,
        }
    ),
    CustomerRole.CUSTOMER_MANAGER: frozenset(
        {
            Action.PROJECT_READ,
            Action.WORKSPACE_READ,
            Action.CUSTOMER_FILE_DOWNLOAD,
            Action.CUSTOMER_FILE_CREATE,
        }
    ),
}


def authorize(
    principal: Principal,
    action: Action,
    project: Project,
    *,
    workspace: Workspace | None = None,
) -> AuthorizationDecision:
    """Authorize an action against a project.

    Authorization follows the GlasHaus security model:

    - inactive principals are denied;
    - internal users require explicit project assignment;
    - customer users require matching customer ownership and project access;
    - customer users may only access the customer workspace;
    - permissions are role-specific;
    - federation is not implemented yet.
    """
    if not principal.active:
        return AuthorizationDecision.DENY

    if isinstance(principal, InternalUserPrincipal):
        return _authorize_internal_user(
            principal,
            action,
            project,
            workspace,
        )

    if isinstance(principal, CustomerUserPrincipal):
        return _authorize_customer_user(
            principal,
            action,
            project,
            workspace,
        )

    return AuthorizationDecision.DENY


def _authorize_internal_user(
    principal: InternalUserPrincipal,
    action: Action,
    project: Project,
    workspace: Workspace | None,
) -> AuthorizationDecision:
    """Authorize an internal user."""
    if project.id not in principal.assigned_project_ids:
        return AuthorizationDecision.DENY

    permissions = _INTERNAL_PERMISSIONS[principal.role]

    if action not in permissions:
        return AuthorizationDecision.DENY

    if workspace is Workspace.CUSTOMER:
        return AuthorizationDecision.ALLOW

    if workspace is Workspace.INTERNAL:
        return AuthorizationDecision.ALLOW

    return AuthorizationDecision.ALLOW


def _authorize_customer_user(
    principal: CustomerUserPrincipal,
    action: Action,
    project: Project,
    workspace: Workspace | None,
) -> AuthorizationDecision:
    """Authorize a customer user."""
    if principal.customer_id != project.customer_id:
        return AuthorizationDecision.DENY

    if project.id not in principal.accessible_project_ids:
        return AuthorizationDecision.DENY

    permissions = _CUSTOMER_PERMISSIONS[principal.role]

    if action not in permissions:
        return AuthorizationDecision.DENY

    if workspace is Workspace.INTERNAL:
        return AuthorizationDecision.DENY

    if workspace is None:
        return AuthorizationDecision.ALLOW

    return AuthorizationDecision.ALLOW
