# GlasHaus Security Architecture

## 1. Purpose

This document defines the security model for GlasHaus.

Security is a system property spanning authentication, authorization, device trust, encryption, auditing and operations.

---

## 2. Security Goals

GlasHaus protects:

- personal/customer data,
- project information,
- documents and photographs,
- financial information,
- credentials,
- authorization state,
- synchronization data,
- cryptographic keys and secrets.

Primary goals:

1. confidentiality,
2. integrity,
3. availability,
4. accountability,
5. least privilege.

---

## 3. Trust Model

```text
                 Internet
                    │
              untrusted network
                    │
                    ▼
              ┌───────────┐
              │   Client  │
              │ untrusted │
              └─────┬─────┘
                    │ TLS/API
                    ▼
              ┌───────────┐
              │  Backend  │
              │ authority │
              └─────┬─────┘
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
      PostgreSQL         Object Storage
```

The client is potentially compromised.

Client-side checks never replace server authorization.

---

## 4. Authentication

Authentication establishes identity.

The final implementation must define:

- password hashing,
- access/session lifecycle,
- session revocation,
- device registration,
- 2FA,
- recovery,
- logout,
- suspicious-session handling.

Passwords must use a modern password-specific hashing scheme.

Passwords must never be reversibly encrypted for storage.

Authentication and authorization remain separate.

---

## 5. Authorization

Authorization is layered:

```text
Authenticated user
      ↓
Role / permission
      ↓
Resource authorization
      ↓
Organization / project scope
      ↓
Action-specific rule
```

RBAC may provide coarse permissions.

Resource rules may further constrain by organization, project, workflow state, device and action.

The server makes the final decision.

---

## 6. Device Trust

Trusted field devices are explicitly registered and revocable.

A lost or compromised device must be revocable independently of the device being online.

Offline authentication and authorization material is cached only for a defined security lifetime.

Previously issued credentials must not restore server access after device revocation.

---

## 7. Offline Security

Offline mode requires cached usability.

Therefore:

- only locally available data is usable,
- only cached permissions are used offline,
- local authentication material is protected,
- sensitive local data is encrypted,
- offline access expires according to policy,
- server revocation becomes authoritative on reconnection.

---

## 8. Transport Security

Production application communication uses authenticated TLS:

- web → API,
- mobile → API,
- API → storage where applicable,
- API → external services,
- mail transport where supported.

Transport encryption does not replace encryption at rest.

---

## 9. Data Protection

Protection layers:

### Transport

TLS.

### Infrastructure storage

Encrypted production database volumes, backups and object storage.

### Application-level encryption

Sensitive fields and documents are encrypted according to `CRYPTOGRAPHY.md`.

---

## 10. Secrets

Never commit:

- passwords,
- API keys,
- tokens,
- database credentials,
- private keys,
- encryption keys,
- production secrets.

Production secrets use dedicated secret management appropriate to the deployment.

Secret values must not be logged.

---

## 11. Audit

Business-critical security events must be auditable.

The system should be able to determine:

- who acted,
- what resource was affected,
- what action occurred,
- when the server received it,
- whether it originated offline,
- whether authorization succeeded.

Audit records should contain references and metadata rather than unnecessary sensitive payloads.

---

## 12. Emergency Access

Emergency access is a privileged workflow.

It must:

- require explicit authorization,
- record a reason,
- identify the actor,
- record the resource/project,
- limit scope,
- be auditable,
- be server-validated.

---

## 13. Document Security

Sensitive documents and photographs require:

- authorization before access,
- authorization before upload,
- content-size limits,
- content validation,
- integrity checks,
- encrypted storage,
- secure temporary handling,
- controlled retention/deletion.

Object-storage URLs must not bypass authorization.

Pre-signed URLs, if used, are short-lived and scoped.

---

## 14. Logging

Logs must not expose:

- passwords,
- tokens,
- encryption keys,
- document contents,
- unnecessary personal data,
- authorization secrets.

Use correlation/request IDs for diagnostics.

---

## 15. Backups and Recovery

Backups require:

- encryption,
- access control,
- retention,
- tested restoration,
- key availability,
- auditability.

A backup is not considered recoverable if the required encryption keys cannot be restored.

---

## 16. Initial Threat Model

| Threat | Primary control |
|---|---|
| stolen credentials | strong authentication, 2FA, session/device revocation |
| compromised client | server-side authorization |
| stolen device | encrypted local data, offline expiry, device revocation |
| database theft | storage + application-level encryption |
| object-store exposure | encrypted objects + scoped access |
| network interception | TLS |
| replayed sync request | operation idempotency |
| stale offline authorization | server authorization on sync |
| leaked logs | redaction |
| backup theft | encrypted backups + key controls |

This is an initial threat model, not a complete security assessment.

---

## 17. Security Testing

Security-sensitive features require tests for:

- authentication failure,
- authorization boundaries,
- revoked sessions/devices,
- offline expiry,
- synchronization authorization,
- object access,
- encryption/decryption,
- key versioning,
- replay/idempotency,
- conflicts,
- audit generation.

---

## 18. Security Invariants

1. The client is never the final authorization authority.
2. Secrets are never stored in source control.
3. Production transport uses TLS.
4. Sensitive local data is protected.
5. Sensitive server-side data follows its classification.
6. Encryption keys are separated from encrypted application data.
7. Lost devices can be revoked.
8. Business-critical access is auditable.
9. Object storage cannot bypass application authorization.
10. Security-sensitive changes require tests and documentation.