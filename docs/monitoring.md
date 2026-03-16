# Monitoring & Observability

## Stack

| Tool | Role | Retention |
|------|------|-----------|
| Prometheus | Metrics collection (scrapes `/metrics` every 15s) | 3 days / 256 MB |
| Grafana | Dashboards and log exploration | -- |
| Loki | Log aggregation backend | 72 hours |
| Promtail | Collects container logs, ships to Loki | -- |

## Grafana Dashboards

Three pre-provisioned dashboards (read-only, non-deletable):

### HTTP Metrics (`/grafana/d/http-metrics`)

- Request rate per service (req/s)
- Error rate (5xx) per service
- Latency percentiles (p50, p95, p99)
- Requests by status code (stacked bars)
- Top 10 endpoints by request count

### Application Logs (`/grafana/d/application-logs`)

- Log volume per container (stacked bars)
- Error log count (error/exception/traceback)
- Live log stream with full-text search
- Filterable by container name

### Event Pipeline (`/grafana/d/event-pipeline`)

- Message throughput per stream (msg/s)
- Error rate by stream and consumer group
- Processing latency (p50, p95, p99)
- Dead-letter queue rate and total count
- Success rate gauge (red/yellow/green)
- Messages by consumer group (stacked bars)

## Prometheus Metrics

### HTTP Metrics (all services)

Defined in `shared/src/shared/http_metrics.py`:

- `http_requests_total` (Counter) -- labels: `method`, `path`, `status_code`
- `http_request_duration_seconds` (Histogram) -- labels: `method`, `path`

### Stream Metrics (all consumers)

Defined in `shared/src/shared/redis/metrics.py`:

- `stream_messages_processed_total` (Counter) -- labels: `stream`, `group`, `status`
- `stream_message_duration_seconds` (Histogram) -- labels: `stream`, `group`
- `stream_dlq_messages_total` (Counter) -- labels: `stream`, `group`

## Quick Links (Docker Compose)

| Tool | URL | Credentials |
|------|-----|-------------|
| Grafana (admin) | <http://localhost/grafana/> | admin / admin |
| HTTP Metrics | <http://localhost/grafana/d/http-metrics> | -- (anonymous) |
| Application Logs | <http://localhost/grafana/d/application-logs> | -- (anonymous) |
| Event Pipeline | <http://localhost/grafana/d/event-pipeline> | -- (anonymous) |
| Prometheus | <http://localhost/prometheus/> | -- (read-only) |

Grafana dashboards are accessible without login (anonymous viewer role).

## Access Control

- **Prometheus** is proxied through NGINX with GET-only restriction -- demo users can query but cannot modify
- **Grafana** anonymous users get Viewer role -- can view dashboards but cannot edit or delete
- Provisioned dashboards are marked `editable: false` and `disableDeletion: true`

## Data Retention

- **Prometheus**: 3-day time retention + 256 MB size cap (whichever triggers first)
- **Loki**: 72-hour retention with compactor auto-cleanup, 4 MB/s ingestion rate limit
- **Promtail**: Only collects logs from application containers (order-service, delivery-service, notifications-service, order-simulator, nginx-proxy, frontend)
