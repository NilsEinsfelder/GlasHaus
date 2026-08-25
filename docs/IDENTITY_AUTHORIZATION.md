# GlasHaus Identity & Authorization Model

## 1. Purpose

This document defines the target identity and authorization architecture of GlasHaus.

It specifies:

- user identity
- user types
- business relationships
- roles
- employment hierarchy
- permissions
- permission grants and restrictions
- resource scopes
- workspace boundaries
- project assignment
- external user access
- authorization evaluation
- permission delegation
- temporary permissions
- separation of duties
- auditability
- future federation
- authorization invariants

This document defines the **approved target model**.

It is not an implementation-status document. The current implementation may temporarily differ from this model. Such differences must be resolved explicitly rather than silently becoming part of the architecture.

GlasHaus is designed as a self-hosted application operated by one organization per server.

Authorization is always enforced server-side.

---

## 2. Core Principles

GlasHaus follows these principles:

1. Every request must have an authenticated security context before protected authorization is evaluated.
2. Authorization is evaluated server-side.
3. Authorization is default-deny.
4. A user never receives access merely because they know a resource identifier.
5. Role defaults do not imply unrestricted access.
6. Individual grants and restrictions may refine baseline permissions only within mandatory policy boundaries.
7. Permissions and resource scopes are evaluated separately.
8. Workspace boundaries are security boundaries.
9. Internal and external access are explicitly separated.
10. Project access is an explicit authorization boundary.
11. There is no emergency or convenience bypass for unassigned projects.
12. Authorization decisions must be deterministic and testable.
13. Security-sensitive authorization changes must be auditable where required.
14. Permission delegation is itself an authorized action.
15. Mandatory security policies cannot be overridden by configurable grants.
16. Sensitive data must be minimized at the response boundary.
17. Future external relationships must not require redefining the core `User` model.
18. Future federation must preserve independent trust domains.

---

## 3. Server as Organizational Boundary

A normal GlasHaus installation represents one organization's local system.

The server itself is therefore the primary organizational boundary.

A local multi-tenant `organization_id` is not required by the normal deployment model.

Conceptually:

    GlasHaus Server
        │
        ├── Internal Users
        ├── External Users
        ├── Customers
        ├── Projects
        └── Business Data

All local identities and resources belong to this server's organization.

This does not prevent a future architectural decision from introducing a different tenancy model. Such a change must be explicit.

Independent GlasHaus servers are separate trust domains.

---

## 4. User Identity

`User` is the central human identity object.

A `User` represents one human account that may authenticate to GlasHaus.

A User may contain identity and account information such as:

- stable user identifier
- display name
- contact information where required
- authentication state
- `user_type`
- role
- date of birth where required
- employment hierarchy level where applicable
- account status
- creation and modification timestamps

A User has exactly:

- one `user_type`
- one role

Internal users may additionally have an employment hierarchy level.

External users may have one or more explicitly assigned business relationships.

### Age

A mutable `age` value must never be persisted.

Age is derived from `date_of_birth` and the current date.

Age-dependent authorization rules must calculate age at authorization-evaluation time.

Tests must use an explicit reference date.

---

## 5. User Types

Every User has exactly one user type.

The initial user types are:

- `INTERNAL`
- `EXTERNAL`

### 5.1 Internal

An internal user belongs to the organization operating the GlasHaus server.

Examples include:

- technician
- office

The exact role catalogue is extensible.

### 5.2 External

An external user does not belong to the organization operating the GlasHaus server.

`EXTERNAL` is intentionally generic.

It must not be replaced by relationship-specific user types such as `CUSTOMER_USER`.

#### External Relationships and Customer Project Access

An external User's business relationship is separate from the User's identity.

The model is:

```text
User
  |
  +-- ExternalRelationship --> Customer
  |
  +-- CustomerProjectAccess --> Project
```

An `ExternalRelationship` describes the business relationship between an external User and a Customer.

Examples include:

```text
CUSTOMER
SUPPLIER
TAX_ADVISOR
PARTNER
```

The relationship does not by itself grant access to every resource of the related Customer.

Project-specific customer access is represented separately through `CustomerProjectAccess`.

A valid customer-facing project authorization therefore requires all applicable conditions to be satisfied:

1. the User is active;
2. the User has an applicable external relationship with the Project's Customer;
3. the User has valid access to the Project;
4. the requested Permission is effective;
5. the Permission applies to the requested scope;
6. all applicable policy and security constraints are satisfied.

Neither an `ExternalRelationship` nor a `CustomerProjectAccess` record alone is sufficient to bypass the authorization model.


---

## 6. Business Relationships

Business relationships are separate from User identity.

A `Customer` is a business/domain entity.

A customer relationship associates one or more external users with a Customer.

Conceptually:

    User
      │
      └── EXTERNAL
            │
            └── Customer Relationship
                  │
                  └── Customer
                        │
                        └── Projects

Multiple external users may belong to the same Customer.

For example:

    Customer: Example General Contractor
        │
        ├── External User A
        ├── External User B
        └── External User C

They remain separate User identities and may receive different permissions.

A User does not become a Customer merely because the User is external.

The same model can later represent:

    User
      │
      └── EXTERNAL
            │
            ├── Customer Relationship
            ├── Supplier Relationship
            ├── Tax Advisor Relationship
            └── Partner Relationship

Only explicitly assigned relationships are valid.

---

## 7. Roles

Each User has exactly one role.

Roles describe functional responsibility.

There is no generic `EMPLOYEE` role.

Examples include:

- `TECHNICIAN`
- `OFFICE`
- `SITE_SUPERVISOR`
- `MANAGEMENT`
- `CUSTOMER`
- `TAX_ADVISOR`
- future roles as required by the domain

The role catalogue is an explicit domain definition and may evolve.

A role provides baseline capabilities.

A role does not provide unrestricted authority.

---

## 8. User Type and Role Compatibility

User type and role are separate concepts but must be compatible.

For example:

    INTERNAL
        ├── TECHNICIAN
        ├── OFFICE
        ├── SITE_SUPERVISOR
        └── MANAGEMENT

    EXTERNAL
        ├── CUSTOMER
        ├── TAX_ADVISOR
        ├── SUPPLIER
        └── PARTNER

Invalid combinations must be rejected.

An internal-only role must not silently be assignable to an external user.

Likewise, an external role or relationship must never implicitly grant Internal Workspace access.

---

## 9. Employment Hierarchy

Internal users may have an employment hierarchy level.

Hierarchy is separate from role.

The same hierarchy level may exist across different roles.

For example:

    INTERNAL
        │
        ├── TECHNICIAN
        │      └── APPRENTICE
        │
        └── OFFICE
               └── APPRENTICE

Both users are apprentices, but their functional permissions differ because their roles differ.

Hierarchy therefore contributes to baseline authorization but does not define the complete permission set.

Hierarchy should normally represent the user's contractual or organizational position rather than being used as a manually maintained access-level mechanism.

---

## 10. Hierarchy Levels

A possible hierarchy catalogue includes:

- `APPRENTICE`
- `JUNIOR`
- `STANDARD`
- `SENIOR`
- `SUPERVISOR`
- `MANAGEMENT`

The exact catalogue may be refined independently of the authorization engine.

Hierarchy effects are role-dependent.

For example:

    TECHNICIAN + APPRENTICE
        → restricted technician capabilities

    TECHNICIAN + SENIOR
        → broader operational capabilities

    TECHNICIAN + SUPERVISOR
        → additional planning capabilities

An identical hierarchy level must not accidentally grant unrelated permissions across roles.

---

## 11. Permission Model

A Permission represents an application-defined capability.

Permissions and resource scopes are separate concepts.

A Permission answers:

> What kind of action may this principal perform?

The scope answers:

> On which resource or resource context may the principal perform that action?

The MVP uses the following canonical permission identifiers.

### Customer

```text
customer.read
customer.write
```

`customer.read` allows reading customer information.

`customer.write` allows creating and modifying customer information.

### Project

```text
project.read
project.write
project.coordinate
```

`project.read` allows reading project information.

`project.write` allows creating and modifying project information.

`project.coordinate` allows project coordination activities beyond ordinary project data management.

### Purchasing

```text
purchase.create
purchase.grant
```

`purchase.create` allows creating purchases within the authorized scope.

`purchase.grant` allows granting or delegating purchase authority to another principal, subject to the granting principal's own authority, scope, and constraints.

A purchase permission is not inherently limited to a project. The applicable scope determines whether the purchase is valid for a specific project, organizational overhead, or another supported purchasing context.

### Documents

```text
document.read
document.write
document.sign
```

`document.read` allows reading documents within the authorized scope.

`document.write` allows creating and modifying documents or document versions within the authorized scope.

`document.sign` allows signing documents within the authorized scope.

### Scheduling

```text
schedule.view_availability
schedule.view_details
schedule.assignment_write
schedule.assignment_request
schedule.assignment_grant
```

`schedule.view_availability` allows viewing scheduling availability without necessarily exposing the reason for an existing assignment.

`schedule.view_details` allows viewing scheduling details where the principal is authorized to see them.

`schedule.assignment_write` allows creating or modifying assignments directly within the authorized scope.

`schedule.assignment_request` allows requesting an assignment or assignment change when direct assignment is not permitted or a workflow requires approval.

`schedule.assignment_grant` allows approving or granting an assignment for another principal within the authorized scope.

### User and Permission Management

```text
user.manage
permission.manage
```

`user.manage` allows managing users and their organizational authorization context within the authorized scope.

`permission.manage` allows managing explicit permission grants and restrictions within the authorized scope and subject to delegation constraints.

`permission.manage` does not constitute unrestricted authority to grant any permission to any principal.

### Canonical MVP Permission Set

The following identifiers are the complete canonical Permission set for the MVP:

```text
customer.read
customer.write

project.read
project.write
project.coordinate

purchase.create
purchase.grant

document.read
document.write
document.sign

schedule.view_availability
schedule.view_details
schedule.assignment_write
schedule.assignment_request
schedule.assignment_grant

user.manage
permission.manage
```

No additional Permission identifiers are part of the MVP unless explicitly added to this catalogue through an architecture decision.

The Permission catalogue is application policy. Ordinary administrators must not create arbitrary new Permission types at runtime.

---

## 12. Permission Grants, Restrictions, Scope and Constraints

Effective authorization is determined from multiple independent dimensions.

The general model is:

```text
Effective Authorization =
    Role Defaults
    + Role/Hierarchy Defaults
    + Explicit Grants
    - Explicit Restrictions
    subject to
    Scope
    Policy Constraints
    Delegation Constraints
```

A Permission alone does not grant unrestricted access.

### Explicit Grants

An explicit grant may assign a Permission to a principal for a defined scope.

For example:

```text
permission = purchase.create
scope      = PROJECT:123
```

This means that the principal may create purchases for Project `123`, provided all other authorization requirements are satisfied.

### Explicit Restrictions

A restriction may prevent an otherwise available Permission from being exercised in a defined scope.

Restrictions must be evaluated by the server and must not be bypassable by ordinary administrative actions.

### Scope

Permissions and scopes are deliberately separate.

A Permission must not encode a specific resource scope in its identifier.

For example, the canonical Permission is:

```text
purchase.create
```

not:

```text
project.purchase_create
```

The scope determines where the Permission applies:

```text
purchase.create
scope = PROJECT:123
```

or, where supported:

```text
purchase.create
scope = ORGANIZATION
```

The same principle applies to documents, projects, scheduling, users, and other resource domains.

### Constraints

Some Permissions require additional constraints beyond a simple allow/deny decision.

A constraint is not itself a Permission.

For example, purchasing may use a financial limit:

```text
permission = purchase.create
scope      = PROJECT:123
constraint:
    purchase_limit = 2000 EUR
```

`purchase_limit` is therefore a constraint on `purchase.create`, not a separate Permission such as `purchase.limit`.

A constraint may be `None` where the applicable policy defines no additional limit.

The server must evaluate such constraints whenever the protected action is executed.

### Delegation Constraints

A principal with `permission.manage` does not automatically have unlimited authority to grant arbitrary Permissions.

A principal may only delegate authority that the principal is itself authorized to delegate.

Delegation must therefore be constrained by:

* the granting principal's own effective authority;
* the Permission being delegated;
* the target scope;
* applicable constraints;
* applicable policy restrictions;
* any temporal validity of the grant.

For example, a principal with:

```text
permission = purchase.create
scope      = PROJECT:123
constraint:
    purchase_limit = 2000 EUR
```

must not be able to delegate:

```text
permission = purchase.create
scope      = PROJECT:123
constraint:
    purchase_limit = None
```

unless the principal independently possesses sufficient authority to delegate that broader purchasing capability.

Permission administration must never provide an implicit privilege-escalation path.

### Default Deny

If no applicable authorization rule grants a requested action, the result is `DENY`.

The absence of an explicit restriction does not imply permission.

---

## 13. Role Defaults

Roles provide baseline permissions.

Example:

    TECHNICIAN
        project.view
        document.view
        schedule.view_availability

    SITE_SUPERVISOR
        project.view
        document.view
        schedule.view_availability
        schedule.request_assignment

    OFFICE
        customer.view
        project.view
        document.view

These defaults describe normal capabilities.

They are not necessarily the final effective permissions of an individual user.

---

## 14. Hierarchy Defaults

Hierarchy levels may add or restrict baseline capabilities.

Examples:

    TECHNICIAN + APPRENTICE
        → limited project operations

    TECHNICIAN + SENIOR
        → additional operational permissions

    TECHNICIAN + SUPERVISOR
        → planning permissions

Hierarchy defaults must be evaluated in the context of the user's role.

An apprentice hierarchy level must not provide unrelated permissions merely because another role uses the same hierarchy level.

---

## 15. Explicit Permission Grants

A specific user may receive an explicit permission grant.

Example:

    User: Technician A
    Role: TECHNICIAN
    Hierarchy: SENIOR

    Explicit Grant:
        purchase.create

The grant allows an otherwise permitted exception without creating an artificial role.

Permission grants must be:

- explicit
- scoped
- attributable
- revocable
- policy-constrained
- auditable where required

Grants may be temporary.

---

## 16. Explicit Permission Restrictions

A specific user may receive an explicit restriction.

Restrictions are used when a user would otherwise inherit a capability but must not exercise it.

Example:

    User: Office Employee A
    Role: OFFICE

    Restriction:
        schedule.view_details

Restrictions participate in the final authorization decision and cannot be bypassed by a less-specific role or hierarchy rule.

An explicit restriction therefore has precedence over an otherwise applicable configurable allow.

Mandatory policy constraints have precedence over both grants and restrictions.

---

## 17. Permission Delegation

Permission management is itself an authorization-controlled operation.

A user may only grant permissions that policy allows that user to delegate.

A delegation request must conceptually evaluate:

1. Is the requester authenticated?
2. Is the requester authorized to manage permissions?
3. Is the requested permission delegable?
4. Is the requested scope valid?
5. Does mandatory policy permit the grant?
6. Does the requester have sufficient authority for the target?
7. Is additional approval required?
8. Is the resulting permission combination valid?

Only after these checks may the grant be created.

The permission system must never become an administrative bypass.

---

## 18. Delegation Scope

A permission delegation should explicitly represent, where applicable:

- permission
- target user
- resource scope
- granting principal
- creation time
- activation time
- expiration time
- reason
- approval state
- revocation state

The exact persistence representation is defined by the persistence architecture.

Security-critical permissions may require additional approval or separation of duties.

---

## 19. Temporary Permissions

Some permissions may be temporary.

Examples include:

- temporary purchasing authority
- temporary project management
- absence coverage
- temporary external collaboration

Temporary grants should support:

- activation time
- expiration time
- scope
- granting authority
- optional approval
- revocation

Expired permissions must not contribute to effective authorization.

Expiration must be evaluated server-side.

---

## 20. Separation of Duties

Some security-sensitive actions may require independent actors.

Examples include:

- permission delegation
- sensitive document approval
- financial approval
- security configuration
- cryptographic key administration
- federation trust changes

The authorization architecture must support future workflows requiring multiple independent approvals.

Administrative status alone must not automatically imply the ability to bypass every security boundary.

---

## 21. Permission Constraints

Some permissions are inherently constrained.

### Age Constraint

Age-dependent permissions are evaluated from:

    date_of_birth + current date

Age is never persisted as an authorization attribute.

### Scope Constraint

A user may have:

    document.download

but only for:

    Project A

### Workspace Constraint

A customer may have:

    document.view

within:

    Customer Workspace

but not:

    Internal Workspace

### Delegation Constraint

A user may have:

    permission.manage

without being authorized to delegate security-critical permissions.

Mandatory constraints override configurable grants.

---

## 22. Resource Scopes

Permissions are evaluated together with resource scope.

A permission without a valid scope does not imply access to every instance of a resource.

Possible scopes include:

- global
- customer
- project
- document
- document category
- workspace
- user
- schedule
- organization-local resource

The applicable scope depends on the resource and action.

Examples:

    project.view
        scope = Project A

    customer.view
        scope = Customer X

    document.download
        scope = Project A

    schedule.view_availability
        scope = permitted users / team

Scope evaluation is a distinct authorization step.

---

## 23. Project Assignment

Project assignment is an explicit authorization boundary.

Internal users must have project access explicitly established before receiving project-specific access.

Assignment may be represented by:

- direct project membership
- an approved domain relationship
- another explicitly defined authorization relationship

The relationship must be explicit, queryable, and enforceable.

Knowing any of the following is insufficient:

- project ID
- customer name
- physical address
- document ID
- URL

There is no emergency address lookup or convenience bypass.

If access is required, the organization must establish an authorized relationship or scope.

---

## 24. Customer Project Access

External customer users access customer-facing project information through their Customer relationship.

A Customer may be associated with multiple projects.

A customer user may therefore access the Customer Workspace representation of projects belonging to that Customer, subject to:

- active user account
- valid Customer relationship
- valid project/customer relationship
- applicable permissions
- project exposure rules
- workspace restrictions

A customer user does not need an internal project assignment merely to access information intentionally exposed to the customer.

Internal project authorization remains separate.

---

## 25. Customer Workspace

The Customer Workspace is a distinct authorization context and security boundary.

It is intentionally smaller than the Internal Workspace.

Customer users may access only information explicitly exposed through this workspace.

Example:

    Customer Workspace
        ├── project status
        ├── customer-facing documents
        ├── agreed project information
        └── customer-facing communication

The Internal Workspace may additionally contain:

    Internal Workspace
        ├── internal notes
        ├── internal scheduling details
        ├── internal costs
        ├── internal personnel information
        └── internal operational information

The same underlying domain resource may therefore have different permitted representations depending on the authorization context.

---

## 26. Workspace Boundaries

Workspace boundaries are security boundaries, not merely UI concepts.

At minimum:

    Internal Workspace
        └── authorized internal users

    Customer Workspace
        └── authorized external customer users

External users must never gain Internal Workspace access merely through a business relationship.

Future external relationships may receive dedicated workspaces.

Examples include:

- Supplier Workspace
- Tax Advisor Workspace
- Partner Workspace

These are authorization contexts within the server, not independent trust domains.

---

## 27. Partial Resource Visibility

Authorization is not always binary at the object level.

Some permissions intentionally expose only a reduced representation.

For example:

    schedule.view_availability

may return:

    Technician B
    Monday: occupied
    Tuesday: available
    Wednesday: occupied

without returning:

    customer
    project address
    appointment details
    internal notes

A more privileged permission such as:

    schedule.view_details

may expose the additional information.

The backend must generate the permitted representation.

Sensitive fields must not be sent to the client merely to be hidden in the UI.

---

## 28. Scheduling Authorization Example

Consider a site supervisor planning Project A.

The supervisor may have:

    project.view
    schedule.view_availability
    schedule.request_assignment

The supervisor does not automatically have:

    schedule.view_details

The supervisor can therefore determine:

    Technician B
    Monday: occupied
    Tuesday: available
    Wednesday: occupied

without learning why Technician B is occupied.

The supervisor may create:

    Assignment Request
        Technician: B
        Project: A
        Requested Date: Tuesday

The actual assignment remains subject to the applicable workflow and authorization rules.

---

## 29. Data Minimization

Authorization should expose only the information necessary for the requested operation.

Access to a parent resource does not automatically authorize every sensitive field belonging to that resource.

This applies to:

- API responses
- database queries
- files
- search results
- exports
- synchronization
- federation

For example:

    schedule.view_availability

must not return:

- customer
- address
- appointment notes
- internal personnel information

unless another applicable authorization rule permits those fields.

---

## 30. Search Authorization

Search must be authorization-aware.

A user searching for a customer, project, document, or other resource must only receive resources they are authorized to discover.

Search must not become a side channel for unauthorized resource existence.

For example, a user without access to Project A must not receive:

    Project A — access denied

The preferred behavior is to omit unauthorized resources from the result set.

---

## 31. Authentication and Authorization

Authentication answers:

    "Who is making this request?"

Authorization answers:

    "Is this identity allowed to perform this action on this resource in this context?"

Conceptually:

    Request
      │
      ▼
    Authentication
      │
      ▼
    Authenticated Principal
      │
      ▼
    Authorization
      │
      ▼
    Resource Access

Authentication mechanisms may evolve independently.

Possible mechanisms include:

- password authentication
- session authentication
- device-bound authentication
- stronger future authentication mechanisms

Business authorization must not be coupled to one permanent authentication mechanism.

---

## 32. Device and Network Context

Device registration and internal network/VPN access may contribute to the security context.

They must not replace application-level authentication and authorization.

A trusted network must not automatically imply unrestricted application access.

A registered device may provide stronger authentication or additional authorization context for particularly sensitive operations.

At the same time, legitimate workflows must remain possible from an appropriate browser-based path when explicitly permitted by security policy.

For example, an internal employee may need to:

- submit a sickness notification
- request vacation
- perform another permitted employee workflow

from another trusted computer.

This is not an authorization bypass.

The user must still:

1. authenticate;
2. establish the required security context;
3. satisfy applicable policy;
4. receive the applicable permission;
5. access only the permitted workflow.

---

## 33. Authorization Evaluation

Authorization must be deterministic and server-side.

Conceptually:

    authenticate(request)
        ↓
    authenticated principal
        ↓
    validate account state
        ↓
    identify resource
        ↓
    determine workspace
        ↓
    determine user type
        ↓
    validate role compatibility
        ↓
    determine hierarchy where applicable
        ↓
    load role defaults
        ↓
    load hierarchy defaults
        ↓
    apply explicit grants
        ↓
    apply explicit restrictions
        ↓
    evaluate mandatory policy constraints
        ↓
    evaluate resource relationship
        ↓
    evaluate resource scope
        ↓
    evaluate requested action
        ↓
    ALLOW or DENY

The exact implementation may optimize this sequence, but the resulting decision semantics must remain equivalent.

Any missing or invalid security context results in denial.

---

## 34. Default Deny

The authorization system must fail closed.

Examples:

- unknown user → `DENY`
- inactive user → `DENY`
- missing role → `DENY`
- invalid role/user-type combination → `DENY`
- missing project assignment → `DENY`
- missing customer relationship → `DENY`
- missing permission → `DENY`
- invalid scope → `DENY`
- forbidden workspace → `DENY`
- failed policy constraint → `DENY`
- expired grant → `DENY`

The absence of an explicit allow condition must never be interpreted as permission.

---

## 35. External Authorization

External users are authorized through their external role and explicitly assigned business relationships.

Example:

    External Customer User
        │
        ├── Customer relationship
        ├── Customer role
        └── Customer Workspace

A future tax advisor may instead have:

    External Tax Advisor
        │
        ├── Tax Advisor relationship
        ├── Tax Advisor role
        └── Tax Workspace

The meaning of `EXTERNAL` therefore remains stable while new external relationships can be added.

---

## 36. Future Federation

Future federation between GlasHaus servers must not reuse local identity assumptions blindly.

A remote user is not automatically a local User.

A federated request must establish:

- remote server identity
- remote principal identity
- trust relationship
- requested action
- resource scope
- applicable federation context
- local authorization decision

The receiving server remains authoritative over its own resources.

Federation must never mean:

    remote server says allowed
        ↓
    local server allows

Instead:

    Remote Identity
        ↓
    Authenticated Federation Context
        ↓
    Local Policy Evaluation
        ↓
    Local Authorization Decision

Each GlasHaus server remains responsible for its own:

- identities
- authorization
- resources
- security policies
- audit
- cryptographic keys

---

## 37. Authorization and Persistence

Authorization must not depend on client-side state.

Persistence queries should exclude unauthorized resources as early as practical.

Database filtering is not, however, the complete authorization model.

The application must retain authoritative authorization evaluation.

Important authorization invariants should additionally be represented by persistence constraints where practical.

Examples include:

- valid user type values
- valid role values
- role/user-type compatibility
- unique stable identities
- valid relationship references
- valid project assignments
- valid permission grant states

The exact persistence representation is defined by `docs/PERSISTENCE_MODEL.md`.

---

## 38. Authorization Does Not Imply Encryption

Authorization and encryption are separate security controls.

Authorization determines whether a principal may access a resource.

Encryption protects against additional threats such as storage compromise or intercepted data.

Conceptually:

    Authorized User
        ↓
    Authorization Allows Access
        ↓
    Application Obtains Permitted Content

Separately:

    Storage Compromise
        ↓
    Encryption Protects Stored Content

Cryptographic requirements are defined in `docs/CRYPTOGRAPHY.md`.

---

## 39. Security-Sensitive Permissions

Certain permissions require special treatment.

Examples include:

- `document.sign`
- document decryption
- `permission.manage`
- `user.manage`
- cryptographic key management
- security configuration
- external data sharing
- federation trust management

Depending on the security policy, such permissions may require:

- stronger authentication
- device trust
- explicit scope
- additional approval
- audit logging
- temporary grants
- separation of duties

The exact requirements are defined by `docs/SECURITY.md` and `docs/CRYPTOGRAPHY.md`.

---

## 40. Auditability

Authorization-relevant security events should be auditable where required.

Examples include:

- role changes
- hierarchy changes
- permission grants
- permission restrictions
- permission revocations
- project assignments
- customer relationships
- external access changes
- delegation
- sensitive authorization decisions
- security-sensitive administrative actions

Audit records should identify the relevant actor and target where appropriate.

Audit data is itself protected information and therefore requires its own access and retention rules.

Detailed audit requirements belong to `docs/SECURITY.md`.

---

## 41. Testing Requirements

The authorization model requires explicit positive and negative tests for:

- user type validation
- role/user-type compatibility
- age calculation
- hierarchy defaults
- role defaults
- explicit grants
- explicit restrictions
- grant expiration
- project assignment
- customer relationships
- workspace separation
- partial resource visibility
- default deny
- permission delegation
- invalid scopes
- external access
- search authorization
- sensitive permission handling
- federation boundaries

Negative tests are particularly important.

Tests must verify that users cannot gain access merely because:

- they know an identifier
- they know a project address
- they belong to the organization
- they have a related but insufficient role
- they possess a broader unrelated permission
- they are an administrator without sufficient delegation authority
- a client-side UI exposes an action
- a resource was returned through an improperly filtered search

Age-dependent tests must use an explicit reference date.

Authorization tests must verify both:

1. whether an action is allowed; and
2. which representation of the resource is returned.

---

## 42. Architectural Invariants

The following invariants remain true unless this architecture is explicitly changed:

1. One User has exactly one User Type.
2. One User has exactly one Role.
3. Age is derived from `date_of_birth`.
4. `EXTERNAL` is a generic User Type.
5. Customer is a business relationship/entity, not a User Type.
6. User identity and business relationship are separate concepts.
7. Internal and external workspace access are separate security boundaries.
8. Project access is explicit.
9. There is no emergency access to an unassigned project.
10. Role defaults are not unrestricted authority.
11. Hierarchy does not replace role-based functional responsibility.
12. Individual grants are explicit and policy-constrained.
13. Individual restrictions cannot be bypassed by configurable permissions.
14. Permission management is itself authorized.
15. Mandatory policy constraints cannot be overridden by grants.
16. Temporary grants expire automatically.
17. Authorization is server-side and default-deny.
18. Resource scope is evaluated separately from permission.
19. Partial resource representations are generated server-side.
20. Unauthorized resources must not be disclosed through search.
21. External relationships must not redefine the core User model.
22. Future federation must preserve independent server trust domains.
23. Encryption does not replace authorization.
24. Authorization does not replace encryption.

---

## 43. Related Documents

This document should be read together with:

- `docs/ARCHITECTURE.md` — overall system architecture and boundaries
- `docs/PERSISTENCE_MODEL.md` — persistence and database model
- `docs/SECURITY.md` — threat model, security boundaries, controls and audit
- `docs/CRYPTOGRAPHY.md` — encryption, key management and cryptographic architecture
- `docs/SYNC.md` — offline synchronization
- `docs/TESTING.md` — testing strategy and verification requirements
- `docs/Roadmap.md` — implementation sequence
- `docs/AI_RULES.md` — AI-assisted development and engineering rules

The implementation must not silently diverge from these documents.

If implementation and architecture conflict, the conflict must be resolved explicitly.

The implementation must then be brought into alignment with the approved architectural decision.