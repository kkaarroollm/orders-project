# Deployment

## Docker Compose

The `docker-compose.yaml` defines the full development stack: application services, databases, monitoring, and reverse proxy.

### Environment Files

Copy the defaults before first run:

```bash
cp envs/default.mongo_db.env envs/mongo_db.env
cp envs/default.redis.env envs/redis.env
cp envs/default.simulator.env envs/simulator.env
cp envs/default.mongo-keyfile envs/mongo-keyfile
```

### Commands

```bash
# Start everything
docker compose up --build

# Restart after config changes
docker compose down -v && docker compose up -d

# View logs for a specific service
docker compose logs -f order-service
```

### NGINX Proxy Routes

| Path | Backend |
|------|---------|
| `/` | Frontend (Vite dev server) |
| `/api/v1/orders`, `/api/v1/menu` | Order service |
| `/ws/v1/order-tracking` | Notifications service (WebSocket) |
| `/grafana/` | Grafana |
| `/prometheus/` | Prometheus (GET-only) |

## Kubernetes (Helm)

### Chart Structure

```
charts/orders-project/          # Umbrella chart
  charts/
    orders/                     # Order service subchart
    delivery/                   # Delivery service subchart
    notifications/              # Notifications service subchart
    frontend/                   # Frontend subchart
    simulator/                  # Simulator subchart
    mongodb/                    # MongoDB StatefulSet
    redis/                      # Redis StatefulSet
  dashboards/                   # Grafana dashboard JSONs
  templates/
    configs.yaml                # Shared ConfigMaps
    secrets.yaml                # Shared Secrets
    ingress.yaml                # Ingress rules
    grafana-dashboards.yaml     # Dashboard ConfigMaps
```

External dependencies (from `Chart.yaml`):

- `ingress-nginx` 4.12.1
- `kube-prometheus-stack` 69.8.2
- `loki` 6.28.0
- `promtail` 6.16.6

### Install

```bash
helm dependency update charts/orders-project
helm install orders charts/orders-project -n prod --create-namespace
```

### Configuration

All values are in `charts/orders-project/values.yaml`:

```yaml
global:
  mongo:
    username: root
    password: <change-me>
    host: mongo-svc
    database: food-delivery
  redis:
    password: <change-me>
    host: redis-svc
```

### Init Jobs

On first install, three Jobs run automatically:

1. **init-rs-job** -- initializes MongoDB replica set (`rs0`)
2. **init-user-job** -- creates the MongoDB admin user
3. **init-dummy-db-job** -- loads demo menu data

### Ingress Routes

| Path | Service |
|------|---------|
| `/api/v1/orders`, `/api/v1/menu` | orders-svc:8003 |
| `/ws/v1/order-tracking` | notifications-svc:8002 |
| `/grafana` | grafana:80 |
| `/` | frontend-svc:80 |

### Monitoring in Kubernetes

ServiceMonitors are defined for orders, delivery, and notifications services. Grafana dashboards are provisioned via ConfigMaps with the `grafana_dashboard: "1"` label (auto-discovered by the sidecar).

Loki is configured as an additional Grafana datasource in `values.yaml`.
