# The Absence Engine — Codebase Architecture

> **Version:** 0.1.0  
> **Last Updated:** 2026-03-12  

---

## Directory Tree

```
TheAbsenceEngine/
│
├── backend/                          # Python FastAPI backend
│   ├── alembic/                      # Database migration tool config
│   │   ├── versions/                 # Individual migration files
│   │   ├── env.py                    # Alembic environment config
│   │   └── script.py.mako            # Migration file template
│   ├── alembic.ini                   # Alembic connection & config
│   │
│   ├── app/                          # Application source root
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI app factory, lifespan, middleware registration
│   │   ├── config.py                 # Pydantic Settings — all env vars, defaults, validation
│   │   ├── dependencies.py           # FastAPI dependency injection (get_db, get_current_user, etc.)
│   │   │
│   │   ├── shared/                   # Cross-cutting utilities (no business logic)
│   │   │   ├── __init__.py
│   │   │   ├── db.py                 # Async SQLAlchemy engine factory, session maker, connection pool config
│   │   │   ├── logger.py             # Structured JSON logger factory
│   │   │   ├── errors.py             # App-wide exception classes + FastAPI exception handlers
│   │   │   ├── pagination.py         # Paginate helper (query → {data, meta})
│   │   │   ├── security.py           # Password hashing (argon2id), JWT encode/decode
│   │   │   ├── middleware.py         # Request ID injection, CORS, security headers, timing
│   │   │   ├── rate_limiter.py       # Redis-backed sliding window rate limiter
│   │   │   ├── retry.py              # LLM retry (tenacity) + circuit breaker wrapper
│   │   │   ├── validators.py         # Reusable Pydantic field validators (email, file size, etc.)
│   │   │   └── storage.py            # S3/MinIO client wrapper (upload, download, delete, presign)
│   │   │
│   │   ├── models/                   # SQLAlchemy ORM models (one file per table)
│   │   │   ├── __init__.py           # Base declarative model, common mixins (TimestampMixin)
│   │   │   ├── user.py               # User model
│   │   │   ├── document.py           # Document model
│   │   │   ├── analysis_job.py       # AnalysisJob model
│   │   │   ├── absence_report.py     # AbsenceReport model
│   │   │   ├── absence_item.py       # AbsenceItem model
│   │   │   ├── suggested_completion.py  # SuggestedCompletion model
│   │   │   ├── custom_schema.py      # CustomSchema model
│   │   │   └── document_embedding.py # DocumentEmbedding model (pgvector column)
│   │   │
│   │   ├── schemas/                  # Pydantic request/response schemas (one file per resource)
│   │   │   ├── __init__.py
│   │   │   ├── auth.py               # RegisterRequest, LoginRequest, TokenResponse
│   │   │   ├── document.py           # DocumentCreate, DocumentResponse, DocumentListResponse
│   │   │   ├── analysis.py           # AnalysisRequest, JobStatusResponse
│   │   │   ├── report.py             # ReportResponse, AbsenceItemResponse, ReportListResponse
│   │   │   └── custom_schema.py      # SchemaCreateRequest, SchemaResponse
│   │   │
│   │   ├── services/                 # Business logic layer (no HTTP awareness)
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py       # Register, login, refresh, logout logic
│   │   │   ├── document_service.py   # Upload, list, get, delete documents
│   │   │   ├── analysis_service.py   # Start analysis, check status, idempotency enforcement
│   │   │   ├── report_service.py     # Retrieve, list, export reports
│   │   │   └── schema_service.py     # CRUD for custom completeness schemas
│   │   │
│   │   ├── routes/                   # FastAPI routers (thin — validate, delegate to service, respond)
│   │   │   ├── __init__.py           # Root router that includes all sub-routers with prefixes
│   │   │   ├── auth.py               # /api/v1/auth/*
│   │   │   ├── documents.py          # /api/v1/documents/*
│   │   │   ├── analysis.py           # /api/v1/analysis/*
│   │   │   ├── reports.py            # /api/v1/reports/*
│   │   │   ├── schemas.py            # /api/v1/schemas/*
│   │   │   └── health.py             # /api/v1/health (liveness + readiness probes)
│   │   │
│   │   └── engine/                   # The Absence Engine — core analysis pipeline
│   │       ├── __init__.py
│   │       ├── orchestrator.py        # Pipeline coordinator: parse → classify → detect → assemble
│   │       ├── assembler.py           # Merge, deduplicate, risk-score, format final report
│   │       │
│   │       ├── parsers/               # Document format parsers
│   │       │   ├── __init__.py        # Parser registry + factory (format → parser)
│   │       │   ├── base.py            # Abstract BaseParser interface
│   │       │   ├── text_parser.py     # .txt / .md parser
│   │       │   ├── pdf_parser.py      # .pdf parser (pdfplumber)
│   │       │   ├── docx_parser.py     # .docx parser (python-docx)
│   │       │   ├── csv_parser.py      # .csv / .xlsx parser
│   │       │   └── code_parser.py     # Source code parser (tree-sitter)
│   │       │
│   │       ├── classifier.py          # Domain classifier (rule-based + LLM two-stage)
│   │       ├── chunker.py             # Text chunker (recursive character split, semantic-aware)
│   │       ├── embedder.py            # Embedding generator (sentence-transformers or API)
│   │       │
│   │       ├── llm/                   # LLM abstraction layer
│   │       │   ├── __init__.py
│   │       │   ├── gateway.py         # LLMGateway interface — provider-agnostic contract
│   │       │   ├── gemini_provider.py # Google Gemini implementation (primary)
│   │       │   ├── openai_provider.py # OpenAI fallback implementation
│   │       │   ├── anthropic_provider.py # Anthropic fallback implementation
│   │       │   └── prompts.py         # All LLM prompt templates (centralized, versionable)
│   │       │
│   │       ├── detectors/             # Absence detection modules
│   │       │   ├── __init__.py        # Detector registry
│   │       │   ├── base.py            # Abstract BaseDetector interface
│   │       │   ├── coverage.py        # Coverage Gap Detector — ontology + peer comparison
│   │       │   ├── implication.py     # Logical Implication Detector — assertion → consequence chasing
│   │       │   ├── temporal.py        # Temporal Absence Detector — timeline gap analysis
│   │       │   └── relational.py      # Emotional/Relational Detector — sentiment topology (beta)
│   │       │
│   │       └── ontologies/            # Domain knowledge configs
│   │           ├── __init__.py        # Ontology loader (YAML → Python objects)
│   │           ├── legal_contract.yaml
│   │           ├── product_spec.yaml
│   │           ├── strategy_doc.yaml
│   │           ├── technical_doc.yaml
│   │           └── interpersonal.yaml
│   │
│   ├── worker/                       # arq async worker (native asyncio)
│   │   ├── __init__.py
│   │   ├── settings.py               # arq WorkerSettings: Redis connection, job timeout, retry config
│   │   └── tasks.py                  # Task definitions (run_analysis, generate_embeddings)
│   │
│   ├── tests/                        # Test suite (mirrors app/ structure)
│   │   ├── __init__.py
│   │   ├── conftest.py               # Shared fixtures: test DB, test client, auth headers, factories
│   │   ├── unit/                     # Unit tests (no DB, no network, mocked dependencies)
│   │   │   ├── __init__.py
│   │   │   ├── test_parsers.py       # Each parser: correct extraction, edge cases
│   │   │   ├── test_classifier.py    # Domain classification accuracy
│   │   │   ├── test_chunker.py       # Chunk sizes, overlaps, boundary handling
│   │   │   ├── test_detectors.py     # Each detector: known absences found, no false positives
│   │   │   ├── test_assembler.py     # Dedup, risk scoring, report structure
│   │   │   ├── test_security.py      # JWT, password hashing, token rotation
│   │   │   └── test_validators.py    # Pydantic model validation edge cases
│   │   └── integration/              # Integration tests (real DB, real HTTP, mocked LLM)
│   │       ├── __init__.py
│   │       ├── test_auth_flow.py     # Register → login → refresh → logout
│   │       ├── test_document_flow.py # Upload → parse → classify
│   │       ├── test_analysis_flow.py # Submit → process → report retrieval
│   │       └── test_rate_limiting.py # Rate limit enforcement
│   │
│   ├── requirements.txt              # Pinned production dependencies
│   ├── requirements-dev.txt          # Dev/test dependencies (pytest, ruff, etc.)
│   ├── Dockerfile                    # Multi-stage production build (non-root)
│   └── .env.example                  # Template for all required environment variables
│
├── frontend/                         # Next.js 15 + React 19 frontend
│   ├── public/                       # Static assets (favicon, OG images)
│   ├── src/
│   │   ├── app/                      # Next.js App Router pages
│   │   │   ├── layout.tsx            # Root layout: fonts, global styles, providers
│   │   │   ├── page.tsx              # Landing page
│   │   │   ├── globals.css           # CSS custom properties (design tokens), resets, typography
│   │   │   ├── (auth)/               # Auth route group (no layout nesting)
│   │   │   │   ├── login/page.tsx    # Login page
│   │   │   │   └── register/page.tsx # Register page
│   │   │   ├── dashboard/
│   │   │   │   ├── layout.tsx        # Dashboard layout (sidebar, auth guard)
│   │   │   │   ├── page.tsx          # Dashboard home — recent reports, upload CTA
│   │   │   │   ├── documents/
│   │   │   │   │   └── page.tsx      # Document list view
│   │   │   │   ├── analysis/
│   │   │   │   │   ├── page.tsx      # Analysis history list
│   │   │   │   │   └── [jobId]/page.tsx  # Single analysis status + live progress
│   │   │   │   ├── reports/
│   │   │   │   │   ├── page.tsx      # Report list view
│   │   │   │   │   └── [reportId]/page.tsx  # Full absence report viewer
│   │   │   │   └── schemas/
│   │   │   │       ├── page.tsx      # Custom schema list
│   │   │   │       └── new/page.tsx  # Schema builder
│   │   │   └── not-found.tsx         # Custom 404
│   │   │
│   │   ├── components/               # Reusable UI components
│   │   │   ├── ui/                   # Primitive UI elements
│   │   │   │   ├── Button.tsx        # Button with variants (primary, secondary, ghost, danger)
│   │   │   │   ├── Input.tsx         # Text input with label, error state, icon support
│   │   │   │   ├── FileUpload.tsx    # Drag-and-drop file upload with progress bar
│   │   │   │   ├── Badge.tsx         # Status/category badges with color variants
│   │   │   │   ├── Card.tsx          # Content card container with glassmorphism option
│   │   │   │   ├── Modal.tsx         # Modal dialog with backdrop + trap focus
│   │   │   │   ├── Spinner.tsx       # Loading spinner animation
│   │   │   │   ├── Toast.tsx         # Toast notification system
│   │   │   │   └── ProgressBar.tsx   # Determinate/indeterminate progress bar
│   │   │   │
│   │   │   ├── layout/              # Layout building blocks
│   │   │   │   ├── Sidebar.tsx       # Dashboard sidebar navigation
│   │   │   │   ├── Header.tsx        # Top header bar (user menu, notifications)
│   │   │   │   └── Footer.tsx        # Footer with links
│   │   │   │
│   │   │   └── features/            # Feature-specific compound components
│   │   │       ├── AbsenceCard.tsx   # Single absence item card (expandable, risk-colored)
│   │   │       ├── RiskGauge.tsx     # Circular risk score visualization (D3)
│   │   │       ├── AbsenceTimeline.tsx  # Visual timeline of temporal absences
│   │   │       ├── PeerComparison.tsx   # Bar chart: input doc vs peer coverage
│   │   │       ├── ReportSummary.tsx    # Report header: overall score, domain, item count
│   │   │       └── SchemaBuilder.tsx    # Interactive schema definition form
│   │   │
│   │   ├── lib/                     # Client-side utilities
│   │   │   ├── api.ts               # Typed API client (fetch wrapper with auth, error handling)
│   │   │   ├── auth.ts              # Auth context provider, token storage, refresh logic
│   │   │   ├── websocket.ts         # WebSocket client for analysis streaming
│   │   │   └── utils.ts             # Date formatting, file size formatting, color helpers
│   │   │
│   │   ├── hooks/                   # Custom React hooks
│   │   │   ├── useAuth.ts           # Auth state + login/logout/register actions
│   │   │   ├── useDocuments.ts      # Document CRUD operations
│   │   │   ├── useAnalysis.ts       # Start analysis, poll/stream status
│   │   │   └── useReports.ts        # Report retrieval and export
│   │   │
│   │   └── types/                   # Shared TypeScript type definitions
│   │       ├── api.ts               # API response types (mirrors backend schemas exactly)
│   │       ├── auth.ts              # Auth state types
│   │       └── report.ts            # Report, AbsenceItem, RiskLevel types
│   │
│   ├── next.config.ts               # Next.js config (API proxy, image domains)
│   ├── tsconfig.json                # TypeScript config
│   ├── package.json                 # Frontend dependencies
│   └── Dockerfile                   # Frontend production build
│
├── docker-compose.yml                # Full stack: backend + frontend + postgres + redis + minio
├── docker-compose.override.yml       # Dev overrides (hot reload, debug ports)
├── .github/
│   └── workflows/
│       ├── ci.yml                    # Lint → test → build on every PR
│       └── deploy.yml                # Deploy on main merge
│
├── .gitignore                        # Project-wide ignore rules
├── .env.example                      # Top-level env template (references backend/.env.example)
├── README.md                         # Project overview, setup instructions, usage
├── plan.md                           # Implementation plan (this project's roadmap)
├── architecture.md                   # This file — codebase architecture reference
├── pyproject.toml                    # Python project metadata
└── main.py                          # Legacy entry point (will be replaced by backend/app/main.py)
```

---

## Module Responsibilities

### Backend

| Module | Single Responsibility |
|---|---|
| `app/main.py` | App factory only — creates FastAPI instance, registers middleware, mounts routers |
| `app/config.py` | Loads and validates all environment variables via Pydantic Settings |
| `app/dependencies.py` | Provides injectable dependencies (DB session, current user, storage client) |
| `app/shared/db.py` | Creates async SQLAlchemy engine + session factory with connection pool config (pool_size, max_overflow, pool_recycle, pool_pre_ping) |
| `app/shared/logger.py` | Creates structured JSON loggers with request-scoped context |
| `app/shared/errors.py` | Defines exception hierarchy + maps exceptions to HTTP responses |
| `app/shared/pagination.py` | Converts SQLAlchemy query + page params into `{data, meta}` envelope |
| `app/shared/security.py` | Handles argon2id hashing, JWT creation/verification, token blacklisting |
| `app/shared/middleware.py` | Request ID injection, CORS, security headers, request timing |
| `app/shared/rate_limiter.py` | Redis sliding-window rate limiter, configurable per endpoint group |
| `app/shared/retry.py` | Wraps tenacity retry + circuitbreaker for LLM calls — exponential backoff, jitter, circuit open after N failures |
| `app/shared/validators.py` | Reusable Pydantic validators (email format, file size limits, etc.) |
| `app/shared/storage.py` | Local filesystem storage backend (`upload`, `get_bytes`, `delete`, `build_key`, `sha256`). Drop-in compatible — swap for S3 impl when cloud access is available. |
| `app/shared/inline_queue.py` | Dev-only arq duck-type shim (`InlineQueue`). Activated by `main.py` lifespan when Redis is unreachable and `APP_ENV != production`. Runs tasks via `asyncio.create_task` in-process. Never active in production. |
| `app/models/*` | One file per DB table — SQLAlchemy 2.0 mapped classes, relationships, indexes |
| `app/schemas/*` | Pydantic v2 models for request validation and response serialization |
| `app/services/*` | Pure business logic — receives validated data, returns results, raises app exceptions |
| `app/routes/*` | Thin HTTP layer — validates input (via Pydantic), calls service, returns response |
| `app/engine/orchestrator.py` | Coordinates the full analysis pipeline: parse → classify → detect → assemble |
| `app/engine/parsers/*` | One parser per file format, all implementing `BaseParser.parse() → ParsedDocument` |
| `app/engine/classifier.py` | Two-stage domain classification: keyword rules + LLM structured output |
| `app/engine/chunker.py` | Splits text into overlapping semantic chunks for embedding |
| `app/engine/embedder.py` | Generates vector embeddings via API (Gemini/OpenAI), stores with model_version |
| `app/engine/llm/factory.py` | `build_gateway()` — builds an ordered fallback chain (primary → fallbacks from `LLM_FALLBACK_CHAIN`). Skips providers with missing API keys. Returns `_FallbackGateway` (multi-provider) or `_RetryingProvider` (single-provider). Each provider is wrapped with tenacity retry. |
| `app/engine/llm/gemini_provider.py` | Gemini implementation of LLMGateway (primary when `GEMINI_API_KEY` is set) |
| `app/engine/llm/openai_provider.py` | OpenAI implementation of LLMGateway — handles `generate`, `generate_structured` (beta.parse), and `embed` (text-embedding-3-large) |
| `app/engine/llm/anthropic_provider.py` | Anthropic implementation — no embed support; `embed()` raises `NotImplementedError` |
| `app/engine/llm/prompts.py` | All prompt templates — centralized, versioned, no prompts scattered in business logic |
| `app/engine/detectors/*` | One detector per absence type, all implementing `BaseDetector.detect() → list[AbsenceCandidate]` |
| `app/engine/ontologies/*` | YAML domain knowledge files loaded at startup by `__init__.py` |
| `app/engine/assembler.py` | Merges detector outputs → dedup → risk scoring → final AbsenceReport |
| `worker/settings.py` | arq WorkerSettings: Redis connection, concurrency, timeout, max retries |
| `worker/tasks.py` | Async task definitions that call `engine/orchestrator.py` |

### Frontend

| Module | Single Responsibility |
|---|---|
| `app/layout.tsx` | Root HTML shell: fonts, meta tags, global CSS, context providers |
| `app/globals.css` | Design tokens (colors, spacing, radii, shadows), CSS reset, typography scale |
| `components/ui/*` | Atomic UI primitives — no business logic, fully reusable |
| `components/layout/*` | Page layout structures (sidebar, header) — no data fetching |
| `components/features/*` | Feature-specific compound components — may consume hooks |
| `lib/api.ts` | Centralized fetch wrapper: base URL, auth headers, error parsing, retry |
| `lib/auth.ts` | Auth context: stores tokens, provides login/logout, handles refresh |
| `lib/websocket.ts` | WebSocket connection manager for real-time analysis updates |
| `hooks/*` | Custom hooks that encapsulate API calls and state management per resource |
| `types/*` | TypeScript interfaces mirroring backend Pydantic schemas 1:1 |

---

## Data Flow

### Document Upload → Analysis → Report

```
┌──────────┐    POST /documents     ┌──────────────┐
│ Frontend │ ──────────────────────► │ routes/      │
│          │    multipart/form-data  │ documents.py │
└──────────┘                        └──────┬───────┘
                                           │ validates file type, size
                                           ▼
                                    ┌──────────────┐
                                    │ services/    │
                                    │ document_    │
                                    │ service.py   │
                                    └──────┬───────┘
                                           │ uploads to S3, creates DB record
                                           ▼
                                    ┌──────────────┐
                                    │ S3 / MinIO   │
                                    └──────────────┘

┌──────────┐    POST /analysis      ┌──────────────┐
│ Frontend │ ──────────────────────► │ routes/      │
│          │    {document_id, ...}   │ analysis.py  │
└──────────┘                        └──────┬───────┘
                                           │ validates, checks idempotency
                                           ▼
                                    ┌──────────────┐
                                    │ services/    │
                                    │ analysis_    │
                                    │ service.py   │
                                    └──────┬───────┘
                                           │ creates AnalysisJob, dispatches Celery task
                                           ▼
                                    ┌──────────────┐
                                    │ arq Task     │
                                    │ (async       │
                                    │  worker)     │
                                    └──────┬───────┘
                                           │
                    ┌──────────────────────┼──────────────────────┐
                    ▼                      ▼                      ▼
             ┌────────────┐        ┌──────────────┐       ┌──────────────┐
             │ parsers/   │        │ classifier   │       │ chunker +    │
             │ (format    │───────►│ (domain      │──────►│ embedder     │
             │ → text)    │        │ detection)   │       │ (→ pgvector) │
             └────────────┘        └──────────────┘       └──────┬───────┘
                                                                  │
                    ┌─────────────────────────────────────────────┘
                    ▼
             ┌──────────────┐
             │ detectors/   │
             │ ┌──────────┐ │
             │ │ coverage  │ │
             │ ├──────────┤ │
             │ │ implic.  │ │
             │ ├──────────┤ │
             │ │ temporal  │ │
             │ ├──────────┤ │
             │ │ relation. │ │
             │ └──────────┘ │
             └──────┬───────┘
                    │ list[AbsenceCandidate]
                    ▼
             ┌──────────────┐
             │ assembler    │
             │ (dedup,      │
             │ risk score,  │
             │ format)      │
             └──────┬───────┘
                    │ AbsenceReport
                    ▼
             ┌──────────────┐
             │ PostgreSQL   │
             │ (report +    │
             │ items saved) │
             └──────────────┘

┌──────────┐    GET /reports/{id}   ┌──────────────┐
│ Frontend │ ◄───────────────────── │ routes/      │
│ (viewer) │    AbsenceReport JSON  │ reports.py   │
└──────────┘                        └──────────────┘
```

---

## Key Interfaces

### BaseParser

```python
class BaseParser(ABC):
    @abstractmethod
    async def parse(self, file_path: str, mime_type: str) -> ParsedDocument:
        """Extract structured text from a file."""

@dataclass
class ParsedDocument:
    text: str
    sections: list[Section]
    metadata: dict
```

### BaseDetector

```python
class BaseDetector(ABC):
    @abstractmethod
    async def detect(self, context: DetectionContext) -> list[AbsenceCandidate]:
        """Analyze document and return candidate absences."""

@dataclass
class DetectionContext:
    document: ParsedDocument
    domain: str
    ontology: DomainOntology
    embeddings: list[EmbeddingChunk]
    llm: LLMGateway

@dataclass
class AbsenceCandidate:
    title: str
    description: str
    reasoning: str
    confidence: float
    risk_score: float
    absence_type: str
    category: str
    evidence: list[dict]
    suggested_completion: str | None
```

### LLMGateway

```python
class LLMGateway(ABC):
    @abstractmethod
    async def generate(self, prompt: str, max_tokens: int = 4096) -> LLMResponse:
        """Send prompt to LLM, return structured response."""

    @abstractmethod
    async def generate_structured(self, prompt: str, schema: type[BaseModel]) -> BaseModel:
        """Send prompt and parse response into Pydantic model."""

@dataclass
class LLMResponse:
    text: str
    tokens_used: int
    model: str
    latency_ms: float
```

---

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/absence_engine
DB_POOL_SIZE=20                       # max persistent connections
DB_MAX_OVERFLOW=10                    # extra connections under load
DB_POOL_RECYCLE=300                   # recycle connections after 5 min
DB_POOL_PRE_PING=true                 # health-check before reuse

# Redis
REDIS_URL=redis://localhost:6379/0

# Local Storage (development — replace with S3 block for production)
LOCAL_STORAGE_DIR=./uploads          # absolute or relative to backend/ working dir

# Auth
JWT_SECRET_KEY=<random-64-char>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# LLM
LLM_PRIMARY_PROVIDER=gemini           # gemini | openai | anthropic
GEMINI_API_KEY=<key>
OPENAI_API_KEY=<key>
ANTHROPIC_API_KEY=<key>
LLM_MODEL=gemini-2.5-pro              # primary model name
LLM_FALLBACK_CHAIN=openai,anthropic   # comma-separated fallback order
LLM_MAX_TOKENS_PER_ANALYSIS=50000     # budget cap
LLM_RETRY_MAX_ATTEMPTS=3              # retries per LLM call
LLM_CIRCUIT_BREAKER_THRESHOLD=5       # consecutive failures to open circuit
LLM_CIRCUIT_BREAKER_TIMEOUT=60        # seconds before half-open

# Embeddings
EMBEDDING_PROVIDER=gemini             # gemini | openai
EMBEDDING_MODEL=text-embedding-005    # model name
EMBEDDING_DIMENSIONS=768              # output vector dimensions

# arq Worker
ARQ_REDIS_URL=redis://localhost:6379/1
ARQ_MAX_JOBS=10                       # max concurrent jobs
ARQ_JOB_TIMEOUT=300                   # seconds per job
ARQ_MAX_RETRIES=2                     # retries on job failure

# App
APP_ENV=development                   # development | staging | production
APP_DEBUG=true
APP_HOST=0.0.0.0
APP_PORT=8000
CORS_ORIGINS=http://localhost:3000    # comma-separated for multiple origins

# Rate Limiting
RATE_LIMIT_AUTH=5/minute
RATE_LIMIT_UPLOAD=10/minute
RATE_LIMIT_ANALYSIS=5/minute
RATE_LIMIT_GENERAL=60/minute
```

---

## Naming Conventions

| Scope | Convention | Example |
|---|---|---|
| Python files | snake_case | `analysis_service.py` |
| Python classes | PascalCase | `AbsenceReport` |
| Python functions | snake_case | `detect_coverage_gaps()` |
| Python constants | UPPER_SNAKE | `MAX_FILE_SIZE_BYTES` |
| DB tables | snake_case plural | `absence_items` |
| DB columns | snake_case | `risk_score` |
| API routes | kebab-case (via prefix only; FastAPI uses snake) | `/api/v1/analysis` |
| TypeScript files | PascalCase (components), camelCase (utils) | `RiskGauge.tsx`, `api.ts` |
| CSS classes | BEM (block__element--modifier) | `.card__header--highlighted` |
| Environment vars | UPPER_SNAKE | `DATABASE_URL` |
| Git branches | `type/short-description` | `feat/coverage-detector` |

---

*This architecture document is the single source of truth for where code lives and what it does. Update it whenever a new module is added.*
