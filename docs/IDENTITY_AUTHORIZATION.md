# Identity & Authorization

## Status

Architecture specification — approved for implementation.

This document defines the identity, authentication context and authorization
model of a self-hosted GlasHaus installation.

GlasHaus is designed as a self-hosted system. Each GlasHaus server operates
autonomously for one owning company.

The authorization model therefore does not use multi-tenant SaaS isolation
inside a single GlasHaus installation.

Future communication between independent GlasHaus servers is treated as a
separate federation trust boundary.

---

## 1. Goals

GlasHaus must provide:

- secure authentication of internal and external users;
- strict isolation of all data belonging to the local GlasHaus installation;
- explicit authorization for every protected resource;
- explicit project assignment for internal users;
- controlled customer access to their projects;
- a dedicated customer-facing workspace;
- different permissions for internal and external users;
- revocation of users, devices and sessions;
- bounded offline authorization;
- auditable security-sensitive actions;
- a future path for secure communication between independent GlasHaus servers.

The authorization model must remain understandable, explicit and testable.

Security must not depend on hidden application conventions or client-side
checks.

---

## 2. Deployment and Trust Model

A GlasHaus installation is self-hosted by one company.

The GlasHaus server is therefore the primary local security boundary.

Conceptually:

    GlasHaus Server
    ├── Internal Users
    ├── Customers
    ├── Projects
    ├── Documents
    └── Devices

All data stored by the server belongs to this local GlasHaus installation.

There is no requirement for an `organization_id` on every local record.

The server itself represents the local organization's data boundary.

---

## 3. Core Security Principles

### 3.1 Server-side authority

The server is the final authority for authorization.

The client must never be trusted to enforce access restrictions.

Every protected API operation must be authorized server-side.

---

### 3.2 Default deny

Access is denied unless all required authorization conditions are satisfied.

There is no implicit access based only on:

- authentication;
- knowledge of a resource ID;
- possession of a URL;
- user role;
- client-side state;
- previous access.

---

### 3.3 Explicit project assignment

Internal users may only access projects to which they are explicitly assigned.

There is no emergency or convenience access to an unassigned project.

This includes project addresses.

A user who is not assigned to a project must not receive project information merely
because the information appears operationally useful.

The organization operating the GlasHaus server is responsible for maintaining
correct project assignments.

---

### 3.4 Least privilege

Users receive only the permissions required for their role and project scope.

Customer users receive only customer-specific permissions.

A customer role must never implicitly inherit internal-user permissions.

---

### 3.5 Resource authorization

A permission does not by itself grant unrestricted access to all resources.

The principal must also have access to the relevant project and workspace.

---

## 4. Security Principals

GlasHaus distinguishes between three principal categories:

- internal users;
- customer users;
- federation peers.

The first two are implemented locally.

Federation peers are reserved for future server-to-server communication.

---

## 5. Internal Users

An internal user is a human user belonging to the company operating the
GlasHaus server.

Internal users may include:

- administrators;
- office staff;
- project managers;
- technicians;
- other employees.

An internal user has:

- an identity;
- one or more roles;
- registered devices;
- active sessions;
- explicit project assignments.

An internal user's role defines what actions they may perform.

Project assignment defines which projects they may access.

Both conditions are required.

---

## 6. Customer

A Customer represents an external client of the GlasHaus installation.

A customer may be:

- a company;
- a private individual.

The customer is not a tenant of the GlasHaus server.

The customer is a business/domain entity to which projects belong.

Example:

    GlasHaus Server
        │
        ├── Customer: ACME GmbH
        │
        ├── Customer: Müller Familie
        │
        └── Customer: General Contractor GmbH

A project has one primary customer.

---

## 7. Customer Users

A customer may have one or more customer users.

Example:

    Customer: ACME GmbH
        │
        ├── Thomas
        ├── Julia
        └── Michael

Customer users authenticate independently.

Customer users do not receive internal-user permissions.

A customer employee does not automatically receive access to every project
of the customer.

Project access remains explicit.

---

## 8. Customer Project Access

A customer may be associated with one or more projects.

Example:

    Customer: ACME GmbH
        │
        ├── Project A
        └── Project B

A customer user may access a project only when:

1. the user is active;
2. the user belongs to the customer associated with the project;
3. the user has an active customer project assignment;
4. the user's customer role grants the requested action.

Customer access is therefore project-scoped.

---

## 9. Projects

A project belongs to the local GlasHaus installation and has one primary
customer.

Conceptually:

    Project
    ├── customer
    ├── address
    ├── Internal Workspace
    └── Customer Workspace

The project is the primary scope for operational access control.

---

## 10. Project Assignments

Internal users receive access through explicit project assignments.

Example:

    Alice
        │
        ├── role = technician
        │
        └── assigned projects:
                ├── Project A
                ├── Project C
                └── Project D

Alice may not access Project B.

There is no fallback rule that grants access to Project B because Alice is an
internal employee.

---

## 11. Customer Workspace

Every project may expose a Customer Workspace.

The Customer Workspace contains information intentionally made available to
the customer.

The Customer Workspace is project-wide.

Once a customer user has authorized access to the project's Customer Workspace,
the user can see the customer-facing project information allowed by their role.

The Customer Workspace is separate from the Internal Workspace.

---

## 12. Internal Workspace

The Internal Workspace contains information intended exclusively for internal
GlasHaus users.

Customer users must never receive access to the Internal Workspace.

This is a hard authorization boundary.

Example:

    Project A
    │
    ├── Internal Workspace
    │   ├── internal notes
    │   ├── internal documents
    │   └── internal project data
    │
    └── Customer Workspace
        ├── project information
        ├── progress information
        ├── customer documents
        └── customer-visible photos

Customer users may access the Customer Workspace only.

---

## 13. Workspace Boundary

For the initial architecture, GlasHaus does not require an additional
per-resource visibility ACL inside the Customer Workspace.

The primary visibility boundary is the workspace:

    Internal Workspace
        → internal users only

    Customer Workspace
        → authorized customer users

Permissions determine what a user may do with customer workspace resources.

This keeps the authorization model explicit and avoids unnecessary
per-document access rules.

A more granular resource-sharing mechanism may be introduced later if a
concrete business requirement requires it.

---

## 14. Customer File Sharing

Internal users with sufficient permissions may place files into the
Customer Workspace.

Placing a file into the Customer Workspace is an explicit action.

A file in the Internal Workspace is never visible to a customer merely because
it belongs to the same project.

Conceptually:

    Internal file
          │
          │ publish / move / copy
          ▼
    Customer Workspace
          │
          ▼
    Customer can access it according to role

The exact storage semantics are defined by the document/storage architecture.

---

## 15. Roles

GlasHaus uses role-based permissions for coarse-grained authorization.

Initial internal roles may include:

- admin;
- office;
- project_manager;
- technician;
- viewer.

Initial customer roles may include:

- customer;
- customer_manager.

Internal and customer roles belong to separate permission domains.

A customer role must never implicitly inherit an internal role.

---

## 16. Permissions

Permissions represent actions.

Examples for internal users:

    project:read
    project:write

    document:read
    document:create
    document:update
    document:delete

    photo:read
    photo:create

Examples for customer users:

    customer_project:read
    customer_document:read
    customer_file:download

Permissions should describe actions, not business exceptions.

---

## 17. Authorization Model

Authorization is evaluated conceptually as:

    authorize(
        principal,
        action,
        resource
    )

For an internal user:

    Authentication
          ↓
    User active
          ↓
    Device valid
          ↓
    Role / Permission
          ↓
    Project assignment
          ↓
    Workspace
          ↓
        ALLOW

For a customer user:

    Authentication
          ↓
    Customer user active
          ↓
    Customer relationship
          ↓
    Customer project access
          ↓
    Role / Permission
          ↓
    Customer Workspace
          ↓
        ALLOW

Any failed condition results in DENY.

---

## 18. Internal User Example

Alice works for the company operating the GlasHaus server.

    Alice
      │
      ├── role = technician
      └── assigned to Project A

Alice requests:

    GET /projects/A/documents

Authorization:

    authenticated              YES
    user active                YES
    device valid               YES
    permission document:read   YES
    assigned to Project A      YES
    internal workspace         YES

Result:

    ALLOW

If Alice requests Project B and is not assigned:

    authenticated              YES
    user active                YES
    device valid               YES
    permission document:read   YES
    assigned to Project B      NO

Result:

    DENY

There is no emergency address-only access.

---

## 19. Customer User Example

ACME GmbH is the customer of Project A.

    Customer:
        ACME GmbH

    Customer users:
        Thomas
        Julia

    Project:
        Project A
        customer = ACME GmbH

Thomas has:

    role = customer

Thomas requests the Customer Workspace of Project A.

Authorization:

    authenticated                   YES
    customer user active            YES
    belongs to ACME                 YES
    customer has access to Project A YES
    customer_project:read           YES
    Customer Workspace              YES

Result:

    ALLOW

Thomas requests Project B, which is not associated with ACME:

    customer relationship            NO

Result:

    DENY

---

## 20. Customer and Internal Data Separation

A customer may never access the Internal Workspace.

Example:

    Project A
    │
    ├── Internal Workspace
    │       └── internal contract notes
    │
    └── Customer Workspace
            └── approved contract document

Customer:

    approved contract document → ALLOW
    internal contract notes    → DENY

The distinction is based on workspace membership, not on the customer role
alone.

---

## 21. Customer Web Application

Customer users use the GlasHaus web application through an external connection.

The customer-facing interface is a restricted presentation of the same
GlasHaus backend.

It must not implement a separate authorization model.

Conceptually:

    GlasHaus Backend
          │
          ├── Internal UI
          │
          └── Customer UI

Both interfaces use the same server-side authorization mechanisms.

The customer UI must not be treated as a security boundary.

---

## 22. Device Identity

Internal devices are independently identifiable security principals associated
with users.

A device has:

- unique ID;
- status;
- registration timestamp;
- last-seen timestamp;
- revocation state;
- device authentication key material.

A revoked device cannot establish new authorized sessions or refresh its
authorization state.

Customer web access does not require the same device-registration workflow as
internal devices.

The exact customer authentication mechanism is specified separately.

---

## 23. Sessions

A session binds:

    User
      +
    Authentication state
      +
    Device context where applicable

Sessions can be expired or revoked independently.

A valid user with a revoked device must not be treated as fully trusted.

---

## 24. Offline Authorization

Offline access applies primarily to internal devices.

Offline authorization is a temporary authorization lease.

An authorization lease contains, conceptually:

- device;
- user;
- allowed permissions;
- allowed project scope;
- issuance time;
- expiration time;
- server authorization state.

Example:

    Device: iPad-17
    User: Alice

    permissions:
        project:read
        document:read
        photo:create

    projects:
        Project A
        Project C

    valid_until:
        2026-08-24T18:00:00

The device may operate within this scope while offline.

After expiration, operations requiring authorization must be restricted until
the server can be reached.

Offline authorization must never expand the user's online permissions.

---

## 25. Authorization Revocation

The following must be independently revocable:

- internal user;
- customer user;
- device;
- session;
- internal project assignment;
- customer project access.

Revocation must take effect on the server immediately.

Offline devices cannot be guaranteed to observe revocation until they reconnect.

Therefore offline authorization leases must have bounded lifetimes.

---

## 26. Error Semantics

Authorization failures must not reveal unnecessary information.

For resources whose existence is itself sensitive, GlasHaus may return:

    404 Not Found

instead of:

    403 Forbidden

This prevents users from discovering resources merely by probing IDs.

The concrete API semantics are defined during API implementation.

---

## 27. Audit

Authorization-relevant actions should be auditable.

An audit event may contain:

- actor;
- actor type;
- customer where applicable;
- device where applicable;
- action;
- resource;
- project;
- workspace;
- timestamp;
- authorization result;
- request correlation ID.

Audit records must not contain protected document contents.

Examples:

    Alice READ Project A Document 123 → ALLOW

    Alice READ Project B Document 456 → DENY

    Admin published Document 123 to Customer Workspace → ALLOW

    Thomas READ Project A Customer Workspace → ALLOW

    Thomas READ Project A Internal Workspace → DENY

---

## 28. Federation

Future GlasHaus versions may allow independent GlasHaus servers to exchange
data.

Federation is a separate trust boundary.

A remote GlasHaus server is not treated as a local organization or tenant.

Instead, it is an explicitly trusted Federation Peer.

Conceptually:

    GlasHaus Server A
          │
          │ explicit trust
          ▼
    GlasHaus Server B

Trust must never be implicit.

A Federation Peer receives only explicitly granted scopes.

---

## 29. Federation Identity

The future principal model includes:

    Principal
    ├── Internal User
    ├── Customer User
    └── Federation Peer

A Federation Peer may later receive scopes such as:

    Project A
        ├── document:read
        ├── photo:read
        └── document:create

The peer does not receive access to the complete local GlasHaus installation.

The federation protocol, cryptographic authentication and synchronization
mechanism are specified separately.

---

## 30. Federation Is Not User Federation

GlasHaus distinguishes between:

- server-to-server federation;
- user authentication.

A future federation protocol must not require that a remote user become a
local user.

Likewise, a local user must not automatically become a user on a remote
GlasHaus server.

The federation architecture must preserve the independent security
boundaries of both installations.

---

## 31. Security Invariants

The following rules are mandatory:

1. The GlasHaus server is the local security boundary.
2. The server is the final authorization authority.
3. Authentication does not imply authorization.
4. Default access is deny.
5. Internal users require explicit project assignment.
6. No emergency access exists for unassigned projects.
7. Customer users require explicit customer project access.
8. Customer users can access only the Customer Workspace of authorized projects.
9. Customer users can never access the Internal Workspace.
10. Customer roles never inherit internal-user permissions.
11. Customer UI is not a security boundary.
12. Client-side restrictions must never be relied upon for security.
13. Devices are independently revocable.
14. Offline authorization is time-limited.
15. Offline authorization cannot expand online permissions.
16. Revoked users and devices cannot receive new authorization.
17. Audit records must not contain protected content.
18. Federation trust is explicit.
19. Federation scopes are explicit.
20. A Federation Peer does not receive implicit access to local data.
21. Federation does not collapse independent server security boundaries.
22. Authorization decisions must be testable independently of the UI.

---

## 32. Deliberately Out of Scope

The following are not defined by this document:

- password hashing implementation;
- OAuth/OIDC provider selection;
- MFA implementation;
- customer invitation workflow;
- customer password recovery;
- cryptographic key hierarchy;
- document encryption algorithms;
- key recovery;
- end-to-end encryption;
- email encryption;
- object-storage implementation;
- federation transport protocol;
- federation cryptographic protocol;
- synchronization conflict resolution.

These are specified separately.

---

## 33. Design Direction

The preferred authorization architecture is:

    Self-hosted single-tenant server
      +
    RBAC
      +
    explicit internal project assignment
      +
    explicit customer project access
      +
    Internal / Customer Workspace separation
      +
    server-side authorization
      +
    future Federation Peer trust boundary

A general-purpose ABAC engine is not required for the initial architecture.

The model should remain explicit, auditable and easy to test.