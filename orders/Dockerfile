FROM python:3.13 AS base

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

COPY orders/pyproject.toml orders/uv.lock orders/.python-version ./
COPY shared /shared

FROM base AS development

COPY orders/ .

RUN uv sync --frozen --no-cache

EXPOSE 8003

CMD ["uv", "run", "fastapi", "dev", "src/main.py", "--proxy-headers", "--port", "8003", "--host", "0.0.0.0"]

FROM base AS production

COPY orders/ .

RUN uv sync --frozen --no-cache --no-dev

EXPOSE 8003

CMD ["uv", "run", "fastapi", "run", "src/main.py", "--proxy-headers", "--port", "8003", "--host", "0.0.0.0"]
