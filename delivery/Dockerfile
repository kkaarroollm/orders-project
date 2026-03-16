FROM python:3.13 AS base

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /workspace

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./
COPY shared ./shared
COPY delivery ./delivery

FROM base AS development

WORKDIR /workspace/delivery
RUN uv sync --frozen --no-cache

EXPOSE 8001

CMD ["uv", "run", "fastapi", "dev", "src/main.py", "--port", "8001", "--host", "0.0.0.0"]

FROM base AS production

WORKDIR /workspace/delivery
RUN uv sync --frozen --no-cache --no-dev

EXPOSE 8001

CMD ["uv", "run", "fastapi", "run", "src/main.py", "--port", "8001", "--host", "0.0.0.0"]
