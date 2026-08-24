# GlasHaus AI Development Rules

## 1. Purpose

This document defines the mandatory rules for AI-assisted development within the GlasHaus repository.

AI-generated code is production code and must be treated exactly like human-written code.

Every change must be:

- understandable
- maintainable
- testable
- secure
- documented
- lint-clean
- type-safe

AI assistance does not lower the review, testing, security, or documentation requirements of the project.

---

## 2. Source of Truth

The following documents define the current architectural and engineering direction of GlasHaus:

1. `docs/ARCHITECTURE.md`
2. `docs/IDENTITY_AUTHORIZATION.md`
3. `docs/PERSISTENCE_MODEL.md`
4. `docs/SECURITY.md`
5. `docs/CRYPTOGRAPHY.md`
6. `docs/SYNC.md`
7. `docs/Roadmap.md`
8. `docs/TESTING.md`

The documents have different purposes:

- Architecture documents define system structure and architectural boundaries.
- Security and authorization documents define security-sensitive behavior.
- Persistence documentation defines the intended database/domain persistence model.
- Testing documentation defines the required verification strategy.
- The roadmap defines planned work and sequencing; it is not itself a technical authority.

If two authoritative design documents conflict, implementation must stop and the conflict must be resolved first.

The documentation describes the target architecture. It does not imply that every described feature is already implemented.

Implementation status must remain distinguishable from planned or designed behavior.

---

## 3. Repository-First Development

Before making a non-trivial change, AI-assisted development must begin by inspecting the current repository state.

At minimum, inspect:

- relevant source files
- relevant tests
- relevant documentation
- current Git status
- existing implementation constraints

For architectural or security-sensitive changes, inspect all directly related design documents before proposing implementation.

Do not assume that a previous conversation, previous implementation, or previous plan still represents the current repository.

The repository is the current implementation source of truth.

The current architectural documentation is the design source of truth.

---

## 4. Architecture Before Implementation

Architectural decisions must be made before implementing code that depends on them.

When a requested change exposes an unresolved architectural question:

1. identify the question;
2. explain the relevant alternatives;
3. state the recommended option and its trade-offs;
4. obtain agreement before implementing the affected architecture.

Do not silently resolve significant architectural questions inside implementation code.

Do not introduce abstractions merely because they might be useful in the future.

Prefer the simplest architecture that satisfies the current requirements while preserving explicitly approved future extension points.

Future requirements may influence interfaces and boundaries, but must not result in speculative implementations.

---

## 5. Current Architectural Baseline

GlasHaus is a self-hosted modular monolith.

One GlasHaus server represents one company's local installation and therefore forms its own organizational and primary trust boundary.

Do not introduce a local `organization_id` multi-tenant layer unless an explicit architecture decision changes this model.

Independent GlasHaus servers are separate trust domains.

Future communication or data exchange between GlasHaus servers must therefore be designed as federation between trust domains rather than as local multi-tenancy.

---

## 6. Identity Rules

`User` is the central human identity.

A User has exactly one user type:

- `INTERNAL`
- `EXTERNAL`

A User has exactly one role.

Do not implement multiple simultaneous roles unless the architecture is explicitly changed.

Internal users may have an applicable employment hierarchy level.

External business relationships are represented separately from the User identity.

A Customer is a business/domain entity, not a User Type.

Do not use `customer` as the general external user type.

Future external relationships such as suppliers, tax advisors, or partner organizations must remain compatible with this separation.

---

## 7. Age and Personal Data

Never persist a mutable `age` value.

Persist `date_of_birth`.

Age-dependent rules must calculate the current age from the stored birth date and the relevant current or reference date.

Tests for age-dependent behavior must use explicit reference dates so that they remain deterministic.

Do not duplicate derived personal data merely for convenience unless an explicit persistence decision justifies it.

Personal data must be handled according to the applicable security and privacy requirements defined by the project.

---

## 8. Authorization

Authorization is server-side and default-deny.

The client is never the final authorization authority.

A role does not automatically grant unrestricted access to resources.

Effective authorization is determined by the authorization model defined in `docs/IDENTITY_AUTHORIZATION.md`.

The implementation must preserve the distinction between:

- User
- User Type
- Role
- Hierarchy Level
- Permission
- Permission Grant or Restriction
- Resource
- Scope
- Workspace
- Security Classification

Do not collapse these concepts merely to simplify implementation.

Permission changes must be explicit, constrained by policy, and auditable where required.

Do not implement a generic administrator mechanism that can silently grant arbitrary permissions.

Security-sensitive authorization rules must have explicit positive and negative tests.

Internal project access requires explicit project assignment where defined by the authorization model.

Do not introduce convenience or emergency access paths that bypass normal authorization without an explicit architecture and security decision.

Customer access must remain separated from the Internal Workspace.

The client-side application may hide unavailable functions for usability, but server-side authorization must always enforce the actual security boundary.

---

## 9. Persistence

The persistence model is defined by `docs/PERSISTENCE_MODEL.md`.

Implement persistence according to the documented domain model rather than designing database structure independently inside individual features.

Production schema changes use Alembic.

Do not use `Base.metadata.create_all()` as a production migration mechanism.

Database constraints should enforce important invariants where practical.

Application-level validation must not be considered a replacement for important database integrity constraints when the invariant can safely be enforced by the database.

Do not introduce speculative generic persistence abstractions.

Do not couple domain authorization decisions unnecessarily to SQLAlchemy implementation details.

Persistence changes require appropriate migration and test coverage.

---

## 10. Security

Security-sensitive behavior must be designed before implementation.

Authentication and authorization are separate concerns.

The client is never the final authorization authority.

Never commit:

- passwords
- API keys
- access tokens
- refresh tokens
- private keys
- encryption keys
- production credentials
- other secrets

Do not introduce a temporary insecure implementation with the intention of replacing it later unless that temporary behavior is explicitly approved as safe for the intended environment.

Security boundaries must fail closed.

Unexpected errors, missing identity information, invalid credentials, missing permissions, and ambiguous resource ownership must not result in access being granted.

Security-sensitive changes must include appropriate negative tests.

Security guarantees must be stated precisely. Do not describe a mechanism as secure merely because it uses a standard component such as TLS.

---

## 11. Cryptography

Use established cryptographic libraries and reviewed primitives.

Never invent cryptographic algorithms.

Never invent a custom encryption protocol without an explicit architecture and security decision.

Encryption keys must be separated from encrypted data.

Key management is part of the cryptographic design and must not be improvised during feature implementation.

Crypto implementation must follow `docs/CRYPTOGRAPHY.md`.

Do not claim end-to-end encryption merely because TLS is used.

Do not store secrets or encryption keys in source code, test fixtures intended for production, database records, or configuration committed to Git unless the documented design explicitly requires a protected representation.

Crypto changes require appropriate security tests and, where applicable, migration and recovery considerations.

---

## 12. Synchronization and Federation

Synchronization is introduced only for entities with a concrete offline or cross-system requirement.

Before synchronizing an entity, define:

- identity
- lifecycle
- authorization scope
- versioning
- deletion semantics
- conflict behavior
- retention
- binary transfer requirements
- security implications

Synchronization must never silently discard user work.

Future federation between GlasHaus servers must be treated as communication between independent trust domains.

Do not implement federation by weakening the local authorization boundary.

Federated access must have explicit identity, trust, authorization, data-sharing, and revocation semantics before implementation.

---

## 13. Testing

Every changed production behavior requires appropriate tests.

Tests must verify behavior rather than merely increase coverage.

Security-sensitive behavior requires explicit negative tests.

Authorization tests must cover denial as deliberately as they cover successful access.

Tests should cover important combinations of:

- identity
- role
- hierarchy
- permission
- grant/restriction
- scope
- resource
- workspace
- security classification
- relevant contextual conditions

Age-dependent behavior must use explicit reference dates.

Existing tests must not be weakened merely to make an implementation pass.

The project currently requires at least 90% total test coverage unless an explicit architecture or testing decision changes this requirement.

A high coverage percentage does not replace meaningful tests.

---

## 14. Code Quality

Production code must be:

- complete
- readable
- maintainable
- type-safe
- testable
- reasonably efficient
- secure by default

Prefer clear domain concepts over clever abstractions.

Avoid unnecessary indirection.

Avoid premature optimization.

Avoid duplicated business rules where a single authoritative implementation is appropriate.

Do not silently change unrelated behavior while implementing a feature.

Do not rewrite working code merely for stylistic preference.

When code structure must change because of an architectural decision, make that relationship explicit in the review.

---

## 15. Dependencies

Do not introduce a new dependency merely because it provides a convenient shortcut.

Before adding a dependency, consider:

- whether the functionality is already available in the standard library or existing dependencies;
- maintenance status;
- security history;
- licensing;
- project compatibility;
- long-term necessity.

AI must not invent dependency names, versions, APIs, or behavior.

Dependency additions should be explicitly visible in the change review.

---

## 16. AI Workflow

When AI contributes code:

1. inspect the current repository;
2. inspect relevant documentation;
3. inspect relevant tests and existing implementation;
4. identify architectural or semantic conflicts;
5. explain unresolved design questions;
6. propose the intended design where required;
7. obtain agreement for significant architectural decisions;
8. implement the complete requested change;
9. add or update tests;
10. run Ruff;
11. run formatting checks;
12. run MyPy;
13. run pytest;
14. run `git diff --check`;
15. review the resulting diff;
16. verify that documentation and implementation remain consistent.

AI must not invent:

- dependencies
- APIs
- database behavior
- security guarantees
- cryptographic properties
- external service behavior
- undocumented architectural assumptions

If the implementation contradicts the documented architecture, stop and resolve the contradiction rather than silently choosing one side.

---

## 17. Documentation Discipline

Documentation is part of the implementation.

When an architectural assumption changes, update the affected documentation before or together with the implementation.

Do not leave obsolete architecture descriptions in the repository after implementing a replacement design.

Design documents should clearly distinguish:

- implemented behavior
- approved design
- planned behavior
- explicitly deferred behavior

Avoid duplicating detailed rules across multiple documents.

Where a concept has one authoritative design document, other documents should reference that definition rather than creating competing versions.

---

## 18. Git and Change Discipline

Prefer small, logically coherent, reviewable commits.

Do not combine unrelated refactoring with feature work.

Do not automatically commit or push changes on behalf of the user.

Before a commit, review:

git status --short
git diff --check
git diff --stat
git diff

For staged changes, review the staged diff as well:

git diff --cached --check
git diff --cached --stat
git diff --cached

Tests and static checks should pass before committing.

When changes have independent architectural purposes, prefer separate commits.

Do not use Git history as a substitute for maintaining the current documentation. Git provides history; the repository documentation must describe the current approved design.

---

## 19. Definition of Done

A change is complete only when all applicable requirements have been satisfied:

implementation is complete
tests exist
relevant negative tests exist for security-sensitive behavior
tests pass
Ruff passes
formatting passes
MyPy passes
documentation is updated
security implications are considered
no secrets were introduced
required migrations exist
git diff --check passes
the resulting diff has been reviewed
implementation and documentation do not contradict each other

For architectural changes, the corresponding design documentation must be updated before the change is considered complete.