from unittest.mock import AsyncMock

import pytest
from shared.events.delivery import DeliveryStatusSimulated
from shared.events.order import OrderCreated, OrderStatusChanged

from src.schemas import DeliverySchema, DeliveryStatus
from src.service import DeliveryService


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
    event = OrderStatusChanged(id="order123", status="out_for_delivery", simulation=1)

    await service.handle_order(event)

    delivery_repo.create.assert_called_once()
    assert publisher.publish.call_count == 2  # DeliveryCreated + DeliverySimulationRequested


@pytest.mark.asyncio
async def test_handle_order_skips_non_delivery_status(service, delivery_repo, publisher):
    event = OrderCreated(id="order123", status="confirmed", simulation=1)

    await service.handle_order(event)

    delivery_repo.create.assert_not_called()
    publisher.publish.assert_not_called()


@pytest.mark.asyncio
async def test_handle_order_no_simulation(service, delivery_repo, publisher):
    delivery_repo.create.return_value = "del123"
    event = OrderStatusChanged(id="order123", status="out_for_delivery", simulation=-1)

    await service.handle_order(event)

    delivery_repo.create.assert_called_once()
    assert publisher.publish.call_count == 1  # DeliveryCreated only


@pytest.mark.asyncio
async def test_handle_status_update_success(service, delivery_repo, publisher):
    delivery = DeliverySchema(order_id="order123")
    delivery.id = "del123"
    delivery_repo.find_one.return_value = delivery
    delivery_repo.update_status.return_value = True

    await service.handle_status_update(DeliveryStatusSimulated(id="order123", status="on_the_way"))

    delivery_repo.update_status.assert_called_once_with("del123", DeliveryStatus.ON_THE_WAY)
    publisher.publish.assert_called_once()


@pytest.mark.asyncio
async def test_handle_status_update_delivery_not_found(service, delivery_repo):
    delivery_repo.find_one.return_value = None

    with pytest.raises(ValueError, match="Delivery not found"):
        await service.handle_status_update(DeliveryStatusSimulated(id="order123", status="on_the_way"))
