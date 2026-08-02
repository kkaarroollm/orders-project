FROM python:3.13-slim AS deps

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /workspace

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_FROZEN=1

# Manifests only. This layer stays cached until a dependency actually changes,
# so editing service code no longer re-resolves the whole workspace. Every
# member is copied because uv needs them all to resolve the workspace graph.
COPY pyproject.toml uv.lock ./
COPY shared/pyproject.toml shared/
COPY orders/pyproject.toml orders/
COPY delivery/pyproject.toml delivery/
COPY notifications/pyproject.toml notifications/
COPY simulator/pyproject.toml simulator/

FROM deps AS development

# curl backs the docker-compose healthcheck; k8s probes use httpGet instead.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-install-workspace --package orders

COPY shared/ shared/
COPY orders/ orders/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --package orders

WORKDIR /workspace/orders

EXPOSE 8003

CMD ["uv", "run", "fastapi", "dev", "src/main.py", "--proxy-headers", "--port", "8003", "--host", "0.0.0.0"]

FROM deps AS builder

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --no-install-workspace --package orders

COPY shared/ shared/
COPY orders/ orders/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --package orders

FROM python:3.13-slim AS production

COPY --from=builder /workspace /workspace

ENV PATH="/workspace/.venv/bin:$PATH" PYTHONPATH=/workspace/orders

WORKDIR /workspace/orders

EXPOSE 8003

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8003", "--proxy-headers"]
