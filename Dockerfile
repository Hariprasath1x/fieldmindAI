# FieldMind FastAPI Backend — Multi-stage Dockerfile
#
# Stage 1: dependency builder (installs Python packages)
# Stage 2: runtime image (lean, non-root, no build tools)
#
# Usage:
#   docker build -t fieldmind-backend .
#   docker run -p 8002:8002 --env-file .env fieldmind-backend

# ─────────────────────────────────────────────────────────────────────────────
# Stage 1 — builder
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ─────────────────────────────────────────────────────────────────────────────
# Stage 2 — runtime
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# Create non-root user
RUN useradd -m -u 1001 fieldmind

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY backend/ ./backend/
COPY models/ ./models/
COPY evaluation/ ./evaluation/

# Set ownership
RUN chown -R fieldmind:fieldmind /app

USER fieldmind

# Environment defaults (overridden by docker-compose / Kubernetes secrets)
ENV FIELDMIND_ENV=production \
    LOG_LEVEL=INFO \
    API_HOST=0.0.0.0 \
    API_PORT=8002 \
    MODELS_DIR=/app/models

EXPOSE 8002

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8002/health')"

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8002", "--workers", "1"]
