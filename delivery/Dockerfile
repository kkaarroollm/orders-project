FROM python:3.13 AS base

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

COPY delivery/pyproject.toml delivery/uv.lock delivery/.python-version ./
COPY shared /shared

FROM base AS development

COPY delivery/ .

RUN uv sync --frozen --no-cache

EXPOSE 8001

CMD ["uv", "run", "fastapi", "dev", "src/main.py", "--port", "8001", "--host", "0.0.0.0"]

FROM base AS production

COPY delivery/ .

RUN uv sync --frozen --no-cache

EXPOSE 8001

CMD ["uv", "run", "fastapi", "run", "src/main.py", "--port", "8001", "--host", "0.0.0.0"]
