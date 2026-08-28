# GlasHaus Architecture Decisions

Dieses Dokument hält die für die weitere Implementierung verbindlichen Architekturentscheidungen fest.

Die Entscheidungen ergänzen die bestehenden autoritativen Dokumente. Sie ersetzen insbesondere nicht:

* `docs/ARCHITECTURE.md`
* `docs/PERSISTENCE_MODEL.md`
* `docs/IDENTITY_AUTHORIZATION.md`
* `docs/SECURITY.md`
* `docs/CRYPTOGRAPHY.md`
* `docs/SYNC.md`
* `docs/Roadmap.md`
* `docs/TESTING.md`
* `docs/AI_RULES.md`

---

## ADR-001 — Sprint B implementiert das Core Persistence Model

### Status

Abgeschlossen

### Entscheidung

Sprint B implementiert die ersten fünf Kernentitäten des autoritativen Persistence Models:

1. `User`
2. `Employment`
3. `Customer`
4. `Project`
5. `ProjectAssignment`

Diese Reihenfolge entspricht der in `docs/PERSISTENCE_MODEL.md` festgelegten dependency-aware Implementation Order.

Folgende später im Persistence Model definierte Entitäten werden in Sprint B ausdrücklich noch nicht implementiert:

* `ExternalRelationship`
* `CustomerProjectAccess`
* `Workspace`
* Permission Persistence
* Session
* Audit
* Document
* DocumentVersion
* Encryption Metadata
* Federation Metadata
* zusätzliche Synchronisationsentitäten

### Begründung

Die ersten fünf Entitäten bilden das minimale stabile Domänenfundament für User-, Customer- und Project-bezogene Workflows.

Die späteren Entitäten hängen fachlich von weiteren Architekturentscheidungen zu Authentication, Authorization, Workspaces, Documents und konkreten Workflows ab.

---

## ADR-002 — Employment stellt keine Customer-Beziehung dar

### Status

Abgeschlossen

### Entscheidung

`Employment` repräsentiert ausschließlich den internen Beschäftigungs- und Hierarchiekontext eines Users.

Es gibt insbesondere keinen direkten `customer_id`-Mechanismus auf `User` oder `Employment`.

Die Beziehung zwischen einem externen User und einem Customer wird später ausschließlich über `ExternalRelationship` modelliert:


User
 └── ExternalRelationship
      └── Customer


Die Zuordnung eines Projects zu einem Customer erfolgt separat:


Customer
 └── Project


Interner Project-Zugriff wird wiederum separat über `ProjectAssignment` dargestellt:


Project
 └── ProjectAssignment
      └── User


#### ExternalRelationship created_from

`ExternalRelationship.created_from` wird als Fremdschlüssel persistiert zu `users.id`.

Die Persistenz garantiert, dass der referenzierte Nutzer existiert.

Die authorization layer MUSS validieren, dass der erstellenede Nutzer zum Anlegen einer `ExternalRelationship` berechtigt ist, bevor diese erstellt wird. Voraussetzung dafür ist unter anderem, dass der User einen gültigen PermissionGrant für diese Tätigkeit hat.

### Begründung

User Type, Employment und Business Relationship sind unterschiedliche fachliche Konzepte.

`EXTERNAL` bedeutet nicht automatisch `CUSTOMER`.

Ein Customer ist eine Business-/Domain-Entität und keine User-Kategorie.

Diese Trennung verhindert, dass spätere Beziehungen zu Suppliern, Tax Advisors oder Partnern Änderungen am Core-User-Modell erfordern.

---

## ADR-003 — Synchronisation wird nicht vor einem konkreten Offline-Workflow implementiert

### Status

Accepted

### Entscheidung

Es wird keine generische Synchronisationsengine als unmittelbarer nächster Entwicklungsschritt implementiert.

Insbesondere werden vor einem konkreten Offline-Workflow nicht vorschnell implementiert:

* generischer Sync Service
* generisches Conflict Resolution Framework
* Last-write-wins
* globale Versionierungsstrategie
* Outbox-System
* Change Feed
* Tombstones
* generische Retry Engine
* allgemeine Idempotency-Infrastruktur

`Device` und `SyncState` bleiben als bestehende technische Foundation bestehen.

Eine spätere Synchronisationsimplementierung erfolgt erst für einen konkret definierten Offline-Workflow.

Vor der Synchronisation einer Entität müssen mindestens definiert sein:

* Identity
* Lifecycle
* Authorization Scope
* Versioning
* Deletion Semantics
* Conflict Behaviour
* Retention
* Binary Transfer Requirements
* Security Implications

### Begründung

Synchronisation ist keine isolierte technische Funktion.

Eine korrekte Synchronisation benötigt bereits definierte Domain-Semantik, Authorization, Lifecycle- und Konfliktregeln.

Die Architektur von GlasHaus verlangt ausdrücklich, dass Synchronisation nicht zu einem zweiten Authorization Model wird.

Ein konkreter Offline-Workflow liefert deshalb die fachliche Grundlage für die spätere Synchronisationsarchitektur.

---

## ADR-004 — Authentication und Authorization bleiben vor geschützten Application Workflows

### Status

Accepted

### Entscheidung

Die Reihenfolge ist:


Core Persistence
      ↓
Authentication
      ↓
Authorization
      ↓
First Domain Workflow
      ↓
Browser / Mobile Foundation
      ↓
Synchronization MVP


API-Routen dürfen später nicht als Ersatz für Authentication oder Authorization dienen.

Insbesondere gilt:


Foreign Key
≠ Authorization

ProjectAssignment
≠ vollständige Permission

ExternalRelationship
≠ vollständige Permission


### Begründung

Persistence stellt strukturelle Beziehungen und Datenintegrität sicher.

Authentication beantwortet:


Wer ist der Benutzer?


Authorization beantwortet:


Darf dieser Benutzer diese konkrete Aktion
auf diese konkrete Ressource in diesem Kontext ausführen?


Diese Verantwortlichkeiten müssen getrennt bleiben.

---

## ADR-005 — Repository Layer enthält Persistence-Zugriff, aber keine Business-Logik

### Status

Accepted

### Entscheidung

Repositories kapseln Datenbankzugriffe und definierte Query-Operationen.

Sie dürfen insbesondere:

* Entities laden
* Entities erstellen
* Entities aktualisieren
* Entities deaktivieren
* definierte Persistence Queries ausführen

Sie dürfen nicht:

* HTTP kennen
* FastAPI kennen
* Pydantic API Contracts kennen
* Authorization-Entscheidungen treffen
* Domain Workflows orchestrieren
* fachliche Policies duplizieren

Die spätere Architektur bleibt:


API
 ↓
Application / Service
 ↓
Repository
 ↓
SQLAlchemy
 ↓
Database


### Begründung

Dadurch bleibt die Persistence-Schicht unabhängig von Transport und Application Layer.

Business-Regeln können später zentral im Service-/Domain-Layer getestet werden.

---

## ADR-006 — Historische Beziehungen werden nicht durch destruktive Cascades gelöscht

### Status

Accepted

### Entscheidung

Für historisch relevante Beziehungen wird kein pauschales `delete-orphan` oder `cascade="all, delete"` verwendet.

Foreign Keys verwenden restriktives Delete-Verhalten.

Insbesondere sollen folgende Datensätze nicht durch das Löschen eines Parent-Datensatzes automatisch zerstört werden:

* Employment
* ProjectAssignment
* Project
* Customer
* User

Wo historische Informationen benötigt werden, wird Deaktivierung gegenüber physischem Löschen bevorzugt.

### Begründung

Das Persistence Model verlangt explizit, historische Zustände zu erhalten.

Ein Parent-Delete darf daher nicht unkontrolliert Security-, Audit- oder Business-Historie vernichten.

---

## ADR-007 — UUIDv7 bleibt der Identifier-Standard

### Status

Accepted

### Entscheidung

Neue persistente Domain-Entities verwenden UUIDv7.

Die Python-Standardbibliothek unter Python 3.14 stellt `uuid.uuid7()` bereit und wird gegenüber einer zusätzlichen Dependency bevorzugt.

Identifier:

* sind stabil
* sind global eindeutig
* sind unabhängig von sequenziellen Datenbank-IDs
* bleiben über Synchronisation hinweg stabil
* enthalten keine Authorization-Semantik

### Begründung

Das bestehende Projekt verwendet bereits UUIDv7 als Identifier-Richtung.

Eine zusätzliche UUID-Library wäre für Sprint B nicht erforderlich und würde der Dependency-Regel aus `AI_RULES.md` widersprechen.

---

## Geltungsbereich

Diese Entscheidungen gelten ab ihrer Aufnahme in das Repository für die weitere Implementierung.

Sollte eine spätere Architekturentscheidung eine dieser Entscheidungen ändern, muss zuerst die autoritative Dokumentation aktualisiert werden.

Die Implementierung darf nicht stillschweigend von diesen Entscheidungen abweichen.
