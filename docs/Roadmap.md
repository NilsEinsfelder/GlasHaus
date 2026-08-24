# GlasHaus Roadmap

## 1. Purpose

This roadmap defines the implementation order for GlasHaus.

The architecture documents define the approved target architecture.

The roadmap defines:

- what is implemented
- what is currently being implemented
- what is next
- what remains planned
- the required sequencing between architectural layers

The roadmap must not redefine architecture.

If implementation requirements conflict with an architecture document, the conflict must be resolved explicitly before implementation continues.

---

## 2. Roadmap Principles

GlasHaus follows these sequencing principles:

1. Architecture precedes implementation.

2. Persistence design precedes production domain implementation.

3. Authentication precedes protected application workflows.

4. Authorization is server-side from the first protected workflow onward.

5. Security architecture precedes sensitive-data implementation.

6. Cryptographic design precedes cryptographic implementation.

7. A concrete domain workflow precedes generic abstractions.

8. A concrete offline workflow precedes generic synchronization infrastructure.

9. Tests are implemented together with the behavior they verify.

10. Security guarantees are never claimed before implementation and testing demonstrate them.

11. Each implementation phase should leave the repository runnable and testable.

12. Future architecture must not be implemented speculatively without a concrete product requirement.

13. Architectural invariants must remain consistent across all implementation phases.

---

## 3. Current Status

GlasHaus has an established backend foundation and an approved architectural baseline.

The current repository contains foundational implementation work including:

- Python 3.14
- FastAPI
- SQLAlchemy foundation
- UUIDv7 identifier direction
- SQLite development/test support
- initial Device model
- initial SyncState model
- configuration layer
- Alembic foundation
- automated tests
- Ruff
- MyPy
- initial authorization-model prototype

The target architecture now defines:

- local server as organizational boundary
- User identity
- Internal and External user types
- one role per User
- employment hierarchy
- modular permissions
- explicit permission grants and restrictions
- explicit internal project assignment
- explicit external customer project access
- Internal and Customer Workspaces
- security boundaries
- application-level cryptography where required
- offline-first synchronization architecture
- auditability
- future federation boundaries
- testing requirements

The implementation does not yet represent the complete target architecture.

Architecture approval must therefore not be confused with implementation completion.

---

## 4. Phase 0 — Architecture Baseline

Status: architecture baseline established.

Goal:

Maintain one consistent target model before expanding production implementation.

The following architecture documents form the baseline:

- `docs/ARCHITECTURE.md`
- `docs/PERSISTENCE_MODEL.md`
- `docs/SECURITY.md`
- `docs/CRYPTOGRAPHY.md`
- `docs/SYNC.md`
- `docs/TESTING.md`
- `docs/Roadmap.md`

The documents must remain mutually consistent.

Core architectural decisions include:

- the local GlasHaus server is the organizational boundary
- there is no normal local `organization_id` requirement
- User and Customer are separate concepts
- `EXTERNAL` is a generic User Type
- business relationships are modeled separately
- one User has exactly one Role
- hierarchy is separate from Role
- permissions are explicit capabilities
- role defaults are not unrestricted authority
- individual grants and restrictions are policy-constrained
- project access is explicit
- Customer Workspace and Internal Workspace are separate
- authorization is server-side and default-deny
- synchronization is domain-driven rather than generic database replication
- federation is a separate future trust boundary

Exit criteria:

- architecture documents describe one consistent target model
- implementation decisions can be traced to the architecture
- unresolved architectural conflicts are explicitly identified

---

## 5. Phase 1 — Backend Foundation

Status: substantially complete.

Goal:

Maintain a reliable backend foundation for the target implementation.

Completed foundations include:

- [x] FastAPI application
- [x] API routing
- [x] configuration
- [x] SQLAlchemy foundation
- [x] SQLite development/test support
- [x] UUIDv7 identifier direction
- [x] quality tooling
- [x] automated tests

Remaining foundation work:

- [ ] production PostgreSQL verification
- [ ] complete Alembic migration workflow verification
- [ ] logging foundation
- [ ] application error handling
- [ ] CI quality gates
- [ ] production configuration verification

Exit criteria:

The backend foundation is reproducible, testable and suitable for the first production-oriented persistence implementation.

---

## 6. Phase 2 — Persistence Model

Status: next implementation phase.

Goal:

Implement the relational foundation for identity, authorization and core business scope.

Implementation order:

1. User
2. Employment
3. Customer
4. Project
5. Project Assignment
6. External Relationship
7. Customer Project Access
8. Workspace
9. Permission model
10. Permission Grant
11. Device integration
12. Session persistence foundation
13. Audit Event
14. Document metadata
15. Document Version
16. Encryption metadata

Required work:

- [ ] SQLAlchemy domain models
- [ ] relational constraints
- [ ] indexes
- [ ] lifecycle/deactivation handling
- [ ] Alembic migrations
- [ ] persistence repositories/services where required
- [ ] persistence tests
- [ ] transaction tests
- [ ] PostgreSQL verification

Important constraints:

- database relationships must use foreign keys where applicable
- historical employment state must be preserved
- sensitive relationships must be explicit
- persistence must not be mistaken for authorization
- document content remains outside the relational database
- secret cryptographic key material must not be stored beside ciphertext

Exit criteria:

The persistence layer can represent the approved identity, authorization, customer, project and workspace model without security-significant shortcuts.

---

## 7. Phase 3 — Authentication

Goal:

Implement a real authenticated security context.

Tasks:

- [ ] credential model
- [ ] secure password hashing
- [ ] login
- [ ] session lifecycle
- [ ] session expiration
- [ ] logout
- [ ] session revocation
- [ ] device registration
- [ ] device revocation
- [ ] 2FA architecture
- [ ] 2FA implementation
- [ ] recovery
- [ ] authentication failure handling
- [ ] authentication audit events
- [ ] authentication tests

Security requirements:

- passwords are never reversibly encrypted
- session credentials are not stored in plaintext where secure hashing/token-reference storage is applicable
- revoked devices cannot establish valid new sessions
- inactive users cannot authenticate successfully
- authentication and authorization remain separate concerns

Exit criteria:

The server can securely establish, maintain and revoke authenticated user identity.

---

## 8. Phase 4 — Authorization

Goal:

Implement the approved authorization architecture before exposing protected business workflows.

Tasks:

- [ ] role catalogue
- [ ] user-type/role compatibility
- [ ] hierarchy catalogue
- [ ] role defaults
- [ ] hierarchy defaults
- [ ] effective permission evaluation
- [ ] explicit permission grants
- [ ] explicit permission restrictions
- [ ] permission expiration
- [ ] permission scopes
- [ ] project assignment enforcement
- [ ] customer project access enforcement
- [ ] workspace boundaries
- [ ] partial resource visibility
- [ ] permission delegation rules
- [ ] default-deny behavior
- [ ] authorization audit events
- [ ] authorization tests

Required invariants:

- [ ] knowing a resource identifier never grants access
- [ ] internal project access requires explicit assignment
- [ ] Customer Workspace cannot cross into Internal Workspace
- [ ] external relationships do not implicitly grant internal access
- [ ] permission administration is itself authorized
- [ ] mandatory policy constraints cannot be bypassed
- [ ] unauthorized resources are excluded from search
- [ ] sensitive fields are excluded from unauthorized representations

Exit criteria:

Authorization is enforced server-side and consistently across API, persistence access, search and protected resource delivery.

---

## 9. Phase 5 — Security and Cryptography

Goal:

Implement the security controls required for sensitive data.

Tasks:

- [ ] finalize data classification
- [ ] select approved cryptographic library
- [ ] define versioned encryption envelope
- [ ] define key hierarchy
- [ ] implement development key provider
- [ ] define production KMS/secret-management boundary
- [ ] implement sensitive structured-field encryption where required
- [ ] implement encrypted document storage
- [ ] implement integrity verification
- [ ] implement key rotation
- [ ] implement decrypt-only historical key handling
- [ ] define backup/key recovery
- [ ] implement required transport security
- [ ] implement crypto tests
- [ ] implement security regression tests

Requirements:

- authenticated encryption
- cryptographically safe nonce generation
- no nonce reuse under the same key
- versioned ciphertext formats
- key separation from encrypted data
- no production secrets in source control
- authorization before protected content is decrypted

Exit criteria:

At least one real sensitive document path can be:

1. authorized
2. encrypted
3. stored
4. retrieved
5. integrity-verified
6. decrypted
7. returned only to an authorized principal

and is covered by automated tests.

---

## 10. Phase 6 — First Domain Workflow

Goal:

Implement one complete, useful business workflow.

Initial direction:

    Customer
        ↓
    Project
        ↓
    Work Order
        ↓
    Document

The exact first workflow may be refined based on product priority.

Every production domain entity must define:

- identity
- lifecycle
- invariants
- persistence
- authorization
- security classification
- audit requirements
- synchronization decision
- deletion/retention behavior

The first workflow should deliberately remain narrow.

The goal is to validate the architecture through real business behavior rather than build every domain module simultaneously.

Exit criteria:

One useful business workflow works end-to-end through:

- persistence
- authentication
- authorization
- API
- security controls
- audit where required
- automated tests

---

## 11. Phase 7 — Browser MVP

Goal:

Deliver the first usable web application.

Tasks:

- [ ] web frontend foundation
- [ ] authentication UI
- [ ] protected routes
- [ ] authorization-aware navigation
- [ ] Internal Workspace
- [ ] Customer Workspace
- [ ] customer views
- [ ] project views
- [ ] first domain workflow
- [ ] document workflow
- [ ] API integration
- [ ] error handling
- [ ] end-to-end tests

The browser is an untrusted client.

The frontend must never be treated as the final authorization authority.

Internal and customer users use the same backend authorization system.

The Customer Workspace is a restricted presentation of authorized data, not a separate authorization system.

Exit criteria:

A user can complete the first domain workflow through the browser while all security boundaries are enforced server-side.

---

## 12. Phase 8 — Mobile Foundation

Goal:

Prepare the field client for controlled offline operation.

Tasks:

- [ ] mobile framework
- [ ] authentication
- [ ] secure local key storage
- [ ] encrypted local database
- [ ] local domain persistence
- [ ] offline UX states
- [ ] camera/assets
- [ ] local authorization state
- [ ] device lifecycle integration

Offline operation must not be implemented as unrestricted local access.

Exit criteria:

The mobile client can securely persist the data required by one future offline workflow without exposing sensitive durable plaintext.

---

## 13. Phase 9 — Synchronization MVP

Goal:

Synchronize one real offline-capable field workflow.

Synchronization must be implemented from the concrete domain workflow outward.

Tasks:

- [ ] local stable identity
- [ ] local transaction
- [ ] atomic outbox
- [ ] push
- [ ] idempotency
- [ ] optimistic concurrency
- [ ] server-side authorization re-evaluation
- [ ] pull
- [ ] authorization-aware change feed
- [ ] durable cursor
- [ ] conflict handling
- [ ] retries
- [ ] tombstones
- [ ] binary asset transfer
- [ ] integrity verification
- [ ] resynchronization
- [ ] authorization-aware baseline
- [ ] synchronization audit information where required

Required resilience:

The workflow must survive:

- application restart
- device restart
- network loss
- duplicate requests
- lost responses
- server failures
- authorization changes
- retries
- synchronization conflicts
- required resynchronization

without silent data loss.

Pending local work must never be silently discarded during synchronization or resynchronization.

Exit criteria:

One real offline workflow operates reliably under the failure conditions defined by `SYNC.md`.

---

## 14. Phase 10 — Domain Expansion

Potential modules include:

- [ ] customers
- [ ] projects
- [ ] work orders
- [ ] protocols
- [ ] photographs
- [ ] documents
- [ ] signatures
- [ ] offers
- [ ] scheduling
- [ ] change orders
- [ ] warranty workflows

Each module requires explicit definition of:

- authorization
- security classification
- persistence
- audit
- lifecycle
- deletion/retention
- synchronization semantics
- conflict behavior
- testing requirements

A module is not considered complete merely because its database tables exist.

---

## 15. Phase 11 — External Relationships

Goal:

Expand controlled external access beyond customers where justified by real business requirements.

Potential relationships:

- [ ] suppliers
- [ ] tax advisors
- [ ] partner companies

Each relationship requires:

- explicit relationship model
- scoped permissions
- workspace/data-access rules
- lifecycle
- audit requirements
- security classification
- synchronization decision where applicable

External relationships must never inherit internal permissions implicitly.

The generic `EXTERNAL` User Type remains unchanged.

---

## 16. Phase 12 — Document Automation

Potential capabilities:

- [ ] PDF generation
- [ ] templates
- [ ] OCR
- [ ] searchable documents
- [ ] signature workflows
- [ ] document sharing
- [ ] retention workflows
- [ ] deletion workflows

Search over sensitive or encrypted data requires an explicit architecture decision before implementation.

A search index must not become an accidental plaintext copy of protected data.

---

## 17. Phase 13 — External Integrations

Potential integrations include:

- [ ] IDS Connect
- [ ] supplier integrations
- [ ] ZUGFeRD/e-invoicing
- [ ] XML export
- [ ] pricing workflows
- [ ] notifications

Each integration requires an explicit security and data-flow review before implementation.

External integrations must not bypass the GlasHaus authorization boundary.

---

## 18. Phase 14 — Federation

Goal:

Allow independent GlasHaus installations to communicate through an explicitly designed trust relationship.

Federation remains future scope.

Tasks:

- [ ] federation identity
- [ ] peer trust
- [ ] server identity keys
- [ ] key management
- [ ] authenticated protocol
- [ ] message integrity
- [ ] replay protection
- [ ] scoped data-sharing contracts
- [ ] local authorization
- [ ] audit
- [ ] revocation
- [ ] synchronization/federation semantics
- [ ] federation tests

Federation must preserve independent server trust domains.

A remote authorization decision must never automatically become a local authorization decision.

Exit criteria:

A federation protocol has been explicitly designed, threat-modeled, implemented and tested before production federation is enabled.

---

## 19. Phase 15 — Advanced Automation

Potential future capabilities include:

- [ ] RFID
- [ ] QR workflows
- [ ] IoT
- [ ] AI-assisted estimation
- [ ] AI-assisted pricing
- [ ] recommendation systems
- [ ] other automation capabilities

These remain product vision until explicitly prioritized.

Advanced automation must not take precedence over incomplete security, authorization, persistence or synchronization foundations.

---

## 20. Cross-Phase Quality Requirements

Every implementation phase must maintain:

- runnable application state
- deterministic tests
- passing quality checks
- documented architectural decisions
- no known security-significant shortcuts

Relevant changes must include:

- unit tests
- persistence tests
- API tests
- authorization/security tests
- cryptography tests
- synchronization tests
- migration tests
- end-to-end tests

where applicable.

The global project target is at least 90% test coverage.

Coverage does not replace meaningful behavioral or security testing.

---

## 21. Definition of Done

A phase or feature is complete only when:

- required behavior is implemented
- positive cases are tested
- negative/security cases are tested
- relevant architectural invariants are tested
- persistence changes have migrations where required
- API behavior is tested where applicable
- documentation is updated
- quality checks pass
- no unrelated regressions are introduced
- security guarantees are supported by implementation and tests

For security-sensitive changes, the affected trust boundary must be explicitly reviewed.

---

## 22. Sequencing Rules

The following rules are mandatory:

1. Architecture precedes implementation.

2. Persistence design precedes production domain models.

3. Authentication precedes protected application workflows.

4. Authorization must protect the first production workflow.

5. Security architecture precedes sensitive-data implementation.

6. Cryptographic design precedes cryptographic implementation.

7. A concrete domain workflow precedes generic abstractions.

8. A concrete offline workflow precedes generic synchronization infrastructure.

9. Synchronization must not be designed as generic database replication.

10. Authorization is always server-side.

11. Offline authorization is bounded and is re-evaluated by the server during synchronization.

12. Sensitive content must not be decrypted before authorization.

13. Security guarantees are never claimed before implementation and testing.

14. Federation must not be implemented before its trust model and protocol are explicitly designed.

15. Each phase leaves the repository runnable and testable.

16. Architectural conflicts stop implementation until explicitly resolved.

---

## 23. Future Scope Policy

Features listed after the first usable domain workflow are intentionally not commitments to immediate implementation.

Future work is prioritized according to:

1. business value
2. security impact
3. architectural dependencies
4. operational necessity
5. implementation complexity
6. offline requirements
7. maintenance cost

A feature must not be promoted from roadmap to implementation solely because its architectural model already exists.

The roadmap therefore distinguishes between:

- approved architecture
- implementation work
- future capability
- product vision