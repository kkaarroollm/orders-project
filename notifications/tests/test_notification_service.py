from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError
from shared.events.delivery import DeliveryStatusChanged
from shared.events.notifications import OrderStatusPush
from shared.events.order import OrderStatusChanged

from src.service import NotificationService, StatusPushFanout


@pytest.fixture
def notification_repo():
    return AsyncMock()


@pytest.fixture
def producer():
    return AsyncMock()


@pytest.fixture
def service(notification_repo, producer):
    return NotificationService(repo=notification_repo, producer=producer)


@pytest.mark.asyncio
async def test_order_event_caches_then_fans_out(service, notification_repo, producer):
    await service.handle_order_event(OrderStatusChanged(id="order123", status="preparing"))

    notification_repo.set_order_status.assert_called_once()
    producer.publish.assert_called_once()
    push = producer.publish.call_args.args[0]
    assert push.order_id == "order123"
    assert push.status == "preparing"
    assert push.stream == "ws-events"


@pytest.mark.asyncio
async def test_delivery_event_uses_order_id(service, producer):
    """Delivery events are keyed by order_id; order events by their own id."""
    await service.handle_delivery_event(DeliveryStatusChanged(order_id="order456", status="on_the_way"))

    assert producer.publish.call_args.args[0].order_id == "order456"


@pytest.mark.asyncio
async def test_fanout_pushes_to_local_clients_only():
    """Every replica consumes the push; only the holder of the stream sends it."""
    registry = AsyncMock()
    fanout = StatusPushFanout(registry)

    await fanout.handle_push(OrderStatusPush(order_id="order123", status="preparing", timestamp="t1"))

    registry.broadcast.assert_awaited_once()
    order_id, payload = registry.broadcast.await_args.args
    assert order_id == "order123"
    assert payload["status"] == "preparing"


def test_event_without_status_is_rejected_at_parse_time():
    """Malformed payloads now fail validation instead of reaching a handler."""
    with pytest.raises(ValidationError):
        # Parsed the way the consumer parses a wire payload.
        OrderStatusChanged.model_validate({"id": "order123"})
