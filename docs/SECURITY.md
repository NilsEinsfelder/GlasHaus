# GlasHaus Security Architecture

## 1. Purpose

This document defines the security architecture of GlasHaus.

Security is a system-wide property spanning:

- identity
- authentication
- authorization
- workspace isolation
- project access
- device trust
- data protection
- encryption
- auditability
- offline operation
- synchronization
- backups
- operations
- future federation

This document defines the security boundaries, security goals, threat model, mandatory controls, and security invariants of the system.

Detailed domain rules are defined in the specialized architecture documents:

- `docs/IDENTITY_AUTHORIZATION.md`
- `docs/PERSISTENCE_MODEL.md`
- `docs/CRYPTOGRAPHY.md`
- `docs/SYNC.md`
- `docs/TESTING.md`

This document does not claim that every security control is already implemented.

It defines the approved target security architecture.

---

## 2. Security Principles

GlasHaus follows these principles:

1. Security decisions are enforced server-side.
2. The client is never the final authority for authorization.
3. Authorization is default-deny.
4. Authentication and authorization are separate concerns.
5. Trust boundaries are explicit.
6. Least privilege is the default.
7. Access to resources is evaluated together with resource scope.
8. Internal and external workspaces are separate security boundaries.
9. Project access is explicit.
10. External relationships do not automatically imply internal access.
11. Sensitive information is minimized at every boundary.
12. Encryption and authorization provide separate security controls.
13. Security-sensitive actions are auditable where required.
14. Revocation must have a defined authoritative point.
15. Offline operation must have bounded trust and lifetime.
16. Security-sensitive configuration must not create authorization bypasses.
17. Future federation must preserve independent server trust domains.
18. Security failures must fail closed.

---

## 3. Security Boundary of a GlasHaus Installation

A normal GlasHaus installation represents one organization's local system.

The GlasHaus server is therefore the primary local security boundary.

Conceptually:

    GlasHaus Server
         │
         ├── Internal Users
         ├── External Users
         ├── Customers
         ├── Projects
         ├── Documents
         ├── Devices
         └── Business Data

Clients are untrusted.

A browser, mobile client, desktop client, or other client application may assist with usability and local enforcement, but it must never be treated as the authoritative security boundary.

The server must independently authenticate requests and evaluate authorization.

---

## 4. Trust Domains

Each independently operated GlasHaus server is a separate trust domain.

For example:

    Organization A
         │
         └── GlasHaus Server A

    Organization B
         │
         └── GlasHaus Server B

The two servers must not implicitly trust one another.

Future server-to-server communication therefore creates an explicit federation trust boundary.

Federation must establish and validate:

- remote server identity
- remote principal identity
- trust relationship
- authentication context
- requested action
- resource scope
- local authorization
- revocation state
- audit context

A remote authorization decision must never automatically become a local authorization decision.

The receiving server remains authoritative over its own resources.

---

## 5. Security Goals

GlasHaus protects, among other things:

- personal data
- customer data
- project information
- project addresses
- documents
- photographs
- financial information
- credentials
- sessions
- authorization state
- synchronization state
- device state
- cryptographic material
- backups

The primary security goals are:

1. confidentiality
2. integrity
3. availability
4. accountability
5. least privilege
6. controlled revocation

---

## 6. Authentication

Authentication establishes the identity and security context of a request.

Authentication is distinct from authorization.

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

The authentication architecture must define:

- credential handling
- password hashing where passwords are used
- session creation
- session expiration
- session revocation
- device registration
- device revocation
- stronger authentication mechanisms such as 2FA where required
- recovery procedures
- logout
- suspicious-session handling

Passwords must never be stored in reversible form.

Authentication credentials must be protected independently from the core `User` identity.

Authentication mechanisms may evolve without changing the fundamental authorization model.

---

## 7. Authorization

Authorization determines whether an authenticated principal may perform an action on a resource in a specific context.

Authorization is always enforced server-side.

The server evaluates relevant security context including:

- authenticated principal
- account state
- user type
- role
- hierarchy
- effective permissions
- resource scope
- workspace
- project assignment
- customer relationship
- resource state
- action-specific policy
- security-sensitive constraints

The default result is deny.

Detailed authorization semantics are defined in:

`docs/IDENTITY_AUTHORIZATION.md`

---

## 8. Workspace Isolation

Workspace boundaries are security boundaries.

The primary workspace contexts are:

- `INTERNAL`
- `CUSTOMER`

Internal users may access the Internal Workspace according to their authorization.

External customer users may access the Customer Workspace according to their authorization.

External users must never gain Internal Workspace access merely because:

- they are associated with a project
- they are associated with a customer
- they know a project identifier
- they know a project address
- they possess a document identifier

The Customer Workspace must expose only information explicitly intended for external users.

The backend must enforce this separation.

Client-side filtering is not sufficient.

---

## 9. Project Access

Project access is an explicit authorization boundary.

Internal users require an active project assignment or another explicitly approved authorization scope.

External customer users require a valid customer relationship and applicable customer project access.

Knowledge of a project identifier, URL, address, customer name, or document identifier must never create authorization.

There is no generic emergency or convenience bypass for unassigned projects.

Future privileged emergency workflows require an explicit architecture decision and must be:

- narrowly scoped
- explicitly authorized
- time-limited
- reasoned
- audited
- revocable

---

## 10. External Users

`EXTERNAL` is a general identity classification.

External users may participate in different business relationships, including:

- customers
- suppliers
- tax advisors
- partners
- other explicitly authorized relationships

An external relationship does not itself grant access.

Authorization must additionally evaluate:

- active relationship
- applicable external role
- workspace
- resource scope
- project relationship
- permission
- resource exposure rules

External users must never inherit internal privileges merely because they are associated with an internal resource.

---

## 11. Permission Administration

Permission administration is itself a privileged authorization action.

A user may only grant, restrict, revoke, or otherwise administer permissions that the authorization policy allows that user to administer.

The system must prevent:

- self-escalation
- arbitrary privilege creation
- unrestricted role modification
- bypassing project scope
- bypassing workspace boundaries
- bypassing mandatory policy constraints
- granting non-delegable security capabilities

A permission-management operation must therefore itself pass through authorization.

Conceptually:

    Grant Permission
         │
         ▼
    Authenticate requester
         │
         ▼
    Authorize permission administration
         │
         ▼
    Validate permission delegability
         │
         ▼
    Validate target scope
         │
         ▼
    Evaluate mandatory policy
         │
         ▼
    Accept or deny

Security-sensitive permission changes must be auditable.

---

## 12. Least Privilege

GlasHaus follows least privilege.

A principal should receive only the capabilities and information required for the intended task.

Permission alone does not necessarily grant access to every instance of a resource.

For example:

    schedule.view_availability

may permit:

    Technician B
    Tuesday: available

without permitting:

    customer
    project address
    appointment details
    internal notes

The backend must return only the representation permitted by the applicable authorization policy.

Sensitive fields must not merely be hidden by the client.

---

## 13. Data Minimization

Authorization must also control the information returned by the system.

A principal must not receive sensitive fields merely because they can access the parent resource.

Data minimization applies to:

- API responses
- database queries
- files
- search results
- exports
- synchronization
- federation
- logs where applicable

Different permissions may therefore result in different resource representations.

---

## 14. Search Security

Search is part of the authorization boundary.

A search operation must return only resources the requesting principal is authorized to discover.

Unauthorized resources must not be exposed through:

- search results
- autocomplete
- filtering
- sorting
- result counts
- existence checks
- error messages
- metadata

For example, a user without access to Project A must not receive:

    Project A — access denied

as a search result.

The preferred behavior is to omit unauthorized resources.

Search must not become a side channel for discovering protected information.

---

## 15. Device Trust

Devices are separate technical trust objects.

A device may provide additional security context but does not replace application authorization.

Devices must have an explicit lifecycle, such as:

- `PENDING`
- `ACTIVE`
- `REVOKED`

A device must be independently revocable.

A lost or compromised device must be revocable without requiring the device to reconnect first.

Device registration must not automatically grant unrestricted application access.

Sensitive operations may require stronger device trust where explicitly defined by security policy.

---

## 16. Browser and Alternate Device Access

Security controls must not unnecessarily prevent legitimate business workflows when a normal work device is unavailable.

For example, an internal employee may need to perform an authorized workflow from another browser or trusted computer.

Such access must still require:

1. authentication
2. an appropriate security context
3. applicable authorization
4. normal server-side policy evaluation

This is not an emergency authorization bypass.

Device trust may strengthen authentication or restrict particularly sensitive operations, but ordinary permitted workflows should not depend on possession of one specific physical device unless explicitly required by policy.

---

## 17. Offline Security

Offline operation is an explicitly bounded security mode.

Offline functionality must define:

- which data may be cached
- which operations may be performed
- authentication lifetime
- authorization lifetime
- device trust requirements
- local encryption requirements
- revocation behavior
- synchronization behavior
- conflict handling

Offline clients may use cached authorization state only within the explicitly defined security lifetime.

Offline authorization must never become an indefinite substitute for server-side authorization.

When the server is reachable, current server-side authorization and revocation state become authoritative.

Detailed synchronization semantics are defined in:

`docs/SYNC.md`

---

## 18. Transport Security

Production communication must use authenticated TLS.

This applies to applicable communication paths including:

- browser → API
- mobile/desktop client → API
- API → object storage
- API → external services
- mail transport where applicable
- future federation channels
- synchronization channels

TLS protects data in transit.

TLS does not replace encryption at rest or application-level encryption where required.

Certificate validation must not be disabled as a convenience measure in production.

---

## 19. Data Protection

GlasHaus uses multiple protection layers where appropriate:

    Transport Security
          +
    Infrastructure Encryption
          +
    Application-Level Encryption
          +
    Authorization

These controls address different threats and are not interchangeable.

Database and backup infrastructure must use appropriately protected storage.

Sensitive durable content may require application-level encryption before being written to durable object storage.

The exact cryptographic architecture is defined in:

`docs/CRYPTOGRAPHY.md`

---

## 20. Document and Object Storage Security

Documents and binary content are protected resources.

Before document access, the server must:

1. authenticate the request
2. authorize the principal
3. validate document and workspace scope
4. retrieve only permitted content
5. decrypt where required
6. return the permitted content

Object storage must never become an authorization bypass.

A user who knows or guesses a storage object identifier must not automatically be able to retrieve the object.

If pre-signed or otherwise delegated object-storage URLs are used, they must be:

- short-lived
- narrowly scoped
- issued only after authorization
- incapable of granting broader access than the originating authorization decision

---

## 21. Encryption and Key Separation

Encryption and authorization are separate security controls.

Authorization determines whether an authenticated principal may access a resource.

Encryption provides additional protection against threats such as:

- storage compromise
- database compromise
- backup theft
- unauthorized infrastructure access

Cryptographic key material must be separated from encrypted application data according to the cryptographic architecture.

Secret production keys must not be committed to source control or stored beside ciphertext merely for convenience.

The complete key hierarchy, key lifecycle, rotation, and recovery model are defined in:

`docs/CRYPTOGRAPHY.md`

---

## 22. Secrets Management

The following must never be committed to source control:

- passwords
- access tokens
- session secrets
- private keys
- encryption keys
- database credentials
- production credentials
- other production secrets

Secrets must be supplied through secure deployment configuration or an appropriate secret-management mechanism.

Development credentials must not accidentally become production credentials.

Logs must not expose secrets.

---

## 23. Backup Security

Backups are sensitive copies of application data.

Backups require:

- encryption
- access control
- defined retention
- tested restoration
- key availability
- monitoring
- auditability where appropriate

A backup is not considered recoverable merely because the encrypted data exists.

Required cryptographic keys and recovery metadata must also be recoverable according to the documented key-management and disaster-recovery procedures.

Backup access must be treated as equivalent to access to highly sensitive application data.

---

## 24. Auditability

Security-sensitive operations must be auditable where required.

Examples include:

- authentication events
- session events
- device registration
- device revocation
- role changes
- hierarchy changes
- permission grants
- permission restrictions
- permission revocations
- project assignments
- customer relationships
- external access
- sensitive document access
- external sharing
- security configuration changes
- key-management operations
- federation trust changes

Audit records should identify, where applicable:

- actor
- action
- target resource
- timestamp
- result
- request/correlation identifier
- relevant authorization context

Audit records must avoid unnecessary sensitive payloads.

Audit data is itself protected information and requires appropriate access control and retention.

---

## 25. Failure Semantics

Security-sensitive failures must fail closed.

Examples include:

- unknown identity
- invalid authentication
- inactive account
- revoked device
- missing permission
- missing project assignment
- missing customer relationship
- invalid scope
- invalid workspace
- invalid federation trust
- unavailable required security context
- failed policy constraint

The system must never interpret missing security information as permission.

Operational failures must not accidentally become successful authorization.

Errors returned to unauthorized clients must not reveal sensitive information.

---

## 26. Revocation

Security controls must define how authorization is revoked.

Revocation applies to, among other things:

- user accounts
- sessions
- devices
- permission grants
- project assignments
- customer relationships
- external access
- federation trust
- cryptographic keys

Revocation must have a defined authoritative point.

For online operation, the server is authoritative.

For offline operation, revocation becomes effective when the security model permits the client to receive updated state, subject to the defined offline lifetime.

No cached authorization may remain valid indefinitely.

---

## 27. Synchronization Security

Synchronization is a security-sensitive operation because it may transport data and authorization state between devices or servers.

Synchronization must preserve:

- identity
- resource ownership
- authorization scope
- workspace boundaries
- version integrity
- deletion semantics
- revocation semantics
- confidentiality
- integrity

Synchronization must not introduce an independent authorization model that conflicts with the server.

Synchronization operations must be authenticated, authorized, and protected against replay and unintended duplication.

Detailed synchronization semantics belong to:

`docs/SYNC.md`

---

## 28. Federation Security

Future federation introduces an independent trust boundary.

A federated request must establish:

- remote server identity
- remote principal identity
- authenticated federation context
- trust state
- requested action
- requested resource
- resource scope
- local policy decision

The receiving server must independently authorize access to its own resources.

The following model is explicitly forbidden:

    Remote server says ALLOW
              │
              ▼
        Local server ALLOW

Instead:

    Remote identity
          │
          ▼
    Authenticated federation context
          │
          ▼
    Local policy evaluation
          │
          ▼
    Local authorization decision

Federation must support explicit trust establishment, scope limitation, revocation, and auditing.

No federation implementation should weaken the local security boundary.

---

## 29. Threat Model

The architecture-level threat model includes at least the following threats:

| Threat | Primary Controls |
|---|---|
| Stolen credentials | strong authentication, secure sessions, revocation, optional 2FA |
| Compromised client | server-side authorization, data minimization |
| Stolen device | local encryption, device revocation, bounded sessions |
| Database compromise | infrastructure encryption, application-level encryption where required |
| Object-storage exposure | authorization boundary, encrypted objects, scoped URLs |
| Network interception | authenticated TLS |
| Stale offline authorization | bounded offline lifetime, server re-evaluation |
| Replay of synchronization operations | authenticated operations, idempotency, versioning |
| Privilege escalation | controlled permission administration, policy constraints |
| Unauthorized project discovery | authorization-aware queries and search |
| Workspace boundary violation | server-side workspace authorization |
| Leaked logs | secret redaction, data minimization |
| Backup theft | encrypted backups, access control, key protection |
| Malicious federation peer | explicit trust, authentication, scoped protocol, local authorization |

This is an architecture-level threat model.

It is not a formal penetration test, security audit, or complete threat assessment.

---

## 30. Security-Sensitive Operations

The following operations may require additional controls depending on their risk:

- document signing
- document decryption
- permission management
- user management
- cryptographic key management
- security configuration
- external data sharing
- federation trust management
- backup administration

Additional controls may include:

- stronger authentication
- device trust
- explicit scope
- additional approval
- temporary authorization
- audit logging
- separation of duties

The exact requirements are defined by the applicable security and cryptographic policies.

---

## 31. Separation of Duties

Certain security-sensitive actions may require independent actors.

Examples include:

- sensitive financial approval
- permission delegation
- cryptographic key administration
- security configuration
- sensitive document approval
- federation trust establishment

Administrative status alone must not automatically bypass separation-of-duties requirements.

Where required, workflows must support:

- independent approval
- explicit approval state
- actor attribution
- auditability
- revocation
- time limits

---

## 32. Security and Persistence

Persistence does not constitute authorization.

A database relationship must never be interpreted as permission by itself.

Application services must evaluate authorization before disclosing protected resources.

For sensitive resources, the conceptual flow is:

    Authenticate
         │
         ▼
    Authorize
         │
         ▼
    Validate Scope
         │
         ▼
    Load Permitted Data
         │
         ▼
    Decrypt Where Required
         │
         ▼
    Return Permitted Representation

Database constraints and foreign keys enforce structural integrity.

They complement but do not replace authorization.

Detailed persistence rules are defined in:

`docs/PERSISTENCE_MODEL.md`

---

## 33. Security and Cryptography

Security architecture determines when protection is required.

Cryptography architecture determines how cryptographic protection is implemented.

These concerns must remain separate.

Security requirements may specify:

- data must be encrypted
- keys must be separated from ciphertext
- backups must be protected
- document content requires additional protection

`docs/CRYPTOGRAPHY.md` defines:

- cryptographic algorithms
- key hierarchy
- key lifecycle
- key storage
- key rotation
- nonce/IV handling
- encryption metadata
- recovery requirements

Cryptographic implementation decisions must not silently weaken the security requirements defined here.

---

## 34. Security Testing

Security requirements must be represented by automated tests where practical.

Tests must cover at least:

- authentication failures
- inactive users
- revoked sessions
- revoked devices
- default-deny behavior
- project authorization
- customer authorization
- workspace isolation
- permission delegation
- permission restrictions
- scope enforcement
- unauthorized search results
- object-storage access
- sensitive field minimization
- offline authorization lifetime
- synchronization authorization
- federation trust boundaries

Negative tests are particularly important.

Tests must demonstrate that a principal cannot gain access merely by:

- knowing an identifier
- knowing a project address
- modifying client-side state
- changing a URL
- being an internal user
- having an unrelated role
- having a customer relationship without applicable project access
- having administrative status without sufficient delegation authority

---

## 35. Security Invariants

The following invariants must remain true unless this architecture is explicitly changed:

1. The client is never the final authorization authority.
2. Authorization is server-side.
3. Default authorization behavior is deny.
4. Authentication and authorization remain separate.
5. Internal project access is explicit.
6. Customer project access requires a valid external relationship and applicable project access.
7. External users cannot access the Internal Workspace.
8. Project identifiers and addresses do not grant access.
9. Permission administration is itself authorized.
10. Mandatory security constraints cannot be bypassed by configurable grants.
11. Devices can be independently revoked.
12. Offline authorization is bounded.
13. Object storage cannot bypass application authorization.
14. Sensitive durable content receives appropriate protection.
15. Cryptographic keys are separated from encrypted data according to the cryptographic architecture.
16. Security-sensitive actions are auditable where required.
17. Search does not reveal unauthorized resources.
18. Backups are treated as sensitive data.
19. Federation is a separate trust boundary.
20. A remote server cannot unilaterally authorize access to local resources.
21. Security failures fail closed.
22. Future implementations must not silently weaken these boundaries.

---

## 36. Architectural Change Rule

A change that affects a security boundary, authorization rule, trust relationship, cryptographic requirement, offline capability, synchronization behavior, or federation behavior requires an explicit architectural decision.

Implementation must not silently introduce a weaker security model for convenience.

When implementation and this document diverge:

1. determine whether the implementation or architecture is incorrect;
2. resolve the conflict explicitly;
3. update the affected architecture document if the target architecture changes;
4. update implementation and tests accordingly.

The repository should never intentionally maintain two contradictory security models.

---

## 37. Related Documents

This document should be read together with:

- `docs/ARCHITECTURE.md`
- `docs/IDENTITY_AUTHORIZATION.md`
- `docs/PERSISTENCE_MODEL.md`
- `docs/CRYPTOGRAPHY.md`
- `docs/SYNC.md`
- `docs/TESTING.md`
- `docs/Roadmap.md`

The implementation must not silently diverge from these documents.