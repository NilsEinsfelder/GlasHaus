# GlasHaus

GlasHaus is a secure, project-oriented software platform for managing customer, project, field-service and document workflows.

The project is currently in the backend-foundation stage.

## Current Status

Implemented foundations:

- Python 3.14 backend
- FastAPI
- SQLAlchemy
- UUIDv7 identifiers
- initial device/synchronization metadata models
- automated tests
- Ruff
- MyPy
- pytest
- Alembic migration foundation

Not yet implemented:

- authentication
- authorization
- application-level encryption
- key management
- document storage
- complete business domain
- mobile application
- offline synchronization engine

Architecture documents describe the target system and must not be interpreted as evidence that a feature is already implemented.

## Architecture

The current target architecture is documented in:

- `docs/ARCHITECTURE.md`
- `docs/SECURITY.md`
- `docs/CRYPTOGRAPHY.md`
- `docs/SYNC.md`
- `docs/Roadmap.md`
- `docs/AI_RULES.md`
- `docs/TESTING.md`

The backend follows a modular-monolith approach.

Conceptually:

```text
API / Transport
      ↓
Application Services
      ↓
Domain
      ↓
Infrastructure
```

Production structured data will use PostgreSQL.

Binary assets will use S3-compatible object storage.

The field client is planned as an offline-capable client.

## Backend Development

From `backend/`:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Start the development server:

```bash
uvicorn app.main:app --reload
```

The API is available at:

```text
http://127.0.0.1:8000
```

FastAPI documentation:

```text
http://127.0.0.1:8000/docs
```

## Database

SQLite may be used for local development and isolated tests.

Production uses PostgreSQL.

Database schema changes are managed exclusively through Alembic migrations.

Typical workflow:

```bash
alembic upgrade head
```

Never use `Base.metadata.create_all()` as a production migration mechanism.

## Quality Checks

From `backend/`:

```bash
ruff check .
ruff format --check .
mypy app
pytest
```

The complete quality configuration is defined in `backend/pyproject.toml`.

## Project Direction

The implementation order is intentionally:

```text
Backend Foundation
        ↓
Security Architecture
        ↓
Cryptography
        ↓
First Domain Workflow
        ↓
Authentication / Authorization
        ↓
Browser MVP
        ↓
Mobile Foundation
        ↓
Synchronization MVP
        ↓
Domain Expansion
        ↓
Integrations / Automation
```

See `docs/Roadmap.md` for details.

## Security

Security and cryptography are architectural concerns, not later add-ons.

No production implementation of encryption, authentication or authorization is claimed until it has been designed, implemented and tested.

See:

- `docs/SECURITY.md`
- `docs/CRYPTOGRAPHY.md`

## License

License information will be added when the project licensing decision has been finalized.