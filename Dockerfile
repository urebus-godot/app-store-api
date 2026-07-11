FROM python:3.13-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/src/.venv

WORKDIR /src
COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

FROM python:3.13-slim AS runner
WORKDIR /src

RUN useradd -u 10001 -m appuser
COPY --from=builder /src/.venv /src/.venv
COPY . .

ENV PATH="/src/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1
USER appuser

EXPOSE 8000
CMD ["python", "-m", "app.main"]