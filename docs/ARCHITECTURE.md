# GlasHaus Architecture

## 1. Purpose

This document defines the stable system-level architecture of GlasHaus.

It describes architectural boundaries, responsibilities and invariants.

Detailed specifications live in:

- `SECURITY.md` — authentication, authorization, trust boundaries and auditing
- `CRYPTOGRAPHY.md` — encryption and key management
- `SYNC.md` — offline-first synchronization
- `Roadmap.md` — implementation order and project status

This document describes the target architecture. It does not imply that every described component is already implemented.

### Normative language

- **MUST** — mandatory architectural requirement.
- **SHOULD** — default recommendation; deviations require a documented reason.
- **MAY** — optional behavior.

---

## 2. Architectural Principles

1. GlasHaus is a modular monolith unless a concrete operational requirement justifies a separate service.
2. The field client is offline-first.
3. Server-side authorization is authoritative.
4. Local work must survive connectivity loss and device restarts.
5. Synchronization must be durable, resumable, idempotent and conflict-aware.
6. Business/domain logic must remain independent from HTTP, database and storage implementations.
7. Sensitive data must be protected according to `SECURITY.md` and `CRYPTOGRAPHY.md`.
8. Binary assets are handled separately from ordinary structured data.
9. Business-critical actions are auditable.
10. Complexity is introduced only when it solves a demonstrated problem.
11. Architectural decisions with material security, data-integrity or synchronization impact must be documented before implementation.
12. The implementation must not claim guarantees that the underlying platform cannot provide.

---

## 3. System Context

```text
                    ┌──────────────────────┐
                    │      Web Client      │
                    │       Next.js        │
                    └──────────┬───────────┘
                               │ HTTPS
                               ▼
                    ┌───────────────────────┐
                    │      GlasHaus API     │
                    │        FastAPI        │
                    │                       │
                    │ Auth / Authorization  │
                    │ Domain Services       │
                    │ Sync                  │
                    │ Audit                 │
                    │ Document Services     │
                    └───────┬──────┬────────┘
                            │      │
                            ▼      ▼
                    ┌──────────┐ ┌──────────────┐
                    │PostgreSQL│ │Object Storage│
                    │          │ │ S3 / MinIO   │
                    └──────────┘ └──────────────┘

                    ┌──────────────────────┐
                    │ Field / Mobile Client│
                    │ local DB + assets    │
                    │ outbox + sync        │
                    └──────────┬───────────┘
                               │ HTTPS
                               ▼
                         GlasHaus API
```

The browser client is primarily an online client.

The field/mobile client is an offline-capable client with durable local state.

---

## 4. Server Architecture

The backend is a modular monolith.

Conceptual structure:

```text
backend/app/
├── api/
├── core/
│   ├── config/
│   ├── security/
│   ├── crypto/
│   └── logging/
├── domain/
│   ├── customers/
│   ├── projects/
│   ├── work_orders/
│   ├── documents/
│   ├── offers/
│   └── users/
├── application/
│   ├── services/
│   └── sync/
└── infrastructure/
    ├── database/
    ├── storage/
    ├── mail/
    └── crypto/
```

The exact package names may evolve.

The important dependency direction is:

```text
API / transport
      ↓
Application services
      ↓
Domain logic
      ↓
Infrastructure adapters
```

Domain code must not depend directly on FastAPI request objects, database sessions or external storage clients.

---

## 5. Data Stores

### PostgreSQL

PostgreSQL is authoritative for synchronized structured business data, including as appropriate:

- users and organizations
- customers and prospects
- projects and work orders
- document metadata
- authorization data
- audit records
- synchronization metadata

Production database storage must use infrastructure-level encryption.

Additional application-level encryption is defined in `CRYPTOGRAPHY.md`.

### Object Storage

S3-compatible storage is used for binary assets such as:

- photographs
- documents
- generated PDFs
- signatures and attachments

Sensitive objects are encrypted before durable storage.

Object-store access control is an additional layer, not the primary confidentiality boundary.

### Local Mobile Storage

The field client has durable local storage.

Sensitive local data must be encrypted according to `CRYPTOGRAPHY.md`.

---

## 6. Domain Model Before Generic Synchronization

Synchronization must not dictate the business domain.

The implementation order is:

1. define the domain entity and invariants,
2. define persistence,
3. decide whether it is offline-capable,
4. define synchronization semantics,
5. implement synchronization.

Not every entity must be offline-capable, synchronizable or automatically mergeable.

---

## 7. Offline-First Boundary

Offline operation is a product requirement for the field client.

The client must be able to continue working with locally available and locally authorized data when:

- there is no network,
- the backend is unavailable,
- connectivity is intermittent,
- the application is restarted while offline.

The client distinguishes:

- locally saved,
- pending synchronization,
- synchronized,
- retryable failure,
- conflict,
- rejected.

Detailed behavior is defined in `SYNC.md`.

---

## 8. Identity

Offline-capable entities require stable client-side identity.

The exact identifier scheme belongs to the data model.

The identity must:

- exist before synchronization,
- remain stable,
- preserve local relationships,
- remain resolvable after synchronization.

The repository's UUIDv7 direction is compatible with this principle; the final identity model belongs in the domain and synchronization specifications.

---

## 9. Security Boundary

The client is untrusted.

The server independently validates:

- authentication,
- authorization,
- resource access,
- synchronization operations,
- entity versions,
- business-critical state,
- financial operations,
- signatures and document state.

Offline authentication and authorization are cached usability mechanisms, not replacements for server-side authority.

See `SECURITY.md`.

---

## 10. Documents and Sensitive Content

Sensitive content is not protected solely by transport encryption.

GlasHaus uses layered protection:

```text
Client
  │
  │ TLS
  ▼
API
  │
  ├── application-level encryption where required
  ▼
PostgreSQL / Object Storage
  │
  └── infrastructure/storage encryption
```

See `CRYPTOGRAPHY.md`.

---

## 11. Auditability

Business-critical server-side actions must be auditable.

Examples include:

- authorization-sensitive access,
- emergency access,
- document operations,
- signatures,
- important status transitions,
- financial changes,
- security events,
- synchronization conflicts.

Audit records must not contain unnecessary sensitive payloads.

---

## 12. Architectural Decision Boundary

An explicit architecture decision is required before implementation when a change materially affects:

- authentication/session architecture,
- authorization,
- encryption/key management,
- data-model assumptions affecting synchronization,
- synchronization protocol,
- document security,
- external integrations,
- deployment topology,
- introduction of a separate service,
- irreversible retention/deletion behavior.

---

## 13. Target Architecture vs Current Implementation

This document describes the target architecture.

The repository currently contains only a subset of the architecture.

Authentication, complete domain logic, application-level encryption, document storage and synchronization are not implied to exist merely because they are described here.

Progress is tracked in `Roadmap.md`.

---

## 14. Architecture Invariants

1. The server is authoritative for synchronized server state.
2. Pending local work may remain client-owned until accepted by the server.
3. Local work survives application/device restart.
4. Server authorization cannot be bypassed by offline state.
5. Sensitive-data protection is layered.
6. Business logic remains independent of transport and persistence.
7. Synchronization never silently discards user work.
8. Unsafe conflicts are explicit.
9. Binary assets use dedicated transfer and integrity handling.
10. Changes to these invariants require an explicit architecture decision.