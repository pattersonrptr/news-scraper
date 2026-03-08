# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.8.3 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1

ENV PATH="$POETRY_HOME/bin:$PATH"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

WORKDIR /app

# ---------------------------------------------------------------------------
# Dependencies stage (cached layer)
# ---------------------------------------------------------------------------
FROM base AS deps

COPY pyproject.toml poetry.lock* ./
RUN poetry install --only main --no-root

# ---------------------------------------------------------------------------
# Development stage
# ---------------------------------------------------------------------------
FROM deps AS development

RUN poetry install --no-root
COPY . .
RUN poetry install

CMD ["uvicorn", "backend.src.interfaces.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ---------------------------------------------------------------------------
# Production stage
# ---------------------------------------------------------------------------
FROM deps AS production

COPY . .
RUN poetry install --only main

# Create non-root user
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
USER appuser

CMD ["uvicorn", "backend.src.interfaces.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
