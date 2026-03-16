# Getting Started

## Prerequisites

- Docker and Docker Compose v2
- Git

For Kubernetes deployment:
- `kubectl` configured for your cluster
- `helm` v3+

## Docker Compose (Quickstart)

### 1. Clone and configure

```bash
git clone https://github.com/kkaarroollm/orders-project.git
cd orders-project

cp envs/default.mongo_db.env envs/mongo_db.env
cp envs/default.redis.env envs/redis.env
cp envs/default.simulator.env envs/simulator.env
cp envs/default.mongo-keyfile envs/mongo-keyfile
```

### 2. Start everything

```bash
docker compose up --build
```

This brings up all application services, MongoDB, Redis, the monitoring stack, and an NGINX reverse proxy. First startup takes a couple of minutes while images build and MongoDB initializes.

### 3. Explore

| What | URL |
|------|-----|
| Frontend | <http://localhost> |
| Dev Tools | <http://localhost/dev> |
| Grafana dashboards | <http://localhost/grafana/> |
| Prometheus (read-only) | <http://localhost/prometheus/> |

The **simulator starts automatically** and generates orders with realistic delays. You'll see orders flowing through the pipeline within seconds.

### 4. Try it yourself

1. Open <http://localhost> and browse the menu
2. Add items to your cart and place an order
3. Watch the order status update in real-time on the tracking page
4. Open the [Event Pipeline dashboard](http://localhost/grafana/d/event-pipeline) to see the messages flowing through Redis Streams

## Kubernetes (Helm)

```bash
helm dependency update charts/orders-project
helm install orders charts/orders-project -n prod --create-namespace
```

On first install, three init Jobs automatically set up MongoDB (replica set, admin user, demo data).

Configure credentials and connection strings in `charts/orders-project/values.yaml`.

See {doc}`deployment` for the full Helm configuration reference.
