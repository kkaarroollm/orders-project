# Orders Project

A microservices-based food delivery system exploring **event-driven architecture**, **distributed systems patterns**, and **container orchestration**. Built with FastAPI, MongoDB, Redis Streams, and React.

Deployed on a self-hosted Kubernetes cluster (Raspberry Pi) at [orders.karolmarszalek.me](https://orders.karolmarszalek.me/).

## What Makes This Interesting

- **Event-driven choreography** -- services communicate exclusively through Redis Streams, with no synchronous inter-service calls
- **Guaranteed message delivery** -- consumer groups, automatic retries, and a dead-letter queue ensure no event is silently lost
- **ACID transactions + eventual consistency** -- MongoDB transactions guard local state, while async events propagate changes across services
- **Real-time push** -- WebSocket connections deliver order status updates to the browser the moment they happen
- **Full observability** -- Prometheus metrics, Grafana dashboards, and Loki log aggregation with structured correlation IDs
- **Dual deployment** -- runs identically on Docker Compose (local) and Kubernetes with Helm (production)

```{toctree}
:maxdepth: 2
:caption: Contents

getting-started
architecture
services
monitoring
deployment
development
```
