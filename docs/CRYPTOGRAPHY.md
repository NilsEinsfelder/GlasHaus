# GlasHaus Cryptography Architecture

## 1. Purpose

This document defines protection for sensitive data:

- in transit,
- at rest,
- on field devices,
- in object storage,
- in backups,
- during synchronization,
- when content is sent externally.

It defines architecture, not a final library selection.

---

## 2. Principles

1. Use established modern cryptographic primitives.
2. Never invent cryptographic algorithms.
3. Use authenticated encryption for confidential application data.
4. Separate key management from encrypted data.
5. Version encryption formats.
6. Support key rotation.
7. Never log cryptographic secrets.
8. Do not encrypt data indiscriminately when this would unnecessarily destroy required functionality.
9. Verify cryptographic choices against current security guidance before implementation.

---

## 3. Protection Layers

```text
Application
   │
   ├── TLS
   ├── application-level encryption where required
   ▼
Database / Object Storage
   │
   └── infrastructure encryption
```

---

## 4. Data Classification

### Class 0 — Operational metadata

Examples:

- IDs,
- timestamps,
- synchronization metadata,
- non-sensitive statuses.

Protection:

- normal storage protection,
- TLS.

### Class 1 — Business-sensitive

Examples:

- customer contacts,
- internal notes,
- project information.

Protection:

- TLS,
- encrypted production storage,
- application-level encryption where required.

### Class 2 — Highly sensitive

Examples:

- contracts,
- signed documents,
- financial documents,
- sensitive photographs.

Protection:

- TLS,
- encrypted production storage,
- application-level encryption,
- strict access control,
- auditability.

The final field-level classification belongs in the domain/data model.

---

## 5. Application-Level Encryption

Use authenticated encryption.

A preferred implementation direction is a standard AEAD construction such as AES-256-GCM, subject to final library/security review.

Requirements:

- cryptographically random nonces,
- no nonce reuse with the same key,
- authenticated metadata where appropriate,
- versioned ciphertext envelope.

Do not invent a custom cryptographic format unnecessarily.

---

## 6. Envelope Encryption

Use envelope encryption:

```text
                 Key Management System
                         │
                     KEK / wrapping key
                         │
                         ▼
                    wrapped DEK
                         │
                         ▼
plaintext ── DEK ──► ciphertext
```

- **KEK** — key-encryption/wrapping key.
- **DEK** — data-encryption key.

The exact DEK scope is an implementation decision.

Possible scopes include:

- organization,
- document,
- document version,
- data class.

---

## 7. Ciphertext Envelope

Conceptually:

```text
{
  encryption_version,
  key_id,
  algorithm,
  nonce,
  ciphertext,
  authentication_tag
}
```

If the selected library combines ciphertext and tag, use its standard representation.

Secrets are never embedded in the envelope.

---

## 8. Key Lifecycle

```text
active
  ↓
rotating
  ↓
decrypt-only
  ↓
retired
  ↓
destroyed (when policy permits)
```

New writes use the current key version.

Rotation should not require immediate rewriting of every existing object.

---

## 9. Key Storage

Production keys are not stored beside ciphertext.

Preferred model:

```text
Application
    │
    ▼
KMS / dedicated secret manager
    │
    ├── key operations
    └── access policy + audit
```

Development keys must never be reused in production.

---

## 10. Database Encryption

Production PostgreSQL storage uses infrastructure encryption.

Application-level encryption is selective because encrypted fields complicate:

- equality search,
- range queries,
- sorting,
- indexing,
- full-text search.

Do not encrypt everything indiscriminately.

Sensitive searchable data requires an explicit search strategy.

---

## 11. Document/Object Encryption

Sensitive files are encrypted before durable object storage:

```text
Original file
    │
    ▼
validated + hashed
    │
    ▼
application encryption
    │
    ▼
encrypted object
    │
    ▼
S3 / MinIO
```

Metadata may include:

- document ID,
- version,
- object key,
- content type,
- size,
- integrity information,
- encryption version,
- key ID.

Clients never receive raw storage credentials.

---

## 12. Integrity

Authenticated encryption provides ciphertext integrity.

Binary assets should additionally have a consistent cryptographic digest for identity/integrity purposes.

The system must distinguish:

- file identity,
- encrypted object identity,
- encryption metadata,
- integrity metadata.

---

## 13. Local Mobile Encryption

The field client protects its local database and sensitive assets.

Preferred model:

```text
OS secure key storage
        │
        ▼
protected local key
        │
        ▼
encrypted local DB / assets
```

The mobile platform's secure key-management facility protects the database key or root material.

Plaintext durable local databases are not acceptable for sensitive data.

---

## 14. Synchronization

Synchronization has two independent protections.

### Transport

Client ↔ API uses TLS.

### Stored data

Sensitive payloads remain protected according to classification.

The server should not persist plaintext sensitive payloads merely as a synchronization queue.

If temporary plaintext processing is unavoidable, lifetime and storage behavior must be explicit.

---

## 15. Backups

Backups are sensitive data.

They must be:

- encrypted,
- access-controlled,
- retained according to policy,
- tested for restoration,
- usable with the corresponding key-management system.

---

## 16. External Content Delivery

Three concepts remain separate.

### TLS transport

HTTPS/SMTP TLS protects the connection.

### Encrypted document delivery

An encrypted document can provide protection beyond transport, but key/password delivery is a separate design.

### True end-to-end email encryption

PGP/S/MIME is a separate product/security capability requiring recipient key management, verification, recovery and usability design.

### Initial recommendation

- mandatory TLS,
- encrypted document storage,
- optional encrypted document/portal delivery,
- no claim of true end-to-end email encryption until a dedicated protocol and key workflow exists.

---

## 17. Prohibited Practices

Never:

- invent a cipher,
- reuse AEAD nonces,
- hard-code production keys,
- commit production keys,
- store keys beside ciphertext without protection,
- reversibly encrypt passwords,
- assume DB encryption replaces application-level encryption,
- assume TLS encrypts stored data,
- call SMTP TLS end-to-end email encryption.

---

## 18. Testing

Tests are required for:

- round-trip encryption/decryption,
- wrong key,
- tampered ciphertext,
- tampered metadata,
- nonce uniqueness,
- key version selection,
- key rotation,
- retired-key behavior,
- corrupted object detection,
- authorization before decryption,
- local database protection,
- backup restoration.

Use known test vectors where available.

---

## 19. Implementation Order

1. finalize data classification,
2. choose approved cryptographic library,
3. implement versioned encryption envelope,
4. implement key-provider abstraction,
5. implement development provider,
6. implement production KMS/secret-manager adapter,
7. encrypt one document path end-to-end,
8. add sensitive structured fields selectively,
9. add local mobile encryption,
10. add encrypted external delivery if required,
11. implement rotation/recovery procedures,
12. add security tests.

Do not build a generic crypto abstraction before the first concrete protected data path is understood.