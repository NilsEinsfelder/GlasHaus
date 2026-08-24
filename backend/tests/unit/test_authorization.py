from datetime import date
from uuid import UUID

import pytest
from app.security.authorization import (
    AuthorizationDecision,
    ExternalRole,
    FederationPeerPrincipal,
    HierarchyLevel,
    InternalRole,
    Permission,
    PermissionGrant,
    Resource,
    ScopeType,
    UserPrincipal,
    UserType,
    Workspace,
    authorize,
    calculate_age,
    default_permissions,
)

PROJECT_A = UUID("00000000-0000-0000-0000-000000000001")
PROJECT_B = UUID("00000000-0000-0000-0000-000000000002")

CUSTOMER_A = UUID("10000000-0000-0000-0000-000000000001")
CUSTOMER_B = UUID("10000000-0000-0000-0000-000000000002")

LEAD_ID = UUID("20000000-0000-0000-0000-000000000001")
TECHNICIAN_ID = UUID("20000000-0000-0000-0000-000000000002")
APPRENTICE_ID = UUID("20000000-0000-0000-0000-000000000003")
OFFICE_ID = UUID("20000000-0000-0000-0000-000000000004")

CUSTOMER_USER_ID = UUID("30000000-0000-0000-0000-000000000001")
TAX_ADVISOR_ID = UUID("30000000-0000-0000-0000-000000000002")
FEDERATION_PEER_ID = UUID("40000000-0000-0000-0000-000000000001")


def internal_user(
    *,
    user_id: UUID = TECHNICIAN_ID,
    role: InternalRole = InternalRole.TECHNICIAN,
    hierarchy: HierarchyLevel = HierarchyLevel.PROFESSIONAL,
    birth_date: date = date(1990, 1, 1),
) -> UserPrincipal:
    return UserPrincipal(
        id=user_id,
        user_type=UserType.INTERNAL,
        role=role,
        hierarchy_level=hierarchy,
        date_of_birth=birth_date,
    )


def customer_user() -> UserPrincipal:
    return UserPrincipal(
        id=CUSTOMER_USER_ID,
        user_type=UserType.EXTERNAL,
        role=ExternalRole.CUSTOMER,
        customer_id=CUSTOMER_A,
    )


def customer_project() -> Resource:
    return Resource(
        id=PROJECT_A,
        project_id=PROJECT_A,
        customer_id=CUSTOMER_A,
    )


def other_customer_project() -> Resource:
    return Resource(
        id=PROJECT_B,
        project_id=PROJECT_B,
        customer_id=CUSTOMER_B,
    )


def customer_workspace() -> Resource:
    return Resource(
        id=PROJECT_A,
        project_id=PROJECT_A,
        customer_id=CUSTOMER_A,
        workspace=Workspace.CUSTOMER,
    )


def internal_workspace() -> Resource:
    return Resource(
        id=PROJECT_A,
        project_id=PROJECT_A,
        customer_id=CUSTOMER_A,
        workspace=Workspace.INTERNAL,
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
                customer_id=CUSTOMER_A,
                hierarchy_level=HierarchyLevel.LEAD,
            )

    def test_customer_requires_customer_id(self) -> None:
        with pytest.raises(ValueError):
            UserPrincipal(
                id=CUSTOMER_USER_ID,
                user_type=UserType.EXTERNAL,
                role=ExternalRole.CUSTOMER,
            )

    def test_internal_user_cannot_have_customer_id(self) -> None:
        with pytest.raises(ValueError):
            UserPrincipal(
                id=TECHNICIAN_ID,
                user_type=UserType.INTERNAL,
                role=InternalRole.TECHNICIAN,
                hierarchy_level=HierarchyLevel.PROFESSIONAL,
                customer_id=CUSTOMER_A,
            )


class TestRoleAndHierarchy:
    def test_technician_role_has_technician_permissions(self) -> None:
        user = internal_user()

        permissions = default_permissions(user)

        assert Permission.PROJECT_READ in permissions
        assert Permission.PROJECT_ADDRESS_READ in permissions
        assert Permission.DOCUMENT_READ in permissions

    def test_office_role_does_not_inherit_technician_address_permission(
        self,
    ) -> None:
        user = internal_user(
            user_id=OFFICE_ID,
            role=InternalRole.OFFICE,
        )

        assert Permission.PROJECT_ADDRESS_READ not in default_permissions(user)

    def test_apprentice_has_no_professional_purchase_permission(self) -> None:
        user = internal_user(
            user_id=APPRENTICE_ID,
            hierarchy=HierarchyLevel.APPRENTICE,
        )

        assert Permission.PURCHASE_CREATE not in default_permissions(user)

    def test_professional_gets_purchase_permission(self) -> None:
        user = internal_user()

        assert Permission.PURCHASE_CREATE in default_permissions(user)

    def test_lead_gets_planning_permissions(self) -> None:
        user = internal_user(
            user_id=LEAD_ID,
            hierarchy=HierarchyLevel.LEAD,
        )

        permissions = default_permissions(user)

        assert Permission.CALENDAR_AVAILABILITY_READ in permissions
        assert Permission.CREW_ASSIGNMENT_REQUEST in permissions

    def test_hierarchy_does_not_replace_role(self) -> None:
        user = internal_user(
            user_id=OFFICE_ID,
            role=InternalRole.OFFICE,
            hierarchy=HierarchyLevel.LEAD,
        )

        permissions = default_permissions(user)

        assert Permission.PROJECT_READ in permissions
        assert Permission.CALENDAR_AVAILABILITY_READ in permissions
        assert Permission.PROJECT_ADDRESS_READ not in permissions


class TestInternalProjectScope:
    def test_internal_user_can_read_assigned_project(self) -> None:
        decision = authorize(
            internal_user(),
            Permission.PROJECT_READ,
            customer_project(),
            assigned_project_ids=frozenset({PROJECT_A}),
            as_of=date(2026, 8, 24),
        )

        assert decision is AuthorizationDecision.ALLOW

    def test_internal_user_cannot_read_unassigned_project(self) -> None:
        decision = authorize(
            internal_user(),
            Permission.PROJECT_READ,
            other_customer_project(),
            assigned_project_ids=frozenset({PROJECT_A}),
            as_of=date(2026, 8, 24),
        )

        assert decision is AuthorizationDecision.DENY

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
            as_of=date(2026, 8, 24),
        )

        assert decision is AuthorizationDecision.DENY


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
            as_of=date(2026, 8, 24),
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
            as_of=date(2026, 8, 24),
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
            as_of=date(2026, 8, 24),
        )

        assert decision is AuthorizationDecision.ALLOW

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
            as_of=date(2026, 8, 24),
        )

        assert decision is AuthorizationDecision.DENY


class TestCustomerWorkspace:
    def test_customer_can_read_own_project(self) -> None:
        decision = authorize(
            customer_user(),
            Permission.PROJECT_READ,
            customer_workspace(),
            as_of=date(2026, 8, 24),
        )

        assert decision is AuthorizationDecision.ALLOW

    def test_customer_cannot_access_other_customer_project(self) -> None:
        resource = Resource(
            id=PROJECT_B,
            project_id=PROJECT_B,
            customer_id=CUSTOMER_B,
            workspace=Workspace.CUSTOMER,
        )

        decision = authorize(
            customer_user(),
            Permission.PROJECT_READ,
            resource,
            as_of=date(2026, 8, 24),
        )

        assert decision is AuthorizationDecision.DENY

    def test_customer_can_create_customer_file(self) -> None:
        decision = authorize(
            customer_user(),
            Permission.CUSTOMER_FILE_CREATE,
            customer_workspace(),
            as_of=date(2026, 8, 24),
        )

        assert decision is AuthorizationDecision.ALLOW

    def test_customer_cannot_access_internal_workspace(self) -> None:
        decision = authorize(
            customer_user(),
            Permission.PROJECT_READ,
            internal_workspace(),
            as_of=date(2026, 8, 24),
        )

        assert decision is AuthorizationDecision.DENY


class TestCalendarVisibility:
    def test_lead_can_see_team_availability(self) -> None:
        user = internal_user(
            user_id=LEAD_ID,
            hierarchy=HierarchyLevel.LEAD,
        )

        resource = Resource(
            id=TECHNICIAN_ID,
            owner_user_id=TECHNICIAN_ID,
        )

        decision = authorize(
            user,
            Permission.CALENDAR_AVAILABILITY_READ,
            resource,
            team_user_ids=frozenset({TECHNICIAN_ID, APPRENTICE_ID}),
            as_of=date(2026, 8, 24),
        )

        assert decision is AuthorizationDecision.ALLOW

    def test_lead_can_see_apprentice_availability(self) -> None:
        user = internal_user(
            user_id=LEAD_ID,
            hierarchy=HierarchyLevel.LEAD,
        )

        resource = Resource(
            id=APPRENTICE_ID,
            owner_user_id=APPRENTICE_ID,
        )

        decision = authorize(
            user,
            Permission.CALENDAR_AVAILABILITY_READ,
            resource,
            team_user_ids=frozenset({TECHNICIAN_ID, APPRENTICE_ID}),
            as_of=date(2026, 8, 24),
        )

        assert decision is AuthorizationDecision.ALLOW

    def test_lead_cannot_see_unrelated_user_availability(self) -> None:
        user = internal_user(
            user_id=LEAD_ID,
            hierarchy=HierarchyLevel.LEAD,
        )

        resource = Resource(
            id=OFFICE_ID,
            owner_user_id=OFFICE_ID,
        )

        decision = authorize(
            user,
            Permission.CALENDAR_AVAILABILITY_READ,
            resource,
            team_user_ids=frozenset({TECHNICIAN_ID}),
            as_of=date(2026, 8, 24),
        )

        assert decision is AuthorizationDecision.DENY

    def test_lead_cannot_see_event_details(self) -> None:
        user = internal_user(
            user_id=LEAD_ID,
            hierarchy=HierarchyLevel.LEAD,
        )

        resource = Resource(
            id=TECHNICIAN_ID,
            owner_user_id=TECHNICIAN_ID,
        )

        decision = authorize(
            user,
            Permission.CALENDAR_EVENT_READ,
            resource,
            team_user_ids=frozenset({TECHNICIAN_ID}),
            as_of=date(2026, 8, 24),
        )

        assert decision is AuthorizationDecision.DENY

    def test_lead_cannot_see_event_location(self) -> None:
        user = internal_user(
            user_id=LEAD_ID,
            hierarchy=HierarchyLevel.LEAD,
        )

        resource = Resource(
            id=TECHNICIAN_ID,
            owner_user_id=TECHNICIAN_ID,
        )

        decision = authorize(
            user,
            Permission.CALENDAR_EVENT_LOCATION_READ,
            resource,
            team_user_ids=frozenset({TECHNICIAN_ID}),
            as_of=date(2026, 8, 24),
        )

        assert decision is AuthorizationDecision.DENY

    def test_lead_can_create_assignment_request(self) -> None:
        user = internal_user(
            user_id=LEAD_ID,
            hierarchy=HierarchyLevel.LEAD,
        )

        decision = authorize(
            user,
            Permission.CREW_ASSIGNMENT_REQUEST,
            customer_project(),
            assigned_project_ids=frozenset({PROJECT_A}),
            as_of=date(2026, 8, 24),
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
            as_of=date(2026, 8, 24),
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
            as_of=date(2026, 8, 24),
        )

        assert decision is AuthorizationDecision.DENY


class TestTaxAdvisor:
    def test_tax_advisor_requires_explicit_tax_desk_grant(self) -> None:
        user = UserPrincipal(
            id=TAX_ADVISOR_ID,
            user_type=UserType.EXTERNAL,
            role=ExternalRole.TAX_ADVISOR,
        )

        resource = Resource(
            id=TAX_ADVISOR_ID,
            workspace=Workspace.TAX_DESK,
        )

        grant = PermissionGrant(
            principal_id=TAX_ADVISOR_ID,
            permission=Permission.TAX_DESK_READ,
            scope_type=ScopeType.WORKSPACE,
            scope_id=Workspace.TAX_DESK.value,
        )

        decision = authorize(
            user,
            Permission.TAX_DESK_READ,
            resource,
            grants=(grant,),
            as_of=date(2026, 8, 24),
        )

        assert decision is AuthorizationDecision.ALLOW

    def test_tax_advisor_without_grant_is_denied(self) -> None:
        user = UserPrincipal(
            id=TAX_ADVISOR_ID,
            user_type=UserType.EXTERNAL,
            role=ExternalRole.TAX_ADVISOR,
        )

        resource = Resource(
            id=TAX_ADVISOR_ID,
            workspace=Workspace.TAX_DESK,
        )

        decision = authorize(
            user,
            Permission.TAX_DESK_READ,
            resource,
            as_of=date(2026, 8, 24),
        )

        assert decision is AuthorizationDecision.DENY


class TestFederation:
    def test_federation_peer_requires_explicit_project_grant(self) -> None:
        peer = FederationPeerPrincipal(
            id=FEDERATION_PEER_ID,
        )

        resource = customer_project()

        grant = PermissionGrant(
            principal_id=FEDERATION_PEER_ID,
            permission=Permission.FEDERATION_PROJECT_READ,
            scope_type=ScopeType.PROJECT,
            scope_id=str(PROJECT_A),
        )

        decision = authorize(
            peer,
            Permission.FEDERATION_PROJECT_READ,
            resource,
            grants=(grant,),
            as_of=date(2026, 8, 24),
        )

        assert decision is AuthorizationDecision.ALLOW

    def test_federation_peer_cannot_access_ungranted_project(self) -> None:
        peer = FederationPeerPrincipal(
            id=FEDERATION_PEER_ID,
        )

        resource = other_customer_project()

        grant = PermissionGrant(
            principal_id=FEDERATION_PEER_ID,
            permission=Permission.FEDERATION_PROJECT_READ,
            scope_type=ScopeType.PROJECT,
            scope_id=str(PROJECT_A),
        )

        decision = authorize(
            peer,
            Permission.FEDERATION_PROJECT_READ,
            resource,
            grants=(grant,),
            as_of=date(2026, 8, 24),
        )

        assert decision is AuthorizationDecision.DENY


class TestDefaultDeny:
    def test_unrelated_permission_is_denied(self) -> None:
        user = internal_user()

        resource = Resource(
            id=PROJECT_A,
            workspace=Workspace.TAX_DESK,
        )

        decision = authorize(
            user,
            Permission.TAX_DESK_READ,
            resource,
            as_of=date(2026, 8, 24),
        )

        assert decision is AuthorizationDecision.DENY

    def test_inactive_user_is_denied(self) -> None:
        user = UserPrincipal(
            id=TECHNICIAN_ID,
            user_type=UserType.INTERNAL,
            role=InternalRole.TECHNICIAN,
            hierarchy_level=HierarchyLevel.PROFESSIONAL,
            active=False,
        )

        decision = authorize(
            user,
            Permission.PROJECT_READ,
            customer_project(),
            assigned_project_ids=frozenset({PROJECT_A}),
            as_of=date(2026, 8, 24),
        )

        assert decision is AuthorizationDecision.DENY


class TestAuthorizationEdgeCases:
    def test_internal_user_with_invalid_role_is_rejected(self) -> None:
        with pytest.raises(ValueError):
            UserPrincipal(
                id=TECHNICIAN_ID,
                user_type=UserType.INTERNAL,
                role=ExternalRole.CUSTOMER,
                hierarchy_level=HierarchyLevel.PROFESSIONAL,
            )

    def test_external_user_with_invalid_role_is_rejected(self) -> None:
        with pytest.raises(ValueError):
            UserPrincipal(
                id=CUSTOMER_USER_ID,
                user_type=UserType.EXTERNAL,
                role=InternalRole.TECHNICIAN,
            )

    def test_external_customer_without_customer_id_is_rejected(self) -> None:
        with pytest.raises(ValueError):
            UserPrincipal(
                id=CUSTOMER_USER_ID,
                user_type=UserType.EXTERNAL,
                role=ExternalRole.CUSTOMER,
                customer_id=None,
            )

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
            as_of=date(2026, 8, 24),
        )

        assert decision is AuthorizationDecision.DENY

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
            as_of=date(2026, 8, 24),
        )

        assert decision is AuthorizationDecision.DENY

    def test_workspace_grant_requires_matching_workspace(self) -> None:
        user = UserPrincipal(
            id=TAX_ADVISOR_ID,
            user_type=UserType.EXTERNAL,
            role=ExternalRole.TAX_ADVISOR,
        )

        grant = PermissionGrant(
            principal_id=TAX_ADVISOR_ID,
            permission=Permission.TAX_DESK_READ,
            scope_type=ScopeType.WORKSPACE,
            scope_id=Workspace.TAX_DESK.value,
        )

        resource = Resource(
            id=TAX_ADVISOR_ID,
            workspace=Workspace.CUSTOMER,
        )

        decision = authorize(
            user,
            Permission.TAX_DESK_READ,
            resource,
            grants=(grant,),
            as_of=date(2026, 8, 24),
        )

        assert decision is AuthorizationDecision.DENY

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
            as_of=date(2026, 8, 24),
        )

        assert decision is AuthorizationDecision.DENY

    def test_customer_resource_without_project_is_denied(self) -> None:
        user = customer_user()

        resource = Resource(
            id=CUSTOMER_A,
            customer_id=CUSTOMER_A,
            workspace=Workspace.CUSTOMER,
        )

        decision = authorize(
            user,
            Permission.PROJECT_READ,
            resource,
            as_of=date(2026, 8, 24),
        )

        assert decision is AuthorizationDecision.DENY

    def test_lead_without_calendar_owner_is_denied(self) -> None:
        user = internal_user(
            user_id=LEAD_ID,
            hierarchy=HierarchyLevel.LEAD,
        )

        resource = Resource(id=PROJECT_A)

        decision = authorize(
            user,
            Permission.CALENDAR_AVAILABILITY_READ,
            resource,
            team_user_ids=frozenset({TECHNICIAN_ID}),
            as_of=date(2026, 8, 24),
        )

        assert decision is AuthorizationDecision.DENY

    def test_tax_desk_permission_requires_tax_desk_resource(self) -> None:
        user = UserPrincipal(
            id=TAX_ADVISOR_ID,
            user_type=UserType.EXTERNAL,
            role=ExternalRole.TAX_ADVISOR,
        )

        grant = PermissionGrant(
            principal_id=TAX_ADVISOR_ID,
            permission=Permission.TAX_DESK_READ,
            scope_type=ScopeType.GLOBAL,
            scope_id="*",
        )

        resource = Resource(
            id=TAX_ADVISOR_ID,
            workspace=Workspace.CUSTOMER,
        )

        decision = authorize(
            user,
            Permission.TAX_DESK_READ,
            resource,
            grants=(grant,),
            as_of=date(2026, 8, 24),
        )

        assert decision is AuthorizationDecision.DENY
