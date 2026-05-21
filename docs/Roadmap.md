# GlasHaus Roadmap

# STATUS

## Current Phase
- [ ] Phase A — Infrastructure & Secure Development Environment

---

# Phase A — Infrastructure & Secure Development Environment

## Goals
Establish a secure Linux server environment for development and future deployment.

## Tasks

### Server Security
- [x] GitHub repository connected
- [ ] Linux server hardening
- [ ] SSH-only authentication
- [ ] Disable root login
- [ ] UFW firewall configuration
- [ ] Fail2Ban setup
- [ ] WireGuard VPN setup
- [ ] Automatic server bootstrap script

### Development Environment
- [ ] VS Code Remote SSH setup
- [ ] WSL integration
- [ ] Python virtual environment setup
- [ ] Linter setup (ruff / flake8)
- [ ] Formatting setup (black)
- [ ] mypy type checking
- [ ] pytest test environment

### CI/CD Preparation
- [ ] GitHub Actions initial setup
- [ ] Automated linting
- [ ] Automated tests

---

# Phase B — Backend Core System

## Goals
Build the secure backend foundation.

## Tasks

### Backend Architecture
- [ ] FastAPI initialization
- [ ] Modular backend structure
- [ ] Environment config system
- [ ] Logging infrastructure
- [ ] Exception handling

### Database
- [ ] PostgreSQL installation
- [ ] SQLAlchemy setup
- [ ] Alembic migrations
- [ ] Base models
- [ ] Offline sync metadata fields

### Authentication & Security
- [ ] JWT auth
- [ ] Refresh token rotation
- [ ] 2FA support
- [ ] RBAC engine
- [ ] ABAC engine
- [ ] Audit logging
- [ ] Encryption utilities

### Storage
- [ ] Secure document storage
- [ ] S3/MinIO abstraction
- [ ] File versioning

---

# Phase C — Browser MVP

## Goals
Build first usable browser interface.

## Tasks

### Frontend Foundation
- [ ] Next.js initialization
- [ ] Authentication pages
- [ ] Protected routes
- [ ] API communication layer

### Admin Dashboard
- [ ] User CRUD
- [ ] Role management
- [ ] ABAC assignment UI
- [ ] Activity overview

### Employee Features
- [ ] Calendar view
- [ ] Time tracking
- [ ] Project assignment
- [ ] Task checklist system

---

# Phase D — Android MVP

## Goals
Mobile-first field usability.

## Tasks

### Mobile Foundation
- [ ] React Native / Flutter setup
- [ ] Authentication flow
- [ ] Secure token storage

### Offline First
- [ ] SQLite local storage
- [ ] Sync engine
- [ ] Conflict resolution
- [ ] Offline document cache

### Device Features
- [ ] Camera integration
- [ ] Background sync
- [ ] Push notifications

---

# Phase E — Customer & Project Management

## Goals
Project-centric workflow management.

## Tasks

### Customer System
- [ ] Customer roles
- [ ] Customer dashboard

### Project System
- [ ] Project CRUD
- [ ] Employee assignment
- [ ] Calendar integration
- [ ] Checklist system
- [ ] Deadline tracking

---

# Phase F — PDF & OCR System

## Goals
Digital document workflows.

## Tasks

### PDF Processing
- [ ] PDF creation
- [ ] Form filling
- [ ] Image attachments
- [ ] Offline PDF editing

### Signature System
- [ ] Digital signatures
- [ ] Signature validation

### OCR
- [ ] OCR pipeline
- [ ] Text extraction
- [ ] Searchable documents

---

# Phase G — IDS Connect & Supplier Integration

## Goals
Supplier integration & pricing automation.

## Tasks

### Supplier APIs
- [ ] IDS Connect integration
- [ ] Supplier abstraction layer

### Pricing
- [ ] Price comparison engine
- [ ] Cart optimization
- [ ] Supplier ranking

### Exports
- [ ] PDF quote generation
- [ ] XML export

---

# Phase H — RFID / QR / IoT Layer

## Goals
Physical workflow automation.

## Tasks

### RFID
- [ ] RFID login
- [ ] Time tracking
- [ ] Access control

### QR System
- [ ] Inventory QR labels
- [ ] QR scanning
- [ ] Automatic stock updates

### IoT
- [ ] Realtime event system
- [ ] WebSocket integration

---

# Phase I — AI Pricing Portal

## Goals
Public customer lead generation.

## Tasks

### Public Portal
- [ ] Product configurator
- [ ] Rule engine
- [ ] Estimation logic

### AI Features
- [ ] AI estimation support
- [ ] Lead qualification
- [ ] Recommendation engine

---