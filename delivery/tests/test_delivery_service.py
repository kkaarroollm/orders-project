from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.schemas import DeliverySchema, DeliveryStatus
from src.service import DeliveryService
from src.streams import OrderEvent


@pytest.fixture
def delivery_repo():
    return AsyncMock()


@pytest.fixture
def publisher():
    return AsyncMock()


@pytest.fixture
def service(delivery_repo, publisher):
    return DeliveryService(repo=delivery_repo, publisher=publisher)


@pytest.mark.asyncio
async def test_handle_order_creates_delivery(service, delivery_repo, publisher):
    delivery_repo.create.return_value = "del123"
    msg = OrderEvent(id="order123", status="out_for_delivery", simulation=1)

    await service.handle_order(msg)

    delivery_repo.create.assert_called_once()
    assert publisher.publish_raw.call_count == 2  # deliveries_stream + simulate_delivery_stream


@pytest.mark.asyncio
async def test_handle_order_skips_non_delivery_status(service, delivery_repo, publisher):
    msg = SimpleNamespace(id="order123", status="confirmed", simulation=1)

    await service.handle_order(msg)

    delivery_repo.create.assert_not_called()
    publisher.publish_raw.assert_not_called()


@pytest.mark.asyncio
async def test_handle_order_no_simulation(service, delivery_repo, publisher):
    delivery_repo.create.return_value = "del123"
    msg = OrderEvent(id="order123", status="out_for_delivery", simulation=-1)

    await service.handle_order(msg)

    delivery_repo.create.assert_called_once()
    assert publisher.publish_raw.call_count == 1  # only deliveries_stream, no simulate


@pytest.mark.asyncio
async def test_handle_status_update_success(service, delivery_repo, publisher):
    delivery = DeliverySchema(order_id="order123")
    delivery.id = "del123"
    delivery_repo.find_one.return_value = delivery
    delivery_repo.update_status.return_value = True

    msg = SimpleNamespace(id=None, order_id="order123", status="on_the_way")

    await service.handle_status_update(msg)

    delivery_repo.update_status.assert_called_once_with("del123", DeliveryStatus.ON_THE_WAY)
    publisher.publish_raw.assert_called_once()


@pytest.mark.asyncio
async def test_handle_status_update_delivery_not_found(service, delivery_repo):
    delivery_repo.find_one.return_value = None
    msg = SimpleNamespace(id=None, order_id="order123", status="on_the_way")

    with pytest.raises(ValueError, match="Delivery not found"):
        await service.handle_status_update(msg)
