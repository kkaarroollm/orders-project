# Orders Project

A microservices-based food delivery system built with **FastAPI + MongoDB + Redis**, supporting **Kubernetes** and **Docker Compose** environments. Features event-driven communication via Redis Streams (SAGA pattern), a full observability stack, and a React frontend.

Deployed on a self-hosted Kubernetes cluster (Raspberry Pi) at [orders.karolmarszalek.me](https://orders.karolmarszalek.me/).

## Architecture

![Architecture Diagram](assets/arch-diagram.svg)

## Quick Start

```bash
cp envs/default.mongo_db.env envs/mongo_db.env
cp envs/default.redis.env envs/redis.env
cp envs/default.simulator.env envs/simulator.env
cp envs/default.mongo-keyfile envs/mongo-keyfile

docker compose up --build
```

Open [http://localhost](http://localhost) for the frontend, [http://localhost/dev](http://localhost/dev) for dev tools (Grafana, Prometheus, API docs).

## Documentation

Full documentation is available at the [docs site](https://kkaarroollm.github.io/orders-project/).

- [Getting Started](https://kkaarroollm.github.io/orders-project/getting-started.html)
- [Architecture](https://kkaarroollm.github.io/orders-project/architecture.html)
- [Services](https://kkaarroollm.github.io/orders-project/services.html)
- [Monitoring](https://kkaarroollm.github.io/orders-project/monitoring.html)
- [Deployment](https://kkaarroollm.github.io/orders-project/deployment.html)
- [Development](https://kkaarroollm.github.io/orders-project/development.html)

## Author

Made with **beer** by **kkaarroollm** -- [website](https://karolmarszalek.me/)
