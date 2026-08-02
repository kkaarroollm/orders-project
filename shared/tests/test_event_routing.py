import json
from unittest.mock import AsyncMock

import pytest

from shared.events import ALL_EVENTS, EVENT_REGISTRY
from shared.events.order import OrderCreated, OrderStatusChanged
from shared.redis.consumer import Route, StreamConsumer


def _envelope(event_type: str, payload: dict) -> dict[str, str]:
    return {
        "data": json.dumps(
            {"event_type": event_type, "correlation_id": "order123", "source": "test", "payload": payload}
        )
    }


@pytest.fixture
def redis():
    return AsyncMock()


def _consumer(redis, routes: dict[str, Route]) -> StreamConsumer:
    return StreamConsumer(
        redis=redis,
        stream="orders-stream",
        group="test-group",
        consumer_name="test-consumer",
        routes=routes,
    )


def test_every_event_registers_its_wire_types():
    for event in ALL_EVENTS:
        assert EVENT_REGISTRY[event.event_type] is event
        for legacy in event.legacy_types:
            assert EVENT_REGISTRY[legacy] is event


@pytest.mark.asyncio
async def test_dispatches_to_the_handler_for_its_event_type(redis):
    created, changed = AsyncMock(), AsyncMock()
    consumer = _consumer(
        redis,
        {
            OrderCreated.event_type: Route(OrderCreated, created),
            OrderStatusChanged.event_type: Route(OrderStatusChanged, changed),
        },
    )

    await consumer._process_message(
        "1-1", _envelope("order.status_updated.v1", {"id": "order123", "status": "preparing"})
    )

    changed.assert_awaited_once()
    created.assert_not_awaited()
    assert changed.await_args is not None
    assert changed.await_args.args[0].status == "preparing"


@pytest.mark.asyncio
async def test_legacy_wire_type_still_routes(redis):
    """A renamed event keeps consuming messages already sitting in the stream."""
    handler = AsyncMock()
    consumer = _consumer(redis, {t: Route(OrderCreated, handler) for t in ("order.created.v1", "order.created")})

    await consumer._process_message("1-1", _envelope("order.created", {"id": "order123", "status": "confirmed"}))

    handler.assert_awaited_once()


@pytest.mark.asyncio
async def test_unrouted_event_is_acked_not_dead_lettered(redis):
    """Streams are shared: another service's events are traffic, not failures."""
    handler = AsyncMock()
    consumer = _consumer(redis, {OrderCreated.event_type: Route(OrderCreated, handler)})

    await consumer._process_message(
        "1-1", _envelope("delivery.created.v1", {"order_id": "order123", "status": "waiting_for_pickup"})
    )

    handler.assert_not_awaited()
    redis.xack.assert_awaited_once()
    redis.xadd.assert_not_awaited()  # nothing sent to the DLQ
