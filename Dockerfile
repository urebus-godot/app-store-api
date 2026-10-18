#syntax=docker/dockerfile:1.7

ARG PYTHON_VERSION=3.13

FROM python:${PYTHON_VERSION}-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.12.3 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

COPY . .

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev


FROM python:${PYTHON_VERSION}-slim AS runtime

RUN groupadd --system --gid 1000 appuser \
    && useradd --system --gid 1000 --uid 1000 --create-home appuser

WORKDIR /app

COPY --from=builder --chown=appuser:appuser app /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PROMETHEUS_MULTIPROC_DIR=/tmp/prom

RUN mkdir -p /tmp/prom && chown -R appuser:appuser /tmp/prom

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--forwarded-allow-ips='*'", "--proxy-headers", "--reload"]