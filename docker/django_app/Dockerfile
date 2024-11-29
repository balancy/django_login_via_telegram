# Base
FROM python:3.12-slim AS base

WORKDIR /app

RUN apt-get update && \
  apt-get install -y postgresql-client netcat-openbsd --no-install-recommends && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/*

COPY django_app/pyproject.toml django_app/uv.lock docker/django_app/entrypoint.sh ./

# Dev stage
FROM base AS dev

RUN --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
  uv sync --frozen --extra dev

ENV PATH="/app/.venv/bin:$PATH"

COPY django_app/src/ /app/src

# Prod stage
