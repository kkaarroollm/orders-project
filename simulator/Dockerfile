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

FROM deps AS builder

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --no-install-workspace --package simulator

COPY shared/ shared/
COPY simulator/ simulator/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --package simulator

FROM python:3.13-slim AS production

COPY --from=builder /workspace /workspace

ENV PATH="/workspace/.venv/bin:$PATH" PYTHONPATH=/workspace/simulator

WORKDIR /workspace/simulator

CMD ["python", "src/main.py"]
