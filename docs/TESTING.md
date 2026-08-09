# GlasHaus Testing Strategy

## 1. Purpose

This document defines the testing strategy and mandatory testing
requirements for the GlasHaus project.

The purpose of the testing strategy is to ensure that GlasHaus is:

- functionally correct
- secure
- maintainable
- reliable
- predictable under failure conditions
- safe for offline operation
- suitable for production use

Tests are part of the implementation and are not considered an optional
step after development.

When production behavior is introduced or changed, the corresponding tests
must be created or updated as part of the same change.

This document complements `docs/AI_RULES.md`.

The requirements in this document apply to both human-written and
AI-assisted code.

## 2. Testing Principles

GlasHaus follows these fundamental testing principles.

### 2.1 Test Behavior

Tests should verify observable behavior and business requirements rather
than implementation details.

Tests must remain useful when internal implementation details change.

### 2.2 Test the Failure Cases

Tests must cover relevant failure conditions in addition to successful
execution.

Examples include:

- invalid input
- unauthorized access
- insufficient permissions
- missing resources
- database failures
- network failures
- expired authentication
- synchronization conflicts
- malformed external data

### 2.3 Deterministic Tests

Tests must be deterministic.

Tests must not depend on:

- execution order
- developer-specific configuration
- local filesystem state
- uncontrolled external services
- current time without explicit control
- random values without deterministic seeding or controlled generation

### 2.4 Isolation

Unit tests should be isolated from external infrastructure.

Integration tests may use controlled infrastructure such as temporary
databases or dedicated test services.

### 2.5 No Test Weakening

Production code must not be changed solely to make a test pass if the
change would weaken the intended behavior or security of the application.

Tests must not be deleted or weakened merely because they expose a defect.

### 2.6 Security Testing

Security-sensitive functionality requires explicit tests.

Authentication, authorization, data access, document handling and
synchronization must be tested against both permitted and prohibited
operations.

### 2.7 Test Naming

Test names must clearly describe the behavior being tested.

Prefer names such as:

test_user_cannot_access_project_of_another_customer
test_admin_can_assign_abac_permission
test_expired_access_token_is_rejected

Avoid vague names such as:

test_user
test_auth
test_project


---

## 3. Test Pyramid


GlasHaus follows a test pyramid.

The majority of tests should be fast unit tests.

                ┌───────────────┐
                │   E2E Tests   │
                │  Few / Slow   │
                └───────┬───────┘
                        │
              ┌─────────▼─────────┐
              │ Integration Tests │
              │  Moderate / Few   │
              └─────────┬─────────┘
                        │
        ┌───────────────▼───────────────┐
        │          Unit Tests            │
        │        Many / Fast             │
        └───────────────────────────────┘

Test Levels
Test level	            Purpose	Typical                             execution
Unit	                Individual functions and components	        Every commit
Integration	            Multiple backend components	                Every CI run
API / Contract	        API behavior and schemas	                Every CI run
Database	            Persistence and migrations	                Every CI run
Security	            Security boundaries and abuse cases	        Every CI run
Offline Sync	        Synchronization and conflicts	            Every CI run
E2E	                    Complete user workflows	                    CI / release validation

Tests should be implemented at the lowest appropriate level.

A business rule that can be tested as a unit test should not require an
E2E test merely to verify the rule.


---

## 4. Unit Tests

Unit tests verify individual units of application logic in isolation.

Typical units include:

- functions
- services
- validators
- domain logic
- permission evaluation
- data transformation
- calculation logic
- synchronization algorithms

Unit tests must be:

- fast
- deterministic
- isolated
- independent of external infrastructure

External dependencies should normally be replaced with controlled test
doubles where appropriate.

### Location

Unit tests are located under:

backend/tests/unit/

Example
backend/
└── tests/
    └── unit/
        ├── test_auth.py
        ├── test_permissions.py
        └── test_pricing.py

Requirements

New production logic should normally include corresponding unit tests.

Unit tests must cover important:

success cases
validation failures
boundary conditions
error conditions
security decisions

A high coverage percentage does not replace meaningful tests.


---

## 5. Integration Tests

Integration tests verify that multiple application components work
correctly together.

Integration tests are required when correctness depends on interaction
between components.

Examples include:

- API + service layer
- service + repository
- repository + database
- authentication + authorization
- document service + storage
- synchronization + database
- background processing + persistence

### Location

Integration tests are located under:

backend/tests/integration/

### External Services

External services should not normally be contacted during ordinary test
execution.

Controlled test environments, mocks or test containers may be used where
appropriate.

Real external integrations should be tested separately in dedicated
integration environments.

### Database Integration

Database integration tests must use an isolated test database or equivalent
controlled database environment.

Tests must not modify developer or production databases.

Database state must be reset or isolated between tests where required.

### Requirements

Integration tests must verify:
- correct component interaction
- transaction behavior
- persistence behavior
- error propagation
- authorization boundaries
- relevant infrastructure behavior

## 6. API / Contract Tests

API tests verify the externally observable behavior of the GlasHaus API.

They must verify:

- HTTP methods
- status codes
- request validation
- response structure
- response data types
- authentication requirements
- authorization requirements
- error responses

API tests must ensure that implementation changes do not unintentionally
break clients.

### API Contracts

Public API contracts should be explicitly defined.

Changes to API schemas must be intentional and documented.

Breaking API changes require explicit review.

### Location

API tests may be located under:

backend/tests/api/

or under the integration test structure when the project architecture
makes that more appropriate.

The final test layout must remain consistent across the project.

## 7. Database Tests

Database tests verify persistence, schema integrity and database-related
application behavior.

Tests should cover:

- model persistence
- relationships
- constraints
- uniqueness requirements
- foreign keys
- transactions
- rollback behavior
- migrations
- serialization and deserialization where applicable

### Migrations

Alembic migrations must be tested against a controlled database.

A migration must be capable of upgrading a supported previous schema to
the current schema.

Where practical, downgrade behavior should also be validated.

### Isolation

Database tests must never use production databases.

Developer databases must not be modified by automated tests unless the
test environment explicitly provides an isolated disposable database.

### Data Integrity

Important business constraints must be enforced and tested at the
appropriate layer.

Database constraints must not be assumed to exist merely because the
application validates the same condition.

## 8. Security Tests

Security testing is mandatory for security-sensitive GlasHaus
functionality.

Security tests verify that security controls cannot be bypassed through
invalid input, manipulated requests or unauthorized access.

Security testing should cover:

- authentication
- authorization
- RBAC
- ABAC
- resource ownership
- session management
- token validation
- input validation
- sensitive data handling
- file access
- document permissions
- API access control
- audit logging where applicable

### Negative Testing

Security tests must explicitly verify that prohibited operations fail.

Examples:

unauthenticated user -> protected endpoint
authenticated user -> unauthorized project
employee -> administrative endpoint
customer -> another customer's document
expired token -> protected endpoint
invalid permission -> protected resource

Security tests must verify the expected failure response without exposing
sensitive information.

## 9. Authentication & Authorization Tests

Authentication and authorization require dedicated tests.

### Authentication Tests

Authentication tests should cover:

- valid credentials
- invalid credentials
- disabled accounts
- expired sessions
- invalid tokens
- revoked tokens
- password changes
- second-factor authentication when implemented
- authentication failure handling

### Authorization Tests

Authorization tests must verify both positive and negative cases.

Examples:
Admin -> allowed
Employee -> allowed only for permitted resource
Customer -> allowed only for own resources
Unauthenticated user -> denied
Unauthorized role -> denied
Unauthorized ABAC condition -> denied

### RBAC

Role-based permissions must be tested independently of individual users
where practical.

### ABAC

Attribute-based permissions must test relevant attributes such as:

user
role
project
customer
resource
ownership
organizational context
action
resource state

Authorization decisions must be deterministic and testable.

Authentication must never be used as a substitute for authorization.

## 10. Offline Synchronization Tests

Offline synchronization is a core GlasHaus requirement and therefore
requires dedicated testing.

Synchronization tests must verify:

- offline creation
- offline modification
- offline deletion
- synchronization after reconnection
- duplicate operations
- version handling
- conflict detection
- conflict resolution
- retry behavior
- partial synchronization failures
- interrupted synchronization
- idempotency

### Conflict Testing

Every synchronized entity must have a defined conflict strategy.

Tests must verify that conflicts are:

- detected
- represented correctly
- resolved according to the defined policy
- never silently lost

### Network Failure Testing

Synchronization tests must simulate relevant network failures such as:

- connection loss
- timeout
- server unavailable
- partial response
- retry
- reconnection

### Idempotency

Repeating the same synchronization request must not unintentionally
duplicate or corrupt data.

Synchronization operations should be designed and tested for idempotent
behavior where appropriate.

## 11. End-to-End Tests

End-to-end tests verify complete user workflows across multiple system
components.

E2E tests should represent important real-world GlasHaus workflows.

Examples include:

Login
  -> authentication
  -> authorization
  -> project selection
  -> calendar entry
  -> time tracking
  -> synchronization

  Other examples:

  Customer
  -> project
  -> document
  -> photo
  -> PDF generation
  -> signature
  -> document storage

  Employee
  -> scan QR code
  -> inventory update
  -> backend synchronization
  -> stock level calculation
  -> low-stock warning

### Requirements

E2E tests should focus on critical business workflows.

They should not attempt to test every possible implementation detail.

E2E tests are slower and more expensive than unit tests and should
therefore remain limited to important workflows.

E2E testing will become increasingly important as the browser and Android
applications are implemented.

## 12. Test Fixtures

Test fixtures provide controlled reusable test data and infrastructure.

Fixtures may provide:

- users
- roles
- permissions
- customers
- projects
- documents
- database sessions
- authentication tokens
- test files
- synchronization states

Fixtures must remain explicit and understandable.

Fixtures must not introduce hidden dependencies between tests.

### Fixture Isolation

Tests must not rely on mutations made by previous tests.

Reusable fixtures should create fresh state where practical.

### Sensitive Test Data

Real production data must never be used as test fixtures.

Test credentials, documents and personal data must be synthetic.

## 13. Test Data

Test data must be deterministic, synthetic and safe.

Production customer, employee or financial data must never be copied into
the test environment.

### Test Data Requirements

Test data should cover:

- normal values
- minimum values
- maximum values
- missing values
- invalid values
- boundary values
- conflicting values
- unauthorized ownership
- malformed external input

### Sensitive Data

Test data that resembles sensitive information must remain clearly
synthetic.

Secrets must never be embedded in test source code.

Test secrets should be injected through controlled test configuration
where required.

### External Data

Data received from external integrations must be tested using representative
fixtures.

Examples include:

- IDS Connect responses
- ZUGFeRD documents
- XML documents
- QR code data
- OCR results
- supplier price data

## 14. Coverage

Code coverage is a quality indicator but is not a substitute for meaningful
tests.

Coverage should be used to identify untested production logic.

### Requirements

Coverage must be measured for the backend test suite.

The project currently uses `pytest-cov`.

Coverage reports should identify:

- total coverage
- missing lines
- missing branches where enabled

### Quality Principle

A high coverage percentage does not guarantee correctness.

The project prioritizes:

1. correct behavior
2. security
3. meaningful test cases
4. important edge cases
5. maintainability
6. coverage

Coverage must not be artificially increased through meaningless tests.

### Exceptions

Generated code, configuration-only code or other explicitly justified
exceptions may be excluded from coverage where appropriate.

Such exclusions must be documented.

## 15. Local Quality Gates

Developers must be able to execute the primary quality gates locally
before committing changes.

The current GlasHaus backend quality gates include:

- Ruff linting
- Ruff formatting
- MyPy type checking
- Unit tests
- Integration tests when applicable

### Pre-Commit

The repository uses `pre-commit` to execute configured quality checks.

Before committing changes, developers should run:

pre-commit run --all-files

### Backend Tests

Backend tests can be executed through:

pytest

Specific test groups may be executed individually, for example:

pytest backend/tests/unit

The exact commands are defined by the repository configuration and may
evolve as the project grows.

### Rule

A developer must not bypass a failing quality gate merely to create a
commit.

The underlying problem must be fixed or explicitly documented.

## 16. CI Quality Gates

The GlasHaus CI pipeline must validate the repository independently of
the developer's local environment.

CI must eventually execute the relevant quality gates including:

- dependency installation
- Ruff linting
- Ruff formatting validation
- MyPy
- unit tests
- integration tests
- coverage reporting
- security tests
- database migration tests where applicable

### Reproducibility

CI must use a controlled and reproducible environment.

The CI environment must not depend on files or configuration that exist
only on a developer's machine.

### Pull Requests

Pull requests must not be considered ready for merge while required
quality gates are failing.

### Future CI Extensions

As GlasHaus grows, CI may additionally include:

- dependency vulnerability scanning
- secret scanning
- container image scanning
- API contract validation
- E2E testing
- mobile application tests
- frontend tests

## 17. Definition of Done

A production change is considered complete only when all applicable
requirements have been fulfilled.

### Code

- implementation is complete
- code follows the project architecture
- type annotations are present
- documentation is appropriate
- no unnecessary complexity was introduced

### Tests

- appropriate unit tests exist
- appropriate integration tests exist
- API/contract tests exist where applicable
- database tests exist where applicable
- security tests exist for security-sensitive behavior
- offline synchronization tests exist for synchronization behavior
- E2E tests exist for critical workflows where applicable

### Quality Gates

The applicable quality gates pass:

- Ruff
- Ruff format
- MyPy
- Pytest
- pre-commit
- CI checks

### Security

- no secrets were introduced
- authorization boundaries were considered
- sensitive data handling was reviewed
- security-relevant failure cases are tested

### Database

If database behavior changed:

- Alembic migrations exist
- migrations have been tested
- data integrity has been considered

### Documentation

Documentation must be updated when:

- public behavior changes
- API behavior changes
- architecture changes
- security behavior changes
- synchronization behavior changes
- configuration changes

### Repository State

Before completion:

git status

must show only intentional changes.

The final change must be reviewable and contain no unrelated modifications.

### AI-Assisted Changes

AI-assisted changes follow the same Definition of Done as
human-written changes.

AI assistance does not reduce testing, security, documentation or review
requirements.