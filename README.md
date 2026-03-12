<div align="center">

<h1>
  <br>
  The Absence Engine
  <br>
</h1>

<p><em>What your document didn't say is often more important than what it did.</em></p>

<p>
  <a href="#"><img src="https://img.shields.io/badge/version-0.1.0-blueviolet?style=flat-square" alt="Version"></a>
  <a href="#"><img src="https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="#"><img src="https://img.shields.io/badge/Next.js-16-000000?style=flat-square&logo=next.js&logoColor=white" alt="Next.js"></a>
  <a href="#"><img src="https://img.shields.io/badge/FastAPI-0.115%2B-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI"></a>
  <a href="#"><img src="https://img.shields.io/badge/status-phase%205%20%E2%80%93%20production%20readiness-orange?style=flat-square" alt="Status"></a>
  <a href="#"><img src="https://img.shields.io/badge/tests-53%2F53%20passing-brightgreen?style=flat-square" alt="Tests"></a>
</p>

<p>
  <a href="#-overview">Overview</a> •
  <a href="#-how-it-works">How It Works</a> •
  <a href="#-tech-stack">Tech Stack</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-getting-started">Getting Started</a> •
  <a href="#-api-reference">API Reference</a> •
  <a href="#-roadmap">Roadmap</a>
</p>

---

<!-- DEMO VIDEO PLACEHOLDER -->
> **📽 Demo** — [Watch a full walkthrough](https://youtu.be/DEMO_LINK_HERE) *

---

</div>

## Overview

The Absence Engine is a **document intelligence system** that surfaces what your documents *forgot to say*. It doesn't summarize. It doesn't correct grammar. It reads any document — a contract, a product spec, a strategy memo, a codebase — and generates a structured report of its **negative space**: missing clauses, unaddressed stakeholders, logical consequences that were never considered, and future scenarios that were never modeled.

Most AI tools tell you what a document contains. This one tells you what it's **missing**.

### Who It's For

| Persona | What They Upload | What They Get |
|---|---|---|
| Legal Analyst | Service agreement / NDA | Missing standard clauses vs. industry benchmarks |
| Product Manager | PRD / Feature spec | Unaddressed user segments, missing edge cases |
| Strategist | Business plan / GTM doc | Unconsidered competitors, missing frameworks |
| Software Engineer | Architecture doc / RFC | Missing failure modes, unhandled paths |
| Anyone | Any text document | A structured audit of what isn't there |

---

## How It Works

The engine runs a **four-stage analysis pipeline**, fully asynchronous, on every submitted document:

```
Upload Document
      │
      ▼
┌─────────────────────────────────────────────────────────┐
│  Stage 1 — Input Processing                             │
│  Format-aware parsing → Domain classification           │
│  (rule-based keywords + LLM structured output)          │
│  → Text chunking → Vector embedding (pgvector)          │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│  Stage 2 — Expected Content Modeling                    │
│  Domain ontology lookup → Peer document comparison      │
│  (cosine similarity via pgvector) → Stakeholder graph   │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│  Stage 3 — Absence Detection (4 independent detectors)  │
│  ├── Coverage Gap Detector   (ontology + peer diff)     │
│  ├── Logical Implication     (assertion → consequence)  │
│  ├── Temporal Absence        (timeline gap modeling)    │
│  └── Relational/Emotional    (sentiment topology, beta) │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│  Stage 4 — Output Assembly                              │
│  Deduplication (semantic clustering) → Risk scoring     │
│  → Structured AbsenceReport with suggested completions  │
└─────────────────────────────────────────────────────────┘
```

Each detected absence is returned with a **title**, **description**, **machine reasoning**, **confidence score**, **risk score** (0.0–1.0), supporting **evidence**, and an optional **draft completion**. The entire pipeline is independently testable at each stage.

---

## Tech Stack

### Backend

| Layer | Technology |
|---|---|
| Language | Python ≥ 3.12 |
| Web Framework | FastAPI 0.115+ |
| ASGI Server | Uvicorn 0.34+ |
| ORM / Migrations | SQLAlchemy 2.0 + Alembic |
| Task Queue | arq (native asyncio, Redis-backed) |
| Validation | Pydantic v2.11+ |
| Document Parsing | pdfplumber · python-docx · openpyxl · tree-sitter |
| LLM Clients | google-genai · openai · anthropic |
| Resilience | tenacity (retry) · circuitbreaker |
| Testing | pytest · pytest-asyncio · httpx |
| Linting | ruff |

### Frontend

| Layer | Technology |
|---|---|
| Framework | Next.js 16 (App Router) |
| UI Library | React 19 |
| Language | TypeScript 5.7+ |
| Styling | Vanilla CSS Modules |
| Charts | D3.js (absence visualizations) |
| State Management | React Context + `use()` hook |

### Infrastructure

| Concern | Technology |
|---|---|
| Primary Database | PostgreSQL 17 + pgvector 0.8+ |
| Vector Search | pgvector HNSW index |
| Cache / Broker | Redis 8 |
| Object Storage | S3-compatible (MinIO local / S3 prod) |
| Containerization | Docker + Docker Compose |
| CI/CD | GitHub Actions |

---

## Architecture

The project follows a **modular monolith** pattern — a single deployable unit with strict internal package boundaries, designed for future microservice extraction without rewrites.

```
TheAbsenceEngine/
├── backend/
│   ├── app/
│   │   ├── main.py              # App factory, lifespan, middleware registration
│   │   ├── config.py            # Pydantic Settings — all env validation
│   │   ├── dependencies.py      # FastAPI DI tree (DB session, current user)
│   │   ├── shared/              # Cross-cutting utilities (no business logic)
│   │   │   ├── db.py            # Async SQLAlchemy engine + pool config
│   │   │   ├── security.py      # argon2id + JWT encode/decode
│   │   │   ├── rate_limiter.py  # Redis sliding-window rate limiter
│   │   │   ├── retry.py         # tenacity retry + circuit breaker
│   │   │   └── storage.py       # S3/MinIO + local filesystem abstraction
│   │   ├── models/              # SQLAlchemy ORM models (one file per table)
│   │   ├── schemas/             # Pydantic request/response contracts
│   │   ├── services/            # Pure business logic — no HTTP awareness
│   │   ├── routes/              # Thin HTTP layer — validate, delegate, respond
│   │   └── engine/              # The core analysis pipeline
│   │       ├── orchestrator.py  # Pipeline coordinator
│   │       ├── parsers/         # Format-specific document parsers
│   │       ├── classifier.py    # Two-stage domain classification
│   │       ├── chunker.py       # Recursive semantic text chunking
│   │       ├── embedder.py      # API-based embedding generation
│   │       ├── llm/             # Provider-agnostic LLM gateway
│   │       │   ├── gateway.py   # Abstract interface
│   │       │   ├── gemini_provider.py
│   │       │   ├── openai_provider.py
│   │       │   └── anthropic_provider.py
│   │       ├── detectors/       # Absence detection modules
│   │       ├── ontologies/      # YAML domain knowledge configs
│   │       └── assembler.py     # Dedup + risk scoring + report formatting
│   └── worker/                  # arq async worker process
│
├── frontend/
│   └── src/
│       ├── app/                 # Next.js App Router pages
│       ├── components/
│       │   ├── ui/              # Atomic primitives (Button, Input, Modal…)
│       │   ├── layout/          # Sidebar, Header, Footer
│       │   └── features/        # Domain components (AbsenceCard, RiskGauge…)
│       ├── lib/                 # API client, auth context, WebSocket client
│       ├── hooks/               # useAuth, useDocuments, useAnalysis, useReports
│       └── types/               # TypeScript types mirroring backend schemas 1:1
│
└── Docs/
    ├── architecture.md          # Full module responsibility matrix + data flows
    ├── plan.md                  # Complete implementation plan + design decisions
    └── live_status.md           # Current phase, what's done, what's next
```

> **Full architecture reference** → [`Docs/architecture.md`](./Docs/architecture.md)

---

## Data Model

Five core entities form the analysis lifecycle:

```
User ──1:N──► Document ──1:N──► AnalysisJob ──1:1──► AbsenceReport ──1:N──► AbsenceItem
                                                                     └──1:N──► SuggestedCompletion
User ──1:N──► CustomSchema
Document ──1:N──► DocumentEmbedding  (pgvector HNSW index)
```

Risk scores on `AbsenceItem` are computed as a weighted combination of domain criticality, detector confidence, peer frequency, and LLM-assessed implication severity.

---

## LLM Provider Strategy

All LLM calls flow through a single **`LLMGateway`** interface. The runtime builds a **fallback chain** — if the primary provider fails or its circuit opens, the next provider in the chain is tried automatically.

```
Default: Gemini 2.5 Pro  →  OpenAI fallback  →  Anthropic fallback
```

Swapping providers is a **config change, not a code change**. Every provider is wrapped with:
- **Tenacity** exponential backoff with jitter
- **Circuit breaker** (opens after N consecutive failures, half-opens after timeout)
- **Token budget cap** per analysis run

---

## Getting Started

### Prerequisites

- Python ≥ 3.12 with [`uv`](https://github.com/astral-sh/uv)
- Node.js ≥ 20
- PostgreSQL 17 with pgvector extension
- Redis 8
- At least one LLM API key (Gemini / OpenAI / Anthropic)

### 1. Clone

```bash
git clone https://github.com/YOUR_USERNAME/TheAbsenceEngine.git
cd TheAbsenceEngine
```

### 2. Backend Setup

```bash
cd backend

# Copy environment template and fill in your values
cp .env.example .env

# Install dependencies
uv sync

# Run database migrations
uv run alembic upgrade head

# Start the API server
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

> **Note:** Redis is optional in development. When unavailable, the backend automatically falls back to an in-process async queue (`InlineQueue`) so the full pipeline still runs locally. Analysis jobs that require Redis are handled gracefully in this mode.

### 3. Frontend Setup

```bash
cd frontend

npm install
npm run dev
```

The frontend will be available at `http://localhost:3000`.

### 4. Run the Worker (for Redis-backed jobs)

```bash
cd backend
uv run python -m arq worker.settings.WorkerSettings
```

### 5. Run Tests

```bash
cd backend
uv run pytest
# → 53/53 passing
```

---

## Environment Variables

All configuration is managed through Pydantic Settings. Copy `backend/.env.example` and set the following:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/absence_engine

# Redis
REDIS_URL=redis://localhost:6379/0

# Auth
JWT_SECRET_KEY=<random-64-char-secret>

# LLM (at least one required)
GEMINI_API_KEY=<key>
OPENAI_API_KEY=<key>
ANTHROPIC_API_KEY=<key>
LLM_PRIMARY_PROVIDER=gemini          # gemini | openai | anthropic
LLM_FALLBACK_CHAIN=openai,anthropic

# App
APP_ENV=development
CORS_ORIGINS=http://localhost:3000
```

Full variable reference → [`backend/.env.example`](./backend/.env.example)

---

## API Reference

All endpoints are versioned under `/api/v1`. Every list endpoint is paginated (`?page=1&per_page=20`).

### Auth — `/api/v1/auth`

| Method | Path | Description |
|---|---|---|
| `POST` | `/register` | Create account |
| `POST` | `/login` | Issue access + refresh tokens |
| `POST` | `/refresh` | Rotate token pair |
| `POST` | `/logout` | Blacklist current token |

### Documents — `/api/v1/documents`

| Method | Path | Description |
|---|---|---|
| `POST` | `/` | Upload document (multipart, max 50MB) |
| `GET` | `/` | List documents (paginated) |
| `GET` | `/{id}` | Get document metadata |
| `DELETE` | `/{id}` | Soft-delete document |

### Analysis — `/api/v1/analysis`

| Method | Path | Description |
|---|---|---|
| `POST` | `/` | Start analysis job (idempotent via key) |
| `GET` | `/{job_id}` | Poll job status |
| `GET` | `/{job_id}/report` | Retrieve completed report |
| `WS` | `/{job_id}/stream` | Stream live progress |

### Reports — `/api/v1/reports`

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | List reports (paginated) |
| `GET` | `/{id}` | Full report with all absence items |
| `GET` | `/{id}/export` | Export as PDF / JSON |
| `DELETE` | `/{id}` | Soft-delete report |

### Custom Schemas — `/api/v1/schemas`

| Method | Path | Description |
|---|---|---|
| `POST` | `/` | Create completeness schema |
| `GET` | `/` | List schemas |
| `PUT` | `/{id}` | Update schema |
| `DELETE` | `/{id}` | Delete schema |

**Error envelope:**
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

## Security

- **Passwords:** argon2id hashing
- **Auth:** JWT access tokens (15 min) + refresh tokens (7 days), with rotation on every refresh
- **Authorization:** Every DB read/write scoped to `WHERE user_id = :current_user_id` — no exceptions
- **Rate limiting:** Redis sliding-window — 5/min on auth, 5/min on analysis, 60/min general
- **Input:** Pydantic strict mode on every endpoint; file upload MIME allowlist + 50MB cap
- **Headers:** `X-Content-Type-Options`, `X-Frame-Options: DENY`, `Strict-Transport-Security`

---

## Roadmap

| Phase | Status | Scope |
|---|---|---|
| 1 — Foundation | ✅ Done | FastAPI app + auth + DB migrations + shared utilities |
| 2 — Document Pipeline | ✅ Done | Parsers + classifier + embedder + arq worker |
| 3 — Absence Engine | ✅ Done | All 4 detectors + assembler + orchestrator |
| 4 — Frontend | ✅ Done | Next.js 16 + full dashboard + WebSocket analysis streaming |
| 5 — Production Readiness | 🔄 In Progress | Rate limiting · Security headers · Dockerization · CI/CD |

---

## Project Structure Rationale

| Decision | Rationale |
|---|---|
| Modular monolith over microservices | Single deployable at this stage; internal package structure enables future extraction without rewrites |
| arq over Celery | Native asyncio — no sync/async impedance mismatch with FastAPI |
| pgvector over a separate vector DB | Eliminates an entire infrastructure dependency at current scale; HNSW index handles ANN search adequately until hundreds of millions of vectors |
| Provider-agnostic LLM gateway | The LLM landscape shifts quarterly; swapping providers must be a config change, never a code change |
| Vanilla CSS Modules | Full design control; no Tailwind specificity wars; zero build-time CSS processing overhead |

---

## Contributing

1. Branch naming: `feat/short-description`, `fix/issue-description`, `chore/what`
2. All new modules must have a corresponding test file mirroring the `app/` structure
3. Update `Docs/architecture.md` for any structural change
4. `ruff check` and `ruff format` must pass before PR

---

## License

This project is currently unlicensed. All rights reserved.

---

<div align="center">

Built with intent. Every absence logged.

</div>
