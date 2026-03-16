# Architecture

## Design Patterns & Principles

### Event-Driven Choreography

The system uses **choreography** over orchestration -- there is no central coordinator managing workflows. Each service independently reacts to domain events published on Redis Streams and emits its own events in response.

This means:

- **Zero inter-service REST calls.** Services never call each other directly. The only REST endpoints face the client (browser).
- **Loose coupling.** Adding a new consumer (e.g., an analytics service) requires zero changes to existing services -- just subscribe to the relevant stream.
- **Independent deployability.** Any service can be restarted or redeployed without breaking the pipeline.

### Why Not SAGA?

A SAGA pattern implies a coordinator (orchestrator) or explicit compensation logic to undo steps on failure. This system doesn't have either -- if an event fails processing, it's retried and eventually moved to a dead-letter queue. The tradeoff: simpler implementation, but no automatic rollback across services.

### Transactional Outbox (Simplified)

The order service uses a **write-then-publish** approach:

1. A MongoDB transaction atomically validates stock and creates the order
2. Only after the transaction commits, the event is published to Redis Streams

This avoids the dual-write problem where a crash between database write and event publish could leave the system in an inconsistent state. The tradeoff vs. a full outbox pattern: if the process crashes after commit but before publish, the event is lost. For a demo system, this is acceptable.

```python
# Simplified flow in order_service.py
async with transaction() as session:
    await menu_repo.decrement_stock(item_id, quantity, session)
    order_id = await order_repo.create(order_data, session)

# Published only after successful commit
await publisher.publish(orders_stream, order_event)
```

---

## System Overview

![Architecture Diagram](../assets/arch-diagram.svg)

### Communication Protocols

| Layer | Protocol | Purpose |
|-------|----------|---------|
| Client ↔ API | **REST** (HTTP/1.1) | Order creation, menu queries |
| Client ↔ Notifications | **WebSocket** | Real-time order tracking with ping/pong keepalive |
| Service ↔ Service | **Redis Streams** | Async event-driven messaging with consumer groups |
| Service ↔ MongoDB | **Wire Protocol** | ACID transactions over replica set |

No gRPC, no GraphQL, no SSE -- intentionally simple protocol choices.

---

## Redis Streams as an Event Bus

Redis Streams provide a **persistent, ordered, append-only log** with consumer group semantics -- similar in concept to Kafka topics and consumer groups, but embedded in Redis.

### Why Redis Streams Over Alternatives?

| Feature | Redis Streams | Redis Pub/Sub | RabbitMQ | Kafka |
|---------|:---:|:---:|:---:|:---:|
| Message persistence | ✅ | ❌ | ✅ | ✅ |
| Consumer groups | ✅ | ❌ | ✅ | ✅ |
| Message acknowledgment | ✅ | ❌ | ✅ | ✅ |
| Replay from offset | ✅ | ❌ | ❌ | ✅ |
| Already in the stack | ✅ | ✅ | ❌ | ❌ |
| Operational complexity | Low | Low | Medium | High |

Redis was already needed for caching. Streams add event bus capabilities without introducing another infrastructure component.

### Consumer Group Mechanics

Each service registers a **consumer group** on the streams it cares about:

```
XREADGROUP GROUP orders-group consumer-1 COUNT 10 BLOCK 5000 STREAMS orders-stream >
```

- `GROUP orders-group` -- the consumer group name (one per service)
- `consumer-1` -- individual consumer within the group (one per pod/replica)
- `COUNT 10` -- batch size per read
- `BLOCK 5000` -- block for 5 seconds if no new messages
- `>` -- only read new (unacknowledged) messages

After successful processing, the message is acknowledged:

```
XACK orders-stream orders-group <message-id>
```

### Retry & Dead-Letter Queue

Unacknowledged messages are automatically reclaimed after a timeout using `XAUTOCLAIM`. A retry counter tracks attempts per message:

```
Message fails processing
  → stays in pending entries list (PEL)
  → XAUTOCLAIM reclaims it after idle timeout
  → retry counter incremented (stored in Redis key)
  → if retries > max_retries → XADD to dead-letters stream
```

The dead-letter stream preserves the original message, stream name, group, and error information for manual inspection.

### Message Envelope

Every event is wrapped in a standardized envelope:

```
{
  "event_type": "order.created",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "source": "orders-service",
  "timestamp": "2024-12-01T14:30:00Z",
  "payload": { "order_id": "...", "items": [...] }
}
```

The `correlation_id` follows an event across all services and appears in every log line, enabling end-to-end tracing through Loki without a dedicated tracing system.

---

## Event Flow

### Order Lifecycle

```
┌─────────┐     POST /orders      ┌────────────────┐
│ Browser  │ ──────────────────── │ Order Service   │
└─────────┘                       └───────┬────────┘
                                          │ order.created
                                          ▼
                                  ┌───────────────┐
                              ┌──│ orders-stream  │──┐
                              │  └───────────────┘   │
                              ▼                      ▼
                    ┌──────────────┐      ┌──────────────────┐
                    │ Delivery Svc │      │ Notifications Svc│
                    └──────┬───────┘      └────────┬─────────┘
                           │                       │
                           │ delivery.created      │ WebSocket push
                           ▼                       ▼
                   ┌─────────────────┐     ┌─────────┐
                   │deliveries-stream│────▶│ Browser  │
                   └─────────────────┘     └─────────┘
```

### Simulation Pipeline

The simulator drives the order through realistic status transitions with configurable delays:

```
Order:    created → confirmed → preparing → out_for_delivery
Delivery: waiting → on_the_way → delivered
```

Each transition publishes a status update event, which the corresponding service picks up and persists.

### Stream Topology

| Stream | Publisher | Consumers |
|--------|-----------|-----------|
| `orders-stream` | Order Service | Delivery, Notifications |
| `deliveries-stream` | Delivery Service | Notifications |
| `order-status-stream` | Simulator | Order Service |
| `delivery-status-stream` | Simulator | Delivery Service |
| `simulate-order-stream` | Order Service | Simulator |
| `simulate-delivery-stream` | Delivery Service | Simulator |
| `dead-letters` | Any consumer (on failure) | Manual inspection |

---

## MongoDB & Transactions

MongoDB runs as a **replica set** (`rs0`), which is required for multi-document ACID transactions.

The order creation flow uses transactions to ensure atomicity:

- Stock is decremented and the order is created in a single transaction
- If stock is insufficient, the entire transaction rolls back
- The event is published only after a successful commit

```python
class MongoTransactionManager:
    async def transaction(self):
        async with await self.client.start_session() as session:
            async with session.start_transaction():
                yield session
```

This prevents overselling: two concurrent orders for the last item will have one succeed and one roll back.

---

## Kubernetes Deployment

![Kubernetes Diagram](../assets/orders-project-v2.svg)

The production deployment uses an **umbrella Helm chart** with subcharts for each service and external dependencies:

- **Deployments** for stateless application services
- **StatefulSets** for MongoDB (replica set) and Redis (persistent storage)
- **Ingress NGINX** with Cloudflared tunnel for public access
- **CronJob** for periodic stock refill (keeps the demo running)
- **kube-prometheus-stack** for monitoring (Prometheus + Grafana)
- **Loki + Promtail** for centralized log aggregation

Three init Jobs run on first deployment:

1. **init-rs-job** -- initializes MongoDB replica set
2. **init-user-job** -- creates MongoDB admin user
3. **init-dummy-db-job** -- loads demo menu data
