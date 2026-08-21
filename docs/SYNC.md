# GlasHaus Synchronization Architecture

## 1. Purpose

GlasHaus uses offline-first synchronization for field workflows.

This document defines synchronization mechanics.

Business semantics remain in the domain model.

---

## 2. Core Model

```text
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
```

A normal offline-capable action must not wait for server synchronization.

---

## 3. Synchronizable Entities

An entity becomes offline-capable only after defining:

- local persistence,
- authorization scope,
- identity,
- lifecycle,
- version/concurrency behavior,
- deletion behavior,
- conflict strategy,
- retention requirements.

The synchronization layer must not automatically synchronize every database table.

---

## 4. Local Identity

An offline-capable entity has a stable local identity.

The identity:

- is generated locally,
- exists before server synchronization,
- remains stable,
- preserves local relationships.

A server/global identity may be assigned when accepted by the server.

---

## 5. Local Transaction and Outbox

A local business mutation and its outbox entry are persisted atomically:

```text
BEGIN
  modify entity
  create outbox operation
COMMIT
```

The outbox survives:

- application restart,
- device restart,
- network loss,
- backend outage.

Each operation has a unique `operation_id`.

---

## 6. Operation Lifecycle

```text
pending
   │
   ├── retryable failure ──► pending
   ├── accepted ────────────► completed
   ├── conflict ────────────► conflict
   └── rejected ────────────► rejected
```

Conflicts and rejections are explicit.

Ordinary retry must never silently overwrite newer state.

---

## 7. Idempotency

Every push operation is idempotent.

If a request reaches the server but the response is lost, retrying the same `operation_id` must not duplicate the mutation.

The server retains sufficient idempotency information for the applicable retention period.

---

## 8. Optimistic Concurrency

Synchronizable mutable entities require a concurrency mechanism.

```text
client base version = 8
server current version = 8
→ update accepted
→ server version = 9
```

If the server is already at version 9, an update based on version 8 must not silently overwrite it.

The result is a conflict unless the domain defines a safe merge.

---

## 9. Conflict Policy

Conflict behavior is domain-specific.

Examples:

- append-only photographs: usually no conflict,
- metadata: potentially mergeable,
- scheduling: may require review,
- signed documents: strict handling,
- financial documents: strict handling.

The synchronization engine provides the mechanism.

The domain defines the meaning.

---

## 10. Server Change Feed

The server should provide a durable ordered feed for synchronized changes.

Conceptual entry:

```text
change_sequence
change_id
entity_type
entity_global_id
entity_version
operation_type
server_created_at
server_updated_at
server_deleted_at
```

`change_sequence` is a feed position.

`entity_version` is an individual entity version.

They must not be conflated.

The feed is authorization-aware.

---

## 11. Client Cursor

Each device stores a durable synchronization cursor.

The cursor represents the highest feed position successfully applied to local persistent state.

Applying a batch and advancing the cursor are atomic:

```text
BEGIN
  apply changes
  update cursor
COMMIT
```

On failure, the cursor remains unchanged.

---

## 12. Pull

The conceptual operation is:

```text
pull(cursor)
    ↓
authorized ordered changes
    ↓
local transaction
    ↓
cursor advancement
```

The final API contract is defined after the domain and authorization model exist.

---

## 13. Push

The server:

1. authenticates the device/user,
2. authorizes the operation,
3. validates domain state,
4. checks idempotency,
5. checks concurrency,
6. applies the mutation transactionally,
7. records required audit/sync data,
8. returns a durable result.

An operation created while authorized offline is not automatically authorized forever.

---

## 14. Dependencies and Ordering

Dependent operations must be applied in an order that makes referenced state resolvable.

Example:

```text
Create Project
      ↓
Create Work Order
      ↓
Create Protocol
      ↓
Upload Photo
```

Failed dependencies remain pending.

---

## 15. Deletions and Tombstones

Synchronizable deletion must remain represented until relevant clients can safely observe it.

A tombstone may contain:

- entity identity,
- entity version,
- deletion timestamp,
- authorization-relevant metadata.

Physical cleanup is separate and must respect synchronization and retention requirements.

---

## 16. Binary Assets

Binary assets are transferred separately from structured mutations.

Metadata may be synchronized normally:

```text
Document
DocumentVersion
AssetMetadata
```

The encrypted binary is transferred through an asset channel.

Required properties:

- integrity verification,
- retry,
- resumability where practical,
- size limits,
- content validation,
- authorization,
- encryption.

---

## 17. Resynchronization

If feed history is no longer available for a client's cursor, the server returns a distinct `resync_required` result.

A full resync must:

1. establish an authorized baseline,
2. preserve pending local mutations,
3. reconcile local state explicitly,
4. establish a new cursor.

Resync must never silently discard pending outbox work.

---

## 18. Access Changes

A change cursor alone is insufficient for newly authorized historical data.

If a user gains access to a project whose historical changes predate the user's cursor, an authorization-aware baseline mechanism must provide the newly accessible state.

This must not become an unrestricted database export.

---

## 19. Offline Authorization

Cached permissions enable offline usability.

At synchronization, the server re-evaluates authorization.

If access has been revoked, the operation is rejected with an actionable result.

---

## 20. Synchronization UX

The client distinguishes:

```text
offline
online + idle
online + syncing
online + pending
online + conflict
online + retryable error
online + resync required
```

Online does not mean synchronized.

Offline does not mean unusable.

---

## 21. Integrity Invariants

1. No successful local mutation exists without its required outbox representation.
2. Retrying cannot duplicate a mutation.
3. The cursor never advances past unapplied data.
4. A conflict never becomes an implicit overwrite.
5. Pending work survives synchronization failure.
6. Authorization is checked server-side.
7. Binary assets have independent integrity/transfer handling.
8. Resync never silently deletes pending work.

---

## 22. Implementation Order

Implement synchronization incrementally:

1. one small offline-capable entity,
2. local persistence,
3. outbox,
4. push,
5. idempotency,
6. server versioning,
7. pull + cursor,
8. conflict handling,
9. deletion,
10. binary assets,
11. background execution,
12. resync,
13. additional entities.

Do not build a generic synchronization framework before real domain semantics exist.