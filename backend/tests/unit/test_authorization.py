from datetime import date
from uuid import UUID

import pytest
from app.security.authorization import (
    AuthorizationDecision,
    CustomerProjectAccess,
    ExternalRelationship,
    ExternalRole,
    FederationPeerPrincipal,
    HierarchyLevel,
    InternalRole,
    Permission,
    PermissionGrant,
    Project,
    Resource,
    ScopeType,
    UserPrincipal,
    UserType,
    Workspace,
    _calendar_availability_allowed,
    _customer_project_access_matches,
    _customer_relationship_matches,
    _customer_workspace_allowed,
    _document_signing_policy,
    authorize,
    calculate_age,
    default_permissions,
    has_explicit_grant,
    hierarchy_permissions,
    role_permissions,
)

PROJECT_A = UUID("00000000-0000-0000-0000-000000000001")
PROJECT_B = UUID("00000000-0000-0000-0000-000000000002")

CUSTOMER_A = UUID("10000000-0000-0000-0000-000000000001")
CUSTOMER_B = UUID("10000000-0000-0000-0000-000000000002")

SENIOR_ID = UUID("20000000-0000-0000-0000-000000000001")
TECHNICIAN_ID = UUID("20000000-0000-0000-0000-000000000002")
APPRENTICE_ID = UUID("20000000-0000-0000-0000-000000000003")
OFFICE_ID = UUID("20000000-0000-0000-0000-000000000004")

CUSTOMER_USER_ID = UUID("30000000-0000-0000-0000-000000000001")
OTHER_USER_ID = UUID("30000000-0000-0000-0000-000000000099")

INTERNAL_WORKSPACE_ID = UUID("40000000-0000-0000-0000-000000000001")
CUSTOMER_WORKSPACE_ID = UUID("40000000-0000-0000-0000-000000000002")

AS_OF = date(2026, 8, 24)


def internal_user(
    *,
    user_id: UUID = TECHNICIAN_ID,
    role: InternalRole = InternalRole.TECHNICIAN,
    hierarchy: HierarchyLevel = HierarchyLevel.STANDARD,
    birth_date: date | None = date(1990, 1, 1),
    active: bool = True,
) -> UserPrincipal:
    return UserPrincipal(
        id=user_id,
        user_type=UserType.INTERNAL,
        role=role,
        hierarchy_level=hierarchy,
        date_of_birth=birth_date,
        active=active,
    )


def customer_user() -> UserPrincipal:
    return UserPrincipal(
        id=CUSTOMER_USER_ID,
        user_type=UserType.EXTERNAL,
        role=ExternalRole.CUSTOMER,
    )


def tax_advisor_user() -> UserPrincipal:
    return UserPrincipal(
        id=OTHER_USER_ID,
        user_type=UserType.EXTERNAL,
        role=ExternalRole.TAX_ADVISOR,
    )


def customer_relationship(
    *,
    user_id: UUID = CUSTOMER_USER_ID,
    customer_id: UUID = CUSTOMER_A,
    active: bool = True,
) -> ExternalRelationship:
    return ExternalRelationship(
        user_id=user_id,
        customer_id=customer_id,
        relationship_type="customer",
        active=active,
    )


def customer_project_access(
    *,
    project_id: UUID = PROJECT_A,
    user_id: UUID = CUSTOMER_USER_ID,
    active: bool = True,
) -> CustomerProjectAccess:
    return CustomerProjectAccess(
        user_id=user_id,
        project_id=project_id,
        active=active,
    )


def customer_project() -> Resource:
    return Resource(
        id=PROJECT_A,
        project_id=PROJECT_A,
        customer_id=CUSTOMER_A,
        workspace=Workspace.CUSTOMER,
    )


def internal_project() -> Resource:
    return Resource(
        id=PROJECT_A,
        project_id=PROJECT_A,
        customer_id=CUSTOMER_A,
        workspace=Workspace.INTERNAL,
    )


def other_customer_project() -> Resource:
    return Resource(
        id=PROJECT_B,
        project_id=PROJECT_B,
        customer_id=CUSTOMER_B,
        workspace=Workspace.CUSTOMER,
    )


class TestAge:
    def test_age_is_derived_from_birth_date(self) -> None:
        assert (
            calculate_age(
                date(2000, 8, 25),
                as_of=date(2026, 8, 24),
            )
            == 25
        )

    def test_age_changes_on_birthday(self) -> None:
        assert (
            calculate_age(
                date(2000, 8, 25),
                as_of=date(2026, 8, 25),
            )
            == 26
        )

    def test_user_does_not_store_age(self) -> None:
        user = internal_user()

        assert not hasattr(user, "age")


class TestUserInvariants:
    def test_internal_user_requires_hierarchy(self) -> None:
        with pytest.raises(ValueError):
            UserPrincipal(
                id=TECHNICIAN_ID,
                user_type=UserType.INTERNAL,
                role=InternalRole.TECHNICIAN,
            )

    def test_external_user_cannot_have_hierarchy(self) -> None:
        with pytest.raises(ValueError):
            UserPrincipal(
                id=CUSTOMER_USER_ID,
                user_type=UserType.EXTERNAL,
                role=ExternalRole.CUSTOMER,
                hierarchy_level=HierarchyLevel.SENIOR,
            )

    def test_internal_user_cannot_have_customer_relationship_on_principal(
        self,
    ) -> None:
        user = internal_user()

        assert not hasattr(user, "customer_id")

    def test_external_user_does_not_store_customer_id_on_principal(
        self,
    ) -> None:
        user = customer_user()

        assert not hasattr(user, "customer_id")

    def test_internal_user_rejects_external_role(self) -> None:
        with pytest.raises(ValueError):
            UserPrincipal(
                id=TECHNICIAN_ID,
                user_type=UserType.INTERNAL,
                role=ExternalRole.CUSTOMER,
                hierarchy_level=HierarchyLevel.STANDARD,
            )

    def test_external_user_rejects_internal_role(self) -> None:
        with pytest.raises(ValueError):
            UserPrincipal(
                id=CUSTOMER_USER_ID,
                user_type=UserType.EXTERNAL,
                role=InternalRole.TECHNICIAN,
            )

    def test_invalid_user_type_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="Unsupported user type"):
            UserPrincipal(
                id=TECHNICIAN_ID,
                user_type="invalid",  # type: ignore[arg-type]
                role=InternalRole.TECHNICIAN,
                hierarchy_level=HierarchyLevel.STANDARD,
            )


class TestProjectInvariants:
    def test_project_requires_distinct_workspaces(self) -> None:
        with pytest.raises(
            ValueError,
            match="distinct internal and customer workspaces",
        ):
            Project(
                id=PROJECT_A,
                customer_id=CUSTOMER_A,
                internal_workspace_id=INTERNAL_WORKSPACE_ID,
                customer_workspace_id=INTERNAL_WORKSPACE_ID,
            )

    def test_project_accepts_distinct_workspaces(self) -> None:
        project = Project(
            id=PROJECT_A,
            customer_id=CUSTOMER_A,
            internal_workspace_id=INTERNAL_WORKSPACE_ID,
            customer_workspace_id=CUSTOMER_WORKSPACE_ID,
        )

        assert project.id == PROJECT_A
        assert project.customer_id == CUSTOMER_A


class TestRoleAndHierarchy:
    def test_technician_role_has_project_and_document_read_permissions(
        self,
    ) -> None:
        user = internal_user()

        permissions = default_permissions(user)

        assert Permission.PROJECT_READ in permissions
        assert Permission.DOCUMENT_READ in permissions

    def test_office_role_does_not_inherit_technician_permissions(
        self,
    ) -> None:
        user = internal_user(
            user_id=OFFICE_ID,
            role=InternalRole.OFFICE,
        )

        permissions = default_permissions(user)

        assert Permission.PROJECT_READ in permissions
        assert Permission.DOCUMENT_READ in permissions

    def test_apprentice_has_no_default_purchase_permission(self) -> None:
        user = internal_user(
            user_id=APPRENTICE_ID,
            hierarchy=HierarchyLevel.APPRENTICE,
        )

        assert Permission.PURCHASE_CREATE not in default_permissions(user)

    def test_standard_has_default_purchase_permission(self) -> None:
        user = internal_user(
            hierarchy=HierarchyLevel.STANDARD,
        )

        assert Permission.PURCHASE_CREATE in default_permissions(user)

    def test_senior_has_schedule_permissions(self) -> None:
        user = internal_user(
            user_id=SENIOR_ID,
            hierarchy=HierarchyLevel.SENIOR,
        )

        permissions = default_permissions(user)

        assert Permission.SCHEDULE_VIEW_AVAILABILITY in permissions
        assert Permission.SCHEDULE_ASSIGNMENT_REQUEST in permissions

    def test_hierarchy_does_not_replace_role(self) -> None:
        user = internal_user(
            user_id=OFFICE_ID,
            role=InternalRole.OFFICE,
            hierarchy=HierarchyLevel.SENIOR,
        )

        permissions = default_permissions(user)

        assert Permission.PROJECT_READ in permissions
        assert Permission.DOCUMENT_READ in permissions

    def test_role_permissions_for_tax_advisor_are_empty(self) -> None:
        user = tax_advisor_user()

        assert role_permissions(user) == frozenset()

    def test_hierarchy_permissions_for_external_user_are_empty(self) -> None:
        user = customer_user()

        assert hierarchy_permissions(user) == frozenset()

    def test_hierarchy_permissions_without_hierarchy_are_empty(self) -> None:
        user = object.__new__(UserPrincipal)

        object.__setattr__(user, "id", TECHNICIAN_ID)
        object.__setattr__(user, "user_type", UserType.INTERNAL)
        object.__setattr__(user, "role", InternalRole.TECHNICIAN)
        object.__setattr__(user, "hierarchy_level", None)
        object.__setattr__(user, "date_of_birth", None)
        object.__setattr__(user, "active", True)

        assert hierarchy_permissions(user) == frozenset()


class TestInternalProjectScope:
    def test_internal_user_can_read_assigned_project(self) -> None:
        decision = authorize(
            internal_user(),
            Permission.PROJECT_READ,
            customer_project(),
            assigned_project_ids=frozenset({PROJECT_A}),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.ALLOW

    def test_internal_user_cannot_read_unassigned_project(self) -> None:
        decision = authorize(
            internal_user(),
            Permission.PROJECT_READ,
            other_customer_project(),
            assigned_project_ids=frozenset({PROJECT_A}),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.DENY

    def test_internal_user_can_access_resource_without_project(self) -> None:
        decision = authorize(
            internal_user(),
            Permission.PROJECT_READ,
            Resource(id=PROJECT_A),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.ALLOW

    def test_explicit_grant_does_not_bypass_project_assignment(self) -> None:
        grant = PermissionGrant(
            principal_id=TECHNICIAN_ID,
            permission=Permission.PURCHASE_CREATE,
            scope_type=ScopeType.PROJECT,
            scope_id=str(PROJECT_B),
        )

        decision = authorize(
            internal_user(),
            Permission.PURCHASE_CREATE,
            other_customer_project(),
            assigned_project_ids=frozenset({PROJECT_A}),
            grants=(grant,),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.DENY


class TestExternalCustomerScope:
    def test_customer_can_read_project_of_related_customer(self) -> None:
        decision = authorize(
            customer_user(),
            Permission.PROJECT_READ,
            customer_project(),
            external_relationships=(customer_relationship(),),
            customer_project_access=(customer_project_access(),),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.ALLOW

    def test_customer_cannot_read_project_of_unrelated_customer(self) -> None:
        decision = authorize(
            customer_user(),
            Permission.PROJECT_READ,
            other_customer_project(),
            external_relationships=(customer_relationship(),),
            customer_project_access=(
                CustomerProjectAccess(
                    user_id=CUSTOMER_USER_ID,
                    project_id=PROJECT_B,
                ),
            ),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.DENY

    def test_customer_cannot_read_project_without_project_access(
        self,
    ) -> None:
        decision = authorize(
            customer_user(),
            Permission.PROJECT_READ,
            customer_project(),
            external_relationships=(customer_relationship(),),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.DENY

    def test_customer_cannot_read_project_without_customer_relationship(
        self,
    ) -> None:
        decision = authorize(
            customer_user(),
            Permission.PROJECT_READ,
            customer_project(),
            customer_project_access=(customer_project_access(),),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.DENY

    def test_customer_project_access_for_different_user_is_ignored(
        self,
    ) -> None:
        decision = authorize(
            customer_user(),
            Permission.PROJECT_READ,
            customer_project(),
            external_relationships=(customer_relationship(),),
            customer_project_access=(
                CustomerProjectAccess(
                    user_id=OTHER_USER_ID,
                    project_id=PROJECT_A,
                ),
            ),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.DENY

    def test_inactive_customer_relationship_is_ignored(self) -> None:
        decision = authorize(
            customer_user(),
            Permission.PROJECT_READ,
            customer_project(),
            external_relationships=(customer_relationship(active=False),),
            customer_project_access=(customer_project_access(),),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.DENY

    def test_inactive_customer_project_access_is_ignored(self) -> None:
        decision = authorize(
            customer_user(),
            Permission.PROJECT_READ,
            customer_project(),
            external_relationships=(customer_relationship(),),
            customer_project_access=(customer_project_access(active=False),),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.DENY

    def test_customer_cannot_access_internal_workspace(self) -> None:
        decision = authorize(
            customer_user(),
            Permission.PROJECT_READ,
            internal_project(),
            external_relationships=(customer_relationship(),),
            customer_project_access=(customer_project_access(),),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.DENY

    def test_customer_can_access_non_project_customer_resource(self) -> None:
        resource = Resource(
            id=CUSTOMER_A,
            customer_id=CUSTOMER_A,
            workspace=Workspace.CUSTOMER,
        )

        decision = authorize(
            customer_user(),
            Permission.CUSTOMER_READ,
            resource,
            external_relationships=(customer_relationship(),),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.ALLOW


class TestExplicitGrants:
    def test_project_grant_can_add_permission(self) -> None:
        user = internal_user(
            user_id=APPRENTICE_ID,
            hierarchy=HierarchyLevel.APPRENTICE,
        )

        grant = PermissionGrant(
            principal_id=APPRENTICE_ID,
            permission=Permission.PURCHASE_CREATE,
            scope_type=ScopeType.PROJECT,
            scope_id=str(PROJECT_A),
        )

        decision = authorize(
            user,
            Permission.PURCHASE_CREATE,
            customer_project(),
            assigned_project_ids=frozenset({PROJECT_A}),
            grants=(grant,),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.ALLOW

    def test_project_grant_does_not_apply_to_other_project(self) -> None:
        user = internal_user(
            user_id=APPRENTICE_ID,
            hierarchy=HierarchyLevel.APPRENTICE,
        )

        grant = PermissionGrant(
            principal_id=APPRENTICE_ID,
            permission=Permission.PURCHASE_CREATE,
            scope_type=ScopeType.PROJECT,
            scope_id=str(PROJECT_A),
        )

        decision = authorize(
            user,
            Permission.PURCHASE_CREATE,
            other_customer_project(),
            assigned_project_ids=frozenset({PROJECT_A, PROJECT_B}),
            grants=(grant,),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.DENY

    def test_global_grant_applies_globally(self) -> None:
        user = internal_user(
            user_id=APPRENTICE_ID,
            hierarchy=HierarchyLevel.APPRENTICE,
        )

        grant = PermissionGrant(
            principal_id=APPRENTICE_ID,
            permission=Permission.PURCHASE_CREATE,
            scope_type=ScopeType.GLOBAL,
            scope_id="*",
        )

        decision = authorize(
            user,
            Permission.PURCHASE_CREATE,
            customer_project(),
            assigned_project_ids=frozenset({PROJECT_A}),
            grants=(grant,),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.ALLOW

    def test_global_grant_with_wrong_scope_id_does_not_apply(self) -> None:

        grant = PermissionGrant(
            principal_id=APPRENTICE_ID,
            permission=Permission.PURCHASE_CREATE,
            scope_type=ScopeType.GLOBAL,
            scope_id="not-global",
        )

        assert not has_explicit_grant(
            APPRENTICE_ID,
            Permission.PURCHASE_CREATE,
            customer_project(),
            (grant,),
        )

    def test_inactive_grant_is_ignored(self) -> None:
        user = internal_user(
            user_id=APPRENTICE_ID,
            hierarchy=HierarchyLevel.APPRENTICE,
        )

        grant = PermissionGrant(
            principal_id=APPRENTICE_ID,
            permission=Permission.PURCHASE_CREATE,
            scope_type=ScopeType.PROJECT,
            scope_id=str(PROJECT_A),
            active=False,
        )

        decision = authorize(
            user,
            Permission.PURCHASE_CREATE,
            customer_project(),
            assigned_project_ids=frozenset({PROJECT_A}),
            grants=(grant,),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.DENY

    def test_grant_for_different_principal_is_ignored(self) -> None:
        grant = PermissionGrant(
            principal_id=OTHER_USER_ID,
            permission=Permission.PURCHASE_CREATE,
            scope_type=ScopeType.GLOBAL,
            scope_id="*",
        )

        assert not has_explicit_grant(
            APPRENTICE_ID,
            Permission.PURCHASE_CREATE,
            customer_project(),
            (grant,),
        )

    def test_grant_for_different_permission_is_ignored(self) -> None:
        grant = PermissionGrant(
            principal_id=APPRENTICE_ID,
            permission=Permission.PROJECT_READ,
            scope_type=ScopeType.GLOBAL,
            scope_id="*",
        )

        assert not has_explicit_grant(
            APPRENTICE_ID,
            Permission.PURCHASE_CREATE,
            customer_project(),
            (grant,),
        )

    def test_user_scope_grant_requires_matching_owner(self) -> None:
        user = internal_user(
            user_id=APPRENTICE_ID,
            hierarchy=HierarchyLevel.APPRENTICE,
        )

        grant = PermissionGrant(
            principal_id=APPRENTICE_ID,
            permission=Permission.PURCHASE_CREATE,
            scope_type=ScopeType.USER,
            scope_id=str(APPRENTICE_ID),
        )

        resource = Resource(
            id=TECHNICIAN_ID,
            owner_user_id=TECHNICIAN_ID,
        )

        decision = authorize(
            user,
            Permission.PURCHASE_CREATE,
            resource,
            grants=(grant,),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.DENY

    def test_user_scope_grant_applies_to_matching_owner(self) -> None:
        user = internal_user(
            user_id=APPRENTICE_ID,
            hierarchy=HierarchyLevel.APPRENTICE,
        )

        grant = PermissionGrant(
            principal_id=APPRENTICE_ID,
            permission=Permission.PURCHASE_CREATE,
            scope_type=ScopeType.USER,
            scope_id=str(APPRENTICE_ID),
        )

        resource = Resource(
            id=APPRENTICE_ID,
            owner_user_id=APPRENTICE_ID,
        )

        decision = authorize(
            user,
            Permission.PURCHASE_CREATE,
            resource,
            grants=(grant,),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.ALLOW

    def test_workspace_grant_applies_to_matching_workspace(self) -> None:
        user = internal_user(
            user_id=APPRENTICE_ID,
            hierarchy=HierarchyLevel.APPRENTICE,
        )

        grant = PermissionGrant(
            principal_id=APPRENTICE_ID,
            permission=Permission.PURCHASE_CREATE,
            scope_type=ScopeType.WORKSPACE,
            scope_id=Workspace.INTERNAL.value,
        )

        resource = Resource(
            id=PROJECT_A,
            workspace=Workspace.INTERNAL,
        )

        decision = authorize(
            user,
            Permission.PURCHASE_CREATE,
            resource,
            grants=(grant,),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.ALLOW

    def test_workspace_grant_does_not_apply_to_other_workspace(self) -> None:
        user = internal_user(
            user_id=APPRENTICE_ID,
            hierarchy=HierarchyLevel.APPRENTICE,
        )

        grant = PermissionGrant(
            principal_id=APPRENTICE_ID,
            permission=Permission.PURCHASE_CREATE,
            scope_type=ScopeType.WORKSPACE,
            scope_id=Workspace.INTERNAL.value,
        )

        resource = Resource(
            id=PROJECT_A,
            workspace=Workspace.CUSTOMER,
        )

        decision = authorize(
            user,
            Permission.PURCHASE_CREATE,
            resource,
            grants=(grant,),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.DENY

    def test_workspace_grant_requires_workspace_resource(self) -> None:

        grant = PermissionGrant(
            principal_id=APPRENTICE_ID,
            permission=Permission.PURCHASE_CREATE,
            scope_type=ScopeType.WORKSPACE,
            scope_id=Workspace.INTERNAL.value,
        )

        resource = Resource(id=PROJECT_A)

        assert not has_explicit_grant(
            APPRENTICE_ID,
            Permission.PURCHASE_CREATE,
            resource,
            (grant,),
        )

    def test_project_grant_requires_project_resource(self) -> None:
        user = internal_user(
            user_id=APPRENTICE_ID,
            hierarchy=HierarchyLevel.APPRENTICE,
        )

        grant = PermissionGrant(
            principal_id=APPRENTICE_ID,
            permission=Permission.PURCHASE_CREATE,
            scope_type=ScopeType.PROJECT,
            scope_id=str(PROJECT_A),
        )

        resource = Resource(id=PROJECT_A)

        decision = authorize(
            user,
            Permission.PURCHASE_CREATE,
            resource,
            grants=(grant,),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.DENY

    def test_inactive_grant_is_not_authorized(self) -> None:
        user = internal_user(
            user_id=APPRENTICE_ID,
            hierarchy=HierarchyLevel.APPRENTICE,
        )

        grant = PermissionGrant(
            principal_id=APPRENTICE_ID,
            permission=Permission.PURCHASE_CREATE,
            scope_type=ScopeType.GLOBAL,
            scope_id="*",
            active=False,
        )

        decision = authorize(
            user,
            Permission.PURCHASE_CREATE,
            customer_project(),
            assigned_project_ids=frozenset({PROJECT_A}),
            grants=(grant,),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.DENY


class TestScheduleAuthorization:
    def test_senior_can_view_team_availability(self) -> None:
        user = internal_user(
            user_id=SENIOR_ID,
            hierarchy=HierarchyLevel.SENIOR,
        )

        resource = Resource(
            id=TECHNICIAN_ID,
            owner_user_id=TECHNICIAN_ID,
        )

        decision = authorize(
            user,
            Permission.SCHEDULE_VIEW_AVAILABILITY,
            resource,
            team_user_ids=frozenset(
                {
                    TECHNICIAN_ID,
                    APPRENTICE_ID,
                }
            ),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.ALLOW

    def test_senior_can_view_apprentice_availability(self) -> None:
        user = internal_user(
            user_id=SENIOR_ID,
            hierarchy=HierarchyLevel.SENIOR,
        )

        resource = Resource(
            id=APPRENTICE_ID,
            owner_user_id=APPRENTICE_ID,
        )

        decision = authorize(
            user,
            Permission.SCHEDULE_VIEW_AVAILABILITY,
            resource,
            team_user_ids=frozenset(
                {
                    TECHNICIAN_ID,
                    APPRENTICE_ID,
                }
            ),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.ALLOW

    def test_senior_can_view_own_availability(self) -> None:
        user = internal_user(
            user_id=SENIOR_ID,
            hierarchy=HierarchyLevel.SENIOR,
        )

        resource = Resource(
            id=SENIOR_ID,
            owner_user_id=SENIOR_ID,
        )

        decision = authorize(
            user,
            Permission.SCHEDULE_VIEW_AVAILABILITY,
            resource,
            team_user_ids=frozenset(),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.ALLOW

    def test_senior_cannot_view_unrelated_user_availability(self) -> None:
        user = internal_user(
            user_id=SENIOR_ID,
            hierarchy=HierarchyLevel.SENIOR,
        )

        resource = Resource(
            id=OFFICE_ID,
            owner_user_id=OFFICE_ID,
        )

        decision = authorize(
            user,
            Permission.SCHEDULE_VIEW_AVAILABILITY,
            resource,
            team_user_ids=frozenset({TECHNICIAN_ID}),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.DENY

    def test_senior_without_calendar_owner_is_denied(self) -> None:
        user = internal_user(
            user_id=SENIOR_ID,
            hierarchy=HierarchyLevel.SENIOR,
        )

        resource = Resource(id=PROJECT_A)

        decision = authorize(
            user,
            Permission.SCHEDULE_VIEW_AVAILABILITY,
            resource,
            team_user_ids=frozenset({TECHNICIAN_ID}),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.DENY

    def test_junior_cannot_view_calendar_availability(self) -> None:
        user = internal_user(
            user_id=TECHNICIAN_ID,
            hierarchy=HierarchyLevel.JUNIOR,
        )

        resource = Resource(
            id=TECHNICIAN_ID,
            owner_user_id=TECHNICIAN_ID,
        )

        decision = authorize(
            user,
            Permission.SCHEDULE_VIEW_AVAILABILITY,
            resource,
            team_user_ids=frozenset({TECHNICIAN_ID}),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.DENY

    def test_external_user_cannot_view_calendar_availability(self) -> None:
        resource = Resource(
            id=CUSTOMER_USER_ID,
            owner_user_id=CUSTOMER_USER_ID,
        )

        decision = authorize(
            customer_user(),
            Permission.SCHEDULE_VIEW_AVAILABILITY,
            resource,
            team_user_ids=frozenset({CUSTOMER_USER_ID}),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.DENY

    def test_senior_can_request_assignment(self) -> None:
        user = internal_user(
            user_id=SENIOR_ID,
            hierarchy=HierarchyLevel.SENIOR,
        )

        decision = authorize(
            user,
            Permission.SCHEDULE_ASSIGNMENT_REQUEST,
            customer_project(),
            assigned_project_ids=frozenset({PROJECT_A}),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.ALLOW


class TestDocumentSigningPolicy:
    def test_minor_cannot_sign_even_with_explicit_grant(self) -> None:
        user = internal_user(
            user_id=APPRENTICE_ID,
            hierarchy=HierarchyLevel.APPRENTICE,
            birth_date=date(2008, 8, 25),
        )

        grant = PermissionGrant(
            principal_id=APPRENTICE_ID,
            permission=Permission.DOCUMENT_SIGN,
            scope_type=ScopeType.PROJECT,
            scope_id=str(PROJECT_A),
        )

        decision = authorize(
            user,
            Permission.DOCUMENT_SIGN,
            customer_project(),
            assigned_project_ids=frozenset({PROJECT_A}),
            grants=(grant,),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.DENY

    def test_user_can_sign_after_eighteenth_birthday_with_grant(self) -> None:
        user = internal_user(
            user_id=TECHNICIAN_ID,
            birth_date=date(2008, 8, 25),
        )

        grant = PermissionGrant(
            principal_id=TECHNICIAN_ID,
            permission=Permission.DOCUMENT_SIGN,
            scope_type=ScopeType.PROJECT,
            scope_id=str(PROJECT_A),
        )

        before_birthday = authorize(
            user,
            Permission.DOCUMENT_SIGN,
            customer_project(),
            assigned_project_ids=frozenset({PROJECT_A}),
            grants=(grant,),
            as_of=date(2026, 8, 24),
        )

        on_birthday = authorize(
            user,
            Permission.DOCUMENT_SIGN,
            customer_project(),
            assigned_project_ids=frozenset({PROJECT_A}),
            grants=(grant,),
            as_of=date(2026, 8, 25),
        )

        assert before_birthday is AuthorizationDecision.DENY
        assert on_birthday is AuthorizationDecision.ALLOW

    def test_adult_without_signing_grant_is_denied(self) -> None:
        user = internal_user(
            birth_date=date(1990, 1, 1),
        )

        decision = authorize(
            user,
            Permission.DOCUMENT_SIGN,
            customer_project(),
            assigned_project_ids=frozenset({PROJECT_A}),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.DENY

    def test_internal_user_without_birth_date_cannot_sign(self) -> None:
        user = internal_user(
            birth_date=None,
        )

        grant = PermissionGrant(
            principal_id=TECHNICIAN_ID,
            permission=Permission.DOCUMENT_SIGN,
            scope_type=ScopeType.PROJECT,
            scope_id=str(PROJECT_A),
        )

        decision = authorize(
            user,
            Permission.DOCUMENT_SIGN,
            customer_project(),
            assigned_project_ids=frozenset({PROJECT_A}),
            grants=(grant,),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.DENY

    def test_external_user_cannot_sign(self) -> None:
        grant = PermissionGrant(
            principal_id=CUSTOMER_USER_ID,
            permission=Permission.DOCUMENT_SIGN,
            scope_type=ScopeType.GLOBAL,
            scope_id="*",
        )

        decision = authorize(
            customer_user(),
            Permission.DOCUMENT_SIGN,
            customer_project(),
            external_relationships=(customer_relationship(),),
            customer_project_access=(customer_project_access(),),
            grants=(grant,),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.DENY


class TestTaxAdvisorAuthorization:
    def test_tax_advisor_has_no_default_permissions(self) -> None:
        user = tax_advisor_user()

        assert default_permissions(user) == frozenset()

    def test_tax_advisor_is_denied_without_grant(self) -> None:
        decision = authorize(
            tax_advisor_user(),
            Permission.PROJECT_READ,
            Resource(id=PROJECT_A),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.DENY

    def test_tax_advisor_cannot_use_grant_for_different_principal(
        self,
    ) -> None:
        user = UserPrincipal(
            id=CUSTOMER_USER_ID,
            user_type=UserType.EXTERNAL,
            role=ExternalRole.TAX_ADVISOR,
        )

        grant = PermissionGrant(
            principal_id=OTHER_USER_ID,
            permission=Permission.PURCHASE_CREATE,
            scope_type=ScopeType.GLOBAL,
            scope_id="*",
        )

        decision = authorize(
            user,
            Permission.PURCHASE_CREATE,
            Resource(id=PROJECT_A),
            grants=(grant,),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.DENY

    def test_tax_advisor_cannot_use_customer_workspace_access(self) -> None:
        user = tax_advisor_user()

        resource = Resource(
            id=PROJECT_A,
            project_id=PROJECT_A,
            customer_id=CUSTOMER_A,
            workspace=Workspace.CUSTOMER,
        )

        decision = authorize(
            user,
            Permission.PROJECT_READ,
            resource,
            external_relationships=(
                ExternalRelationship(
                    user_id=OTHER_USER_ID,
                    customer_id=CUSTOMER_A,
                    relationship_type="tax_advisor",
                ),
            ),
            customer_project_access=(
                CustomerProjectAccess(
                    user_id=OTHER_USER_ID,
                    project_id=PROJECT_A,
                ),
            ),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.DENY


class TestFederationAuthorization:
    def test_active_federation_peer_is_denied(self) -> None:
        peer = FederationPeerPrincipal(
            id=UUID("50000000-0000-0000-0000-000000000001"),
        )

        decision = authorize(
            peer,
            Permission.PROJECT_READ,
            Resource(id=PROJECT_A),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.DENY

    def test_inactive_federation_peer_is_denied(self) -> None:
        peer = FederationPeerPrincipal(
            id=UUID("50000000-0000-0000-0000-000000000001"),
            active=False,
        )

        decision = authorize(
            peer,
            Permission.PROJECT_READ,
            Resource(id=PROJECT_A),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.DENY


class TestDefaultDeny:
    def test_unrelated_permission_is_denied(self) -> None:
        user = internal_user()

        resource = Resource(id=PROJECT_A)

        decision = authorize(
            user,
            Permission.DOCUMENT_SIGN,
            resource,
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.DENY

    def test_inactive_user_is_denied(self) -> None:
        user = internal_user(
            active=False,
        )

        decision = authorize(
            user,
            Permission.PROJECT_READ,
            customer_project(),
            assigned_project_ids=frozenset({PROJECT_A}),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.DENY

    def test_permission_not_in_defaults_is_denied(self) -> None:
        user = internal_user(
            hierarchy=HierarchyLevel.APPRENTICE,
        )

        decision = authorize(
            user,
            Permission.USER_MANAGE,
            Resource(id=PROJECT_A),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.DENY


class TestAuthorizationEdgeCases:
    def test_project_grant_requires_project_resource(self) -> None:
        user = internal_user(
            user_id=APPRENTICE_ID,
            hierarchy=HierarchyLevel.APPRENTICE,
        )

        grant = PermissionGrant(
            principal_id=APPRENTICE_ID,
            permission=Permission.PURCHASE_CREATE,
            scope_type=ScopeType.PROJECT,
            scope_id=str(PROJECT_A),
        )

        resource = Resource(id=PROJECT_A)

        decision = authorize(
            user,
            Permission.PURCHASE_CREATE,
            resource,
            grants=(grant,),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.DENY

    def test_inactive_grant_is_not_authorized(self) -> None:
        user = internal_user(
            user_id=APPRENTICE_ID,
            hierarchy=HierarchyLevel.APPRENTICE,
        )

        grant = PermissionGrant(
            principal_id=APPRENTICE_ID,
            permission=Permission.PURCHASE_CREATE,
            scope_type=ScopeType.GLOBAL,
            scope_id="*",
            active=False,
        )

        decision = authorize(
            user,
            Permission.PURCHASE_CREATE,
            customer_project(),
            assigned_project_ids=frozenset({PROJECT_A}),
            grants=(grant,),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.DENY

    def test_lead_without_calendar_owner_is_denied(self) -> None:
        user = internal_user(
            user_id=SENIOR_ID,
            hierarchy=HierarchyLevel.SENIOR,
        )

        resource = Resource(id=PROJECT_A)

        decision = authorize(
            user,
            Permission.SCHEDULE_VIEW_AVAILABILITY,
            resource,
            team_user_ids=frozenset({TECHNICIAN_ID}),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.DENY

    def test_explicit_grant_cannot_bypass_calendar_policy(self) -> None:
        user = internal_user(
            user_id=SENIOR_ID,
            hierarchy=HierarchyLevel.SENIOR,
        )

        grant = PermissionGrant(
            principal_id=SENIOR_ID,
            permission=Permission.SCHEDULE_VIEW_AVAILABILITY,
            scope_type=ScopeType.GLOBAL,
            scope_id="*",
        )

        resource = Resource(
            id=OTHER_USER_ID,
            owner_user_id=OTHER_USER_ID,
        )

        decision = authorize(
            user,
            Permission.SCHEDULE_VIEW_AVAILABILITY,
            resource,
            team_user_ids=frozenset(),
            grants=(grant,),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.DENY


class TestAuthorizationRemainingBranches:
    """Cover the remaining defensive and policy branches."""

    def test_customer_relationship_match_rejects_internal_user(self) -> None:
        user = internal_user()

        result = _customer_relationship_matches(
            user,
            customer_project(),
            (customer_relationship(),),
        )

        assert result is False

    def test_customer_project_access_match_rejects_internal_user(
        self,
    ) -> None:
        user = internal_user()

        result = _customer_project_access_matches(
            user,
            customer_project(),
            (customer_project_access(),),
        )

        assert result is False

    def test_customer_project_access_match_rejects_resource_without_project(
        self,
    ) -> None:
        user = customer_user()

        resource = Resource(
            id=PROJECT_A,
            customer_id=CUSTOMER_A,
            workspace=Workspace.CUSTOMER,
        )

        result = _customer_project_access_matches(
            user,
            resource,
            (customer_project_access(),),
        )

        assert result is False

    def test_customer_workspace_rejects_tax_advisor(self) -> None:
        user = UserPrincipal(
            id=CUSTOMER_USER_ID,
            user_type=UserType.EXTERNAL,
            role=ExternalRole.TAX_ADVISOR,
        )

        result = _customer_workspace_allowed(
            user,
            customer_project(),
        )

        assert result is False

    def test_document_signing_rejects_external_user(self) -> None:
        user = customer_user()

        result = _document_signing_policy(
            user,
            as_of=AS_OF,
        )

        assert result is False

    def test_calendar_availability_rejects_external_user(self) -> None:
        user = customer_user()

        resource = Resource(
            id=TECHNICIAN_ID,
            owner_user_id=TECHNICIAN_ID,
        )

        result = _calendar_availability_allowed(
            user,
            resource,
            team_user_ids=frozenset({TECHNICIAN_ID}),
        )

        assert result is False

    def test_tax_advisor_reaches_external_authorization_path(
        self,
    ) -> None:
        user = UserPrincipal(
            id=CUSTOMER_USER_ID,
            user_type=UserType.EXTERNAL,
            role=ExternalRole.TAX_ADVISOR,
        )

        decision = authorize(
            user,
            Permission.PURCHASE_CREATE,
            Resource(id=PROJECT_A),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.DENY

    def test_tax_advisor_is_denied_after_default_permission_check(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        user = UserPrincipal(
            id=CUSTOMER_USER_ID,
            user_type=UserType.EXTERNAL,
            role=ExternalRole.TAX_ADVISOR,
        )

        monkeypatch.setattr(
            "app.security.authorization.default_permissions",
            lambda _: frozenset({Permission.PROJECT_READ}),
        )

        decision = authorize(
            user,
            Permission.PROJECT_READ,
            Resource(id=PROJECT_A),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.DENY

    def test_external_non_customer_reaches_permission_policy(self) -> None:
        user = UserPrincipal(
            id=OTHER_USER_ID,
            user_type=UserType.EXTERNAL,
            role=ExternalRole.TAX_ADVISOR,
        )

        decision = authorize(
            user,
            Permission.PROJECT_READ,
            Resource(id=PROJECT_A),
            grants=(
                PermissionGrant(
                    principal_id=OTHER_USER_ID,
                    permission=Permission.PROJECT_READ,
                    scope_type=ScopeType.GLOBAL,
                    scope_id="*",
                ),
            ),
            as_of=AS_OF,
        )

        assert decision is AuthorizationDecision.ALLOW
