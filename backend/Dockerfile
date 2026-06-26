# ---- Builder stage: install dependencies ----
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies for psycopg2
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Install production dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir --prefix=/install -e "."

# ---- Production stage: lean runtime ----
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Install C libraries needed at runtime by psycopg2
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN adduser --disabled-password --gecos "" appuser && \
    chown -R appuser:appuser /app

COPY . .

USER appuser

EXPOSE 8000

# Production: gunicorn with multiple Uvicorn workers for horizontal scaling
# Dev: override with `docker compose up` or `uvicorn app.main:app --reload`
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
