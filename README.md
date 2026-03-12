<div align="center">

<br>

# The Absence Engine

**Most AI tools tell you what a document contains.**  
**This one tells you what it's missing.**

<br>

[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-16-000000?style=flat-square&logo=next.js&logoColor=white)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://postgresql.org)
[![License](https://img.shields.io/badge/license-All%20Rights%20Reserved-red?style=flat-square)](#)

<br>

<!-- Demo video -->
> **📽 Demo** — [Watch a full walkthrough](https://youtu.be/DEMO_LINK_HERE) *

<br>

</div>

---

## What Is This?

The Absence Engine is a document intelligence tool that analyzes any text — a contract, a product spec, a strategy doc, a codebase — and produces a structured report of its **negative space**.

Not a summary. Not grammar checks. Not a chatbot.

It answers: *"What questions were never asked? What stakeholders were never considered? What failure modes were never modeled? What does this document implicitly promise but never actually address?"*

Upload a service agreement → get flagged for a missing force majeure clause.  
Upload a product spec → get flagged for unaddressed user segments.  
Upload an architecture doc → get flagged for unhandled failure paths.

---

## Features

- **Multi-format parsing** — PDF, DOCX, TXT, CSV, XLSX, and source code
- **Auto domain detection** — identifies document type (legal, product, strategy, technical, interpersonal) with LLM-confirmed confidence
- **Four absence detectors** running in parallel:
  - *Coverage Gap* — topics that should exist per domain ontology, but don't
  - *Logical Implication* — statements made that logically require follow-up never provided
  - *Temporal Absence* — scenarios, timeframes, or contingencies never considered
  - *Relational/Emotional* — entities systematically absent from evaluative context *(beta)*
- **Risk scoring** per absence item (0.0–1.0), ranked by domain criticality and peer frequency
- **Suggested completions** — optional draft of what the missing content could look like
- **Custom schemas** — define your own completeness criteria for niche document types
- **Real-time progress** via WebSocket streaming during analysis
- **Multi-LLM support** — Gemini (primary), OpenAI, Anthropic — automatic fallback chain

---

## Quick Start

### Prerequisites

- Python ≥ 3.12 + [`uv`](https://github.com/astral-sh/uv)
- Node.js ≥ 20
- PostgreSQL 17 with pgvector
- Redis 8
- At least one LLM API key (Gemini / OpenAI / Anthropic)

### 1 — Clone & configure

```bash
git clone https://github.com/Prasaderp/TheAbsenceEngine.git
cd TheAbsenceEngine/backend
cp .env.example .env   # fill in your keys
```

### 2 — Backend

```bash
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

> **No Redis?** No problem. In development, the engine falls back to an in-process queue automatically — the full pipeline still runs.

### 3 — Frontend

```bash
cd ../frontend
npm install
npm run dev
```

Open [`http://localhost:3000`](http://localhost:3000).

### 4 — Worker (optional, for Redis-backed job queue)

```bash
cd backend
uv run python -m arq worker.settings.WorkerSettings
```

---

## How an Analysis Works

```
You upload a document
        ↓
Engine parses it (PDF / DOCX / code / CSV / plaintext)
        ↓
Auto-detects domain — legal / product / strategy / technical / interpersonal
        ↓
Runs 4 independent absence detectors against domain ontologies + LLM reasoning
        ↓
Assembles a structured report — deduplicated, risk-ranked, with evidence
        ↓
You get: title · description · reasoning · confidence · risk score · suggested fix
```

The whole pipeline is async. You submit a job, get a job ID, and stream real-time progress — no blocking.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI · Python 3.12 · SQLAlchemy 2.0 · Alembic · Pydantic v2 |
| Frontend | Next.js 16 · React 19 · TypeScript 5.7 · Vanilla CSS Modules |
| Database | PostgreSQL 17 + pgvector (embeddings + vector search) |
| Cache / Queue | Redis 8 · arq (async task queue) |
| LLM | Gemini 2.5 Pro (primary) · OpenAI · Anthropic (fallbacks) |
| Parsing | pdfplumber · python-docx · openpyxl · tree-sitter |
| Storage | MinIO (local) / S3-compatible (production) |

---

## Project Structure

```
TheAbsenceEngine/
├── backend/
│   ├── app/
│   │   ├── engine/          # Core analysis pipeline
│   │   │   ├── parsers/     # Document format parsers
│   │   │   ├── detectors/   # The four absence detectors
│   │   │   ├── llm/         # Provider-agnostic LLM gateway
│   │   │   └── ontologies/  # Domain knowledge configs (YAML)
│   │   ├── routes/          # REST API endpoints
│   │   ├── services/        # Business logic
│   │   ├── models/          # Database models
│   │   └── shared/          # Auth, security, rate limiting, storage
│   └── worker/              # Async job worker (arq)
│
├── frontend/
│   └── src/
│       ├── app/             # Pages (App Router)
│       ├── components/      # UI primitives + feature components
│       ├── lib/             # API client, auth, WebSocket
│       └── hooks/           # Data-fetching hooks
│
└── Docs/                    # Architecture reference + implementation plan
```

---

## Environment Variables

Copy `backend/.env.example` and set at minimum:

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/absence_engine
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=<64-char-random-secret>

# At least one LLM key
GEMINI_API_KEY=...
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
```

Full reference in [`backend/.env.example`](./backend/.env.example).

---

## Contributing

Pull requests are welcome. Please:

- Branch from `main` using `feat/`, `fix/`, or `chore/` prefixes
- Add tests for any new behavior
- Run `ruff check` and `ruff format` before opening a PR

---

## License

All rights reserved © Prasad Somvanshi.  
Not licensed for redistribution or commercial use.
