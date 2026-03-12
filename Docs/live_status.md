# Live Status

**Phase:** 1 ✅ → 2 ✅ → 3 ✅ → Phase 4 ✅ → **Phase 5 (In Progress)**

## Done
- `shared/` — db, logger, errors, pagination, storage, security
- `models/` — user, document, analysis_job, absence_report, absence_item, **custom_schema**
- `schemas/` — auth, document, analysis, report, absence_item, **custom_schema**
- `services/` — auth, document, analysis, report, **schema**
- `routes/` — health, auth (+`/me`), documents, analysis, reports, **schemas**
- `dependencies.py`, `main.py`, `worker/`
- `engine/` — parsers, llm, ontologies, chunker, embedder, classifier, detectors, assembler, orchestrator
- `alembic/versions/` — users, documents, analysis_jobs, absence_reports+items, **custom_schemas**
- `frontend/` — Next.js 16 + React 19 + TS 5.7
  - Design system (CSS vars, dark theme, Inter font)
  - `lib/` — api client (fetch+auth+refresh), auth context, utils
  - `types/` — all API types mirroring backend schemas
  - `components/ui/` — Button, Input, Badge, Spinner, Toast
  - `components/layout/` — Sidebar
  - `components/features/` — ReportView (SVG gauge + expandable absence cards)
  - Pages: `/` landing, `/login`, `/register`
  - Dashboard: home, documents (upload+list), analysis (list+detail+WS), reports (list+detail), schemas (list+new)

## Local Dev Fixes Applied (2026-03-12)
- **CORS middleware** added to `backend/app/main.py` — was missing, blocked all browser→backend requests
- **`cors_origins`** field added to `config.py` — configurable via env var, defaults to `http://localhost:3000`
- **`backend/.env.example`** created — documents all required env vars for local dev
- **`next.config.ts`** — added `turbopack.root` to suppress multi-lockfile warning
- **Run backend from `backend/` dir**: `uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
  - ⚠️ Running with `backend.app.main:app` from root dir fails (`No module named 'backend'`) — use the above

**Running services (local):**
- Backend: `http://localhost:8000` (Redis unavailable → analysis 503, all other endpoints ✅)
- Frontend: `http://localhost:3000`

**Tests: 53/53 passed** | **Frontend build: ✅**

## Next
Phase 5 — Production readiness: rate limiting middleware, security headers, integration tests, CI/CD, Docker
