FROM python:3.12-slim

WORKDIR /app

COPY bot/pyproject.toml bot/uv.lock ./

RUN --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
  uv sync --frozen

ENV PATH="/app/.venv/bin:$PATH"

COPY bot/src/ /app

CMD [ "python", "telegram_bot.py" ]