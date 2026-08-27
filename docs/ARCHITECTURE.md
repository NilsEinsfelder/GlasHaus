# GlasHaus Architecture

## 1. Purpose

This document defines the approved target architecture of GlasHaus.

It describes:

- the system boundaries
- the deployment and trust model
- the major application layers
- client responsibilities
- domain and persistence boundaries
- workspace boundaries
- security boundaries
- offline and synchronization boundaries
- future federation boundaries
- architectural invariants

This document describes the intended architecture, not the current implementation status.

A feature described here may therefore be approved as part of the target architecture without being implemented yet.

Detailed rules for individual concerns are defined in the specialized documents:

- `docs/IDENTITY_AUTHORIZATION.md`
- `docs/PERSISTENCE_MODEL.md`
- `docs/SECURITY.md`
- `docs/CRYPTOGRAPHY.md`
- `docs/SYNC.md`
- `docs/TESTING.md`

If documents conflict, implementation must stop until the conflict is resolved.

---

## 2. Architectural Goals

GlasHaus is an open-source, self-hosted application for businesses.

The primary architectural goals are:

- local ownership of business data
- operation on infrastructure controlled by the customer organization
- strong separation between internal and external access
- explicit server-side authorization
- secure handling of sensitive business information
- reliable durable persistence
- controlled offline capabilities where required
- understandable and maintainable open-source architecture
- extensibility without unnecessary infrastructure
- future interoperability between independently operated GlasHaus servers

Security boundaries must remain explicit.

They must not depend on undocumented framework behavior, client-side assumptions, or network location alone.

The architecture should support future capabilities without requiring speculative infrastructure before those capabilities are needed.

---

## 3. Deployment Model

A normal GlasHaus installation is operated as one self-contained server by one business organization.

Conceptually:

    GlasHaus Installation
    │
    ├── Internal Users
    ├── External Users
    ├── Customers
    ├── Projects
    ├── Documents
    ├── Scheduling
    └── Other Business Data

The GlasHaus server is therefore the primary organizational boundary.

A local `organization_id` tenant layer is not required for the normal deployment model.

Data stored by a GlasHaus installation belongs to the organization operating that installation.

Independent GlasHaus installations are separate trust domains.

A future architectural decision may introduce a different tenancy model, but such a change must be explicit and must not be introduced implicitly through persistence implementation.

---

## 4. Trust Domains

Each independently operated GlasHaus installation is a separate trust domain.

For example:

    Company A
        │
        └── GlasHaus Server A

    Company B
        │
        └── GlasHaus Server B

The servers must not implicitly trust each other merely because they run the same software.

Future communication between independent installations is therefore federation between separate trust domains.

Federation must establish explicit:

- peer identity
- trust
- authentication
- authorization
- data-sharing scope
- revocation
- auditing
- failure behavior

Federation must not weaken the local security boundary.

A federated request must never become an implicit local authorization grant.

---

## 5. System Architecture

GlasHaus is a modular monolith.

The initial system should remain one deployable backend rather than being split into independent microservices.

Logical modules must nevertheless have clear boundaries.

The conceptual architecture is:

    Client
      │
      ▼
    API / Transport
      │
      ▼
    Application Services
      │
      ▼
    Domain Logic
      │
      ├── Identity
      ├── Authorization
      ├── Customers
      ├── Projects
      ├── Documents
      ├── Scheduling
      ├── Other Business Domains
      │
      ▼
    Infrastructure
      │
      ├── Persistence
      ├── Object Storage
      ├── Synchronization
      ├── Security
      └── Cryptography
      │
      ▼
    External Systems / Storage

The exact module structure may evolve.

The dependency direction should remain explicit:

    Transport
        ↓
    Application
        ↓
    Domain
        ↓
    Infrastructure

Domain logic must not depend on a specific persistence implementation merely because that implementation is currently used.

A module boundary should represent a meaningful domain or technical boundary rather than merely additional directory structure.

---

## 6. Backend Responsibilities

The backend is the authoritative application boundary.

It is responsible for:

- authentication
- authorization
- request validation
- business rules
- persistence
- security-sensitive operations
- audit-relevant actions
- controlled access to binary data
- synchronization
- future federation

The backend must independently validate all security-sensitive operations.

The client is not a trusted authorization authority.

Client applications may improve usability by hiding unavailable actions, but such behavior is never sufficient to enforce access control.

The server must independently validate:

- authenticated identity
- authorization
- resource access
- synchronization operations
- entity versions
- business-critical state transitions
- financial or otherwise sensitive operations
- document state
- signatures where applicable

---

## 7. Client Architecture

GlasHaus may provide multiple client experiences while sharing the same backend.

The clients have different operational requirements but share the same server-side security boundary.

### 7.1 Browser Client

The browser client is primarily online.

It should not be treated as a durable source of authoritative business state.

The browser may cache data for usability, but server-side persistence remains authoritative unless an explicitly defined offline workflow applies.

### 7.2 Field / Mobile Client

Selected field workflows may support offline operation.

An offline-capable client may require:

- local persistent data
- locally available assets
- an outbound operation queue
- synchronization state
- retry handling
- conflict handling

Offline capability is not assumed for every entity or workflow.

An offline client must not silently discard user work.

Conceptually, locally managed operations may transition through states such as:

    locally saved
        ↓
    pending synchronization
        ↓
    synchronized

Failure states may include:

    retryable failure
    conflict
    rejected

The exact synchronization semantics are defined in `docs/SYNC.md`.

Offline state is never an independent authorization authority.

---

## 8. Identity Model

`User` is the central human identity object.

Every user has exactly one user type:

- `INTERNAL`
- `EXTERNAL`

Every user has exactly one role.

The role describes the user's functional responsibility.

An applicable hierarchy level describes the user's position within the internal employment structure.

Role and hierarchy are separate concepts.

For example:

    Internal User
    │
    ├── Role: Technician
    └── Hierarchy: Apprentice

or:

    Internal User
    │
    ├── Role: Office
    └── Hierarchy: Apprentice

The same hierarchy level therefore does not imply identical permissions across different roles.

The complete identity and authorization model is defined in:

`docs/IDENTITY_AUTHORIZATION.md`

---

## 9. External Users and Business Relationships

`EXTERNAL` is a general user type.

A customer relationship is not itself a user type.

Business relationships are represented separately from human identity.

Conceptually:

    User
    └── External
          │
          └── Business Relationship
                │
                └── Customer
                      │
                      └── Projects

Multiple external users may belong to the same Customer.

For example:

    Customer: Example General Contractor
        │
        ├── External User: Project Manager
        ├── External User: Site Manager
        └── External User: Accounting Contact

These users retain separate identities and authorization decisions even when they belong to the same customer.

The same separation should be used for future relationships such as:

- suppliers
- tax advisors
- partners
- other external organizations

External relationships may receive dedicated workspaces in the future.

---

## 10. Workspace Boundaries

Workspaces are security boundaries, not merely UI concepts.

There are two different Pathways:

                    PROJECT
                       │
          ┌────────────┴────────────┐
          │                         │
          ▼                         ▼
 ProjectAssignment       CustomerProjectAccess
          │                         │
          ▼                         ▼
 INTERNAL USER              EXTERNAL USER
          │                         │
          │                         │
          ▼                         ▼
  INTERNAL / CUSTOMER          CUSTOMER ONLY
      Workspace                  Workspace
          │                         │
          └──────────┬──────────────┘
                     ▼
               AUTHORIZATION
                     │
                     ▼
                Permission
                     │
                     ▼
              ALLOW / DENY


### 10.1 Internal Workspace

The Internal Workspace is available to authorized internal users.

It may contain:

- internal project information
- internal scheduling
- internal notes
- operational information
- customer information
- documents not intended for external users
- internal administrative information

Access remains subject to authorization.

### 10.2 Customer Workspace

The Customer Workspace is available to authorized external customer users.

It exposes only information intentionally made available to the customer.

Customer access is constrained by:

- customer relationship
- project access
- applicable permissions
- resource scope
- workspace policy

The Customer Workspace must never expose internal-only information merely because a customer is associated with a project.

Customers must never gain access to the Internal Workspace.

### 10.3 Future External Workspaces

Future external relationships may receive dedicated workspaces.

Examples include:

- Supplier Workspace
- Tax Advisor Workspace
- Partner Workspace

These remain access surfaces within the same GlasHaus installation.

They are not independent trust domains.

---

## 11. Projects and Resource Ownership

Projects are first-class business resources.

A project may be associated with:

- a Customer
- internal users
- external users through business relationships
- documents
- scheduling information
- other project resources

Project access is explicitly assigned or otherwise established by the authorization model.

Internal users must not automatically receive access to every project merely because they belong to the organization.

For internal users, project assignment is therefore an important authorization boundary.

External customer access is derived from the customer's relationship with the project and the user's applicable permissions.

Knowing or guessing a project identifier, address, or other resource identifier must not grant access.

There is no emergency or convenience path that bypasses normal project authorization.

---

## 12. Authorization Boundary

Authorization is a server-side security decision.

A permission does not automatically imply unrestricted access to every instance of a resource.

Conceptually:

    Authenticated Identity
            │
            ▼
    Effective Permissions
            │
            ▼
    Resource
            │
            ▼
    Scope / Policy
            │
            ▼
    Allowed or Denied Action

Authorization may depend on:

- identity
- user type
- role
- hierarchy
- explicit permission grants
- resource ownership
- project assignment
- customer relationship
- workspace
- security classification
- action-specific policy
- other explicitly defined security constraints

Authorization is default-deny.

Explicit permission grants may add access only where mandatory security constraints permit the action.

The detailed authorization semantics are defined in:

`docs/IDENTITY_AUTHORIZATION.md`

---

## 13. Resource and Scope Model

Authorization is evaluated against a concrete resource and its applicable scope.

A permission alone is therefore not necessarily sufficient to access a resource.

Potential scopes include:

- global
- project
- customer
- workspace
- user
- document
- document category
- security classification
- other explicitly defined resource scopes

Scopes must be meaningful within the domain.

Do not introduce generic scope mechanisms merely because they appear reusable.

A scope must not silently broaden access beyond the intended security boundary.

---

## 14. Persistence Boundary

Persistence is a separate architectural concern from domain and authorization logic.

The domain and application layers express business concepts and rules.

The persistence layer maps those concepts to durable storage.

The database is responsible for durable storage and should enforce important structural invariants where practical.

Production schema evolution is managed through Alembic migrations.

The application must not depend on implicit schema creation during normal production startup.

`Base.metadata.create_all()` is not a production migration mechanism.

The detailed persistence architecture is defined in:

`docs/PERSISTENCE_MODEL.md`

The intended development order is:

1. define the domain model
2. define persistence semantics
3. determine which entities require offline capability
4. define synchronization semantics for those entities
5. implement synchronization

Persistence must not be designed around synchronization requirements that have not yet been established.

---

## 15. Database and Object Storage

PostgreSQL is the authoritative store for server-side structured application data.

Binary content may require separate object storage.

Conceptually:

    Application
       │
       ├── Structured Data ──→ PostgreSQL
       │
       └── Binary Data ──────→ Object Storage

The exact object-storage implementation may evolve.

Binary data remains a protected application resource regardless of where the bytes are physically stored.

Storage-level access control must not become the primary application authorization boundary.

A user who can identify or guess a file identifier must not automatically be able to retrieve its contents.

Access to binary content must pass through the appropriate authorization boundary.

Persistence details are defined in `docs/PERSISTENCE_MODEL.md`.

Storage encryption and key-management requirements are defined in `docs/CRYPTOGRAPHY.md`.

---

## 16. Domain, Persistence, and Synchronization Separation

Domain concepts must be defined independently of persistence implementation.

Persistence provides durable representation of domain state.

Synchronization provides controlled replication of selected state between server and offline-capable clients.

These are separate concerns.

The architecture therefore follows:

    Domain
       ↓
    Persistence
       ↓
    Offline Capability Decision
       ↓
    Synchronization Semantics
       ↓
    Synchronization Implementation

An entity must not become synchronizable merely because it exists in the database.

Before an entity becomes offline-capable, its synchronization behavior must be explicitly defined.

---

## 17. Entity Identity

Persistent entities require stable identities.

Entities that may participate in offline workflows should use identifiers suitable for local creation and later synchronization.

UUIDv7 is the preferred identifier strategy where its ordering and distributed-generation properties are beneficial.

Identifier choice must remain consistent with the persistence and synchronization requirements of the entity.

Identifiers are not authorization credentials.

Knowledge of an identifier must never be treated as proof of authorization.

---

## 18. File and Binary Data

Business documents and other binary data are first-class protected resources.

Binary content may have different lifecycle and storage requirements from relational application data.

The architecture therefore separates:

- metadata
- authorization
- lifecycle
- binary content storage

A document record may exist independently from the physical storage object.

Deleting or replacing a binary object must follow the domain lifecycle and persistence rules.

Binary access must be authorized independently of whether a client knows:

- an object key
- a document identifier
- a URL
- a storage location

Temporary or indirect access mechanisms must not bypass application authorization.

---

## 19. Security Classification

Not all business data has the same sensitivity.

GlasHaus therefore supports security classification as an architectural concept.

Classification may influence:

- authorization
- visibility
- encryption
- audit requirements
- export behavior
- synchronization
- external sharing

Security classification is an additional policy input.

It is not a substitute for authorization.

The security architecture defines the classification model and its interaction with other security controls.

See:

`docs/SECURITY.md`

---

## 20. Authentication Boundary

Authentication establishes the identity associated with a request.

Authorization determines whether that identity may perform a requested action.

These concerns must remain separate.

Conceptually:

    Request
      │
      ▼
    Authentication
      │
      ▼
    Authenticated Identity
      │
      ▼
    Authorization
      │
      ▼
    Resource Access

Authentication mechanisms may evolve.

Business authorization must therefore not be coupled directly to one particular authentication mechanism.

Detailed requirements are defined in:

- `docs/IDENTITY_AUTHORIZATION.md`
- `docs/SECURITY.md`

---

## 21. Device and Network Trust

Internal users may primarily access GlasHaus through registered or otherwise trusted devices and through the organization's internal network or VPN.

Device registration and network location may form part of the security context.

They must never replace application-level authentication and authorization.

A trusted network must not imply unrestricted application access.

The architecture must support explicit browser-based authentication when legitimate workflows require access outside the normal workstation environment.

For example, an internal employee may need to submit a vacation request or sickness notification from a browser without access to their normal work device.

Such workflows must use normal authentication and authorization.

There is no emergency bypass based solely on the user's organizational affiliation.

---

## 22. Offline Operation

Offline operation is an explicit capability of selected workflows.

It must not be assumed for every entity.

Before an entity becomes offline-capable, the architecture must define:

- identity
- ownership
- authorization scope
- lifecycle
- versioning
- conflict behavior
- deletion semantics
- retention
- binary content handling
- synchronization state

Offline clients may create or modify local state before synchronization.

The server remains authoritative for security-sensitive decisions and for conflicts that cannot safely be resolved locally.

Synchronization must never silently discard user work.

Detailed synchronization semantics are defined in:

`docs/SYNC.md`

---

## 23. Synchronization

Synchronization is controlled replication between explicitly defined endpoints.

It is not a second application architecture.

It must preserve the same:

- identity boundaries
- authorization boundaries
- resource ownership
- lifecycle rules
- security policies

A synchronized entity requires explicit semantics for:

- creation
- update
- deletion
- versioning
- retries
- conflict resolution
- rejection
- authorization changes
- retention
- binary transfer

The synchronization mechanism must not silently overwrite newer server state with stale client state.

The server must independently validate synchronization requests.

Detailed synchronization architecture is defined in:

`docs/SYNC.md`

---

## 24. Federation

Future GlasHaus versions may allow independently operated servers to communicate.

Federation is not local multi-tenancy.

Each server remains authoritative for its own:

- identities
- authorization
- data
- security policies
- audit
- cryptographic keys

A federated request must contain sufficient authenticated context for the receiving server to determine what the remote party is permitted to access.

Federation requires explicit:

- peer identity
- trust establishment
- authentication
- authorization
- data-sharing scope
- revocation
- auditability
- failure semantics

Federation must not be implemented until its identity, authorization, cryptographic, and data-sharing semantics are documented.

---

## 25. Security Architecture

Security is cross-cutting and applies to every architectural layer.

The principal security path is:

    User / Peer
        │
        ▼
    Client / Transport
        │
        ▼
    Authentication
        │
        ▼
    Authorization
        │
        ▼
    Application / Domain
        │
        ▼
    Persistence / Object Storage

Additional trust boundaries exist around:

- external users
- registered devices
- network/VPN access
- backups
- offline clients
- synchronization
- external integrations
- federation peers

Security-sensitive failures must fail closed.

Examples include:

- unknown identity
- invalid authentication
- missing permission
- invalid project assignment
- invalid resource scope
- invalid synchronization state
- invalid federation trust
- missing security context

An operational error must not accidentally become successful access.

Detailed security requirements are defined in:

`docs/SECURITY.md`

Cryptographic mechanisms are defined separately in:

`docs/CRYPTOGRAPHY.md`

---

## 26. Auditability

Security-sensitive actions should be auditable where required by the security architecture.

Examples include:

- authentication events
- permission changes
- sensitive data access
- external sharing
- administrative actions
- security configuration changes
- cryptographic key-management events
- synchronization security events
- federation trust changes

Audit data is itself protected information.

It therefore requires appropriate:

- access control
- retention
- integrity protection
- lifecycle management

Detailed audit requirements belong to:

`docs/SECURITY.md`

---

## 27. Modularity Principles

The modular monolith should allow major domain areas to evolve independently within one deployment.

Modules should:

- expose explicit interfaces
- minimize unnecessary coupling
- avoid circular dependencies
- keep authoritative security decisions close to their authoritative implementation
- avoid leaking persistence implementation details into unrelated domains
- avoid depending on framework-specific behavior across domain boundaries

Shared infrastructure should be introduced only where the shared behavior is genuinely architectural.

Do not create generic abstractions solely to anticipate hypothetical future requirements.

---

## 28. Architectural Invariants

The following invariants apply across the architecture.

### Deployment

- One normal GlasHaus installation represents one organization's primary application boundary.
- Local multi-tenancy is not assumed.
- Independent installations are separate trust domains.

### Identity

- A human user has exactly one user type.
- A human user has exactly one role.
- Internal hierarchy is separate from functional role.
- Business relationships are separate from human identity.

### Authorization

- Authorization is server-side.
- Authorization is default-deny.
- Client-side access decisions are never authoritative.
- Resource identifiers do not grant access.
- Project assignment and external business relationships are explicit authorization boundaries.
- Workspace boundaries are security boundaries.
- No emergency or convenience path bypasses authorization.

### Persistence

- PostgreSQL is authoritative for server-side structured application state.
- Production schema changes use migrations.
- Persistence does not imply offline capability.
- Domain logic must not depend on implicit database schema creation.

### Offline and Synchronization

- Offline capability is explicit per workflow/entity.
- Synchronization does not create a second authorization model.
- Synchronization must not silently discard user work.
- The server independently validates synchronized state.

### Security

- Authentication and authorization remain separate.
- Trusted networks and devices do not replace application authorization.
- Binary storage must not bypass authorization.
- Security-sensitive failures fail closed.
- Cryptographic guarantees must be explicitly defined.

### Federation

- Federation is not multi-tenancy.
- Federation requires explicit trust.
- A remote server is not implicitly trusted.
- Federation must not weaken local authorization.

---

## 29. Architectural Evolution

The architecture is intentionally designed to support future capabilities without requiring them in the initial implementation.

Known future directions include:

- additional external relationships
- additional external workspaces
- richer authorization policies
- encrypted stored content
- stronger device trust
- offline synchronization
- additional storage backends
- server-to-server federation
- external integrations

Future functionality must be introduced through explicit architectural decisions.

Do not implement speculative infrastructure merely to accommodate a possible future requirement.

At the same time, approved security, trust, domain, and persistence boundaries must not be designed away through shortcuts in the initial implementation.

When an architectural assumption changes, the relevant documentation must be updated before or together with the implementation change.

---

## 30. Implementation Status

This document defines the approved target architecture.

It does not claim that every described component is currently implemented.

Implementation status is tracked by:

- the repository
- automated tests
- migrations
- the roadmap
- implementation-specific documentation where necessary

When implementation diverges from the approved architecture:

1. determine whether the implementation or architecture is incorrect;
2. if the architecture is still correct, change the implementation;
3. if the architecture has changed, update the relevant documentation;
4. do not silently maintain two contradictory designs.

The target architecture is the reference against which implementation changes are reviewed.

---

## 31. Architectural Decision Rule

Every significant new feature should be evaluated against:

1. identity boundaries
2. authorization boundaries
3. workspace boundaries
4. resource ownership
5. persistence boundaries
6. security classification
7. encryption requirements
8. offline requirements
9. synchronization semantics
10. federation requirements
11. audit requirements
12. operational complexity

Before implementation, the interaction of the feature with these boundaries must be understood.

Security-sensitive ambiguity must be resolved before implementation.

New infrastructure should be introduced only when the corresponding architectural requirement is established.

---

## 32. Related Documents

The following documents provide detailed architecture for individual concerns:

- `docs/IDENTITY_AUTHORIZATION.md` — identity, roles, hierarchy, permissions, scopes and workspace authorization
- `docs/PERSISTENCE_MODEL.md` — domain persistence and database model
- `docs/SECURITY.md` — threat model, security boundaries and security controls
- `docs/CRYPTOGRAPHY.md` — encryption, key management and cryptographic architecture
- `docs/SYNC.md` — offline synchronization
- `docs/TESTING.md` — testing strategy and verification requirements
- `docs/Roadmap.md` — planned implementation sequence
- `docs/AI_RULES.md` — AI-assisted development and engineering rules