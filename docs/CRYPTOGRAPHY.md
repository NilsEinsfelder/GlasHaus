# GlasHaus Cryptography Architecture

## 1. Purpose

This document defines the target cryptographic protection architecture of GlasHaus.

It covers:

- data in transit
- sensitive structured data at rest
- documents
- object storage
- local device data
- backups
- synchronization payloads
- externally delivered content
- future federation communication

This document defines cryptographic architecture and requirements.

It does not claim that the cryptographic system is already completely implemented.

The architecture must be implemented using established, reviewed cryptographic libraries and primitives.

---

## 2. Cryptographic Principles

GlasHaus follows these principles:

1. Never invent cryptographic algorithms.
2. Use established and maintained cryptographic libraries.
3. Use authenticated encryption for confidential application data.
4. Separate cryptographic key management from encrypted application data.
5. Version all persistent encryption formats.
6. Support cryptographic key rotation.
7. Protect key material independently from ciphertext.
8. Never log cryptographic secrets.
9. Never commit production cryptographic secrets to source control.
10. Do not encrypt data indiscriminately when normal infrastructure protection is sufficient.
11. Preserve confidentiality and integrity requirements independently from authorization.
12. Do not treat TLS as encryption at rest.
13. Do not treat infrastructure/database encryption as a replacement for application-level encryption where application-level protection is required.
14. Use cryptographically secure randomness for keys, nonces, and other security-sensitive values.
15. Never reuse an AEAD nonce with the same key.
16. Cryptographic formats must support safe migration and key rotation.
17. Cryptographic recovery requirements must be defined before encrypted production data is introduced.
18. Cryptographic choices must be reviewed against current security guidance before implementation.

---

## 3. Protection Layers

GlasHaus uses multiple protection layers.

Conceptually:

    Application
         │
         ├── Authentication
         ├── Authorization
         ├── TLS
         ├── Application-level encryption
         │
         ▼
    Database / Object Storage
         │
         └── Infrastructure encryption
                  │
                  ▼
               Backups

These layers address different threats.

Authorization determines whether an authenticated principal may access data.

Encryption protects data against additional threats such as:

- storage compromise
- database compromise
- backup theft
- unauthorized infrastructure access
- interception of protected content outside the authorization boundary

No individual protection layer should be treated as a replacement for the others.

---

## 4. Data Classification

Cryptographic protection is based on data sensitivity.

### Class 0 — Operational

Examples:

- stable identifiers
- timestamps
- non-sensitive status values
- non-sensitive synchronization metadata

Protection:

- normal database/storage protection
- authenticated TLS in transit
- infrastructure encryption where applicable

Application-level encryption is not automatically required.

### Class 1 — Business Sensitive

Examples:

- customer contact information
- project information
- internal notes
- operational business information
- non-public scheduling information

Protection:

- TLS
- encrypted infrastructure storage
- application-level encryption where required by field sensitivity, threat model, or deployment policy
- server-side authorization

### Class 2 — Highly Sensitive

Examples:

- contracts
- signed documents
- financial documents
- sensitive photographs
- highly sensitive personal data
- sensitive security information

Protection:

- TLS
- encrypted infrastructure storage
- application-level encryption
- strict authorization
- appropriate auditability
- protected key management

The exact classification of individual fields and resources belongs to the domain and security architecture.

Cryptographic classification must not replace authorization classification.

---

## 5. Authentication Credentials

Authentication credentials are not treated as ordinary encrypted application data.

Passwords must be stored using an approved password-hashing mechanism.

Passwords must never be reversibly encrypted for storage.

Password hashing, session protection, authentication recovery, and related controls are defined by the authentication/security architecture.

Cryptographic key material must never be derived from a password unless an explicitly reviewed password-based key derivation design requires it.

---

## 6. Application-Level Encryption

Sensitive application data requiring cryptographic protection must use authenticated encryption.

An approved AEAD construction must be selected during implementation based on:

- security properties
- library support
- maintenance status
- deployment environment
- interoperability requirements
- current security guidance

AES-256-GCM is a possible implementation choice.

The architecture does not permanently mandate a single algorithm before the implementation/security review is complete.

The selected implementation must provide:

- confidentiality
- ciphertext integrity
- authenticated associated data where required
- cryptographically secure nonces
- safe nonce management
- versioned ciphertext envelopes

No custom cipher or cryptographic construction may be introduced.

---

## 7. Nonce Requirements

AEAD nonce reuse with the same key is prohibited.

Nonces must be generated or managed using a construction that guarantees the required uniqueness properties.

Random nonce generation is acceptable only where the selected algorithm and operational design provide sufficient collision resistance for the expected number of encryptions.

Nonce handling must therefore be part of the encryption implementation design rather than left to callers to manage informally.

Nonce values are not secret.

They must nevertheless be authenticated as part of the ciphertext envelope where required by the selected construction.

---

## 8. Authenticated Metadata

Security-relevant metadata associated with ciphertext must be protected against unauthorized modification.

Depending on the encryption format, associated authenticated data may include:

- object identifier
- document identifier
- document version
- encryption format version
- algorithm identifier
- key identifier
- resource classification
- encryption context

The exact authenticated-data set must be defined by the encryption envelope.

Changing authenticated metadata without re-encryption must cause authentication failure where that metadata is security-critical.

---

## 9. Encryption Envelope

Persistent encrypted data must use a versioned envelope.

Conceptually:

    EncryptionEnvelope

        version
        algorithm
        key_id
        nonce
        authenticated_metadata
        ciphertext
        authentication_tag

The exact serialization format must be defined before production encrypted data is introduced.

The envelope must contain identifiers and metadata required for decryption and migration.

It must never contain secret key material.

The format must be deterministic to parse and explicitly versioned.

Unknown or unsupported encryption versions must fail closed.

---

## 10. Envelope Encryption

The preferred architecture is envelope encryption.

Conceptually:

    Key Management System
             │
             │
             │ KEK / wrapping key
             ▼
       wrapped DEK
             │
             ▼
    plaintext ─ DEK ─► ciphertext

A Data Encryption Key (DEK) encrypts application data.

A Key Encryption Key (KEK), or equivalent key-management mechanism, protects the DEK.

The exact hierarchy must be selected during implementation.

Possible data-key scopes include:

- installation
- data class
- document
- document version
- other explicitly defined security domains

The selected scope must balance:

- isolation
- rotation
- performance
- recovery
- operational complexity

---

## 11. Key Management

Production cryptographic keys must be managed separately from application ciphertext.

The preferred architecture is:

    Application
         │
         ▼
    Key Management Layer
         │
         ├── Secret Manager / KMS
         ├── key policy
         ├── key lifecycle
         └── audit
         
The application should not embed production keys in source code.

Where practical, applications should request cryptographic operations or protected key material through the approved key-management abstraction rather than implementing ad-hoc key storage.

The architecture must remain portable and must not depend unnecessarily on one specific KMS vendor.

---

## 12. Key Lifecycle

Cryptographic keys have an explicit lifecycle.

Conceptually:

    active
      │
      ▼
    rotating
      │
      ▼
    decrypt-only
      │
      ▼
    retired
      │
      ▼
    destroyed when policy permits

New encryption operations use the current encryption key version.

Older key versions remain available for decryption for as long as required by retained ciphertext.

Key destruction must never occur while retained encrypted data still requires that key unless an explicit data-destruction policy permits the resulting loss.

Key rotation should not require immediate rewriting of all existing ciphertext.

---

## 13. Key Identification

Encrypted objects must identify the key version required for decryption.

A key identifier must be:

- non-secret
- stable enough to resolve the appropriate key version
- associated with an explicit key-management lifecycle

A key identifier must never itself provide access to the underlying key.

Unknown, revoked, or unavailable key identifiers must cause secure failure.

---

## 14. Key Rotation

Key rotation must support:

- creation of a new encryption key
- use of the new key for new writes
- continued decryption of existing data
- controlled migration of old ciphertext
- retirement of old keys
- eventual destruction where policy permits

Rotation must not require plaintext exposure outside the trusted application/key-management boundary.

Where ciphertext is re-encrypted, integrity must be verified before and after migration.

---

## 15. Key Recovery

Cryptographic recovery is part of data recovery.

Encrypted production data must not become permanently unrecoverable merely because:

- a server was rebuilt
- a database was restored
- object storage was restored
- a key-management service was replaced
- a key version was rotated

Recovery procedures must therefore define:

- required key material
- key metadata
- key version mapping
- backup dependencies
- recovery authorization
- restoration order
- key availability requirements

A backup is not considered successfully recoverable if the encrypted application data cannot be decrypted with the recovered cryptographic state.

---

## 16. Database Encryption

Production PostgreSQL storage must use appropriate infrastructure-level encryption.

Application-level encryption is selective.

Encrypting database fields can affect:

- equality search
- indexing
- sorting
- range queries
- uniqueness constraints
- full-text search
- reporting

Therefore, application-level encryption must be introduced intentionally.

Sensitive searchable data requires an explicit search design.

No plaintext search index, cache, materialized view, export, or secondary storage may accidentally become a bypass around the intended encryption boundary.

---

## 17. Document Encryption

Sensitive document content must be encrypted before durable object storage.

Conceptually:

    original file
         │
         ▼
    validation
         │
         ▼
    content digest
         │
         ▼
    application encryption
         │
         ▼
    encrypted object
         │
         ▼
    S3 / MinIO / equivalent storage

Document metadata may contain:

- document ID
- document version
- object reference
- content type
- size
- integrity information
- encryption version
- key identifier

Document metadata does not automatically receive the same cryptographic treatment as document content.

Its protection is determined by its data classification.

Clients must never receive raw object-storage credentials merely to access protected documents.

---

## 18. Document Versions

Document versions are independently addressable protected resources.

Where document versions are encrypted, each version must retain sufficient metadata to determine:

- encryption format
- encryption key version
- integrity information
- storage object
- required decryption context

Document version encryption must support immutable historical versions.

Encryption key rotation must not destroy the ability to decrypt retained historical versions.

This is consistent with the persistence model defined in:

`docs/PERSISTENCE_MODEL.md`

---

## 19. Integrity and Digests

Cryptographic integrity and content digests serve different purposes.

Authenticated encryption provides integrity protection for encrypted content.

A content digest may additionally provide:

- content identity
- corruption detection
- synchronization comparison
- version verification
- migration verification

A digest must not be treated as a secret.

Where a digest is security-sensitive, its exact cryptographic construction must use an approved hash function.

A digest alone is not a substitute for authenticated encryption.

---

## 20. Local Device Encryption

Sensitive local data stored on devices must be encrypted at rest.

The preferred architecture is:

    OS Secure Storage / Key Store
                │
                ▼
          protected key
                │
                ▼
       encrypted local data
                │
                ├── local database
                └── protected assets

Platform-provided secure key storage should be preferred over application-managed plaintext key files.

Plaintext durable storage of sensitive local data is not acceptable where the platform security model supports appropriate encryption.

Local encryption does not replace server-side authorization.

---

## 21. Local Key Lifecycle

Local cryptographic material must have a defined lifecycle.

It must account for:

- device registration
- device revocation
- logout
- session expiration
- application removal
- device compromise
- offline authorization expiration
- re-enrollment

Revoking a device on the server must prevent continued authorized use when the device reconnects and receives the updated security state.

Offline operation cannot guarantee instantaneous remote revocation while disconnected; therefore offline cryptographic and authorization lifetimes must be explicitly bounded.

---

## 22. Synchronization

Synchronization has separate transport, storage, and authorization requirements.

Transport:

    Client ↔ API
         │
         └── TLS

Stored synchronization payloads:

    sensitive content
         │
         └── protected according to data classification

The synchronization subsystem must not persist sensitive plaintext merely because the data is part of a synchronization queue.

Cached synchronized data must remain subject to:

- authorization scope
- device trust
- local encryption
- retention rules
- deletion rules
- offline lifetime

Synchronization must not create an independent cryptographic trust model that contradicts the server architecture.

Detailed synchronization requirements are defined in:

`docs/SYNC.md`

---

## 23. External Delivery

Transport encryption, document encryption, and true end-to-end messaging are separate concepts.

### Transport Encryption

Examples:

- HTTPS/TLS
- SMTP TLS

Transport encryption protects the communication channel.

It does not necessarily protect the message after delivery.

### Encrypted Document Delivery

A document may remain encrypted beyond transport.

Such a design requires an explicit mechanism for:

- recipient authentication
- key delivery
- access control
- expiration
- revocation where possible
- recovery

### True End-to-End Email Encryption

Technologies such as PGP or S/MIME require a separate recipient-key architecture.

GlasHaus must not claim true end-to-end email encryption merely because SMTP uses TLS.

The initial architecture is therefore:

- mandatory TLS for applicable transport
- encrypted durable document storage where required
- optional encrypted document/portal delivery
- separate architecture before true E2E email encryption is implemented

---

## 24. Federation Cryptography

Future federation requires cryptographic mechanisms for establishing trust between independently operated servers.

The federation design must define:

- server identity keys
- peer authentication
- authenticated and/or signed messages
- replay protection
- key rotation
- key revocation
- trust establishment
- trust expiration where applicable
- auditability

The receiving server remains authoritative over its own resources.

Federation cryptography must not be implemented before the federation protocol and trust model are explicitly designed.

The federation design must also define whether security properties are provided by:

- mutually authenticated transport
- message signatures
- both
- another explicitly reviewed mechanism

---

## 25. Cryptographic Separation of Concerns

The following concerns must remain distinct:

### Authentication

Proves or establishes identity.

### Authorization

Determines whether an identity may perform an action.

### Encryption

Protects confidentiality and integrity of protected data.

### Hashing

Provides one-way transformations for approved purposes such as password hashing or content digests.

### Key Management

Controls cryptographic key lifecycle and access.

No one of these mechanisms may silently be treated as a substitute for another.

---

## 26. Prohibited Practices

The following practices are prohibited:

- inventing a cipher
- implementing custom cryptographic primitives
- reusing AEAD nonces with the same key
- hard-coding production keys
- committing production keys
- storing plaintext production keys beside ciphertext
- storing passwords in reversible encrypted form
- treating database encryption as a replacement for application encryption
- treating TLS as encryption at rest
- claiming SMTP TLS is end-to-end email encryption
- silently changing an encryption format without versioning
- destroying a key while retained ciphertext still requires it
- logging secret keys or plaintext credentials
- disabling certificate validation in production as a convenience
- creating plaintext search indexes that bypass the intended encryption boundary

---

## 27. Cryptographic Testing

Cryptographic implementations require dedicated tests.

Tests must include, where applicable:

- encryption/decryption round trip
- wrong key
- wrong key version
- tampered ciphertext
- tampered nonce
- tampered authenticated metadata
- invalid envelope version
- invalid algorithm identifier
- invalid key identifier
- nonce uniqueness
- key rotation
- decrypt-only keys
- retired keys
- destroyed/unavailable keys
- corrupted object detection
- document version integrity
- authorization before decryption
- local storage protection
- backup restoration
- recovery of encrypted data
- synchronization payload protection

Known test vectors should be used where applicable.

Tests must also verify that decryption is never performed merely because a resource identifier is known.

Authorization must precede protected resource disclosure and decryption wherever the architecture requires it.

---

## 28. Operational Requirements

Cryptographic systems require operational controls in addition to application code.

Operations must define:

- key backup/recovery
- key rotation procedures
- key revocation
- KMS/secret-manager access
- incident response
- emergency key recovery procedures
- audit access
- disaster recovery
- cryptographic migration procedures

Cryptographic configuration must be observable without exposing secrets.

Production logs must contain sufficient information to diagnose cryptographic failures without logging plaintext keys or sensitive secret material.

---

## 29. Cryptographic Change Management

Changes to any of the following require explicit architectural review:

- encryption algorithm
- AEAD construction
- key hierarchy
- key scope
- encryption envelope
- key-storage mechanism
- nonce strategy
- cryptographic metadata
- password hashing mechanism
- federation cryptography
- local encryption architecture
- backup key recovery

Existing ciphertext must remain decryptable during a supported migration period unless an explicit data-destruction decision has been made.

Cryptographic migrations must be versioned and tested.

No implementation may silently introduce a second incompatible cryptographic format.

---

## 30. Implementation Order

The target implementation sequence is:

1. finalize data classification
2. select approved cryptographic libraries
3. define the encryption envelope
4. define the key hierarchy
5. define key recovery requirements
6. implement a development key provider
7. implement the production key-management adapter
8. protect one real document path
9. protect selected sensitive structured fields
10. implement local device encryption
11. define encrypted external delivery if required
12. implement key rotation
13. implement recovery procedures
14. define federation cryptography
15. add comprehensive cryptographic security tests

Implementation must not proceed to production encryption of durable data before the corresponding recovery model is understood.

---

## 31. Architectural Invariants

The following invariants must remain true unless this architecture is explicitly changed:

1. Established cryptographic primitives are used.
2. Custom cryptographic algorithms are not introduced.
3. Confidential application data uses authenticated encryption where application-level encryption is required.
4. AEAD nonce reuse under the same key is prohibited.
5. Encryption formats are versioned.
6. Production keys are separated from ciphertext.
7. Key rotation is supported.
8. Retained ciphertext remains decryptable for its required retention period.
9. Cryptographic recovery is part of backup/recovery planning.
10. Passwords are never stored using reversible encryption.
11. TLS is not treated as encryption at rest.
12. Infrastructure encryption does not replace application-level encryption where the latter is required.
13. Object storage cannot bypass authorization.
14. Local sensitive data is encrypted where required by the device security model.
15. Synchronization does not create a plaintext persistence bypass.
16. Federation cryptography preserves independent server trust domains.
17. Cryptographic secrets are never logged or committed to source control.
18. Cryptographic changes are explicitly versioned and reviewed.
19. Unknown or invalid cryptographic state fails closed.

---

## 32. Related Documents

This document should be read together with:

- `docs/ARCHITECTURE.md`
- `docs/IDENTITY_AUTHORIZATION.md`
- `docs/PERSISTENCE_MODEL.md`
- `docs/SECURITY.md`
- `docs/SYNC.md`
- `docs/TESTING.md`
- `docs/Roadmap.md`

The cryptographic implementation must not silently diverge from these documents.

If an implementation requirement conflicts with the cryptographic architecture, the conflict must be resolved explicitly before implementation proceeds.