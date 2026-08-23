# GlasHaus Roadmap

## 1. Purpose

This roadmap defines the implementation order for GlasHaus.

It separates:

- current implementation status,
- engineering priorities,
- long-term product vision.

Architecture documents describe the target system. They do not imply that the corresponding functionality is implemented.

---

# 2. Current Status

GlasHaus is currently at the backend-foundation stage.

Implemented foundations include:

- Python/FastAPI application,
- SQLAlchemy persistence foundation,
- UUIDv7 identifier generation,
- initial Device model,
- initial synchronization-state model,
- automated tests,
- Ruff,
- MyPy,
- pytest,
- Alembic dependency.

Not yet implemented:

- business domain,
- authentication,
- authorization,
- application-level encryption,
- key management,
- document storage,
- document workflows,
- mobile client,
- synchronization engine.

The existing Device and SyncState models are treated as foundation metadata and are not currently expanded into a generic synchronization engine.

---

# 3. Phase 1 — Backend Foundation

## Goal

Create a clean, reproducible backend foundation.

### Tasks

- [x] FastAPI application
- [x] basic API routing
- [x] configuration layer
- [x] SQLAlchemy foundation
- [x] development/test database support
- [ ] production PostgreSQL verification
- [ ] Alembic migration workflow
- [ ] database integration tests
- [ ] logging foundation
- [ ] consistent application error handling
- [ ] CI quality gates

### Exit Criteria

The backend can be installed, started, migrated and tested reproducibly.

---

# 4. Phase 2 — Security Architecture

## Goal

Define the security model before implementing sensitive application behavior.

### Tasks

- [ ] data classification
- [ ] authentication architecture
- [ ] session/token architecture
- [ ] authorization model
- [ ] RBAC/ABAC boundary
- [ ] resource authorization
- [ ] device trust model
- [ ] audit model
- [ ] threat model

### Exit Criteria

Security boundaries are explicit and implementation decisions are documented.

---

# 5. Phase 3 — Cryptography

## Goal

Protect sensitive stored and transmitted content correctly.

### Tasks

- [ ] select cryptographic libraries
- [ ] define encryption envelope
- [ ] define key hierarchy
- [ ] define key storage/KMS boundary
- [ ] define key rotation
- [ ] implement crypto provider abstraction
- [ ] implement encrypted document proof-of-concept
- [ ] implement integrity verification
- [ ] define backup/key recovery
- [ ] add cryptography tests

### Exit Criteria

One real sensitive document path is protected end-to-end and tested.

---

# 6. Phase 4 — First Domain Model

## Goal

Implement the first real business workflow.

Initial direction:

```text
Customer
   ↓
Project
   ↓
Work Order
   ↓
Document
```

The exact first entity may be adjusted during domain modeling.

For each entity define:

- identity,
- lifecycle,
- invariants,
- persistence,
- authorization,
- audit requirements,
- sensitivity classification,
- offline capability.

### Exit Criteria

At least one complete domain workflow exists without speculative synchronization infrastructure.

---

# 7. Phase 5 — Authentication and Authorization

## Goal

Make the first domain workflow secure.

### Tasks

- [ ] user identity
- [ ] authentication
- [ ] password hashing
- [ ] session lifecycle
- [ ] 2FA
- [ ] role permissions
- [ ] resource authorization
- [ ] device registration
- [ ] device revocation
- [ ] authorization tests
- [ ] audit events

### Exit Criteria

The server reliably determines who may access and modify every implemented protected resource.

---

# 8. Phase 6 — Browser MVP

## Goal

Deliver the first usable web workflow.

### Tasks

- [ ] Next.js foundation
- [ ] authentication UI
- [ ] protected routes
- [ ] customer/project views
- [ ] work-order workflow
- [ ] document workflow
- [ ] API integration
- [ ] end-to-end tests

### Exit Criteria

A real user can complete the first core workflow through the browser.

---

# 9. Phase 7 — Mobile Foundation

## Goal

Prepare the field client without prematurely implementing generic sync.

### Tasks

- [ ] select mobile framework
- [ ] authentication
- [ ] secure local key storage
- [ ] encrypted local database
- [ ] local domain persistence
- [ ] offline UX
- [ ] camera/assets

### Exit Criteria

The mobile client can securely work with locally available data.

---

# 10. Phase 8 — Synchronization MVP

## Goal

Synchronize one real offline-capable workflow.

### Tasks

- [ ] local identity
- [ ] atomic local mutation + outbox
- [ ] push
- [ ] idempotency
- [ ] optimistic concurrency
- [ ] pull
- [ ] durable cursor
- [ ] conflict handling
- [ ] retries
- [ ] deletion/tombstones
- [ ] binary asset transfer
- [ ] resynchronization

### Exit Criteria

A real offline workflow survives:

- application restart,
- device restart,
- network loss,
- retry,
- server failure,

without silent data loss.

---

# 11. Phase 9 — Domain Expansion

Potential modules:

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
- [ ] emergency access

Each module receives explicit authorization, security and synchronization semantics.

---

# 12. Phase 10 — Document Automation

- [ ] PDF generation
- [ ] document templates
- [ ] OCR
- [ ] searchable documents
- [ ] signature workflows
- [ ] document sharing
- [ ] retention/deletion workflows

---

# 13. Phase 11 — External Integrations

Only after the core product is stable:

- [ ] IDS Connect
- [ ] supplier integrations
- [ ] ZUGFeRD/e-invoicing
- [ ] XML export
- [ ] pricing workflows
- [ ] notifications

---

# 14. Phase 12 — Advanced Automation

Potential future capabilities:

- [ ] RFID
- [ ] QR workflows
- [ ] IoT
- [ ] AI-assisted estimation
- [ ] AI-assisted pricing
- [ ] recommendation systems

These remain product vision until explicitly prioritized.

---

# 15. Sequencing Rules

1. Architecture precedes implementation.
2. Security architecture precedes sensitive-data implementation.
3. Domain modeling precedes generic synchronization.
4. A real use case precedes a generic abstraction.
5. One complete vertical slice is preferred over many incomplete modules.
6. Offline synchronization is introduced incrementally.
7. Security guarantees must never be claimed before they are implemented and tested.
8. Every completed phase leaves the repository runnable and testable.