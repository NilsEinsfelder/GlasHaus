# GlasHaus

GlasHaus is an open-source, self-hosted software platform for managing customer, project, field-service and document workflows.

Each GlasHaus installation is operated autonomously by one company on its own infrastructure or trusted network.

The server is the local organizational and security boundary.

## Current Status

GlasHaus is currently in the backend foundation and architecture implementation stage.

Implemented foundations include:

- Python 3.14 backend
- FastAPI
- SQLAlchemy
- UUIDv7 identifiers
- initial device and synchronization metadata models
- authentication/authorization model prototypes
- automated tests
- Ruff
- MyPy
- pytest
- Alembic migration foundation

The following areas are designed but not yet fully implemented:

- production authentication
- production authorization integration
- application-level encryption
- key management
- complete business domain
- document storage
- browser application
- mobile application
- offline synchronization engine
- federation between independent GlasHaus installations

Architecture documentation describes the target design. It must not be interpreted as evidence that a feature is already implemented.

## Architecture

GlasHaus is designed as a modular monolith.

Conceptually:

    API / Transport
          ↓
    Application Services
          ↓
    Domain
          ↓
    Infrastructure

The server is the authoritative authority for:

- authentication
- authorization
- business state
- project access
- document access
- synchronization acceptance
- security-sensitive operations

The browser is an online client.

The future field/mobile client is designed to support offline workflows using explicitly authorized local data.

## Self-Hosted Model

One GlasHaus server represents one company's local installation.

There is no SaaS-style multi-tenant organization layer inside a server.

Conceptually:

    GlasHaus Server
    ├── Internal Users
    ├── External Users
    │   ├── Customers
    │   ├── Suppliers (future)
    │   ├── Tax Advisors (future)
    │   └── Partners (future)
    ├── Customers
    ├── Projects
    ├── Documents
    └── Devices

Communication between independent GlasHaus servers is a future federation feature and constitutes a separate trust boundary.

## Identity and Authorization

A user has:

- one identity
- one user type
- one role
- an applicable employment hierarchy level for internal users
- zero or more scoped permission grants
- registered devices and sessions where applicable

The two initial user types are:

- `INTERNAL`
- `EXTERNAL`

An external user is a Customer only when they have an explicit Customer relationship.

A Customer is a business entity and may have multiple external users.

Authorization follows:

    Authentication
          ↓
    User state
          ↓
    Role defaults
          +
    Hierarchy defaults
          +
    Explicit permission grants/restrictions
          ↓
    Resource scope
          ↓
    Workspace scope
          ↓
    Action-specific rules
          ↓
    ALLOW / DENY

Default is deny.

Internal users require explicit project assignment.

External customer users require explicit access to the relevant customer project.

Customer users can access the Customer Workspace but never the Internal Workspace.

## Persistence

Production structured data will use PostgreSQL.

SQLite may be used for local development and isolated tests.

Binary assets will use S3-compatible object storage.

Database schema changes are managed exclusively through Alembic migrations.

The persistence design is specified in:

`docs/PERSISTENCE_MODEL.md`

## Security

Security is an architectural property, not a later add-on.

GlasHaus uses layered protection:

- authenticated transport
- server-side authorization
- device/session controls
- infrastructure encryption
- application-level encryption for sensitive data
- encrypted object storage
- auditability of security-sensitive operations
- protected backups

Encryption keys are separated from encrypted application data.

No production security guarantee is claimed until the corresponding feature has been implemented and tested.

## Documentation

The main architecture documents are:

- `docs/ARCHITECTURE.md`
- `docs/IDENTITY_AUTHORIZATION.md`
- `docs/PERSISTENCE_MODEL.md`
- `docs/SECURITY.md`
- `docs/CRYPTOGRAPHY.md`
- `docs/SYNC.md`
- `docs/Roadmap.md`
- `docs/TESTING.md`
- `docs/AI_RULES.md`

## Backend Development

From `backend/`:

    python -m venv .venv
    source .venv/bin/activate
    python -m pip install -e ".[dev]"

Start the development server:

    uvicorn app.main:app --reload

The API is available at:

    http://127.0.0.1:8000

FastAPI documentation:

    http://127.0.0.1:8000/docs

## Database

SQLite may be used for local development and isolated tests.

Production uses PostgreSQL.

Database schema changes are managed exclusively through Alembic migrations.

Typical workflow:

    alembic upgrade head

Never use `Base.metadata.create_all()` as a production migration mechanism.

## Quality Checks

From `backend/`:

    ruff check .
    ruff format --check .
    mypy app
    pytest
    git diff --check

All production changes must pass the applicable quality gates.

## Project Direction

The implementation order is intentionally:

    Backend Foundation
            ↓
    Architecture / Persistence Model
            ↓
    Authentication
            ↓
    Security / Crypto Implementation
            ↓
    First Domain Workflow
            ↓
    Browser MVP
            ↓
    Mobile Foundation
            ↓
    Synchronization MVP
            ↓
    Domain Expansion
            ↓
    Federation / Integrations / Automation

See `docs/Roadmap.md` for details.

## License

License information will be added when the project licensing decision has been finalized.