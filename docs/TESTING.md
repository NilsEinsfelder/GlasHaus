# GlasHaus Testing Strategy

## 1. Purpose

Testing is part of the GlasHaus architecture and Definition of Done.

Tests must validate:

- domain behavior
- authorization boundaries
- authentication behavior
- persistence invariants
- cryptographic invariants
- synchronization semantics
- API contracts
- security-critical failure modes

Coverage is a quality indicator, not the purpose of testing.

Tests must verify both what the system permits and what it must never permit.

---

## 2. Testing Principles

GlasHaus follows these principles:

1. Security boundaries require explicit tests.

2. Negative tests are first-class tests.

3. Authorization tests must verify default-deny behavior.

4. Persistence tests must verify database constraints as well as application behavior.

5. Synchronization tests must verify failure and retry behavior, not only successful synchronization.

6. Cryptographic tests must verify integrity and failure behavior, not only successful decryption.

7. Tests must be deterministic.

8. Time-dependent behavior must use explicit reference times.

9. Tests must not depend on production secrets or external infrastructure unless explicitly required by an integration test.

10. Tests must not weaken security guarantees for convenience.

11. Architectural invariants should be represented by automated tests where practical.

12. A passing test suite does not replace security review for security-critical design changes.

---

## 3. Test Layers

GlasHaus uses the following test layers:

1. unit tests

2. persistence/integration tests

3. API tests

4. authentication tests

5. authorization/security tests

6. cryptography tests

7. synchronization tests

8. end-to-end tests when the corresponding clients exist

9. migration tests where schema changes are introduced

Each layer has a defined purpose.

A test should be placed at the lowest layer that can meaningfully verify the behavior.

---

## 4. Unit Tests

Unit tests cover deterministic domain behavior without requiring external infrastructure.

Examples include:

- age calculation
- role/user-type compatibility
- hierarchy behavior
- role defaults
- hierarchy defaults
- effective permission calculation
- explicit grants
- explicit restrictions
- permission expiration
- scope evaluation
- workspace rules
- domain invariants
- conflict classification
- synchronization state transitions

Age-dependent tests must use an explicit reference date.

Tests must not depend on the current system clock implicitly.

---

## 5. Authorization Tests

Authorization is a security boundary and requires comprehensive positive and negative testing.

Tests must cover at least:

- valid authorization
- unauthenticated requests
- inactive users
- invalid user types
- invalid role/user-type combinations
- insufficient permissions
- explicit permission restrictions
- explicit permission grants
- expired grants
- invalid scopes
- project scope mismatch
- missing project assignment
- wrong project
- missing customer relationship
- wrong customer
- missing customer project access
- Internal Workspace access
- Customer Workspace access
- forbidden workspace access
- hierarchy differences
- age-dependent restrictions
- mandatory policy constraints
- privileged permission administration
- unauthorized permission delegation
- self-escalation attempts
- external users attempting internal access
- access through manipulated resource identifiers
- access through direct object URLs
- unauthorized search results

Every important allow rule should have a corresponding deny case.

---

## 6. Authorization Invariants

The following security invariants require explicit automated coverage:

1. Default is deny.

2. An inactive user cannot access protected resources.

3. An internal user without project assignment cannot access project-specific resources.

4. Knowing a project ID does not grant access.

5. Knowing a project address does not grant access.

6. Knowing a document ID does not grant access.

7. Customer access does not imply Internal Workspace access.

8. External users cannot cross workspace boundaries.

9. Permission grants cannot bypass mandatory policy constraints.

10. A user cannot grant permissions they are not authorized to delegate.

11. A restriction cannot be bypassed by a less-specific inherited permission.

12. Authorization is evaluated server-side.

13. Partial resource representations do not contain unauthorized fields.

14. Unauthorized resources are not exposed through search.

15. Authorization is evaluated before protected content is decrypted.

---

## 7. Authentication Tests

Authentication tests cover the lifecycle of authenticated security contexts.

Required scenarios include:

- valid login
- invalid credentials
- disabled/inactive user
- session creation
- session expiration
- session revocation
- logout
- revoked device
- device registration
- device lifecycle transitions
- 2FA
- recovery
- invalid recovery attempts
- suspicious authentication behavior where implemented
- concurrent/revoked sessions where applicable

Tests must verify that authentication failure cannot result in an authenticated authorization context.

Secrets must never appear in:

- test output
- logs
- snapshots
- fixtures
- committed test data

---

## 8. Persistence Tests

Persistence tests verify both relational integrity and application persistence behavior.

Required coverage includes:

- primary key behavior
- UUIDv7 identifier persistence
- foreign keys
- uniqueness constraints
- nullability constraints
- check constraints where applicable
- valid relationships
- invalid relationships
- user lifecycle
- employment history
- role/user-type compatibility
- permission grant persistence
- permission grant lifecycle
- customer relationships
- project/customer relationships
- project assignments
- customer project access
- workspace boundaries
- document/workspace relationships
- document/project relationships
- document versions
- historical state
- deactivation behavior
- transaction atomicity
- concurrent updates where applicable

Database constraints must complement application validation.

A test must not assume that application validation alone is sufficient to maintain relational integrity.

---

## 9. Migration Tests

Schema changes require migration testing.

Migration tests must verify:

- migration applies successfully to the supported starting schema
- migration produces the expected schema
- existing required data is preserved
- constraints are correctly introduced
- indexes are correctly introduced
- downgrade behavior is explicitly understood where supported
- irreversible operations are documented
- representative production-like data remains valid

Production schema changes must use Alembic.

A model change without the corresponding migration is incomplete when the persisted schema is affected.

---

## 10. API Tests

API tests verify externally observable server behavior.

They should cover:

- authentication requirements
- authorization requirements
- request validation
- response validation
- correct HTTP status behavior
- resource scoping
- workspace boundaries
- error behavior
- pagination where applicable
- search authorization
- upload/download authorization
- idempotency where applicable
- concurrency behavior where applicable

API tests must verify that sensitive fields are absent when the caller is not authorized to receive them.

A client-side field-hiding mechanism is not considered an authorization test.

---

## 11. Data Minimization Tests

Where resources have multiple visibility levels, tests must verify the returned representation.

For example:

A caller with:

    schedule.view_availability

may receive:

    technician
    availability

but must not receive:

    customer
    project address
    appointment details
    internal notes

Tests must assert both the presence of permitted fields and the absence of forbidden fields.

The same principle applies to:

- API responses
- search results
- exports
- synchronization payloads
- downloaded metadata
- federation payloads
- future client-specific representations

---

## 12. Cryptography Tests

Cryptographic implementations require explicit success and failure tests.

Required scenarios include:

- encryption/decryption round trip
- wrong key
- wrong key version
- ciphertext tampering
- authentication-tag failure
- metadata tampering
- nonce uniqueness
- invalid nonce handling
- key rotation
- current key selection
- decrypt-only historical keys
- retired keys
- invalid encryption version
- corrupted ciphertext
- corrupted object detection
- authorization before decryption
- encrypted local storage
- backup recovery
- key availability during recovery

Known test vectors should be used where applicable.

Tests must never use production cryptographic keys.

Cryptographic tests must verify the behavior of the selected cryptographic library and the GlasHaus encryption envelope.

They must not attempt to prove the mathematical security of standard cryptographic primitives.

---

## 13. Synchronization Tests

Synchronization tests must cover the complete operation lifecycle.

Required scenarios include:

- local mutation + outbox atomicity
- application restart with pending operations
- device restart with pending operations
- network loss
- server outage
- retry
- idempotency
- lost response followed by retry
- duplicate operation submission
- concurrency conflict
- rejected operation
- authorization change
- project access revocation
- expired authorization
- cursor advancement
- atomic change application + cursor advancement
- partial batch failure
- tombstones
- binary asset transfer
- interrupted asset transfer
- integrity verification
- resynchronization
- newly granted access
- preservation of pending local work

Tests must verify that a retry cannot duplicate a successful server-side mutation.

---

## 14. Synchronization Security Tests

Synchronization must be tested as an authorization boundary.

Tests must verify that:

1. Offline authorization is not permanent authorization.

2. The server re-evaluates authorization when receiving a mutation.

3. A revoked project assignment causes subsequent unauthorized mutations to be rejected.

4. Unauthorized synchronization data is not included in a pull response.

5. A newly granted project does not expose unrelated projects.

6. A cursor cannot be used to bypass authorization.

7. A resynchronization cannot become an unrestricted database export.

8. Sensitive synchronization payloads remain protected.

9. Pending local work is not silently discarded during resynchronization.

10. Replayed operations do not duplicate domain mutations.

---

## 15. Conflict Tests

Conflict handling is domain-specific.

Tests must verify that conflicts are not silently converted into overwrites.

Examples include:

- append-only photographs
- mergeable metadata
- concurrent project metadata updates
- scheduling conflicts
- signed document conflicts
- financial document conflicts

For each synchronizable entity, the domain must define whether a concurrent mutation is:

- automatically mergeable
- last-writer-wins where explicitly acceptable
- rejected
- requires review
- immutable

The synchronization engine must not invent domain semantics.

---

## 16. Binary Asset Tests

Binary assets use a dedicated synchronization path.

Tests must cover:

- authorization
- content validation
- content digest verification
- encryption
- upload retry
- download retry
- interrupted transfer
- resumability where supported
- duplicate transfer handling
- size limits
- corrupted content
- unauthorized asset access
- expired/invalid asset references

Object-storage access must never bypass application authorization.

---

## 17. Federation Tests

Federation is a future trust boundary.

When implemented, federation tests must cover:

- peer authentication
- trust establishment
- invalid peer
- revoked peer
- message integrity
- invalid signature
- replay protection
- malformed messages
- authorization
- resource scope
- key rotation
- trust revocation
- protocol/version incompatibility
- failure handling

A remote authorization decision must never automatically become a local authorization decision.

---

## 18. Device and Offline Tests

Device and offline workflows require explicit testing because the server may temporarily be unavailable.

Tests must cover:

- device registration
- device activation
- device revocation
- offline session lifetime
- cached authorization lifetime
- encrypted local storage
- expired offline authorization
- synchronization after revocation
- synchronization after permission changes
- synchronization after project reassignment
- recovery after application restart
- recovery after device restart

Offline behavior must remain bounded by the security policy.

---

## 19. Audit Tests

Security-sensitive operations should generate the required audit events.

Tests should verify:

- actor identity
- action
- resource type
- resource ID
- result
- timestamp
- correlation/request identifier
- relevant authorization context where required

Tests must also verify that audit records do not unnecessarily contain:

- passwords
- authentication tokens
- private keys
- encryption keys
- plaintext secrets
- unnecessarily sensitive document content

Audit failures must not silently turn into successful security-sensitive operations where the architecture requires auditability as a prerequisite.

---

## 20. Negative Testing

Negative testing is a core security requirement.

Tests should deliberately attempt:

- unauthorized resource access
- invalid identifiers
- guessed identifiers
- manipulated URLs
- wrong project IDs
- wrong customer IDs
- unauthorized workspace access
- expired permissions
- revoked devices
- revoked project assignments
- invalid permission delegation
- self-escalation
- malformed synchronization operations
- replayed operations
- tampered ciphertext
- tampered synchronization payloads
- invalid federation messages

The expected result must be explicit and deterministic.

---

## 21. Property and Invariant Testing

Where practical, property-based or invariant tests should be used for security-critical state transitions.

Examples:

- authorization never allows an invalid principal
- expired grants never contribute to effective permissions
- revoked devices cannot create valid authenticated sessions
- duplicate operation IDs cannot create duplicate mutations
- cursor advancement never skips unapplied changes
- tampered ciphertext never decrypts successfully
- unauthorized resources never appear in authorized search results

Property-based testing is complementary to scenario-based tests.

---

## 22. Test Data and Secrets

Test data must be synthetic unless a specific controlled fixture is required.

Production data must not be copied into the normal test suite.

Test secrets must be:

- generated for testing
- isolated from production
- excluded from source control when sensitive
- rotated where appropriate

Private keys and encryption keys used in tests must never be production keys.

Tests must cleanly distinguish:

- test credentials
- development credentials
- production credentials

---

## 23. External Dependencies

Tests should avoid unnecessary dependence on external services.

Where external dependencies are required, the test architecture should provide controlled test doubles or dedicated integration environments.

Examples include:

- object storage
- mail delivery
- KMS/secret manager
- federation peers
- external identity providers

Security-critical integrations should additionally have real integration tests against supported production-like implementations before release.

---

## 24. Determinism and Time

Tests must be deterministic.

Time-dependent behavior must use injectable or explicitly controlled reference time.

This applies to:

- age calculation
- permission validity
- employment validity
- session expiration
- device authorization
- temporary grants
- synchronization timestamps
- key rotation
- retention behavior

Tests must not rely on arbitrary sleeps or the wall clock when deterministic time control is possible.

---

## 25. Coverage

The project currently requires at least 90% total test coverage.

Coverage must not be increased by:

- deleting tests
- weakening assertions
- excluding meaningful production code
- replacing behavior tests with trivial execution tests
- artificially executing code without validating behavior

Missing coverage should normally result in a test for meaningful behavior.

Coverage thresholds apply to quality control and do not replace architectural or security testing.

Security-critical code may require substantially stronger coverage than the global minimum.

---

## 26. Quality Gate

A normal backend change should pass:

    ruff check .
    ruff format --check .
    mypy app
    pytest
    git diff --check

Where applicable, changes must additionally pass:

- migration tests
- integration tests
- synchronization tests
- cryptography tests
- API tests
- end-to-end tests
- security-specific test suites

The exact CI command set is defined by the project tooling.

A change must not be considered complete merely because the default unit test command passes.

---

## 27. Definition of Done

A security-, persistence-, synchronization- or domain-relevant change is complete only when:

- behavior is tested
- relevant negative/security cases are tested
- affected architectural invariants are tested
- API behavior is tested where applicable
- migrations exist where required
- documentation is updated
- quality checks pass
- no unrelated regressions are introduced

Security-sensitive changes require explicit review of the affected security boundary.

---

## 28. Architectural Test Invariants

The following invariants should remain continuously testable:

1. Authorization is server-side.

2. Default is deny.

3. Internal project access requires explicit assignment.

4. Customer project access requires the applicable customer relationship and project access.

5. Customer users cannot access Internal Workspace.

6. Permission administration is itself authorized.

7. Permission grants cannot bypass mandatory policy constraints.

8. Sensitive data is not exposed through unauthorized fields, search or synchronization.

9. Authorization is evaluated before protected content is decrypted.

10. Local mutations and required outbox entries are atomic.

11. Synchronization operations are idempotent.

12. Cursor advancement is atomic with change application.

13. Conflicts are explicit and never silently overwrite protected domain state.

14. Pending offline work survives synchronization failure.

15. Cryptographic tampering is detected.

16. Production secrets are never used in tests.

17. Database relationships are enforced by persistence constraints where applicable.

18. Historical security-relevant state is preserved according to retention policy.

19. Federation does not bypass local authorization.

20. Security-critical failures fail closed.