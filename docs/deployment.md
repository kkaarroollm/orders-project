# Deployment

## Docker Images

All application images are built for **linux/amd64** and **linux/arm64** (Raspberry Pi compatible).

### Registries

Images are published to both Docker Hub and GitHub Container Registry on every release:

| Service | Docker Hub | GHCR |
|---------|-----------|------|
| Orders | `kkaarroollm/orders-service` | `ghcr.io/kkaarroollm/orders-service` |
| Delivery | `kkaarroollm/delivery-service` | `ghcr.io/kkaarroollm/delivery-service` |
| Notifications | `kkaarroollm/notifications-service` | `ghcr.io/kkaarroollm/notifications-service` |
| Simulator | `kkaarroollm/simulator-service` | `ghcr.io/kkaarroollm/simulator-service` |
| Frontend | `kkaarroollm/frontend-service` | `ghcr.io/kkaarroollm/frontend-service` |

Tags follow semver: `:0.1.0`, `:0.2.0`, etc. The `:latest` tag always points to the most recent release.

### CI/CD Pipeline

- **On PR / push to master**: all 5 images are built for both architectures (no push) to catch build failures early
- **On GitHub release**: images are built, tagged with the release version, and pushed to both registries

---

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

---

## Raspberry Pi Deployment

All images are built for `linux/arm64`, so the full stack runs on a Raspberry Pi 4 or 5.

### Resource Estimates

| Stack | RAM | Disk |
|-------|-----|------|
| App only (5 services + MongoDB + Redis + NGINX) | ~1 GB | ~2 GB |
| App + monitoring (Prometheus, Grafana, Loki, Promtail) | ~2-3 GB | ~5-10 GB |

The retention limits (Prometheus 3 days / 256 MB, Loki 72 hours) keep disk usage bounded over time.

### Tips

- A Raspberry Pi 4 with **4 GB RAM** can run the full stack including monitoring
- Use `DEPLOY_ENV=prod` for production-grade passwords
- Consider reducing `replicaCount` to 1 in Helm values for single-node clusters
- Cloudflare Tunnel works well for exposing the cluster without port forwarding
