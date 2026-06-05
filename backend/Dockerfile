# Multi-stage build for FastAPI backend
# Stage 1: Builder - install dependencies
FROM python:3.13-slim@sha256:7ba5f5888fbe0014ab9edb2278922995c2201fc3752c46b0be24763eb46fa9f3 AS builder

WORKDIR /app

# Install system dependencies needed for compiling Python wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies into a shared prefix
# (/install). Using a shared location instead of --user keeps the runtime
# stage free of per-user assumptions and lets a non-root user read the libs.
#
# --require-hashes enforces the SHA-256 hashes baked into requirements.txt
# by `uv pip compile --generate-hashes`, so a hijacked PyPI mirror cannot
# substitute an alternate wheel. See OpenSSF Scorecard Pinned-Dependencies.
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install --require-hashes -r requirements.txt

# Stage 2: Runtime - minimal production image
FROM python:3.13-slim@sha256:7ba5f5888fbe0014ab9edb2278922995c2201fc3752c46b0be24763eb46fa9f3

# Create non-root user (CI-016). All runtime files are owned by appuser.
RUN groupadd --system --gid 1001 appgroup \
    && useradd --system --uid 1001 --gid appgroup --home /app --shell /sbin/nologin appuser

WORKDIR /app

# Copy Python dependencies from the builder stage into the system prefix
COPY --from=builder /install /usr/local

# Copy application code
COPY --chown=appuser:appgroup . .

# Runtime env
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Drop privileges
USER appuser

# Expose port
EXPOSE 8000

# Health check using stdlib urllib (no extra deps)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1

# Run with uvicorn directly (simpler for debugging)
CMD ["python", "-m", "uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000"]
