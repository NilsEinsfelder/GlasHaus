# GlasHaus Identity & Authorization

## Status

Architecture specification — approved design baseline.

This document defines identity and authorization for a self-hosted GlasHaus installation.

## 1. Deployment Model

Each GlasHaus server is operated autonomously by one company.

The server itself is the local organizational and security boundary.

There is no SaaS-style organization/tenant layer inside the installation.

Independent GlasHaus servers are separate trust domains.

## 2. Identity Model

`User` is the central human identity.

A User has exactly one:

- user type
- role

Internal users additionally have an applicable employment hierarchy level.

The initial user types are:

- `INTERNAL`
- `EXTERNAL`

### Internal

An internal user belongs to the company operating the server.

Examples:

- office employee
- project manager
- technician
- apprentice
- management

### External

An external user does not belong to the operating company.

External relationships determine what kind of external party the user represents.

Future external relationships include:

- Customer
- Supplier
- Tax Advisor
- Partner

An external user is a Customer only when an explicit Customer relationship exists.

## 3. User Data

A User stores:

- stable identifier
- login identity
- display information
- date of birth
- user type
- active/inactive state
- lifecycle timestamps

Age is never stored.

Age is calculated from `date_of_birth` and the current date.

This is required for rules such as minimum-age restrictions.

## 4. Employment

Internal employment is represented separately from the User identity.

Conceptually:

    User
      ↓
    Employment
      ├── role
      ├── hierarchy level
      ├── employment status
      ├── valid from
      └── valid until

This allows hierarchy changes to be represented historically.

Example:

    Technician Apprentice
          ↓
    Technician Professional
          ↓
    Senior Technician
          ↓
    Lead Technician

The effective employment context is the one valid for the relevant date.

## 5. Role

A User has exactly one role.

Roles represent the user's primary functional responsibility.

Examples:

    INTERNAL
    ├── OFFICE
    ├── PROJECT_MANAGER
    ├── TECHNICIAN
    └── ADMINISTRATOR

    EXTERNAL
    ├── CUSTOMER
    ├── TAX_ADVISOR
    ├── SUPPLIER
    └── PARTNER

Roles are not sufficient to determine final authorization.

## 6. Hierarchy

Hierarchy represents the organizational/contractual level of an internal employee.

Initial levels may include:

- APPRENTICE
- PROFESSIONAL
- SENIOR
- LEAD
- MANAGEMENT

Hierarchy defaults are role-aware.

For example:

    TECHNICIAN + APPRENTICE
    TECHNICIAN + PROFESSIONAL
    TECHNICIAN + LEAD

may have different effective permissions.

An office apprentice and technician apprentice therefore do not automatically receive the same access.

## 7. Permissions

Permissions represent actions.

Examples:

    project:read
    project:write

    document:read
    document:create
    document:update
    document:delete
    document:publish_customer

    purchase:create

    calendar:availability:read
    calendar:details:read

    customer_project:read
    customer_document:read
    customer_file:download

Permissions describe capabilities, not job titles.

## 8. Effective Permissions

Effective permissions are calculated from:

    Role defaults
          +
    Hierarchy defaults
          +
    Explicit user grants/restrictions
          +
    Resource scope
          +
    Workspace scope
          +
    Action-specific rules

The result is evaluated server-side.

Default is deny.

## 9. Permission Grants

A Permission Grant may:

- allow a permission
- deny/restrict a permission

It may be scoped to:

- global
- project
- workspace
- user
- another explicitly supported resource scope

A grant may have:

- granting actor
- reason
- valid-from timestamp
- valid-until timestamp
- active state

A grant is an explicit security decision and may be audited.

## 10. Permission Administration

No administrator receives an unrestricted "permission editor".

Permission changes are subject to policy.

A grant may only be created when the granting actor is themselves authorized to grant that permission within the relevant scope.

The system must prevent privilege escalation such as:

    user
      ↓
    grants self
      ↓
    administrator permission

Permission administration therefore consists of controlled permission-management capabilities, not arbitrary database manipulation.

## 11. Internal Project Access

Internal users require explicit Project Assignment.

Example:

    Alice
      role = TECHNICIAN
      hierarchy = PROFESSIONAL

    assignments:
      Project A
      Project C
      Project D

Alice may access Project A, C and D according to her permissions.

She may not access Project B.

There is no emergency address-only access.

Project addresses are protected project data.

## 12. Customer

A Customer is a business/domain entity.

A Customer may represent:

- a company
- a private customer

A Customer is not an organization/tenant.

A Project has one primary Customer.

## 13. External Relationships

External relationships connect an external User to a business entity.

Example:

    User: Thomas Müller
       ↓
    ExternalRelationship
       ↓
    Customer: ACME GmbH

The relationship type identifies the external relationship.

This model allows future relationships such as:

    Customer
    Supplier
    Tax Advisor
    Partner

without changing the identity model.

## 14. Customer Users

A Customer may have multiple external users.

Example:

    ACME GmbH
      ├── Thomas
      ├── Julia
      └── Michael

Each user authenticates independently.

All users remain subject to their own permissions.

Being an employee of the Customer does not automatically grant unrestricted access to all customer projects.

## 15. Customer Project Access

Customer access is explicit.

A customer user may access a project only when:

1. the user is active;
2. the external Customer relationship is valid;
3. the project belongs to that Customer;
4. the user has active project access;
5. the requested permission is granted;
6. the requested workspace is permitted.

This allows:

    ACME
      ├── Project A
      ├── Project B
      └── Project C

    Thomas
      ├── A
      └── B

    Julia
      └── C

## 16. Workspaces

Each Project has two primary workspaces:

    Project
      ├── Internal Workspace
      └── Customer Workspace

### Internal Workspace

Contains internal-only information.

External users can never access it.

### Customer Workspace

Contains information intentionally exposed to the Customer.

The Customer Workspace is project-wide.

A customer user who is authorized for the project can access the customer-visible content according to their permissions.

## 17. Customer File Sharing

Internal users with appropriate permissions may publish content to the Customer Workspace.

Moving or publishing a file to the Customer Workspace is explicit.

A file in the Internal Workspace does not become visible to customers merely because it belongs to the same project.

## 18. Resource Authorization

Permission alone does not grant resource access.

Authorization requires both:

    capability
       +
    resource scope

For internal users:

    Authentication
        ↓
    Active user
        ↓
    Valid session/device where required
        ↓
    Effective permission
        ↓
    Project assignment
        ↓
    Workspace authorization
        ↓
    Action-specific rule
        ↓
    ALLOW

For external customer users:

    Authentication
        ↓
    Active user
        ↓
    Customer relationship
        ↓
    Customer project access
        ↓
    Effective permission
        ↓
    Customer Workspace
        ↓
    ALLOW

Any failed condition results in DENY.

## 19. Projection and Partial Visibility

Permission may determine whether a user can see a resource, while a separate permission determines how much detail is exposed.

Example:

    calendar:availability:read

allows a Lead Technician to see:

    Monday      BUSY
    Tuesday     FREE

without allowing:

    calendar:details:read

which could reveal:

    customer
    location
    appointment details

This distinction is required for operational planning without unnecessary disclosure.

## 20. Example: Lead Technician

A Lead Technician may have:

    TECHNICIAN
    hierarchy = LEAD

and:

    calendar:availability:read

The Lead Technician can determine whether other technicians and apprentices are available.

He can then create a staffing request for another technician on a project.

He does not automatically receive the detailed content of the technician's appointments.

## 21. Example: Apprentice

A Technician Apprentice may receive normal technician training/work permissions.

A particular apprentice may be explicitly denied:

    document:sign

or:

    purchase:create

even if a general technician role contains related capabilities.

A trusted employee may later receive an explicit, scoped permission grant if policy allows it.

Age-dependent rules remain independently enforced.

Example:

    calculate_age(date_of_birth, current_date) < 18
        ↓
    signing action denied

The result is never based on a manually stored age.

## 22. No Unassigned Project Access

GlasHaus deliberately does not provide:

- emergency address access
- convenience access
- "employee can see all projects" fallback
- URL-based access
- ID-based access

If a user needs access, the organization must assign the user correctly.

This keeps the security model predictable.

## 23. Authorization Invariants

1. Default deny.
2. Authentication does not imply authorization.
3. Role does not imply unrestricted resource access.
4. A User has one role.
5. Hierarchy is separate from role.
6. Permission grants are explicit.
7. Permission grants are scoped.
8. Permission administration is itself authorized.
9. Internal project access requires assignment.
10. External project access requires explicit customer project access.
11. External users never access Internal Workspace.
12. Project addresses are protected project data.
13. The client is never authoritative.
14. Age is calculated from date of birth.
15. Authorization decisions are auditable where security-sensitive.