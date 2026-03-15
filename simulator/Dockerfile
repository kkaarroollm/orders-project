FROM python:3.13

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONPATH=/app

COPY simulator/pyproject.toml simulator/uv.lock simulator/.python-version ./
COPY shared /shared

RUN uv sync --frozen --no-cache

COPY simulator/ .

CMD ["uv", "run", "python", "src/main.py"]
