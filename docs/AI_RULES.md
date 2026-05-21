# GlasHaus AI Development Rules

## Core Principles

All code must follow:

### 1. Code Quality
- Python-first backend (FastAPI recommended)
- Strict linting compliance (ruff / flake8)
- Type hints required (mypy compatible)
- Modular architecture

### 2. Testing
- Every module MUST include:
  - unit tests (pytest)
  - integration test stubs
  - clear test naming conventions
- No untested production logic

### 3. Documentation
- Every function must include:
  - docstrings (Google style)
  - parameter typing
  - return typing
- Public APIs must be documented

### 4. Security First
- No plaintext secrets
- Environment variables for config
- AES-256 for sensitive data
- JWT + refresh token auth required

### 5. Architecture Rules
- Separation of concerns mandatory
- API / Service / Repository pattern
- No business logic inside controllers

### 6. Offline Sync Requirement
- All data models must support:
  - versioning
  - conflict resolution fields
  - timestamps (created_at, updated_at)

### 7. AI Assistance Rule
When AI (ChatGPT or other) contributes code:
- Always generate production-ready code
- No placeholders unless explicitly requested
- Include comments where logic is non-trivial