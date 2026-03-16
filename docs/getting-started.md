# Getting Started

## Prerequisites

- Docker and Docker Compose
- Git

For Kubernetes deployment, you also need:
- `kubectl` configured for your cluster
- `helm` v3+

## Docker Compose (Quickstart)

1. Clone and set up environment files:

```bash
git clone https://github.com/kkaarroollm/orders-project.git
cd orders-project

cp envs/default.mongo_db.env envs/mongo_db.env
cp envs/default.redis.env envs/redis.env
cp envs/default.simulator.env envs/simulator.env
cp envs/default.mongo-keyfile envs/mongo-keyfile
```

2. Start everything:

```bash
docker compose up --build
```

3. Open the app:

| What | URL |
|------|-----|
| Frontend | <http://localhost> |
| Dev Tools | <http://localhost/dev> |
| Grafana | <http://localhost/grafana/> |
| Prometheus | <http://localhost/prometheus/> |

The simulator starts automatically and generates orders.

## Kubernetes (Helm)

```bash
helm dependency update charts/orders-project
helm install orders charts/orders-project -n prod --create-namespace
```

On first install, three Jobs initialize MongoDB (replica set, user, seed data).

Configure credentials and connection strings in `charts/orders-project/values.yaml`.

See {doc}`deployment` for detailed Helm configuration.
