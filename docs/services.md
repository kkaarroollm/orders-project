# Services

## Overview

```
┌──────────────────────────────────────────────────────────┐
│                      NGINX Proxy                          │
│  / → Frontend  │  /api → Orders  │  /ws → Notifications  │
└──────────────────────────────────────────────────────────┘
         │                │                    │
    ┌────▼────┐    ┌──────▼──────┐    ┌───────▼────────┐
    │Frontend │    │Order Service│    │Notifications   │
    │ (React) │    │  (FastAPI)  │    │   (FastAPI)    │
    └─────────┘    └──────┬──────┘    └───────┬────────┘
                          │                    │
                   ┌──────▼──────┐    ┌───────▼────────┐
                   │  Delivery   │    │   Simulator    │
                   │  (FastAPI)  │    │   (Python)     │
                   └─────────────┘    └────────────────┘
```

| Service | Port | Role |
|---------|------|------|
| `order-service` | 8003 | Order management, menu, stock control |
| `delivery-service` | 8001 | Delivery record creation and tracking |
| `notifications-service` | 8002 | WebSocket gateway for real-time updates |
| `order-simulator` | -- | Drives order lifecycle transitions |
| `frontend` | 3000 | React UI for browsing, ordering, tracking |

---

## Order Service

**The entry point for all business logic.** Handles order creation with stock validation inside MongoDB transactions, and publishes domain events to Redis Streams.

Endpoints
: - `GET /api/v1/menu` -- list menu items with stock levels
: - `POST /api/v1/orders` -- create an order (validates stock, decrements atomically)
: - `GET /api/v1/orders/{id}` -- get order details and current status
: - `GET /api/v1/health` -- readiness check
: - `GET /metrics` -- Prometheus metrics

Publishes to
: `orders-stream`, `simulate-order-stream`

Consumes from
: `order-status-stream` (status updates from simulator)

Key behavior
: Order creation runs inside a MongoDB transaction. Stock is checked and decremented atomically -- if two users order the last pizza simultaneously, one gets the order and the other gets a 400 error. The event is published only after the transaction commits.

---

## Delivery Service

**Reacts to orders reaching "out for delivery" status.** Creates delivery records and tracks the delivery lifecycle.

Endpoints
: - `GET /api/v1/health` -- readiness check
: - `GET /metrics` -- Prometheus metrics

Publishes to
: `deliveries-stream`, `simulate-delivery-stream`

Consumes from
: `orders-stream` (new orders), `delivery-status-stream` (status updates from simulator)

Key behavior
: Listens to `orders-stream` and only acts when an order reaches `out_for_delivery` status. Creates a delivery record in MongoDB and publishes a `delivery.created` event. Has no REST API for delivery management -- everything is event-driven.

---

## Notifications Service

**The WebSocket gateway.** Bridges the event bus to the browser, pushing real-time status updates to connected clients.

Endpoints
: - `WS /ws/v1/order-tracking/{order_id}` -- WebSocket for live order tracking
: - `GET /api/v1/health` -- readiness check
: - `GET /metrics` -- Prometheus metrics

Consumes from
: `orders-stream`, `deliveries-stream`

Key behavior
: When a client connects via WebSocket, the service first checks Redis cache for the latest known status (instant response), then keeps the connection alive and pushes updates as they arrive from the event bus. Uses ping/pong frames with a 60-second timeout for keepalive. No database dependency -- purely stateless, backed by Redis.

---

## Order Simulator

**Drives the demo.** Simulates realistic order lifecycle transitions with configurable delays, making the system useful without manual interaction.

Consumes from
: `simulate-order-stream`, `simulate-delivery-stream`

Publishes to
: `order-status-stream`, `delivery-status-stream`

Status transitions
: ```
  Order:    created → confirmed → preparing → out_for_delivery
  Delivery: waiting → on_the_way → delivered
  ```

Each transition has a randomized delay (configurable via environment variables) to simulate real-world processing times.

---

## Frontend

**React 19 + TypeScript** single-page application with:

- Menu browsing with stock indicators
- Shopping cart with real-time validation
- Order placement with instant feedback
- Live order tracking via WebSocket connection
- Dev tools page with links to Grafana dashboards and API docs

Built with Vite, styled with Tailwind CSS + shadcn/ui, data fetching via TanStack Query, routing via TanStack Router.

---

## Supporting Infrastructure

| Service | Role | Details |
|---------|------|---------|
| **MongoDB** | Document store | Replica set (`rs0`) for transaction support, keyfile auth |
| **Redis** | Event bus + cache | Streams with consumer groups, status caching with 24h TTL |
| **NGINX** | Reverse proxy | Routes traffic, WebSocket upgrade, Prometheus GET-only restriction |
| **Prometheus** | Metrics | Scrapes `/metrics` from all services every 15s |
| **Grafana** | Dashboards | 3 pre-provisioned dashboards, anonymous viewer access |
| **Loki** | Log aggregation | Receives logs from Promtail, 72h retention |
| **Promtail** | Log collector | Docker service discovery, filters to app containers only |
