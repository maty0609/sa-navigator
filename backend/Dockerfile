FROM python:3.11-slim

WORKDIR /app

# Install production dependencies first (layer caching)
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e "."

# Install dev dependencies (for local dev with reload)
RUN pip install --no-cache-dir -e ".[dev]"

COPY . .

EXPOSE 8000

# Production: gunicorn with multiple Uvicorn workers for horizontal scaling
# Dev: fallback to single uvicorn with --reload
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--forwarded-allow-ips", "*"]
