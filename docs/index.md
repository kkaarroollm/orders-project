# Orders Project

A microservices-based food delivery system built with **FastAPI**, **MongoDB**, **Redis**, and **React**. Supports both Docker Compose and Kubernetes (Helm) deployments.

Deployed on a self-hosted Kubernetes cluster (Raspberry Pi) at [orders.karolmarszalek.me](https://orders.karolmarszalek.me/).

## Highlights

- **Event-driven architecture** using Redis Streams with SAGA pattern
- **Full observability** with Prometheus, Grafana, and Loki
- **Typed Python** codebase with `ty` type checker and `ruff` linter
- **UV workspace** for unified dependency management across all services
- **Helm chart** with monitoring stack (kube-prometheus-stack, Loki, Promtail)

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
