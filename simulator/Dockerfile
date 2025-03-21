FROM python:3.13

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONPATH=/app

COPY pyproject.toml ./uv.lock .python-version ./

RUN uv sync --frozen --no-cache

COPY . .

CMD ["uv", "run", "python", "src/main.py"]