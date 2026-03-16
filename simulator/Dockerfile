FROM python:3.13

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /workspace

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONPATH=/workspace/simulator

COPY pyproject.toml uv.lock ./
COPY shared ./shared
COPY simulator ./simulator

WORKDIR /workspace/simulator
RUN uv sync --frozen --no-cache

CMD ["uv", "run", "python", "src/main.py"]
