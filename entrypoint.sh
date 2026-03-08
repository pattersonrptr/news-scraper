#!/bin/bash
# Docker entrypoint — run migrations then start the server.
set -e

echo "==> Running Alembic migrations..."
cd /app
alembic upgrade head

echo "==> Starting server..."
exec "$@"
