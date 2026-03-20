# ── Python 3.12 slim base ─────────────────────────────────────────────────────
FROM python:3.12-slim AS base

# Install system deps + Node.js (for gws CLI)
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && npm install -g @googleworkspace/cli \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ── Python dependencies ───────────────────────────────────────────────────────
FROM base AS deps

WORKDIR /build
COPY api/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── Final runtime image ───────────────────────────────────────────────────────
FROM deps AS runtime

# Create non-root user
RUN useradd -r -s /bin/false appuser

WORKDIR /app

# Copy application code
COPY api/app ./app

# Copy content packs
COPY content ./content

# Fix ownership
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8080

ENV PORT=8080
ENV CONTENT_DIR=./content
ENV TZ=America/Los_Angeles
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/healthz || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
