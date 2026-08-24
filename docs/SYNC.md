# GlasHaus Synchronization Architecture

## 1. Purpose

GlasHaus uses offline-first synchronization for selected field workflows.

This document defines the target synchronization architecture and mechanics.

Synchronization is not a generic database replication mechanism.

Business semantics remain in the domain model.

An entity becomes synchronizable only when its offline behavior has been explicitly defined.

The server remains authoritative for server-side state, authorization, and security policy.

---

## 2. Core Model

The conceptual synchronization flow is:

    User action
         │
         ▼
    Local validation
         │
         ▼
    Local transaction
         ├── domain state
         └── outbox operation
                  │
                  ▼
            background sync
                  │
                  ▼
             GlasHaus API
                  │
                  ▼
          authoritative state

A normal offline-capable action must not wait for server synchronization.

The local transaction must establish a consistent local state before synchronization occurs.

---

## 3. Synchronizable Entities

An entity becomes offline-capable only after defining:

- local persistence
- identity
- lifecycle
- ownership
- authorization scope
- versioning and concurrency behavior
- deletion behavior
- conflict strategy
- retention requirements
- security classification
- local encryption requirements where applicable
- binary-content behavior where applicable

The synchronization layer must not automatically synchronize every database table.

Synchronization support is a deliberate domain decision.

---

## 4. Local Identity

An offline-capable entity requires a stable local identity.

The identity:

- is generated locally
- exists before server synchronization
- remains stable
- preserves local relationships
- can be resolved by the server
- survives retries and synchronization failures

The existing UUIDv7 direction is compatible with this requirement.

Where an entity is created offline, its identity must not depend on server-generated sequential identifiers.

A server/global identity may be confirmed or assigned when the operation is accepted by the server, but local relationships must remain valid throughout synchronization.

---

## 5. Local Transaction and Outbox

A local business mutation and its required outbox entry are persisted atomically.

    BEGIN
        modify entity
        create outbox operation
    COMMIT

The outbox survives:

- application restart
- device restart
- network loss
- backend outage

Each operation has a unique `operation_id`.

A successful local mutation must never exist without the corresponding outbox representation when synchronization is required for that mutation.

---

## 6. Outbox Operation

An outbox operation represents a local mutation that must eventually be synchronized with the server.

Conceptually:

    OutboxOperation
        ├── operation_id
        ├── entity_type
        ├── entity_id
        ├── operation_type
        ├── base_version
        ├── payload
        ├── created_at
        ├── status
        └── retry metadata

The exact persistence model belongs to the persistence architecture.

Outbox payloads must not contain unnecessary sensitive plaintext.

Sensitive synchronization data must remain protected according to its security classification.

---

## 7. Operation Lifecycle

The basic lifecycle is:

    pending
       │
       ├── retryable failure ──► pending
       ├── accepted ────────────► completed
       ├── conflict ────────────► conflict
       └── rejected ────────────► rejected

Conflicts and rejections are explicit states.

Ordinary retry must never silently overwrite newer server state.

Failed dependencies may keep an operation pending until the required prerequisite state exists.

---

## 8. Idempotency

Every push operation is idempotent.

If a request reaches the server but the response is lost, retrying the same `operation_id` must not duplicate the mutation.

The server retains sufficient idempotency information for the applicable retention period.

A repeated operation must produce a stable result rather than applying the mutation again.

Idempotency records are part of synchronization correctness and must not be removed before the applicable retry/recovery window has expired.

---

## 9. Optimistic Concurrency

Synchronizable mutable entities require an explicit concurrency mechanism.

A mutation should carry the version of the entity from which the local change was based.

Example:

    client base version = 8
    server current version = 8

    → update accepted
    → server version = 9

If the server is already at version 9, an update based on version 8 must not silently overwrite the newer state.

The result is a conflict unless the domain explicitly defines a safe merge strategy.

Version checking is separate from feed position.

---

## 10. Conflict Policy

Conflict behavior is domain-specific.

Examples:

- append-only photographs: usually no conflict
- metadata: potentially mergeable
- scheduling: may require review
- signed documents: strict handling
- financial documents: strict handling

The synchronization engine provides the conflict mechanism.

The domain defines the meaning and resolution policy.

Conflicts must remain visible and must never be converted into implicit last-write-wins behavior unless the domain explicitly approves that strategy.

---

## 11. Dependencies and Ordering

Dependent operations must be applied in an order that makes referenced state resolvable.

Example:

    Create Project
          ↓
    Create Work Order
          ↓
    Create Protocol
          ↓
    Upload Photo

An operation that depends on unavailable state must remain pending or receive an explicit dependency-related result.

The synchronization engine must not apply dependent mutations in an order that produces invalid domain state.

---

## 12. Server Change Feed

The server should provide a durable, ordered, authorization-aware change feed for synchronized entities.

A conceptual feed entry contains:

    change_sequence
    change_id
    entity_type
    entity_global_id
    entity_version
    operation_type
    server_created_at
    server_updated_at
    server_deleted_at

`change_sequence` represents the position within the synchronization feed.

`entity_version` represents the version of an individual entity.

These concepts must not be conflated.

The feed is authorization-aware.

A client must only receive changes it is currently authorized to discover and synchronize.

---

## 13. Client Cursor

Each synchronized device stores a durable synchronization cursor.

The cursor represents the highest feed position successfully applied to local persistent state.

Applying a batch and advancing the cursor are atomic:

    BEGIN
        apply changes
        update cursor
    COMMIT

If application of the batch fails, the cursor remains unchanged.

The client must therefore be able to retry the same feed range without silently skipping changes.

---

## 14. Pull

The conceptual pull operation is:

    pull(cursor)
        ↓
    authorized ordered changes
        ↓
    local transaction
        ↓
    cursor advancement

The final API contract is defined after the relevant domain and authorization models exist.

The synchronization API must not expose an unrestricted change stream.

---

## 15. Push

The server processes a synchronization operation conceptually as follows:

1. authenticate the device/user;
2. establish the authenticated synchronization context;
3. authorize the operation;
4. validate domain state;
5. check idempotency;
6. check dependencies;
7. check optimistic concurrency;
8. apply the mutation transactionally;
9. create required change-feed state;
10. record required audit/synchronization information;
11. return a durable result.

An operation created while authorized offline is not automatically authorized forever.

Server-side authorization is authoritative.

---

## 16. Offline Authorization

Offline authorization is cached usability, not permanent authority.

The client may use cached authorization information to determine whether an offline workflow may be initiated.

When an operation reaches the server, the server re-evaluates:

- user state
- device state
- authentication context
- current permissions
- project scope
- workspace scope
- resource state
- action-specific policy

If authorization has been revoked, the operation is rejected with an explicit and actionable result.

The client must not treat a previously successful offline authorization as permanent authorization.

---

## 17. Access Revocation

If a user loses access while operating offline:

- existing local state remains subject to local device and retention policy
- pending synchronization is not automatically considered authorized
- new server synchronization is re-authorized
- unauthorized mutations are rejected
- the rejection is represented explicitly
- newly prohibited data must not continue to be synchronized

The server remains authoritative.

Device revocation must also be respected when synchronization resumes.

---

## 18. Access Changes and Newly Granted Data

A change cursor alone is insufficient when a user gains access to historical project data.

If a user gains access to a project whose historical changes predate the user's cursor, an authorization-aware baseline mechanism must provide the newly accessible state.

This mechanism must:

- evaluate current authorization
- provide only currently authorized data
- respect workspace boundaries
- respect resource scope
- preserve synchronization ordering
- avoid unrestricted database export

Authorization changes therefore require synchronization semantics of their own.

---

## 19. Deletions and Tombstones

Synchronizable deletion must remain represented until relevant clients can safely observe the deletion.

A tombstone may contain:

- entity identity
- entity version
- deletion timestamp
- authorization-relevant metadata
- synchronization metadata

Physical cleanup is separate from logical deletion.

Cleanup must respect:

- synchronization state
- retention requirements
- audit requirements
- legal/business requirements

A deleted entity must not silently reappear because an old client reconnects with stale state.

---

## 20. Binary Assets

Binary assets are transferred separately from structured mutations.

Structured metadata may synchronize normally:

    Document
    DocumentVersion
    AssetMetadata

Encrypted binary content is transferred through a dedicated asset channel.

Required properties include:

- authorization
- integrity verification
- encryption
- retry
- resumability where practical
- size limits
- content validation
- content-type validation
- safe storage handling

Binary transfer must not create an authorization bypass.

Object-storage access remains subject to the same security boundary as structured document access.

---

## 21. Binary Asset Integrity

Binary synchronization must verify that the received object corresponds to the expected content.

Where applicable, integrity metadata may include:

- content digest
- object size
- document version
- encryption version
- storage object identifier

A corrupted or mismatched asset must not silently replace valid local content.

---

## 22. Synchronization Security Classification

Synchronizable data retains its domain security classification.

Synchronization must not lower the protection level of the underlying data.

For example:

    highly sensitive document
            ↓
    encrypted server storage
            ↓
    encrypted synchronization payload
            ↓
    encrypted local storage

The synchronization layer must not create a plaintext copy merely because data is queued for synchronization.

Sensitive synchronization metadata must also be minimized.

---

## 23. Local Storage Protection

Sensitive offline data must be protected at rest.

The local client should use the operating system's secure key storage where available.

Conceptually:

    OS secure key storage
             ↓
        protected key
             ↓
    encrypted local database/assets

Plaintext durable storage of sensitive offline data is not acceptable where the security classification requires encryption.

Local retention must be limited according to the relevant security and business policy.

---

## 24. Resynchronization

If the server no longer retains the history required by a client's cursor, the server returns a distinct:

    resync_required

result.

A full resynchronization must:

1. establish an authorized baseline;
2. preserve pending local mutations;
3. reconcile local state explicitly;
4. establish a new cursor;
5. continue synchronization only after the new baseline is valid.

Resynchronization must never silently discard pending outbox work.

---

## 25. Pending Local Work During Resync

Pending local mutations must remain identifiable throughout resynchronization.

The client must distinguish:

- server state
- local pending state
- accepted local mutations
- rejected mutations
- conflicts
- unresolved dependencies

A resynchronization operation must not overwrite pending work merely to obtain a clean local baseline.

Any required reconciliation must be explicit.

---

## 26. Synchronization Retention

Synchronization data has retention requirements independent of normal domain data.

Retention may apply to:

- outbox operations
- idempotency records
- change-feed entries
- tombstones
- synchronization cursors
- conflict records
- synchronization audit information

Retention must be long enough to support the applicable retry, recovery, resynchronization, and audit requirements.

Physical cleanup must not occur merely because synchronization data is no longer immediately visible to the application.

---

## 27. Synchronization and Audit

Security-sensitive synchronization events must be auditable where required.

Examples include:

- rejected authorization
- permission-related synchronization rejection
- device revocation affecting synchronization
- sensitive data synchronization
- conflict resolution
- administrative synchronization actions
- resynchronization events

Audit records must not unnecessarily contain sensitive synchronization payloads.

---

## 28. Synchronization and Federation

Local synchronization and future server-to-server federation are separate mechanisms.

A remote GlasHaus server is not automatically a synchronization client with local privileges.

Federation requires its own:

- authentication
- trust model
- authorization
- replay protection
- data-sharing scope
- cryptographic protocol
- revocation behavior

Synchronization architecture must not implicitly define federation semantics.

---

## 29. Synchronization UX

The client distinguishes at minimum:

    offline
    online + idle
    online + syncing
    online + pending
    online + conflict
    online + retryable error
    online + resync required

Online does not mean synchronized.

Offline does not mean unusable.

The client should expose actionable information when synchronization fails because of:

- authorization
- conflict
- dependency
- validation
- connectivity
- server availability

---

## 30. Synchronization Invariants

The following invariants must remain true:

1. No successful local mutation exists without its required outbox representation.

2. Every synchronization operation has a stable unique operation identity.

3. Retrying an operation cannot duplicate its mutation.

4. Idempotency information remains available for the applicable retry/recovery period.

5. Mutable synchronizable entities use explicit concurrency control.

6. A conflict never becomes an implicit overwrite.

7. Dependent operations are not applied before their required state exists.

8. The cursor never advances past unapplied data.

9. Pending work survives synchronization failure.

10. Authorization is re-evaluated server-side.

11. Offline authorization is not permanent authorization.

12. Newly granted historical access is provided through an authorization-aware baseline mechanism.

13. Deletions remain represented until relevant clients can safely observe them.

14. Binary assets have independent transfer and integrity handling.

15. Sensitive synchronized content remains protected according to its classification.

16. Resynchronization never silently deletes pending work.

17. Synchronization cannot bypass workspace or resource authorization boundaries.

18. Synchronization does not implicitly create federation trust.

---

## 31. Implementation Order

Synchronization should be implemented incrementally:

1. one small offline-capable domain entity
2. local persistence
3. stable local identity
4. atomic local mutation + outbox
5. push
6. idempotency
7. server-side authorization re-evaluation
8. server versioning and optimistic concurrency
9. pull + authorization-aware change feed
10. client cursor
11. dependency ordering
12. conflict handling
13. deletion and tombstones
14. binary assets
15. local encryption
16. background execution
17. access-change baseline handling
18. resynchronization
19. synchronization audit
20. additional entities

Do not build a generic synchronization framework before real domain semantics exist.

Each newly synchronized entity must have its own documented:

- authorization scope
- conflict behavior
- lifecycle
- deletion semantics
- retention policy
- security classification
- binary-content behavior where applicable