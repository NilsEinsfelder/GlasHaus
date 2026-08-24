"""Authorization policy for the GlasHaus backend.

The authorization model combines:

- user type;
- exactly one role per user;
- internal hierarchy level;
- role-based default permissions;
- hierarchy-based default permissions;
- explicit scoped permission grants;
- project/customer relationships;
- policy constraints such as minimum age.

Authentication and cryptographic identity verification are deliberately outside
this module.

The authorization layer operates on domain-level relationship information.
Persistence and database access are deliberately kept outside this module.
"""

from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from uuid import UUID


class AuthorizationDecision(StrEnum):
    """Result of an authorization decision."""

    ALLOW = "allow"
    DENY = "deny"


class UserType(StrEnum):
    """High-level user types supported by GlasHaus."""

    INTERNAL = "internal"
    EXTERNAL = "external"


class InternalRole(StrEnum):
    """Concrete roles for internal users."""

    TECHNICIAN = "technician"
    OFFICE = "office"


class ExternalRole(StrEnum):
    """Concrete roles for external users."""

    CUSTOMER = "customer"
    TAX_ADVISOR = "tax_advisor"


class HierarchyLevel(StrEnum):
    """Employment hierarchy for internal users."""

    APPRENTICE = "apprentice"
    JUNIOR = "junior"
    STANDARD = "standard"
    SENIOR = "senior"
    SUPERVISOR = "supervisor"
    MANAGEMENT = "management"


class Workspace(StrEnum):
    """Logical GlasHaus workspaces."""

    INTERNAL = "internal"
    CUSTOMER = "customer"


class Permission(StrEnum):
    """Canonical MVP permissions supported by GlasHaus."""

    CUSTOMER_READ = "customer.read"
    CUSTOMER_WRITE = "customer.write"

    PROJECT_READ = "project.read"
    PROJECT_WRITE = "project.write"
    PROJECT_COORDINATE = "project.coordinate"

    PURCHASE_CREATE = "purchase.create"
    PURCHASE_GRANT = "purchase.grant"

    DOCUMENT_READ = "document.read"
    DOCUMENT_WRITE = "document.write"
    DOCUMENT_SIGN = "document.sign"

    SCHEDULE_VIEW_AVAILABILITY = "schedule.view_availability"
    SCHEDULE_VIEW_DETAILS = "schedule.view_details"
    SCHEDULE_ASSIGNMENT_WRITE = "schedule.assignment_write"
    SCHEDULE_ASSIGNMENT_REQUEST = "schedule.assignment_request"
    SCHEDULE_ASSIGNMENT_GRANT = "schedule.assignment_grant"

    USER_MANAGE = "user.manage"
    PERMISSION_MANAGE = "permission.manage"


class ScopeType(StrEnum):
    """Scope types for explicit permission grants."""

    GLOBAL = "global"
    PROJECT = "project"
    WORKSPACE = "workspace"
    USER = "user"


@dataclass(frozen=True, slots=True)
class UserPrincipal:
    """Authenticated GlasHaus user.

    A user has exactly one role. Internal users additionally have one
    hierarchy level derived from their effective employment relationship.

    Customer affiliation is deliberately not stored directly on the user.
    External business relationships are represented separately by
    ExternalRelationship and CustomerProjectAccess.
    """

    id: UUID
    user_type: UserType
    role: InternalRole | ExternalRole
    hierarchy_level: HierarchyLevel | None = None
    date_of_birth: date | None = None
    active: bool = True

    def __post_init__(self) -> None:
        """Validate identity invariants."""

        if self.user_type is UserType.INTERNAL:
            if not isinstance(self.role, InternalRole):
                raise ValueError("Internal users require an InternalRole.")

            if self.hierarchy_level is None:
                raise ValueError("Internal users require a hierarchy level.")

        elif self.user_type is UserType.EXTERNAL:
            if not isinstance(self.role, ExternalRole):
                raise ValueError("External users require an ExternalRole.")

            if self.hierarchy_level is not None:
                raise ValueError("External users cannot have a hierarchy level.")

        else:
            raise ValueError("Unsupported user type.")


@dataclass(frozen=True, slots=True)
class FederationPeerPrincipal:
    """Authenticated peer GlasHaus server.

    Federation peers are intentionally separate from human users.
    Federation authorization is not part of the current MVP permission set.
    """

    id: UUID
    active: bool = True


Principal = UserPrincipal | FederationPeerPrincipal


@dataclass(frozen=True, slots=True)
class ExternalRelationship:
    """Business relationship between an external user and a customer.

    This is a domain-level authorization input. It is deliberately not a
    persistence model and does not perform database access.
    """

    user_id: UUID
    customer_id: UUID
    relationship_type: str
    active: bool = True


@dataclass(frozen=True, slots=True)
class CustomerProjectAccess:
    """Explicit project access granted to an external user.

    A valid customer project access relationship is evaluated together with
    the corresponding ExternalRelationship.
    """

    user_id: UUID
    project_id: UUID
    active: bool = True


@dataclass(frozen=True, slots=True)
class Project:
    """Project with its two mandatory authorization workspaces."""

    id: UUID
    customer_id: UUID

    internal_workspace_id: UUID
    customer_workspace_id: UUID

    def __post_init__(self) -> None:
        """Validate the mandatory project workspace invariant."""

        if self.internal_workspace_id == self.customer_workspace_id:
            raise ValueError(
                "A project requires distinct internal and customer workspaces."
            )


@dataclass(frozen=True, slots=True)
class Resource:
    """Minimal resource information needed by authorization.

    Not every resource belongs to a project. Resource-specific authorization
    rules are evaluated by the authorization policy.
    """

    id: UUID
    project_id: UUID | None = None
    customer_id: UUID | None = None
    workspace: Workspace | None = None
    owner_user_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class PermissionGrant:
    """Explicit permission granted to one principal within a scope.

    Effect, validity and constraints will be added in the subsequent
    authorization steps.
    """

    principal_id: UUID
    permission: Permission
    scope_type: ScopeType
    scope_id: str
    active: bool = True


_ROLE_PERMISSIONS: dict[
    InternalRole | ExternalRole,
    frozenset[Permission],
] = {
    InternalRole.TECHNICIAN: frozenset(
        {
            Permission.PROJECT_READ,
            Permission.DOCUMENT_READ,
        }
    ),
    InternalRole.OFFICE: frozenset(
        {
            Permission.PROJECT_READ,
            Permission.DOCUMENT_READ,
        }
    ),
    ExternalRole.CUSTOMER: frozenset(
        {
            Permission.PROJECT_READ,
            Permission.CUSTOMER_READ,
        }
    ),
    ExternalRole.TAX_ADVISOR: frozenset(),
}


_HIERARCHY_PERMISSIONS: dict[
    HierarchyLevel,
    frozenset[Permission],
] = {
    HierarchyLevel.APPRENTICE: frozenset(),
    HierarchyLevel.JUNIOR: frozenset(),
    HierarchyLevel.STANDARD: frozenset(
        {
            Permission.PURCHASE_CREATE,
        }
    ),
    HierarchyLevel.SENIOR: frozenset(
        {
            Permission.SCHEDULE_VIEW_AVAILABILITY,
            Permission.SCHEDULE_ASSIGNMENT_REQUEST,
        }
    ),
    HierarchyLevel.SUPERVISOR: frozenset(
        {
            Permission.SCHEDULE_VIEW_AVAILABILITY,
            Permission.SCHEDULE_VIEW_DETAILS,
            Permission.SCHEDULE_ASSIGNMENT_WRITE,
            Permission.SCHEDULE_ASSIGNMENT_REQUEST,
            Permission.SCHEDULE_ASSIGNMENT_GRANT,
        }
    ),
    HierarchyLevel.MANAGEMENT: frozenset(
        {
            Permission.SCHEDULE_VIEW_AVAILABILITY,
            Permission.SCHEDULE_VIEW_DETAILS,
            Permission.SCHEDULE_ASSIGNMENT_WRITE,
            Permission.SCHEDULE_ASSIGNMENT_REQUEST,
            Permission.SCHEDULE_ASSIGNMENT_GRANT,
            Permission.USER_MANAGE,
            Permission.PERMISSION_MANAGE,
        }
    ),
}


def calculate_age(
    date_of_birth: date,
    *,
    as_of: date,
) -> int:
    """Calculate a user's age without persisting it."""

    age = as_of.year - date_of_birth.year

    if (as_of.month, as_of.day) < (
        date_of_birth.month,
        date_of_birth.day,
    ):
        age -= 1

    return age


def role_permissions(
    user: UserPrincipal,
) -> frozenset[Permission]:
    """Return permissions provided by the user's concrete role."""

    return _ROLE_PERMISSIONS[user.role]


def hierarchy_permissions(
    user: UserPrincipal,
) -> frozenset[Permission]:
    """Return permissions provided by the user's hierarchy level."""

    if user.hierarchy_level is None:
        return frozenset()

    return _HIERARCHY_PERMISSIONS[user.hierarchy_level]


def default_permissions(
    user: UserPrincipal,
) -> frozenset[Permission]:
    """Return role and hierarchy permissions before explicit grants."""

    return role_permissions(user) | hierarchy_permissions(user)


def _project_scope_matches(
    grant: PermissionGrant,
    resource: Resource,
) -> bool:
    """Return whether a project-scoped grant matches the resource."""

    return (
        grant.scope_type is ScopeType.PROJECT
        and resource.project_id is not None
        and grant.scope_id == str(resource.project_id)
    )


def _workspace_scope_matches(
    grant: PermissionGrant,
    resource: Resource,
) -> bool:
    """Return whether a workspace-scoped grant matches the resource."""

    return (
        grant.scope_type is ScopeType.WORKSPACE
        and resource.workspace is not None
        and grant.scope_id == resource.workspace.value
    )


def _user_scope_matches(
    grant: PermissionGrant,
    resource: Resource,
) -> bool:
    """Return whether a user-scoped grant matches the resource."""

    return (
        grant.scope_type is ScopeType.USER
        and resource.owner_user_id is not None
        and grant.scope_id == str(resource.owner_user_id)
    )


def _grant_matches(
    grant: PermissionGrant,
    *,
    principal_id: UUID,
    permission: Permission,
    resource: Resource,
) -> bool:
    """Return whether an explicit grant applies."""

    if not grant.active:
        return False

    if grant.principal_id != principal_id:
        return False

    if grant.permission is not permission:
        return False

    if grant.scope_type is ScopeType.GLOBAL:
        return grant.scope_id == "*"

    if _project_scope_matches(grant, resource):
        return True

    if _workspace_scope_matches(grant, resource):
        return True

    return _user_scope_matches(grant, resource)


def has_explicit_grant(
    principal_id: UUID,
    permission: Permission,
    resource: Resource,
    grants: tuple[PermissionGrant, ...],
) -> bool:
    """Return whether an explicit grant exists for the requested action."""

    return any(
        _grant_matches(
            grant,
            principal_id=principal_id,
            permission=permission,
            resource=resource,
        )
        for grant in grants
    )


def _customer_relationship_matches(
    user: UserPrincipal,
    resource: Resource,
    external_relationships: tuple[ExternalRelationship, ...],
) -> bool:
    """Return whether an external user has an applicable customer relation."""

    if user.user_type is not UserType.EXTERNAL:
        return False

    if resource.customer_id is None:
        return False

    return any(
        relationship.user_id == user.id
        and relationship.customer_id == resource.customer_id
        and relationship.active
        for relationship in external_relationships
    )


def _customer_project_access_matches(
    user: UserPrincipal,
    resource: Resource,
    customer_project_access: tuple[CustomerProjectAccess, ...],
) -> bool:
    """Return whether an external user has explicit project access."""

    if user.user_type is not UserType.EXTERNAL:
        return False

    if resource.project_id is None:
        return False

    return any(
        access.user_id == user.id
        and access.project_id == resource.project_id
        and access.active
        for access in customer_project_access
    )


def _internal_project_scope_matches(
    user: UserPrincipal,
    resource: Resource,
    assigned_project_ids: frozenset[UUID],
) -> bool:
    """Return whether an internal user is assigned to the project."""

    if resource.project_id is None:
        return True

    return resource.project_id in assigned_project_ids


def _customer_workspace_allowed(
    user: UserPrincipal,
    resource: Resource,
) -> bool:
    """Return whether an external customer may access this workspace."""

    if user.role is not ExternalRole.CUSTOMER:
        return False

    return resource.workspace is Workspace.CUSTOMER


def _document_signing_policy(
    user: UserPrincipal,
    *,
    as_of: date,
) -> bool:
    """Apply non-RBAC constraints for document signing."""

    if user.user_type is not UserType.INTERNAL:
        return False

    if user.date_of_birth is None:
        return False

    return (
        calculate_age(
            user.date_of_birth,
            as_of=as_of,
        )
        >= 18
    )


def _calendar_availability_allowed(
    user: UserPrincipal,
    resource: Resource,
    *,
    team_user_ids: frozenset[UUID],
) -> bool:
    """Limit senior calendar access to availability of their team."""

    if user.user_type is not UserType.INTERNAL:
        return False

    if user.hierarchy_level not in {
        HierarchyLevel.SENIOR,
        HierarchyLevel.SUPERVISOR,
        HierarchyLevel.MANAGEMENT,
    }:
        return False

    if resource.owner_user_id is None:
        return False

    if resource.owner_user_id == user.id:
        return True

    return resource.owner_user_id in team_user_ids


def authorize(
    principal: Principal,
    permission: Permission,
    resource: Resource,
    *,
    assigned_project_ids: frozenset[UUID] = frozenset(),
    team_user_ids: frozenset[UUID] = frozenset(),
    external_relationships: tuple[ExternalRelationship, ...] = (),
    customer_project_access: tuple[CustomerProjectAccess, ...] = (),
    grants: tuple[PermissionGrant, ...] = (),
    as_of: date,
) -> AuthorizationDecision:
    """Authorize one action against one resource.

    Evaluation order is intentionally conservative:

    1. identity must be active and structurally valid;
    2. relationship and scope restrictions are enforced;
    3. policy constraints are enforced;
    4. explicit grants are considered;
    5. role/hierarchy defaults are considered.

    Explicit grants can add permissions but cannot bypass mandatory security
    constraints such as project assignment, customer isolation, or age policy.

    Persistence is deliberately outside this function. Relationship data is
    supplied as domain-level inputs and may later be populated by repositories
    or persistence adapters.
    """

    if not principal.active:
        return AuthorizationDecision.DENY

    if isinstance(principal, FederationPeerPrincipal):
        return AuthorizationDecision.DENY

    if principal.user_type is UserType.INTERNAL:
        if not _internal_project_scope_matches(
            principal,
            resource,
            assigned_project_ids,
        ):
            return AuthorizationDecision.DENY

    elif principal.user_type is UserType.EXTERNAL:  # pragma: no branch
        if principal.role is ExternalRole.CUSTOMER:
            if not _customer_relationship_matches(
                principal,
                resource,
                external_relationships,
            ):
                return AuthorizationDecision.DENY

            if resource.project_id is not None:
                if not _customer_project_access_matches(
                    principal,
                    resource,
                    customer_project_access,
                ):
                    return AuthorizationDecision.DENY

            if not _customer_workspace_allowed(
                principal,
                resource,
            ):
                return AuthorizationDecision.DENY

    if permission is Permission.SCHEDULE_VIEW_AVAILABILITY:
        if not _calendar_availability_allowed(
            principal,
            resource,
            team_user_ids=team_user_ids,
        ):
            return AuthorizationDecision.DENY

    if permission is Permission.DOCUMENT_SIGN:
        if not _document_signing_policy(
            principal,
            as_of=as_of,
        ):
            return AuthorizationDecision.DENY

    if has_explicit_grant(
        principal.id,
        permission,
        resource,
        grants,
    ):
        return AuthorizationDecision.ALLOW

    if permission not in default_permissions(principal):
        return AuthorizationDecision.DENY

    if principal.role is ExternalRole.TAX_ADVISOR:
        return AuthorizationDecision.DENY

    return AuthorizationDecision.ALLOW
