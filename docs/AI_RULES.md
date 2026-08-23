# GlasHaus AI Development Rules

## 1. Purpose

This document defines the mandatory rules for AI-assisted development within the GlasHaus repository.

AI-generated code is treated exactly like human-written production code.

Every change must therefore be:

- understandable
- maintainable
- testable
- secure
- documented
- lint-clean
- type-safe

Detailed testing requirements are defined in `docs/TESTING.md`.

---

## 2. Source of Truth

The following documents define the current architectural direction:

1. `docs/ARCHITECTURE.md`
2. `docs/SECURITY.md`
3. `docs/CRYPTOGRAPHY.md`
4. `docs/SYNC.md`
5. `docs/Roadmap.md`

If another document conflicts with these documents, the conflict must be resolved before implementing architectural changes.

The architecture documents describe target behavior. They do not imply that the functionality is already implemented.

---

## 3. Core Development Principles

### 3.1 Python-first Backend

The backend is implemented primarily in Python.

Current backend foundation:

- Python 3.14
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL in production
- SQLite for development/tests where useful

Major technology changes require an explicit architectural decision.

### 3.2 Minimal Complexity

Do not introduce abstractions merely because they may be useful later.

Prefer:

- simple modules,
- explicit dependencies,
- small interfaces,
- concrete implementations,
- incremental evolution.

Generic frameworks for synchronization, authorization, encryption or domain behavior must not be built before a real use case requires them.

### 3.3 Vertical Slices

Prefer completing one coherent workflow over implementing many disconnected subsystems.

A vertical slice should normally include the required:

- domain behavior,
- persistence,
- API,
- tests,
- authorization,
- security considerations.

---

## 4. Architecture and Dependency Direction

The backend follows this conceptual dependency direction:

```text
API / Transport
      ↓
Application Services
      ↓
Domain
      ↓
Infrastructure
```

Infrastructure contains technical implementations such as:

- database access,
- object storage,
- mail,
- cryptographic providers,
- external integrations.

Domain logic must not depend directly on FastAPI, HTTP requests, SQLAlchemy sessions or external service clients.

API endpoints must remain thin.

Business rules belong in application/domain code.

Database access belongs in infrastructure/data-access components.

---

## 5. Code Quality

Production code must:

- pass Ruff,
- pass Ruff formatting,
- pass MyPy,
- use meaningful names,
- use appropriate type annotations,
- avoid unnecessary complexity,
- follow separation of concerns.

Quality gates must not be bypassed without documented justification.

---

## 6. Testing

Every production behavior introduced or changed by AI must have appropriate automated tests.

Tests must validate behavior rather than merely increase coverage.

Existing tests must not be weakened or removed merely to make a change pass.

Critical security, persistence, synchronization and domain behavior requires explicit tests.

The repository's `docs/TESTING.md` is part of the Definition of Done.

---

## 7. Documentation

Public functions and APIs must be documented where appropriate.

Production functions require:

- type annotations,
- return type annotations,
- clear naming,
- concise docstrings where appropriate.

Complex logic should contain comments explaining intent where the code alone is insufficient.

Comments must not merely restate the implementation.

Architectural decisions must be documented before or together with implementation.

---

## 8. Database Rules

Production database schema changes MUST use Alembic migrations.

Never rely on:

```python
Base.metadata.create_all()
```

for production schema management.

`create_all()` may be used by isolated development/test helpers when appropriate.

Production database changes must be reproducible from migrations.

Database constraints should be enforced at the database layer where practical.

---

## 9. Security First

Security applies to every component.

Never commit:

- passwords,
- API keys,
- private keys,
- access tokens,
- refresh tokens,
- database credentials,
- encryption keys,
- production secrets.

Secrets must be supplied through secure configuration or secret-management infrastructure.

Authentication and authorization are separate concerns.

The client must never be treated as the final authorization authority.

---

## 10. Cryptography

Cryptographic implementations must use established, reviewed primitives and libraries.

Never invent cryptographic algorithms.

Encryption decisions must follow `docs/CRYPTOGRAPHY.md`.

Password storage must use password-specific password hashing.

Encryption keys must be separated from encrypted application data.

Crypto implementation must not begin before the corresponding architecture decision has been documented.

---

## 11. Sensitive Data

Sensitive information must be handled according to:

- `docs/SECURITY.md`
- `docs/CRYPTOGRAPHY.md`

Logs must never contain unnecessary sensitive information.

Do not expose:

- passwords,
- tokens,
- encryption keys,
- document contents,
- unnecessary personal data.

---

## 12. Authentication and Authorization

Authentication establishes identity.

Authorization determines whether an authenticated actor may perform an action.

The server is authoritative for:

- authentication state,
- authorization,
- resource access,
- device access,
- synchronization operations.

Offline permissions are usability mechanisms and do not replace server authorization.

---

## 13. Offline Synchronization

GlasHaus is designed to support offline field workflows.

However, synchronization is implemented incrementally.

An entity must not become synchronizable merely because a generic synchronization framework exists.

Before synchronizing an entity, define:

- identity,
- lifecycle,
- authorization scope,
- versioning,
- deletion semantics,
- conflict policy,
- retention requirements.

Synchronization must never silently overwrite user work.

See `docs/SYNC.md`.

---

## 14. API Design

API endpoints must:

- validate input,
- validate authorization,
- return documented responses,
- use appropriate HTTP semantics,
- avoid leaking internal implementation details,
- delegate business behavior to application/domain layers.

Endpoints must remain thin.

---

## 15. Error Handling

Errors must be handled deliberately.

Do not:

- silently ignore exceptions,
- expose stack traces,
- expose secrets,
- use broad exception handling without justification.

User-facing responses must not expose internal implementation details.

Logs may contain diagnostic information only when appropriate and safe.

---

## 16. AI-Assisted Development

When AI contributes code:

1. inspect the existing implementation first,
2. respect the current architecture,
3. identify affected files,
4. implement the complete requested behavior,
5. add or update tests,
6. update documentation where required,
7. run quality checks,
8. review the resulting diff.

AI must not invent:

- dependencies,
- APIs,
- configuration options,
- security guarantees,
- database behavior.

Dependencies and external APIs must be verified before use.

---

## 17. Change Discipline

Changes should be:

- focused,
- reviewable,
- minimal,
- reversible where practical.

Do not mix unrelated refactoring into a feature change without justification.

Do not rewrite working code merely for stylistic preference.

Preserve existing behavior unless the change explicitly requires otherwise.

---

## 18. Architectural Decision Triggers

An explicit architecture review is required before introducing or substantially changing:

- authentication,
- authorization,
- encryption,
- key management,
- synchronization,
- document storage,
- external integrations,
- deployment topology,
- data retention/deletion,
- separate services,
- irreversible data migrations.

---

## 19. Definition of Done

An AI-assisted production change is complete only when:

- implementation is complete,
- appropriate tests exist,
- tests pass,
- Ruff passes,
- formatting passes,
- MyPy passes,
- documentation is updated where required,
- security implications have been considered,
- no secrets were introduced,
- database migrations exist where required,
- the working tree contains only intentional changes.

The applicable requirements in `docs/TESTING.md` are part of the Definition of Done.