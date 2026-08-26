# GlasHaus Persistence Model

## 1. Purpose

This document defines the approved target relational persistence model for GlasHaus.

It is the source of truth for the domain entities, relationships, historical state, and persistence boundaries that will be implemented using SQLAlchemy and Alembic.

The model is designed to support:

* self-hosted installations
* local identity and authentication
* employment and hierarchy
* explicit application roles
* modular permissions
* individual permission grants and restrictions
* customers and external business relationships
* projects and explicit project access
* internal and customer workspaces
* documents and immutable document versions
* devices and sessions
* audit records
* encryption metadata
* future federation
* future synchronization

This document defines the target architecture.

It does not imply that every entity or capability is already implemented.

---

## 2. Persistence Principles

GlasHaus follows these persistence principles:

1. The local GlasHaus server is the organizational boundary.

2. Normal local records do not require a tenant `organization_id`.

3. Stable identifiers are used for all persistent domain entities.

4. Important domain relationships are represented explicitly.

5. Foreign keys enforce structural relationships wherever practical.

6. Security-sensitive relationships must not be represented only through implicit conventions.

7. Historical state must not be destroyed merely to represent current state.

8. Security-relevant identities and relationships should normally be deactivated rather than physically deleted when historical references are required.

9. Production schema changes are performed through Alembic migrations.

10. Binary content is stored outside the relational database.

11. Encryption metadata may be persisted, but secret production key material is not stored alongside ciphertext.

12. Synchronization metadata remains separate from core domain semantics.

13. Persistence is not an authorization mechanism.

14. Database relationships must never be interpreted as authorization grants by themselves.

---

## 3. Organizational Boundary

A normal GlasHaus installation represents one organization.

The local server is therefore the primary organizational and persistence boundary.

There is no local multi-tenant `organization_id` requirement in the normal deployment model.

Conceptually:

```text
GlasHaus Server
    │
    ├── Users
    ├── Customers
    ├── Projects
    ├── Documents
    ├── Scheduling
    └── Other Business Data
```

All local domain records belong to this server.

Independent GlasHaus servers are separate trust domains.

Future federation between servers must therefore use explicit federation entities rather than treating remote records as local organizational records.

---

## 4. Identifier Model

Persistent domain entities use stable identifiers.

The existing UUIDv7 direction is retained.

Identifiers must:

* be globally unique
* be stable over the lifetime of the entity
* preserve relationships
* survive synchronization
* not depend on database-generated sequential identifiers

Identifiers must not encode authorization state.

A known identifier never grants access to the corresponding resource.

---

## 5. User

`User` is the central human identity object.

Conceptual fields:

```text
User
├── id
├── login_identifier
├── display_name
├── email
├── date_of_birth
├── user_type
├── role
├── active
├── created_at
└── updated_at
```

A User represents one human account that can authenticate to GlasHaus.

Every User has exactly one:

* `user_type`
* `role`

The role represents the user's current functional responsibility.

The role catalogue is controlled by application policy and is not an arbitrary collection of administrator-created roles.

There is no persisted `age` field.

Age is derived from `date_of_birth` and the current evaluation date.

Authentication credentials are modeled separately from the core identity.

---

## 6. User Type

Every User has exactly one user type.

Initial values are:

* `INTERNAL`
* `EXTERNAL`

`INTERNAL` identifies a person belonging to the organization operating the server.

`EXTERNAL` identifies a person who does not belong to that internal workforce.

`EXTERNAL` is intentionally generic.

It must not be replaced by relationship-specific user types such as `CUSTOMER_USER`.

Business relationships are represented separately.

---

## 7. Role

Every User has exactly one role.

Roles describe functional responsibility.

Initial examples include:

* `TECHNICIAN`
* `OFFICE`
* `SITE_SUPERVISOR`
* `MANAGEMENT`
* `CUSTOMER`

Future external roles may include:

* `TAX_ADVISOR`
* `SUPPLIER`
* `PARTNER`

Role assignment must be compatible with the user's `user_type`.

For example:

```text
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
```

An external role must never implicitly provide internal workspace access.

Role definitions and their default permissions are application policy, not arbitrary database configuration.

---

## 8. Employment

`Employment` represents the internal user's employment history and organizational context.

Conceptual fields:

```text
Employment
├── id
├── user_id
├── hierarchy_level
├── employment_status
├── valid_from
├── valid_until
├── created_at
└── updated_at
```

Employment records are only applicable to internal users.

A User may have multiple historical Employment records.

Normally, at most one Employment record is effective for a given user and point in time.

Employment history must preserve previous organizational states.

Changing a user's current hierarchy must therefore not overwrite historical hierarchy information.

The current hierarchy level is derived from the currently effective Employment record.

The current role remains the User's authoritative role.

Historical employment records may preserve the historical hierarchy and employment status that applied during their validity period.

---

## 9. Hierarchy

Hierarchy is separate from role.

The initial hierarchy levels are:

* `APPRENTICE`
* `JUNIOR`
* `STANDARD`
* `SENIOR`
* `SUPERVISOR`
* `MANAGEMENT`

The exact catalogue may evolve independently of the authorization engine.

Hierarchy contributes to the user's baseline authorization but does not define the complete permission set.

Hierarchy effects are evaluated in combination with the user's role.

For example:

```text
TECHNICIAN + APPRENTICE
    → restricted technician capabilities

TECHNICIAN + SENIOR
    → broader technician capabilities

TECHNICIAN + SUPERVISOR
    → additional planning capabilities
```

The same hierarchy level may occur across multiple roles without implying identical permissions.

A hierarchy level must therefore never be interpreted as a globally applicable permission set independent of role.

---

## 10. Permissions

A Permission is an application-defined capability.

The MVP uses the following canonical Permission identifiers:

### Customer

```text
customer.read
customer.write
```

### Project

```text
project.read
project.write
project.coordinate
```

### Purchasing

```text
purchase.create
purchase.grant
```

### Documents

```text
document.read
document.write
document.sign
```

### Scheduling

```text
schedule.view_availability
schedule.view_details
schedule.assignment_write
schedule.assignment_request
schedule.assignment_grant
```

### User and Permission Management

```text
user.manage
permission.manage
```

The complete canonical MVP Permission set is therefore:

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

These identifiers are shared with the authorization model defined in `docs/IDENTITY_AUTHORIZATION.md`.

Persistence must not introduce an independent Permission naming scheme.

Permission identifiers are application policy and must remain consistent across:

* authorization evaluation
* persistence
* tests
* API contracts
* audit records
* documentation

The Permission catalogue is application policy and must remain explicit, reviewable, and testable.

Ordinary administrators must not create arbitrary new Permission types at runtime.

Permission and scope are separate concepts.

For example:

```text
permission = purchase.create
scope = PROJECT:123
```

The Permission identifier must not encode the resource scope.

The persistence layer stores Permission references and authorization data, but the authorization engine remains responsible for evaluating whether a Permission is effective for a particular operation.

---

## 11. Permission Grants and Restrictions

Individual permission changes are persisted explicitly.

Conceptual fields:

```text
PermissionGrant
├── id
├── user_id
├── permission
├── effect
├── scope_type
├── scope_id
├── granted_by_user_id
├── reason
├── valid_from
├── valid_until
├── active
├── created_at
└── updated_at
```

`effect` may be:

* `ALLOW`
* `DENY`

A grant or restriction must be:

* explicit
* scoped
* attributable
* revocable
* optionally time-limited
* auditable where required
* subject to mandatory authorization policy

Possible scope types include:

* `GLOBAL`
* `PROJECT`
* `WORKSPACE`
* `DOCUMENT`
* `USER`
* other explicitly approved resource scopes

Additional scope types require an architectural decision.

The database must not allow persistence of a permission grant to bypass application-level permission-management policy.

A persisted grant is therefore not automatically an effective authorization decision.

### Grant Constraints

Some Permissions may carry additional constraints.

A constraint is not itself a Permission.

For example, purchasing may use a financial purchase limit:

```text
permission = purchase.create
scope = PROJECT:123
purchase_limit = 2000 EUR
```

The `purchase_limit` is therefore a constraint on `purchase.create`, not a separate Permission.

The persistence model must be capable of representing:

```text
purchase_limit = integer value
```

or:

```text
purchase_limit = None
```

where `None` means that no additional purchase limit is imposed by that grant.

The exact representation of monetary values must use a lossless monetary representation and must not use floating-point storage.

Grant constraints must be evaluated by the authorization layer whenever the protected operation is executed.

A principal with `permission.manage` must not be able to persist a grant that exceeds the principal's own delegable authority.

### Delegation Constraints

A principal with `permission.manage` does not automatically have unlimited authority to grant arbitrary Permissions.

A principal may only delegate authority that the principal is itself authorized to delegate.

Delegation must therefore be constrained by:

* the granting principal's own effective authority
* the Permission being delegated
* the target scope
* applicable constraints
* applicable policy restrictions
* any temporal validity of the grant

For example, a principal with:

```text
permission = purchase.create
scope = PROJECT:123
purchase_limit = 2000 EUR
```

must not be able to delegate:

```text
permission = purchase.create
scope = PROJECT:123
purchase_limit = None
```

unless the principal independently possesses sufficient authority to delegate that broader purchasing capability.

Permission administration must never provide an implicit privilege-escalation path.

---

## 12. Customer

`Customer` is a business/domain entity.

Conceptual fields:

```text
Customer
├── id
├── customer_type
├── name
├── contact_metadata
├── active
├── created_at
└── updated_at
```

Initial customer types include:

* `COMPANY`
* `PRIVATE`

A Customer is not a tenant and is not a User.

A Customer may own or be associated with multiple Projects.

---

## 13. External Relationship

An `ExternalRelationship` represents a business relationship between a User and a Customer.

The relationship is separate from the User's identity.

An External User must therefore not contain a direct `customer_id` as its primary mechanism for Customer affiliation.

Conceptually:

```text
User
  │
  └── ExternalRelationship
          │
          └── Customer
```

The model should support:

```text
ExternalRelationship
├── id
├── user_id
├── relationship_type
├── customer_id
├── valid_from
├── valid_until
├── active
├── created_at
├── created_from
└── updated_at
```

The initial relationship types are:

* `OWNER`
* `CONTACT`

A User may have only the relationships explicitly assigned to that identity.

A Customer relationship does not change the User's identity.

An ExternalRelationship must not be interpreted as granting access to all resources of the related Customer.

The relationship establishes a business relationship between the User and the Customer.

Project-specific access is represented separately through `CustomerProjectAccess` and remains subject to authorization policy.

The model therefore remains extensible:

```text
User
  │
  └── EXTERNAL
        │
        ├── Customer Relationship
        ├── Supplier Relationship
        ├── Tax Advisor Relationship
        └── Partner Relationship
```

Future relationship types must not require redefining the core User model.

---

## 14. Project

A Project is a first-class local business resource.

Conceptual fields:

```text
Project
├── id
├── customer_id
├── name
├── status
├── address_metadata
├── created_at
└── updated_at
```

Each Project has exactly one primary Customer.

Project address and other project metadata are protected business information.

Project access is never granted merely because a User knows:

* the project ID
* the project name
* the customer name
* the physical address
* a document ID
* a URL

---

## 15. Internal Project Assignment

Internal project access is represented explicitly.

Conceptual fields:

```text
ProjectAssignment
├── id
├── project_id
├── user_id
├── assignment_context
├── valid_from
├── valid_until
├── active
├── created_at
└── updated_at
```

An internal User without an active ProjectAssignment does not receive project-specific access merely because the User is internal.

Assignments may represent different approved operational contexts.

The exact assignment context is domain data and must not itself bypass permission evaluation.

There is no emergency or convenience access path for unassigned projects.

---

## 16. Customer Project Access

Customer project access is represented explicitly.

Conceptual fields:

```text
CustomerProjectAccess
├── id
├── project_id
├── user_id
├── valid_from
├── valid_until
├── active
├── created_at
└── updated_at
```

The application must additionally verify:

1. the User is active;
2. the User is external;
3. the User has an active Customer relationship;
4. the relationship belongs to the Project's Customer;
5. the access record is active and within its validity period;
6. the requested action is permitted;
7. the requested resource is exposed through the Customer Workspace.

Customer project access therefore does not replace authorization.

It establishes the project relationship that is required for customer-facing access.

CustomerProjectAccess does not replace the User's ExternalRelationship.

A valid customer-facing project authorization therefore requires both:

1. an applicable ExternalRelationship between the User and the Project's Customer; and
2. an active CustomerProjectAccess record for the Project.

Neither relationship alone is sufficient to grant access.

---

## 17. Workspace

Each Project has two primary workspaces.

Conceptual fields:

```text
Workspace
├── id
├── project_id
├── workspace_type
├── created_at
└── updated_at
```

Workspace types are:

* `INTERNAL`
* `CUSTOMER`

Exactly one Internal Workspace and one Customer Workspace exist for each Project.

The Customer Workspace is project-wide.

Workspace type is a security boundary and must participate in authorization evaluation.

A Customer Workspace must never expose Internal Workspace data merely because both belong to the same Project.

---

## 18. Documents

`Document` represents a logical protected file/resource.

Conceptual fields:

```text
Document
├── id
├── project_id
├── workspace_id
├── created_by_user_id
├── filename
├── media_type
├── status
├── sensitivity_class
├── storage_object_id
├── created_at
└── updated_at
```

A Document belongs to exactly one Project and one Workspace.

The workspace must belong to the same Project.

Document metadata is subject to the same authorization boundary as document content.

Document contents are not stored directly in the relational database.

### Document Scope

The MVP defines document Permissions independently from Project scope.

For example:

```text
permission = document.read
scope = PROJECT:123
```

or:

```text
permission = document.sign
scope = DOCUMENT:456
```

The Permission identifier must not encode the Project or Workspace relationship.

---

## 19. Document Versions

Documents may contain immutable versions.

Conceptual fields:

```text
DocumentVersion
├── id
├── document_id
├── version_number
├── content_digest
├── storage_object_id
├── size
├── encryption_version
├── encryption_key_id
├── created_by_user_id
└── created_at
```

Document versions support:

* auditability
* integrity verification
* immutable historical content
* encryption rotation
* synchronization
* controlled restoration

Version records should not be mutated merely to represent a new document state.

A new content version should normally create a new immutable DocumentVersion.

---

## 20. Encryption Metadata

Encryption metadata may be persisted with DocumentVersion or an associated encryption metadata entity.

Possible metadata includes:

* encryption scheme/version
* key identifier
* nonce/IV
* wrapped data-key metadata
* integrity metadata

Secret production key material must not be stored in the same relational database table as encrypted document content metadata.

The exact key hierarchy, key storage, rotation, and recovery model are defined by `docs/CRYPTOGRAPHY.md`.

Persistence must not imply that possessing an encryption key identifier grants authorization to decrypt the associated resource.

---

## 21. Device

`Device` is a separate technical trust object.

Conceptually:

```text
User
  │
  ├── Device
  └── Session
```

A Device may have lifecycle states such as:

* `PENDING`
* `ACTIVE`
* `REVOKED`

A Device may be revoked independently of its User.

Device registration is a security control and does not replace application authentication or authorization.

Device state may contribute to security policy for sensitive operations.

---

## 22. Session

A Session represents an authenticated interaction.

Conceptual fields:

```text
Session
├── id
├── user_id
├── device_id (where applicable)
├── created_at
├── expires_at
├── revoked_at
└── authentication_metadata
```

Session credentials must not be stored in plaintext where a secure hashed/token-reference design is applicable.

A valid Session establishes authentication context.

It does not by itself grant authorization to any resource.

---

## 23. Audit Event

Security-sensitive and business-critical actions require audit records where defined by the security architecture.

Conceptual fields:

```text
AuditEvent
├── id
├── actor_user_id
├── action
├── resource_type
├── resource_id
├── result
├── timestamp
├── request_correlation_id
└── metadata
```

Audit records should identify the relevant actor, target resource, action, result, and correlation context where available.

Audit records must avoid unnecessary sensitive payloads.

Audit data is itself protected information and requires appropriate retention and access controls.

---

## 24. Federation Peer

Future server-to-server trust is represented separately from local identity.

Conceptual fields:

```text
FederationPeer
├── id
├── remote_server_id
├── display_name
├── trust_state
├── public_key
├── created_at
└── revoked_at
```

Federation peers are not Users.

A remote principal is not automatically created as a local User merely because a federation relationship exists.

Federation requires explicit authentication, trust, authorization, revocation, and data-sharing semantics.

The exact federation model is defined separately before implementation.

---

## 25. Synchronization Metadata

Synchronization metadata remains separate from domain semantics.

A device synchronization state may be represented as:

```text
SyncState
├── device_id
├── cursor
├── state
├── created_at
└── updated_at
```

Future synchronization infrastructure may include:

```text
OutboxOperation
ChangeFeedEntry
Tombstone
```

These entities are introduced only when a concrete offline workflow requires them.

Synchronization metadata must not become a second authorization model.

Every synchronized resource remains subject to the same authorization semantics as its server-side counterpart.

---

## 26. Purchasing Scope

Purchasing is modeled as a separate capability domain.

The canonical purchasing Permissions are:

```text
purchase.create
purchase.grant
```

Purchasing Permissions are scoped independently from the Permission identifier.

A project purchase may therefore be authorized as:

```text
permission = purchase.create
scope = PROJECT:123
```

The architecture must also support purchases that are not associated with a Customer Project.

Such purchases represent organizational or overhead spending and must not require an artificial Project such as `Office` or `Warehouse`.

A future Purchase domain model may therefore allow:

```text
Purchase
├── id
├── project_id
├── organizational_scope
├── created_by_user_id
├── amount
└── ...
```

For a project purchase:

```text
project_id = Project.id
```

For a non-project purchase:

```text
project_id = NULL
```

A `NULL` project reference represents a purchase that is not attributable to a Customer Project.

The exact organizational scope for non-project purchases will be defined when the Purchase domain is implemented.

Project-scoped purchasing must remain possible independently of organization-wide purchasing.

A User may therefore be authorized to create purchases for a specific Project without automatically receiving authority to create general organizational purchases.

A future Purchase implementation must also preserve the distinction between:

* the Permission `purchase.create`
* the purchase scope
* the purchase amount
* any applicable `purchase_limit`
* the authority of the principal creating or granting the purchase permission

An artificial Project such as `Office` or `Warehouse` must not be introduced solely to represent organizational overhead purchases.

---

## 27. Principal Relationships

The principal persistence relationships are:

```text
User
  ├── Employment
  ├── ExternalRelationship
  ├── Device
  ├── Session
  ├── PermissionGrant
  ├── ProjectAssignment
  └── CustomerProjectAccess

Customer
  └── Project

Project
  ├── ProjectAssignment
  ├── CustomerProjectAccess
  ├── Workspace
  └── Document

Workspace
  └── Document

Document
  └── DocumentVersion
```

The exact cardinality and database constraints must be enforced through schema design where practical.

---

## 28. Referential Integrity

Important domain relationships must use database foreign keys.

Examples include:

* Employment → User
* ExternalRelationship → User
* ExternalRelationship → Customer where applicable
* Project → Customer
* ProjectAssignment → Project/User
* CustomerProjectAccess → Project/User
* Workspace → Project
* Document → Project/Workspace
* DocumentVersion → Document
* Device → User
* Session → User/Device where applicable
* PermissionGrant → User
* PermissionGrant → granting User where applicable
* AuditEvent → actor User where applicable

Application validation complements database constraints but does not replace them.

Important cross-entity invariants that cannot be expressed directly through foreign keys must be enforced at the application/domain layer and tested explicitly.

---

## 29. Temporal and Historical State

Entities whose state affects security or business history should support temporal validity where required.

Examples include:

* Employment
* ExternalRelationship
* ProjectAssignment
* CustomerProjectAccess
* PermissionGrant

Temporal records should use explicit validity fields such as:

* `valid_from`
* `valid_until`

Current state must be derived according to deterministic rules.

Expired records must not contribute to current authorization.

Historical records must remain available when required for auditability and historical reconstruction.

---

## 30. Deactivation and Deletion

Security-relevant identities and resources should normally be deactivated rather than physically deleted when historical references are required.

Examples include:

* User
* Customer
* Project
* Device
* PermissionGrant
* ExternalRelationship
* ProjectAssignment
* CustomerProjectAccess

Physical deletion is permitted only when:

* retention policy allows it
* audit requirements are satisfied
* referential integrity remains valid
* synchronization implications are understood
* legal and business requirements are satisfied

Deactivation must not silently remove historical evidence required for security or audit.

---

## 31. Persistence and Authorization

Persistence is not authorization.

A database relationship does not itself grant access.

The application must evaluate authorization before disclosing protected resources.

Conceptually:

```text
authenticate
    ↓
establish principal
    ↓
authorize requested action and scope
    ↓
load permitted resource
    ↓
decrypt where required
    ↓
return permitted representation
```

For sensitive resources, unauthorized records should be excluded as early as practical.

However, repository-level filtering is not itself the complete authorization model.

The authoritative authorization decision remains a domain/application responsibility.

---

## 32. Persistence and Partial Visibility

Persistence must support authorization decisions that expose only a permitted representation of a resource.

For example:

```text
schedule.view_availability
```

may permit:

```text
Technician B
Tuesday: available
```

without permitting:

```text
Customer
Project Address
Appointment Details
Internal Notes
```

Sensitive fields must not be loaded into or returned through an API merely because the caller can access the parent entity.

Queries and serialization should therefore support data minimization.

---

## 33. Persistence and Search

Search must be authorization-aware.

Unauthorized resources must not be discoverable merely through search.

A search query must not return information such as:

```text
Project A — access denied
```

to a user who is not authorized to discover Project A.

Unauthorized resources should normally be omitted entirely.

Sensitive encrypted fields may not support ordinary:

* equality search
* sorting
* range queries
* full-text search

without additional design.

Any searchable representation of sensitive data must be explicitly designed.

Search indexes must not become accidental plaintext copies of encrypted data.

---

## 34. Persistence and Binary Storage

Binary content is stored outside the relational database.

The relational database stores logical resource metadata and references to storage objects.

The storage object identifier must not itself be sufficient to retrieve content.

Binary retrieval must pass through the same authorization boundary as relational resource access.

Conceptually:

```text
Request
  ↓
Authentication
  ↓
Authorization
  ↓
Document metadata
  ↓
Storage object retrieval
  ↓
Decryption where required
  ↓
Authorized content
```

The object storage layer must never become an authorization bypass.

---

## 35. Persistence and Encryption

Encryption and authorization are separate controls.

Persistence may store:

* ciphertext metadata
* key identifiers
* encryption versions
* integrity metadata
* storage references

Persistence must not store secret production key material alongside ciphertext.

Authorization determines whether the principal may access the resource.

Cryptography determines how stored or transmitted data is protected against additional threats.

The cryptographic architecture is defined in `docs/CRYPTOGRAPHY.md`.

---

## 36. Migration Rules

All production schema changes use Alembic.

Every migration must:

* be deterministic
* preserve required data
* maintain referential integrity
* be reviewed
* have tests where behavior is non-trivial
* document irreversible operations
* avoid accidental destructive changes

The application must not rely on implicit schema creation during normal production startup.

Database schema state must be reproducible from the migration history.

---

## 37. Implementation Order

The target persistence model should be implemented in a dependency-aware sequence:

1. User
2. Employment
3. Customer
4. Project
5. Project Assignment
6. External Relationship
7. Customer Project Access
8. Workspace
9. Permission persistence
10. Device and Session
11. Audit
12. Document metadata
13. Document versions
14. Encryption metadata
15. Federation metadata
16. Synchronization metadata when required by the first concrete offline workflow

The implementation order does not change the architectural relationships defined by this document.

Purchasing is currently defined as an authorization and domain-design concern.

The concrete `Purchase` persistence model is intentionally deferred until the purchasing workflow is implemented.

---

## 38. Persistence Invariants

The following persistence invariants must remain true unless this architecture is explicitly changed:

1. The local server is the normal organizational boundary.

2. Local domain records do not require a tenant `organization_id`.

3. Every User has exactly one User Type.

4. Every User has exactly one current Role.

5. Age is derived from `date_of_birth`.

6. Employment history does not overwrite historical state.

7. Current hierarchy is derived from the effective Employment context for internal users.

8. `EXTERNAL` is a generic User Type.

9. Customer is a business entity, not a User Type.

10. External business relationships are persisted separately from User identity.

11. Project access is represented explicitly.

12. Internal project access requires an applicable ProjectAssignment.

13. Customer project access requires both the applicable Customer relationship and explicit project access.

14. Workspace type is a security boundary.

15. Internal and Customer Workspaces remain separate.

16. Documents belong to a Project and Workspace.

17. Document versions are immutable historical resources.

18. Permission grants and restrictions are explicit and scoped.

19. Persisted permission grants do not bypass authorization policy.

20. Permission identifiers are canonical and shared with the authorization model.

21. Permission scope is represented separately from the Permission identifier.

22. Purchasing limits are constraints on purchasing authority, not separate Permissions.

23. Project-scoped purchasing does not imply organization-wide purchasing authority.

24. Devices can be revoked independently of Users.

25. Sessions establish authentication context but do not grant authorization.

26. Audit data is protected information.

27. Federation peers are not local Users.

28. Synchronization metadata does not create a second authorization model.

29. Binary content is stored outside the relational database.

30. Secret production key material is not stored alongside ciphertext.

31. Authorization is not delegated to persistence relationships.

32. Known resource identifiers never imply access.

33. Production schema changes are managed through Alembic.

---

## 39. Related Documents

This document must be read together with:

* `docs/ARCHITECTURE.md`
* `docs/IDENTITY_AUTHORIZATION.md`
* `docs/SECURITY.md`
* `docs/CRYPTOGRAPHY.md`
* `docs/SYNC.md`
* `docs/TESTING.md`
* `docs/Roadmap.md`

`docs/IDENTITY_AUTHORIZATION.md` defines authorization semantics.

`docs/PERSISTENCE_MODEL.md` defines how those domain concepts are represented persistently.

`docs/SECURITY.md` defines the security controls and threat model.

`docs/CRYPTOGRAPHY.md` defines cryptographic mechanisms and key management.

`docs/SYNC.md` defines synchronization semantics.

The implementation must not silently diverge from these documents.

If a conflict between implementation and approved architecture is discovered:

1. stop and identify the conflicting assumption;
2. determine whether the implementation or architecture is incorrect;
3. update the authoritative documentation if the target architecture changes;
4. only then continue implementation.

The goal is to maintain one coherent target architecture rather than parallel contradictory designs.
