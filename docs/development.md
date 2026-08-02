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
uv sync --all-packages --dev

# Check interpreter
uv run python -c "import sys; print(sys.executable)"
```

There is exactly one lockfile, `uv.lock` at the repository root -- workspace
members must not carry their own.

The root `pyproject.toml` defines workspace members:

```toml
[tool.uv.workspace]
members = ["shared", "orders", "delivery", "notifications", "simulator"]
```

The `shared` package is a workspace dependency used by all services. Its
optional extras keep each service's image free of drivers it never imports:

| Extra | Pulls in | Used by |
|-------|----------|---------|
| `mongo` | `pymongo` | orders, delivery |
| `web` | `fastapi[standard]`, `starlette` | orders, delivery, notifications |
| (none) | `redis`, `pydantic`, `prometheus-client` | simulator |

```toml
[project]
dependencies = ["shared[mongo,web]"]

[tool.uv.sources]
shared = { workspace = true }
```

Third-party versions are pinned once, in `shared/pyproject.toml`. Services
declare no versions of their own so they cannot drift apart.

## Linting & Type Checking

Both tools are configured once in the root `pyproject.toml` and run across the
whole workspace from the repository root:

```bash
uv run ruff check
uv run ty check
```

CI runs both once per push/PR, plus the test suites.

## Testing

```bash
# Run tests for a service
cd orders && uv run pytest
```

Test dependencies (`pytest`, `pytest-asyncio`) live in the root `pyproject.toml`
dev group, shared by every member of the workspace.

## Project Structure

```
.
+-- frontend/               # React + TS + Tailwind UI
+-- orders/                 # FastAPI -- orders service
+-- delivery/               # FastAPI -- delivery logic
+-- notifications/          # FastAPI -- notifications + SSE
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
