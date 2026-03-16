# Services

## Overview

| Service | Port | Description |
|---------|------|-------------|
| `order-service` | 8003 | Processes customer orders, manages menu items |
| `delivery-service` | 8001 | Handles shipment and delivery status tracking |
| `notifications-service` | 8002 | Real-time updates via WebSockets and Redis Streams |
| `order-simulator` | -- | Simulates the full order lifecycle (creation to delivery) |
| `frontend` | 3000 | React UI with menu browsing, cart, ordering, and live tracking |

## Order Service

**Port:** 8003 | **API Docs:** `/docs` (dev only)

Manages orders and menu items. Publishes `order.created` events to Redis Streams.

Endpoints
: - `GET /api/v1/menu` -- list menu items
: - `POST /api/v1/orders` -- create an order
: - `GET /api/v1/orders/{id}` -- get order details
: - `GET /api/v1/health` -- readiness check
: - `GET /metrics` -- Prometheus metrics

Dependencies
: MongoDB, Redis, shared library

## Delivery Service

**Port:** 8001 | **API Docs:** `/docs` (dev only)

Listens for new orders on `orders-stream`, creates delivery records, and tracks status changes.

Endpoints
: - `GET /api/v1/health` -- readiness check
: - `GET /metrics` -- Prometheus metrics

Dependencies
: MongoDB, Redis, shared library

## Notifications Service

**Port:** 8002 | **API Docs:** `/docs` (dev only)

Consumes events from `orders-stream` and `deliveries-stream`. Pushes real-time status updates to connected frontends over WebSockets.

Endpoints
: - `WS /ws/v1/order-tracking/{order_id}` -- WebSocket for live order status
: - `GET /api/v1/health` -- readiness check
: - `GET /metrics` -- Prometheus metrics

Dependencies
: Redis, shared library

## Order Simulator

Generates synthetic order events to exercise the full pipeline. Simulates order creation, status changes, and delivery completion with configurable delays.

Dependencies
: Redis, shared library

## Supporting Services

| Service | Purpose |
|---------|---------|
| MongoDB | Document store (replica set) |
| Redis | Event bus (Streams), pub/sub messaging |
| NGINX | Reverse proxy for frontend, APIs, Grafana, Prometheus |
| Prometheus | Scrapes `/metrics` from all services every 15s |
| Grafana | Dashboards and log exploration |
| Loki | Log aggregation backend |
| Promtail | Collects container logs, ships to Loki |
