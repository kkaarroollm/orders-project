# Orders Project

Event-driven food delivery system: **FastAPI + MongoDB + Redis Streams**, a
React frontend, running on a self-hosted Raspberry Pi Kubernetes cluster.

Live at [orders.karolmarszalek.me](https://orders.karolmarszalek.me/) ·
source on [GitHub](https://github.com/kkaarroollm/orders-project).

There is no orchestrator and no service-to-service call. Each service reacts to
events on Redis Streams and emits its own.

```bash
git clone https://github.com/kkaarroollm/orders-project
cd orders-project
./scripts/setup.sh          # generates envs/mongo-keyfile
docker compose up --build
```

[localhost](http://localhost) serves the app, [localhost/dev](http://localhost/dev)
serves Grafana, Prometheus and the API docs.

The [README](https://github.com/kkaarroollm/orders-project#readme) covers the
workspace layout and day-to-day development. This site covers the design.

```{toctree}
:maxdepth: 2
:caption: Contents

design
```
