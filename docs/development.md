# Development

## Tech Stack

### Backend (Python 3.13+)

- **FastAPI** -- async REST APIs
- **Pydantic** -- schema validation and settings
- **Motor** -- async MongoDB client
- **Redis (async)** -- event bus and pub/sub
- **prometheus-client** -- metrics exposition

### Frontend

- **React 19** + **TypeScript**
- **Vite** -- build tool and dev server
- **Tailwind CSS** + **shadcn/ui** -- styling
- **TanStack Query & Router** -- data fetching and routing
- **Zod** -- schema validation

## UV Workspace

The project uses a UV workspace to manage all Python services under a single virtual environment.

```bash
# Install all dependencies
uv lock
uv sync --dev

# Check interpreter
uv run python -c "import sys; print(sys.executable)"
```

The root `pyproject.toml` defines workspace members:

```toml
[tool.uv.workspace]
members = ["shared", "orders", "delivery", "notifications", "simulator"]
```

The `shared` package is a workspace dependency used by all services:

```toml
[project]
dependencies = ["shared"]

[tool.uv.sources]
shared = { workspace = true }
```

## Linting & Type Checking

```bash
# Ruff linter (all services)
uv run ruff check .

# Type checker (per service)
cd orders && uv run ty check
cd delivery && uv run ty check
cd notifications && uv run ty check
```

CI runs both `ruff check` and `ty check` for every service on push/PR.

## Testing

```bash
# Run tests for a service
cd orders && uv run pytest
```

Test dependencies (`pytest`, `pytest-asyncio`) are declared as dev dependencies in each service's `pyproject.toml`.

## Project Structure

```
.
+-- frontend/               # React + TS + Tailwind UI
+-- orders/                 # FastAPI -- orders service
+-- delivery/               # FastAPI -- delivery logic
+-- notifications/          # FastAPI -- notifications + WebSockets
+-- shared/                 # Shared Python library (Redis, metrics, settings)
+-- simulator/              # Event generator for order lifecycle
+-- monitoring/             # Prometheus, Grafana, Loki & Promtail configs
+-- nginx/                  # Reverse proxy configs (dev & prod)
+-- charts/                 # Helm umbrella chart & subcharts
+-- envs/                   # Environment files
+-- scripts/                # Init scripts (replica set, seed data)
+-- assets/                 # Architecture diagrams
+-- docs/                   # Sphinx documentation (this site)
+-- docker-compose.yaml     # Dev-only deployment stack
```
