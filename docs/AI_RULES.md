# GlasHaus AI Development Rules

## 1. Purpose

This document defines the mandatory rules for AI-assisted development
within the GlasHaus repository.

AI-generated code is treated exactly like human-written production code.

All changes must therefore be:

- understandable
- maintainable
- testable
- secure
- documented
- lint-clean
- type-safe

Detailed testing rules are defined in `docs/TESTING.md`.

---

## 2. Core Development Principles

### 2.1 Python-first Backend

The backend is implemented primarily in Python.

The current backend technology stack includes:

- Python
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL

Technology decisions must be documented before introducing major
architectural dependencies.

---

### 2.2 Code Quality

All production code must:

- pass Ruff
- pass MyPy
- follow the repository formatting rules
- use meaningful names
- use appropriate type annotations
- avoid unnecessary complexity
- follow separation of concerns

No code may intentionally bypass configured quality gates without
documented justification.

---

### 2.3 Testing

Production behavior must be covered by appropriate automated tests.

Testing requirements are defined in:

docs/TESTING.md

When AI introduces or modifies production behavior, the corresponding
tests must be created or updated as part of the same change.

Tests must validate behavior rather than merely increasing coverage.

## 3. Documentation
### 3.1 Functions

Every production function must include:

type annotations
a return type annotation
a docstring where appropriate

Public functions and APIs must be documented.

Docstrings should follow Google-style conventions.

### 3.2 Complex Logic

Non-trivial logic must contain concise comments explaining the reason
for the implementation where the code itself is not sufficiently clear.

Comments must explain intent rather than restating obvious code.

### 3.3 Architectural Decisions

Major architectural decisions must be documented before or together with
their implementation.

Examples include:

authentication architecture
encryption architecture
database architecture
offline synchronization
external integrations
document storage
key management

## 4. Security First

Security requirements apply to every component of GlasHaus.

### 4.1 Secrets

The following must never be committed to the repository:

passwords
API keys
private keys
access tokens
refresh tokens
database credentials
encryption keys
production secrets

Configuration containing secrets must use an appropriate secure mechanism,
such as environment variables or a dedicated secret-management system.

### 4.2 Cryptography

Sensitive information must use established, modern cryptographic mechanisms
appropriate to the specific use case.

Cryptographic algorithms must not be selected merely because they are
familiar or convenient.

Password storage must use password-specific password hashing mechanisms.

Encryption key management must be separated from encrypted application data.

Cryptographic decisions must be documented before implementation.

### 4.3 Authentication and Authorization

Authentication and session management must use a documented secure
architecture.

Authorization must support the GlasHaus permission model, including:

authentication
RBAC
ABAC
resource-level authorization

Authentication must never be treated as authorization.

### 4.4 Sensitive Data

Personally identifiable information, financial information, documents,
credentials and other sensitive information must be handled according to
the GlasHaus security architecture.

Logging must never expose sensitive information.

## 5. Architecture
### 5.1 Separation of Concerns

The backend must maintain clear separation between:

API
 ↓
Service
 ↓
Repository
 ↓
Database

Controllers/API endpoints must not contain business logic.

Business rules belong in the appropriate service/domain layer.

Database access belongs in repository/data-access components where
appropriate.

### 5.2 Dependency Direction

Dependencies should point toward well-defined abstractions.

Infrastructure-specific implementation details must not unnecessarily
leak into business logic.

### 5.3 Modularity

Components should have a single clear responsibility.

Large modules must be split when doing so improves maintainability,
testability or security.

## 6. Offline Synchronization

GlasHaus is designed as an offline-capable system.

Data models participating in synchronization must provide the information
required for deterministic synchronization.

Depending on the entity, this may include:

stable identifiers
version information
timestamps
synchronization state
conflict information
deletion/tombstone information

Offline synchronization behavior must be explicitly defined for each
synchronized entity.

Conflict resolution must never silently overwrite data without a defined
policy.

## 7. Database and Data Integrity

Database changes must be implemented through Alembic migrations.

Production database schema changes must never rely on manual undocumented
database modifications.

Data integrity constraints should be enforced at the appropriate layer,
preferably as close to the database as practical.

## 8. API Design

APIs must:

validate input
validate authorization
return documented responses
avoid leaking internal implementation details
handle errors consistently
use appropriate HTTP semantics

API endpoints must remain thin and delegate business logic to services.

## 9. Error Handling

Errors must be handled deliberately.

Do not:

silently ignore exceptions
expose stack traces to users
expose secrets or sensitive information
use overly broad exception handling without justification

Errors should be logged appropriately while keeping sensitive information
out of logs.

## 10. AI-Assisted Development

When AI contributes code:

The complete implementation must be provided unless the task explicitly
requests a partial implementation.
No placeholders may be introduced unless explicitly requested.
Existing project architecture must be respected.
Existing tests must not be weakened or removed merely to make a change
pass.
New behavior must include appropriate tests.
Existing tests must continue to pass.
Ruff must pass.
MyPy must pass.
Documentation must be updated when behavior or architecture changes.
Security implications must be considered for security-sensitive changes.

AI must not invent dependencies, APIs or configuration options without
verification.

## 11. Change Discipline

Changes should be:

focused
reviewable
minimal
reversible where practical

Unrelated refactoring must not be mixed into feature changes unless
explicitly justified.

Existing behavior must not be changed unintentionally.

## 12. Definition of Done

AI-assisted production changes are considered complete only when:

implementation is complete
appropriate tests exist
tests pass
Ruff passes
MyPy passes
documentation is updated where required
security implications have been considered
no secrets are introduced
database migrations exist where required
the working tree contains only intentional changes

The applicable requirements in docs/TESTING.md are part of the
Definition of Done.