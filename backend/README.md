# GlasHaus Backend

The GlasHaus backend provides the secure server-side application layer for the GlasHaus platform.

## Planned Features

* Secure customer and employee management
* Role-Based Access Control (RBAC)
* Attribute-Based Access Control (ABAC)
* Secure document storage
* Document integrity and audit trails
* E-invoicing with ZUGFeRD and XML
* Offline-first synchronization
* RFID and QR-based inventory management
* IDS Connect integration
* Wholesale price comparison
* AI-based pricing estimator

## Technology

* Python 3.14
* FastAPI
* SQLAlchemy
* Alembic
* PostgreSQL

## Development

The backend uses a dedicated Python virtual environment.

From the `backend/` directory:

```bash
source .venv/bin/activate
```

The backend development dependencies are defined exclusively in `pyproject.toml`.

Install the project in editable mode with development dependencies:

```bash
python -m pip install -e ".[dev]"
```

## Quality Checks

Before committing changes, the project uses automated quality checks based on:

* Ruff
* Ruff Format
* MyPy
* Pytest
* Pre-commit

The complete test and quality-gate configuration is defined in `pyproject.toml` and `.pre-commit-config.yaml`.

## Server Setup

Server initialization and infrastructure setup scripts are maintained in the repository-level `scripts/` directory.

Detailed infrastructure documentation will be maintained in `docs/`.
