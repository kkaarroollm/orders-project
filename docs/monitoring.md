# Monitoring & Observability

The project implements the **three pillars of observability**: metrics (Prometheus), logs (Loki), and real-time dashboards (Grafana). Every service exposes a `/metrics` endpoint, and all container logs are collected automatically.

## Stack

| Tool | Role | Retention |
|------|------|-----------|
| **Prometheus** | Time-series metrics, scrapes `/metrics` every 15s | 3 days / 256 MB |
| **Grafana** | Visualization, dashboards, log exploration | -- |
| **Loki** | Log aggregation (like Prometheus, but for logs) | 72 hours |
| **Promtail** | Log shipper, Docker service discovery | -- |

## Grafana Dashboards

Three pre-provisioned, read-only dashboards ship with the project. They're automatically loaded on startup (Docker Compose: volume mounts, Kubernetes: ConfigMap sidecar).

### HTTP Metrics (`/grafana/d/http-metrics`)

Answers: *"Is the API healthy? Where are the bottlenecks?"*

- Request rate per service (req/s)
- Error rate (5xx) per service
- Latency percentiles (p50, p95, p99)
- Requests by status code (stacked bars)
- Top 10 endpoints by request count

### Application Logs (`/grafana/d/application-logs`)

Answers: *"What happened? What errors are occurring?"*

- Log volume per container (stacked bars)
- Error log count (error/exception/traceback keywords)
- Live log stream with full-text search
- Filterable by container name

### Event Pipeline (`/grafana/d/event-pipeline`)

Answers: *"Is the event bus healthy? Are messages being processed?"*

- Message throughput per stream (msg/s)
- Processing error rate by stream and consumer group
- Processing latency (p50, p95, p99)
- Dead-letter queue rate and cumulative count
- Success rate gauge (green > 99%, yellow > 95%, red below)
- Messages by consumer group (stacked bars)

## Prometheus Metrics

### HTTP Metrics (all services)

Defined in `shared/src/shared/http_metrics.py`. Middleware automatically instruments every request.

| Metric | Type | Labels |
|--------|------|--------|
| `http_requests_total` | Counter | `method`, `path`, `status_code` |
| `http_request_duration_seconds` | Histogram | `method`, `path` |

:::{note}
The GZip middleware is configured to skip `/metrics` to prevent Prometheus from receiving compressed responses it can't parse.
:::

### Stream Metrics (all consumers)

Defined in `shared/src/shared/redis/metrics.py`. Consumer group processing is automatically instrumented.

| Metric | Type | Labels |
|--------|------|--------|
| `stream_messages_processed_total` | Counter | `stream`, `group`, `status` |
| `stream_message_duration_seconds` | Histogram | `stream`, `group` |
| `stream_dlq_messages_total` | Counter | `stream`, `group` |

The `status` label on `stream_messages_processed_total` distinguishes `success` from `error`, enabling per-stream error rate calculations.

## Quick Links (Docker Compose)

| Tool | URL | Access |
|------|-----|--------|
| Grafana (admin) | <http://localhost/grafana/> | admin / admin |
| HTTP Metrics dashboard | <http://localhost/grafana/d/http-metrics> | anonymous viewer |
| Application Logs dashboard | <http://localhost/grafana/d/application-logs> | anonymous viewer |
| Event Pipeline dashboard | <http://localhost/grafana/d/event-pipeline> | anonymous viewer |
| Prometheus | <http://localhost/prometheus/> | read-only (GET only) |

## Access Control

Demo-safe by default:

- **Prometheus** is proxied through NGINX with `limit_except GET { deny all; }` -- users can query metrics but cannot modify configuration or delete data
- **Grafana** anonymous users get the Viewer role -- dashboards are visible without login, but editing and deletion are blocked
- Provisioned dashboards are marked `editable: false` and `disableDeletion: true`

## Data Retention

Lightweight retention policies keep resource usage bounded, which matters on a Raspberry Pi cluster:

- **Prometheus**: 3-day time retention + 256 MB size cap (whichever triggers first)
- **Loki**: 72-hour retention with compactor auto-cleanup, 4 MB/s ingestion rate limit, 8 MB burst
- **Promtail**: Only collects logs from application containers (order-service, delivery-service, notifications-service, order-simulator, nginx-proxy, frontend) -- monitoring stack logs are excluded to avoid feedback loops

## Correlation & Tracing

Instead of a dedicated tracing system (Jaeger, Zipkin), the project uses `correlation_id` propagation:

1. Order service generates a UUID `correlation_id` when an order is created
2. The ID is included in every event envelope published to Redis Streams
3. Every service logs the `correlation_id` with each action
4. In Loki/Grafana, you can filter by `correlation_id` to see the full lifecycle of an order across all services
