# The Absence Engine — Implementation Plan

> **Version:** 0.1.0  
> **Date:** 2026-03-12  
> **Status:** Pre-Implementation  
> **Python:** ≥ 3.12  

---

## Table of Contents

1. [Product Definition](#1-product-definition)
2. [System Design Decisions](#2-system-design-decisions)
3. [Tech Stack](#3-tech-stack)
4. [Data Model & Schema](#4-data-model--schema)
5. [API Contract](#5-api-contract)
6. [Engine Design — Deep Dive](#6-engine-design--deep-dive)
7. [Caching Strategy](#7-caching-strategy)
8. [Security Plan](#8-security-plan)
9. [Observability & Logging](#9-observability--logging)
10. [Testing Strategy](#10-testing-strategy)
11. [Implementation Phases](#11-implementation-phases)
12. [Risk Register](#12-risk-register)

---

## 1. Product Definition

### 1.1 What It Does

Takes any document (text, PDF, DOCX, code, CSV) and surfaces **structured negative space** — what questions were never asked, what stakeholders were never considered, what failure modes were never modeled.

### 1.2 What It Does NOT Do

- Grammar/spelling correction.
- Summarization of present content.
- Plagiarism detection.
- General-purpose chatbot responses.

### 1.3 User Personas

| Persona | Use Case |
|---|---|
| **Legal analyst** | Upload contract → find missing clauses vs. standard clause libraries |
| **Product manager** | Upload PRD → find unconsidered user segments, missing edge cases |
| **Strategist** | Upload strategy doc → find unaddressed competitors, missing frameworks |
| **Engineer** | Upload codebase/design doc → find missing error handling, untested paths |
| **General user** | Upload any text → get structured absence report |

### 1.4 Core User Flow

```
Upload Document → Select Domain (or auto-detect) → Engine Analyzes
→ Absence Report Generated → User Reviews → (Optional) Fill Gaps
```

---

## 2. System Design Decisions

### 2.1 Monolith vs. Microservices

**Decision:** Modular monolith (single deployable, strict internal module boundaries).

**Rationale:** Early stage — no need for network overhead of microservices. Internal module boundaries enforced via Python package structure allow future extraction without rewrites.

### 2.2 Sync vs. Async Processing

**Decision:** Async task queue for document analysis. Sync API for CRUD and report retrieval.

**Rationale:** Document analysis involves LLM calls (2-30s latency). Blocking a request thread is unacceptable. User submits → gets a job ID → polls or subscribes via WebSocket for completion.

### 2.3 LLM Provider Strategy

**Decision:** Provider-agnostic adapter pattern. Default: Google Gemini API. Fallbacks: OpenAI, Anthropic. All LLM calls go through a single `LLMGateway` interface with built-in retry logic and circuit breaker.

**Rationale:** LLM landscape shifts fast. Swapping providers should be a config change, not a code rewrite. All three major providers now support native structured output (JSON schema response mode) — the gateway exploits this to eliminate brittle output parsing.

### 2.4 Storage

| Concern | Choice | Why |
|---|---|---|
| Relational data (users, jobs, reports) | PostgreSQL 17 | ACID, JSONB for flexible report storage, pg_trgm for text search, incremental JSON path operations |
| Document storage | S3-compatible (MinIO local / S3 prod) | Binary blobs don't belong in Postgres |
| Embeddings / vector search | pgvector 0.8+ extension | HNSW + IVFFlat indexes, keeps infra simple — no separate vector DB until scale demands it |
| Cache | Redis 8 | Session, rate-limit counters, job status pub/sub, hash field expiration |
| Task queue | arq (async Redis queue) | Native asyncio — no sync/async impedance mismatch with FastAPI. Lighter than Celery, built for async Python |
| DB connection pool | asyncpg pool (via SQLAlchemy async engine) | Bounded pool with min/max size, health checks, overflow control |

### 2.5 Frontend

**Decision:** Next.js 15 (App Router) with React 19 + TypeScript 5.7 + vanilla CSS modules.

**Rationale:** SSR for SEO on landing/docs pages. App Router for streaming responses. React 19 for `use()` hook, Server Components, and improved Suspense. No Tailwind unless explicitly requested.

---

## 3. Tech Stack

### 3.1 Backend

| Layer | Technology | Version |
|---|---|---|
| Language | Python | ≥ 3.12 |
| Web framework | FastAPI | 0.115+ |
| ASGI server | Uvicorn | 0.34+ |
| ORM / migrations | SQLAlchemy 2.0 + Alembic | Latest |
| Task queue | arq | 0.26+ |
| Message broker / cache | Redis | 8+ |
| Validation | Pydantic v2 | 2.11+ |
| PDF parsing | pdfplumber | Latest |
| DOCX parsing | python-docx | Latest |
| Spreadsheet parsing | openpyxl (xlsx), csv stdlib (csv) | Latest |
| Code parsing | tree-sitter | Latest |
| LLM clients | google-genai, openai, anthropic | Latest |
| Embeddings | API-based (Gemini `text-embedding-005`, OpenAI `text-embedding-3-large`) | Latest |
| Resilience | tenacity (retry), circuitbreaker | Latest |
| Testing | pytest, pytest-asyncio, httpx | Latest |
| Linting | ruff | Latest |

### 3.2 Frontend

| Layer | Technology | Version |
|---|---|---|
| Framework | Next.js | 15+ |
| UI library | React | 19+ |
| Language | TypeScript | 5.7+ |
| Styling | CSS Modules (vanilla) | — |
| HTTP client | Native fetch | — |
| State | React Context + `use()` hook | — |
| Charts | D3.js (for absence visualizations) | 7+ |
| Testing | Vitest + React Testing Library | Latest |

### 3.3 Infrastructure

| Concern | Technology |
|---|---|
| Containerization | Docker + docker-compose |
| CI/CD | GitHub Actions |
| Reverse proxy | Nginx (production) |
| Secrets management | `.env` files (dev), cloud KMS (prod) |

---

## 4. Data Model & Schema

### 4.1 Entity Relationship

```
User 1──N Document 1──N AnalysisJob 1──1 AbsenceReport 1──N AbsenceItem
                                                          1──N SuggestedCompletion
User 1──N CustomSchema
```

### 4.2 Tables

#### `users`

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK, default gen_random_uuid() |
| email | VARCHAR(255) | UNIQUE, NOT NULL |
| password_hash | VARCHAR(255) | NOT NULL |
| name | VARCHAR(100) | NOT NULL |
| role | VARCHAR(20) | NOT NULL, DEFAULT 'user' |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

**Indexes:** `email` (unique), `created_at`

#### `documents`

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK → users.id, NOT NULL |
| filename | VARCHAR(255) | NOT NULL |
| mime_type | VARCHAR(100) | NOT NULL |
| storage_key | VARCHAR(500) | NOT NULL (S3 key) |
| size_bytes | BIGINT | NOT NULL |
| extracted_text | TEXT | NULL (populated after parsing) |
| domain | VARCHAR(50) | NULL (populated after classification) |
| domain_confidence | FLOAT | NULL |
| checksum_sha256 | VARCHAR(64) | NOT NULL |
| is_deleted | BOOLEAN | NOT NULL, DEFAULT false |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

**Indexes:** `user_id`, `domain`, `checksum_sha256`, `created_at`

#### `analysis_jobs`

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| document_id | UUID | FK → documents.id, NOT NULL |
| user_id | UUID | FK → users.id, NOT NULL |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'pending' |
| idempotency_key | VARCHAR(64) | UNIQUE, NOT NULL |
| domain_override | VARCHAR(50) | NULL |
| custom_schema_id | UUID | FK → custom_schemas.id, NULL |
| started_at | TIMESTAMPTZ | NULL |
| completed_at | TIMESTAMPTZ | NULL |
| error_message | TEXT | NULL |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

**Indexes:** `document_id`, `user_id`, `status`, `idempotency_key` (unique), `created_at`  
**Status enum values:** `pending`, `processing`, `completed`, `failed`

#### `absence_reports`

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| job_id | UUID | FK → analysis_jobs.id, UNIQUE, NOT NULL |
| document_id | UUID | FK → documents.id, NOT NULL |
| user_id | UUID | FK → users.id, NOT NULL |
| summary | TEXT | NOT NULL |
| overall_risk_score | FLOAT | NOT NULL (0.0 - 1.0) |
| domain_detected | VARCHAR(50) | NOT NULL |
| metadata | JSONB | NOT NULL, DEFAULT '{}' |
| is_deleted | BOOLEAN | NOT NULL, DEFAULT false |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

**Indexes:** `job_id` (unique), `document_id`, `user_id`, `overall_risk_score`, `created_at`

#### `absence_items`

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| report_id | UUID | FK → absence_reports.id, NOT NULL |
| category | VARCHAR(50) | NOT NULL |
| title | VARCHAR(255) | NOT NULL |
| description | TEXT | NOT NULL |
| reasoning | TEXT | NOT NULL |
| confidence | FLOAT | NOT NULL (0.0 - 1.0) |
| risk_score | FLOAT | NOT NULL (0.0 - 1.0) |
| absence_type | VARCHAR(30) | NOT NULL |
| evidence | JSONB | NOT NULL, DEFAULT '[]' |
| sort_order | INT | NOT NULL, DEFAULT 0 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

**Indexes:** `report_id`, `category`, `absence_type`, `risk_score`, `sort_order`  
**Absence type enum:** `coverage_gap`, `logical_implication`, `stakeholder_gap`, `temporal_gap`, `emotional_relational`, `structural_gap`

#### `suggested_completions`

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| absence_item_id | UUID | FK → absence_items.id, NOT NULL |
| suggestion_text | TEXT | NOT NULL |
| confidence | FLOAT | NOT NULL |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

**Indexes:** `absence_item_id`

#### `custom_schemas`

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK → users.id, NOT NULL |
| name | VARCHAR(100) | NOT NULL |
| domain | VARCHAR(50) | NOT NULL |
| schema_definition | JSONB | NOT NULL |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

**Indexes:** `user_id`, `domain`

#### `document_embeddings`

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| document_id | UUID | FK → documents.id, NOT NULL |
| chunk_index | INT | NOT NULL |
| chunk_text | TEXT | NOT NULL |
| embedding | VECTOR(768) | NOT NULL |
| model_version | VARCHAR(50) | NOT NULL (e.g. 'text-embedding-005') |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

**Indexes:** `document_id`, `model_version`, HNSW index on `embedding` (for ANN search, `lists=100` for <100K rows)

---

## 5. API Contract

### 5.1 Auth

| Method | Endpoint | Body | Response |
|---|---|---|---|
| POST | `/api/v1/auth/register` | `{email, password, name}` | `{user, access_token, refresh_token}` |
| POST | `/api/v1/auth/login` | `{email, password}` | `{access_token, refresh_token}` |
| POST | `/api/v1/auth/refresh` | `{refresh_token}` | `{access_token}` |
| POST | `/api/v1/auth/logout` | — | `204` |

### 5.2 Documents

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/documents` | Upload document (multipart/form-data) |
| GET | `/api/v1/documents` | List user's documents (paginated) |
| GET | `/api/v1/documents/{id}` | Get document metadata |
| DELETE | `/api/v1/documents/{id}` | Soft-delete document |

### 5.3 Analysis

| Method | Endpoint | Body | Description |
|---|---|---|---|
| POST | `/api/v1/analysis` | `{document_id, domain_override?, custom_schema_id?, idempotency_key}` | Start analysis job |
| GET | `/api/v1/analysis/{job_id}` | — | Get job status |
| GET | `/api/v1/analysis/{job_id}/report` | — | Get absence report |
| WS | `/api/v1/analysis/{job_id}/stream` | — | Stream job progress in real-time |

### 5.4 Reports

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/reports` | List user's reports (paginated) |
| GET | `/api/v1/reports/{id}` | Get full report with absence items |
| GET | `/api/v1/reports/{id}/export` | Export as PDF/JSON |
| DELETE | `/api/v1/reports/{id}` | Soft-delete report |

### 5.5 Custom Schemas

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/schemas` | Create custom completeness schema |
| GET | `/api/v1/schemas` | List user's schemas (paginated) |
| GET | `/api/v1/schemas/{id}` | Get schema detail |
| PUT | `/api/v1/schemas/{id}` | Update schema |
| DELETE | `/api/v1/schemas/{id}` | Delete schema |

### 5.6 Pagination Convention

All list endpoints accept `?page=1&per_page=20` (max 100).  
Response envelope:

```json
{
  "data": [...],
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 142,
    "total_pages": 8
  }
}
```

### 5.7 Error Envelope

```json
{
  "error": {
    "code": "DOCUMENT_NOT_FOUND",
    "message": "The requested document does not exist.",
    "request_id": "req_abc123"
  }
}
```

---

## 6. Engine Design — Deep Dive

This is the intellectual core of the system. Four sequential pipeline stages, each independently testable.

### 6.1 Stage 1 — Input Processing

**Goal:** Convert raw uploaded file into clean, structured text + domain classification.

#### 6.1.1 Document Parsing

| Format | Parser | Output |
|---|---|---|
| .txt / .md | Raw read + markdown stripping | Plain text |
| .pdf | pdfplumber → page-by-page extraction | Plain text with page markers |
| .docx | python-docx → paragraph extraction | Plain text with heading hierarchy |
| .csv | csv stdlib → row serialization | Tabular text representation |
| .xlsx | openpyxl → row serialization | Tabular text representation |
| Code files | tree-sitter → AST + raw source | Structured code representation |

**Edge cases to handle:**
- Scanned PDFs (no selectable text) → flag for user, suggest OCR.
- Encrypted/password-protected files → reject with clear error.
- Files > 50MB → reject at upload validation.
- Empty files → reject at upload validation.

#### 6.1.2 Domain Classification

**Approach:** Two-stage classification.

1. **Rule-based pre-classifier:** Check file extension, keyword density (e.g., "WHEREAS", "indemnify" → legal; "sprint", "user story" → product).
2. **LLM classifier:** Send first 2000 tokens to LLM using **native structured output** (JSON schema response mode — both Gemini and OpenAI support this natively as of 2025). Schema:
   ```json
   {"domain": "string (enum)", "confidence": "float 0.0-1.0", "reasoning": "string"}
   ```
   No regex/text parsing needed — the LLM returns a Pydantic-validated object directly.
3. **Consensus:** If rule-based and LLM agree → high confidence. If disagree → use LLM result but lower confidence. If confidence < 0.6 → prompt user to select domain.

#### 6.1.3 Text Chunking

**Strategy:** Recursive character splitting with semantic awareness.

- Chunk size: 1500 tokens (with 200-token overlap).
- Split boundaries: paragraph → sentence → word (prefer semantic breaks).
- Each chunk gets an embedding via API-based embedding (Gemini `text-embedding-005` 768-dim, or OpenAI `text-embedding-3-large` 3072-dim truncated to 768-dim for storage uniformity).
- Each embedding row stores `model_version` — if the embedding model changes, stale embeddings are re-computed lazily on next analysis.
- Chunks stored in `document_embeddings` table for peer comparison.

### 6.2 Stage 2 — Expected Content Modeling

**Goal:** Build a model of "what SHOULD be in this document" given its domain and type.

#### 6.2.1 Domain Ontology Lookup

Each domain has a pre-built ontology — a structured checklist of topics, clauses, sections, considerations that a complete document of that type should address.

**Ontology structure (stored as JSON/YAML config files):**

```yaml
# ontologies/legal_contract.yaml
domain: legal
document_types:
  - name: service_agreement
    required_sections:
      - scope_of_work
      - payment_terms
      - termination_clause
      - liability_limitation
      - intellectual_property
      - confidentiality
      - dispute_resolution
      - force_majeure
      - amendment_procedure
      - governing_law
    required_considerations:
      - vendor_bankruptcy
      - data_breach_liability
      - subcontractor_provisions
      - insurance_requirements
      - compliance_obligations
    stakeholders:
      - buyer
      - seller
      - end_users
      - regulators
      - subcontractors
```

**Built-in ontologies to ship with v1:**
- Legal contracts (service agreement, NDA, employment, licensing)
- Product specs (PRD, technical spec, design doc)
- Strategy docs (business plan, competitive analysis, go-to-market)
- Technical docs (architecture doc, runbook, RFC)
- Interpersonal (meeting notes, performance review, 1:1 notes)

#### 6.2.2 Custom Schema Integration

Users can define their own completeness schemas via the API. These are merged with (or replace) the built-in ontology for the analysis run.

#### 6.2.3 Peer Comparison (Embedding-Based)

**Approach:** Compare the uploaded document's embedding vectors against a reference corpus of similar documents.

- For v1, the reference corpus is bootstrapped from public datasets (e.g., SEC filings for legal, open-source PRDs for product).
- Cosine similarity search via pgvector to find top-K most similar reference documents.
- Extract the topic distribution of peer documents to identify what topics peers cover that this document does not.

**Implementation detail:**
- Pre-compute topic fingerprints for reference docs (list of topics with presence scores).
- At analysis time: compute topic fingerprint for input doc → diff against peer average → gaps = candidate absences.

#### 6.2.4 Stakeholder Graph Inference

**Approach:** Named Entity Recognition on the document to extract all mentioned persons, orgs, roles. Cross-reference against the ontology's `stakeholders` list to find who is never mentioned.

- Use LLM for NER (more accurate for varied document types than spaCy alone).
- Build a mention graph: `{entity → [sections where mentioned]}`.
- Compare against expected stakeholders for the domain → absent stakeholders flagged.

### 6.3 Stage 3 — Absence Detection Engine

**Goal:** The core analysis. Four independent detectors, each producing a list of `AbsenceItem` candidates.

#### 6.3.1 Coverage Gap Detector

**Input:** Document text + domain ontology + peer topic fingerprints.  
**Output:** List of topics/sections that should exist but don't.

**Algorithm:**
1. For each item in the domain ontology's required sections/considerations:
   - Semantic search: embed the ontology item description → search document chunks.
   - If best match similarity < threshold (0.65) → candidate gap.
2. For each topic in peer average that is absent from input doc:
   - If peer coverage > 70% and input coverage < 10% → candidate gap.
3. Rank candidates by (ontology importance weight × peer frequency × inverse similarity score).

**LLM verification pass:**
- Send top-N candidates to LLM with relevant document context:
  ```
  Document excerpt: "..."
  Expected topic: "force majeure clause"
  Is this topic adequately addressed in the document? If no, explain what specifically is missing.
  ```
- Filter out false positives (topic addressed implicitly or under different terminology).

#### 6.3.2 Logical Implication Detector

**Input:** Document text (full).  
**Output:** Cases where a stated fact logically implies something that is never addressed.

**Algorithm:**
1. Extract key assertions from the document via LLM:
   ```
   Extract all factual claims, commitments, and assumptions from this document.
   Return as: [{"assertion": "...", "section": "...", "implications": ["..."]}]
   ```
2. For each assertion, ask: "What follow-up questions or provisions does this assertion necessitate?"
3. Search the document for evidence that those follow-ups are addressed.
4. Unaddressed implications → candidate absences.

**Example:**
- Assertion: "The service will be available 99.9% of the time."
- Implication: "There should be a definition of how downtime is measured, what the remedy is for SLA breach, and what constitutes an exclusion."
- If none of these are in the document → absence flagged.

#### 6.3.3 Emotional/Relational Absence Detector

**Input:** Document text (for interpersonal domain primarily, but applicable to all).  
**Output:** Patterns of who/what is systematically not discussed in emotional or relational context.

**Algorithm:**
1. Build sentiment map: for each entity mentioned, score the sentiment of surrounding context.
2. Identify entities that are mentioned only in neutral/transactional context but never in evaluative context (praise, criticism, trust, concern).
3. Identify relational patterns: e.g., in a team meeting doc, Person A is discussed as completing tasks but never in terms of growth, feedback, or collaboration.
4. Flag: "Entity X is mentioned N times but never in context of [trust/feedback/concern/growth]."

**Scope control:** This detector is marked `beta`. Confidence scores are discounted by 20% relative to other detectors. The user can disable it.

#### 6.3.4 Temporal Absence Detector

**Input:** Document text + domain ontology.  
**Output:** Scenarios, timeframes, or future states that are never considered.

**Algorithm:**
1. Extract temporal references from the document (dates, "next quarter", "Phase 2", etc.).
2. Build a timeline of what the document plans for.
3. Identify gaps:
   - No mention of what happens after contract expiry.
   - No contingency for project delay.
   - No consideration of market changes in 12+ month horizon.
4. Cross-reference with domain ontology's temporal considerations.

### 6.4 Stage 4 — Output Assembly

**Goal:** Merge, deduplicate, rank, and format all detected absences into a coherent report.

#### 6.4.1 Deduplication

- Embed all candidate absence titles → cluster by cosine similarity > 0.85 → merge clusters into single items.
- Prefer the highest-confidence item in each cluster as the representative.

#### 6.4.2 Risk Scoring

Each absence item gets a risk score (0.0 - 1.0) computed as:

```
risk = (domain_weight × 0.3) + (confidence × 0.3) + (peer_frequency × 0.2) + (implication_severity × 0.2)
```

- `domain_weight`: How critical this type of absence is for the domain (from ontology config).
- `confidence`: The detector's confidence in this being a true absence.
- `peer_frequency`: How often peer documents include this topic (higher = more alarming that it's missing).
- `implication_severity`: LLM-assessed severity of consequences if this absence is exploited/encountered.

#### 6.4.3 Report Generation

Structure of the final `AbsenceReport`:

```json
{
  "summary": "This service agreement has 7 significant absences...",
  "overall_risk_score": 0.72,
  "domain_detected": "legal",
  "items": [
    {
      "title": "No Force Majeure Clause",
      "category": "legal_protection",
      "absence_type": "coverage_gap",
      "description": "The contract does not address...",
      "reasoning": "Standard service agreements include... because...",
      "confidence": 0.94,
      "risk_score": 0.88,
      "evidence": [
        {"type": "ontology_mismatch", "detail": "..."},
        {"type": "peer_comparison", "detail": "92% of similar contracts include this"}
      ],
      "suggested_completion": "Consider adding: 'Neither party shall be liable for...'"
    }
  ]
}
```

#### 6.4.4 Suggested Completions (Optional)

For each absence item, optionally generate a draft of what the missing content could look like:

- LLM prompt: "Given this document context and this identified absence, draft a paragraph that addresses the gap. Match the document's tone and style."
- Marked as suggestions, never auto-inserted.

---

## 7. Caching Strategy

| Data | Cache Layer | TTL | Invalidation |
|---|---|---|---|
| Domain ontologies | In-memory (app startup) | Infinite (until redeploy) | Redeploy |
| LLM classification results | Redis | 24h | Document re-upload |
| Embedding vectors | PostgreSQL (pgvector) | Permanent | Document deletion or model version change (lazy recompute) |
| Peer comparison results | Redis | 1h | New reference docs added |
| Completed reports | PostgreSQL (source of truth) + Redis (hot cache) | Redis: 1h | Report regeneration |
| Auth tokens (blacklist) | Redis | Token TTL | Logout |
| Rate limit counters | Redis | Window duration | Auto-expire |
| DB connection pool | asyncpg pool (in-process) | Connection lifetime: 300s | Health check every 30s, stale connections recycled |

---

## 8. Security Plan

### 8.1 Authentication

- JWT access tokens (15 min TTL), refresh tokens (7 day TTL, stored hashed in DB).
- Password hashing: argon2id.
- Refresh token rotation: each use invalidates the old token and issues new pair.

### 8.2 Authorization

- Role-based: `user`, `admin`.
- Every data-access query includes `WHERE user_id = :current_user_id`. No exceptions.
- Admin endpoints behind separate middleware.

### 8.3 Input Validation

- Pydantic v2 models on every endpoint — strict mode, no extra fields allowed.
- File upload: validate MIME type (allowlist: `application/pdf`, `text/plain`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`, etc.), max 50MB, virus scan placeholder for production.
- All string inputs: strip, truncate to max length, reject null bytes.

### 8.4 Rate Limiting

| Endpoint Group | Limit |
|---|---|
| Auth (login, register) | 5 req/min per IP |
| Document upload | 10 req/min per user |
| Analysis start | 5 req/min per user |
| General API | 60 req/min per user |

### 8.5 CORS & CSRF

- CORS: allowlist of frontend origins only.
- CSRF: SameSite=Strict cookies + custom header check for state-changing requests.
- All responses: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Strict-Transport-Security`.

---

## 9. Observability & Logging

### 9.1 Structured Logging

Every log line is JSON with fields:

```json
{
  "timestamp": "ISO8601",
  "level": "INFO|WARN|ERROR",
  "request_id": "req_xxx",
  "user_id": "uuid (if authenticated)",
  "action": "document.upload",
  "status": "success|failure",
  "duration_ms": 142,
  "metadata": {}
}
```

### 9.2 What Is Never Logged

- Passwords, tokens, API keys.
- Full request bodies.
- Document contents.
- PII beyond user_id.

### 9.3 Key Metrics

| Metric | Type |
|---|---|
| `analysis.duration_seconds` | Histogram |
| `analysis.status` | Counter (by status) |
| `llm.call_duration_seconds` | Histogram (by provider) |
| `llm.token_usage` | Counter (by model) |
| `document.upload_size_bytes` | Histogram |
| `api.request_duration_seconds` | Histogram (by endpoint) |
| `api.error_rate` | Counter (by endpoint, status code) |

---

## 10. Testing Strategy

### 10.1 Unit Tests

| Module | What to Test |
|---|---|
| Document parsers | Each format → correct text extraction, edge cases (empty, corrupt, large) |
| Domain classifier | Known documents → correct domain, confidence thresholds |
| Each absence detector | Known inputs → expected absences found, no false positives on clean docs |
| Risk scorer | Score calculation with known inputs |
| Auth service | Token generation, validation, refresh, expiry |
| Pydantic models | Valid/invalid payloads, edge cases |

### 10.2 Integration Tests

| Flow | What to Test |
|---|---|
| Upload → analysis → report | Full happy path, end-to-end |
| Auth flow | Register → login → access protected endpoint → refresh → logout |
| Pagination | Correct page counts, boundary conditions |
| Idempotency | Duplicate analysis request → same job returned |
| Rate limiting | Exceeding limit → 429 response |
| File validation | Reject oversized, wrong type, corrupt files |

### 10.3 Coverage Target

- **Backend:** ≥ 85% line coverage. 100% on auth, validation, and financial/risk calculations.
- **Frontend:** ≥ 70% component coverage. 100% on form validation and auth flows.

---

## 11. Implementation Phases

### Phase 1 — Foundation (Weeks 1-2)

| Step | Task | Deliverable |
|---|---|---|
| 1.1 | Project scaffolding: backend package structure, linting, pre-commit hooks | Runnable empty FastAPI app |
| 1.2 | Docker Compose: Postgres + Redis + app | `docker-compose.yml` |
| 1.3 | Database: Alembic setup, initial migration with all tables | Migration files |
| 1.4 | Config management: Pydantic Settings, `.env.example` | `config.py` |
| 1.5 | Shared utilities: structured logger, error handlers, pagination helper, request ID middleware | `shared/` package |
| 1.6 | Auth module: register, login, refresh, logout, JWT middleware | `auth/` package + tests |

### Phase 2 — Document Pipeline (Weeks 3-4)

| Step | Task | Deliverable |
|---|---|---|
| 2.1 | S3/MinIO client wrapper | `services/storage.py` |
| 2.2 | File upload endpoint with validation | `routes/documents.py` |
| 2.3 | Document parsers: txt, pdf, docx, csv, xlsx | `engine/parsers/` package + tests |
| 2.4 | Domain classifier (rule-based + LLM with structured output) | `engine/classifier.py` + tests |
| 2.5 | Text chunker + embedding pipeline (API-based) | `engine/chunker.py` + tests |
| 2.6 | arq worker setup for async processing | `worker/` package |
| 2.7 | Document CRUD endpoints | Complete `routes/documents.py` |

### Phase 3 — Absence Engine Core (Weeks 5-7)

| Step | Task | Deliverable |
|---|---|---|
| 3.1 | LLM Gateway (provider-agnostic interface) | `engine/llm/gateway.py` |
| 3.2 | Domain ontologies (YAML configs for 5 domains) | `engine/ontologies/` |
| 3.3 | Coverage Gap Detector | `engine/detectors/coverage.py` + tests |
| 3.4 | Logical Implication Detector | `engine/detectors/implication.py` + tests |
| 3.5 | Temporal Absence Detector | `engine/detectors/temporal.py` + tests |
| 3.6 | Emotional/Relational Detector (beta) | `engine/detectors/relational.py` + tests |
| 3.7 | Output assembler: dedup, risk scoring, report generation | `engine/assembler.py` + tests |
| 3.8 | Analysis orchestrator: ties pipeline together | `engine/orchestrator.py` + tests |
| 3.9 | Analysis API endpoints | `routes/analysis.py` |
| 3.10 | Report API endpoints + export | `routes/reports.py` |

### Phase 4 — Frontend (Weeks 8-10)

| Step | Task | Deliverable |
|---|---|---|
| 4.1 | Next.js project scaffolding + design system (CSS tokens, typography) | `frontend/` project |
| 4.2 | Auth pages: login, register | Auth UI + API integration |
| 4.3 | Dashboard: document list, upload, analysis history | Dashboard UI |
| 4.4 | Document upload flow with progress | Upload component |
| 4.5 | Analysis status page with real-time updates (WebSocket) | Analysis status UI |
| 4.6 | Absence report viewer: interactive, expandable items, risk gauge | Report viewer UI |
| 4.7 | Report export (PDF download) | Export functionality |
| 4.8 | Custom schema builder UI | Schema CRUD pages |
| 4.9 | Landing page + documentation | Marketing/docs pages |

### Phase 5 — Polish & Production Readiness (Weeks 11-12)

| Step | Task | Deliverable |
|---|---|---|
| 5.1 | Integration test suite | Full E2E coverage |
| 5.2 | Rate limiting implementation | Redis-backed limiter |
| 5.3 | CORS, security headers, CSRF protection | Security middleware |
| 5.4 | Logging and metrics pipeline | Structured logging in all modules |
| 5.5 | CI/CD pipeline (lint → test → build → deploy) | GitHub Actions workflows |
| 5.6 | Production Docker build (multi-stage, non-root) | Production Dockerfile |
| 5.7 | Load testing | k6 or locust scripts + results |
| 5.8 | Documentation: API docs (auto-generated), README, contributing guide | Docs |

---

## 12. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| LLM hallucinations producing false absences | High | Medium | Multi-stage verification, confidence thresholds, user feedback loop |
| LLM API cost escalation | Medium | High | Token budgets per analysis, caching, batch prompts, model tiering (use Flash for classification, Pro for detection) |
| LLM provider downtime | Medium | High | Three-provider fallback chain (Gemini → OpenAI → Anthropic), circuit breaker with exponential backoff |
| LLM transient failures (rate limits, timeouts) | High | Medium | tenacity retry with exponential backoff + jitter, per-provider circuit breaker (open after 5 consecutive failures, half-open after 60s) |
| Slow analysis (>60s) frustrating users | Medium | Medium | Async processing via arq, streaming progress via WebSocket, parallel detector execution |
| Ontology incompleteness for niche domains | High | Medium | Custom schema feature, continuous ontology expansion, community contributions |
| Document parsing failures on edge-case formats | Medium | Low | Robust error handling, clear user feedback, format support roadmap |
| pgvector performance at scale | Low | Medium | Monitor query latency, plan migration to dedicated vector DB if needed |
| Embedding model version drift | Medium | Medium | `model_version` column on embeddings, lazy recompute on version mismatch, never mix embedding spaces |
| DB connection exhaustion under load | Low | High | asyncpg pool with bounded max (20), overflow (10), connection health checks, recycle stale connections |

---

*This plan is a living document. Update it as decisions evolve.*
