from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError
from shared.events.delivery import DeliveryStatusChanged
from shared.events.order import OrderStatusChanged

from src.service import NotificationService


@pytest.fixture
def notification_repo():
    return AsyncMock()


@pytest.fixture
def registry():
    return AsyncMock()


@pytest.fixture
def service(notification_repo, registry):
    return NotificationService(repo=notification_repo, registry=registry)


@pytest.mark.asyncio
async def test_order_event_broadcasts_and_caches(service, notification_repo, registry):
    await service.handle_order_event(OrderStatusChanged(id="order123", status="preparing"))

    registry.broadcast.assert_called_once()
    order_id, payload = registry.broadcast.call_args[0]
    assert order_id == "order123"
    assert payload["status"] == "preparing"

    notification_repo.set_order_status.assert_called_once()


@pytest.mark.asyncio
async def test_delivery_event_uses_order_id(service, registry):
    """Delivery events are keyed by order_id; order events by their own id."""
    await service.handle_delivery_event(DeliveryStatusChanged(order_id="order456", status="on_the_way"))

    registry.broadcast.assert_called_once()
    assert registry.broadcast.call_args[0][0] == "order456"


def test_event_without_status_is_rejected_at_parse_time():
    """Malformed payloads now fail validation instead of reaching a handler."""
    with pytest.raises(ValidationError):
        # Parsed the way the consumer parses a wire payload.
        OrderStatusChanged.model_validate({"id": "order123"})
