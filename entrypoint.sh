#!/bin/bash
# Docker entrypoint — run migrations then start the server.
set -e

echo "==> Running Alembic migrations..."
cd /app
alembic upgrade head

# Seed default sources only when starting the API server (not celery/flower).
# Idempotent: seed_sources skips rows that already exist.
if [[ "$*" == *"uvicorn"* ]]; then
  echo "==> Seeding default sources..."
  python -m backend.src.interfaces.cli.seed_sources 2>&1 | grep -E "seed_sources\.(done|error)" || true
fi

echo "==> Starting server..."
exec "$@"
