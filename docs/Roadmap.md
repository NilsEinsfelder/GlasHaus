# GlasHaus Roadmap

## 1. Purpose

This roadmap separates long-term product vision from near-term engineering work.

The repository is currently at foundation stage.

Architecture documents describe target behavior and are not evidence that the described functionality is already implemented.

---

## 2. Current Status

Current repository foundations include:

- backend foundation,
- FastAPI foundation,
- SQLAlchemy persistence foundation,
- initial device/synchronization models,
- development and quality tooling.

The following are not yet considered implemented merely because they appear in the architecture:

- complete business domain,
- authentication,
- authorization,
- application-level encryption,
- encrypted document storage,
- document workflows,
- offline synchronization,
- mobile client.

---

# 3. Engineering Roadmap

## Phase 0 — Architecture Reset

- [ ] consolidate `ARCHITECTURE.md`
- [ ] add `SECURITY.md`
- [ ] add `CRYPTOGRAPHY.md`
- [ ] add `SYNC.md`
- [ ] rewrite roadmap around implementation order
- [ ] review `AI_RULES.md` for obsolete architecture references
- [ ] remove duplicate/obsolete architecture documentation

**Exit:** architecture documents are consistent and clearly distinguish target architecture from implementation status.

---

## Phase 1 — Security and Cryptography Foundation

- [ ] define data classification
- [ ] define authentication/session model
- [ ] define authorization model
- [ ] define device trust
- [ ] define audit model
- [ ] choose cryptographic library
- [ ] implement key-provider abstraction
- [ ] implement versioned encryption envelope
- [ ] implement encrypted document storage path
- [ ] define backup/key recovery
- [ ] add security and cryptography tests

**Exit:** one real sensitive-data path is encrypted, authorized, audited and tested end-to-end.

---

## Phase 2 — Domain Model and Persistence

Initial candidates:

- [ ] Organization
- [ ] User
- [ ] Device
- [ ] Customer / Prospect
- [ ] Project
- [ ] Work Order
- [ ] Document
- [ ] Document Version

For each entity:

- [ ] business invariants
- [ ] lifecycle
- [ ] authorization scope
- [ ] persistence model
- [ ] audit requirements
- [ ] offline-capability decision

**Exit:** the first coherent business workflow persists without speculative generic abstractions.

---

## Phase 3 — Authentication and Authorization

- [ ] user authentication
- [ ] password hashing
- [ ] session/token lifecycle
- [ ] 2FA
- [ ] role/permission model
- [ ] resource authorization
- [ ] device registration/revocation
- [ ] audit events
- [ ] security tests

**Exit:** authenticated users can access only authorized resources.

---

## Phase 4 — First Usable Web MVP

Recommended vertical slice:

```text
User
  ↓
Customer
  ↓
Project
  ↓
Work Order
  ↓
Document
```

- [ ] Next.js foundation
- [ ] authentication
- [ ] protected routes
- [ ] customer/project views
- [ ] work-order workflow
- [ ] document upload/download
- [ ] authorization UI
- [ ] end-to-end tests

Do not build every planned feature before this slice works.

---

## Phase 5 — Document and Communication Workflows

- [ ] encrypted document versions
- [ ] document metadata
- [ ] secure downloads
- [ ] PDF generation
- [ ] document preview
- [ ] controlled document sharing
- [ ] outbound mail integration
- [ ] TLS mail transport
- [ ] optional encrypted delivery
- [ ] retention/deletion policy

---

## Phase 6 — Mobile Foundation

- [ ] select React Native or Flutter
- [ ] authentication
- [ ] secure local key storage
- [ ] encrypted local database
- [ ] local domain persistence
- [ ] camera/assets
- [ ] basic offline UX
- [ ] local authorization cache

Do not implement the complete synchronization engine yet.

---

## Phase 7 — Synchronization MVP

Start with one or two real entities.

- [ ] local identity
- [ ] outbox
- [ ] push
- [ ] idempotency
- [ ] optimistic concurrency
- [ ] pull
- [ ] cursor
- [ ] explicit conflicts
- [ ] retry
- [ ] deletion/tombstones
- [ ] background sync
- [ ] sync status UI

**Exit:** a real offline workflow survives restart, retry and connectivity loss without silent data loss.

---

## Phase 8 — Domain Expansion

Incrementally add:

- [ ] protocols
- [ ] photographs
- [ ] signatures
- [ ] offers
- [ ] calendar/planning
- [ ] change orders
- [ ] warranty work
- [ ] emergency project access
- [ ] completed/archived projects

Each offline-capable entity defines its own synchronization semantics.

---

## Phase 9 — Advanced Document Automation

- [ ] OCR
- [ ] searchable documents
- [ ] advanced PDF workflows
- [ ] signature validation
- [ ] document templates
- [ ] automated document generation

---

## Phase 10 — Integrations and Automation

Only after the core product is stable:

- [ ] IDS Connect
- [ ] supplier integrations
- [ ] pricing workflows
- [ ] XML/export integrations
- [ ] notifications
- [ ] QR/RFID
- [ ] IoT integrations
- [ ] AI-assisted pricing

---

# 4. Product Vision

Long-term goals may include:

- complete customer/project management,
- mobile field operations,
- offline-first workflows,
- document management,
- signatures,
- scheduling,
- supplier integration,
- pricing automation,
- RFID/QR/IoT workflows,
- AI-assisted estimation.

These are product goals, not current engineering commitments.

---

# 5. Sequencing Rules

1. Security architecture precedes sensitive-data implementation.
2. Domain modeling precedes generic synchronization.
3. One complete vertical slice is preferred over many unfinished modules.
4. Generic infrastructure requires a real use case.
5. Offline synchronization is introduced incrementally.
6. New infrastructure requires a concrete operational reason.
7. Product-vision items enter active engineering only after explicit prioritization.
8. Every phase leaves the repository runnable and tested.

---

# 6. Definition of Done

A phase is complete only when:

- intended behavior exists,
- automated tests cover critical behavior,
- quality gates pass,
- security implications are addressed,
- documentation matches implementation,
- no known architectural contradiction is introduced.

---

# 7. Immediate Next Work

```text
Architecture Reset
      ↓
Crypto/Security Design Review
      ↓
Encrypted Document Proof-of-Concept
      ↓
Domain Model
      ↓
Authentication/Authorization
      ↓
First Web Vertical Slice
      ↓
Mobile
      ↓
Sync MVP
```

The synchronization engine is deliberately not the next implementation task.