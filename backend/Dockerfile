# syntax=docker/dockerfile:1
ARG PYTHON_VERSION=3.12

# ── Builder stage ──────────────────────────────────────────────────────────────
FROM python:${PYTHON_VERSION}-slim AS builder
WORKDIR /build

RUN pip install --no-cache-dir uv

COPY requirements.txt .
RUN uv pip install --system --no-cache-dir -r requirements.txt

# ── Runtime stage ──────────────────────────────────────────────────────────────
FROM python:${PYTHON_VERSION}-slim AS runtime

# Security: non-root user
RUN useradd --no-create-home --shell /bin/false appuser

WORKDIR /app

# libmagic for python-magic (file type detection)
RUN apt-get update && apt-get install -y --no-install-recommends libmagic1 && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source
COPY app/ ./app/
COPY worker/ ./worker/
COPY alembic/ ./alembic/
COPY alembic.ini .

USER appuser

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--no-access-log"]
