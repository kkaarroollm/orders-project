from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.schemas import MenuItemSchema, OrderSchema, OrderStatus, OrderedItemSchema, OrderingPersonSchema
from src.services.order_service import OrderService


@pytest.fixture
def order_repo():
    repo = AsyncMock()
    return repo


@pytest.fixture
def menu_repo():
    repo = AsyncMock()
    return repo


@pytest.fixture
def publisher():
    pub = AsyncMock()
    return pub


@pytest.fixture
def mongo_client():
    client = MagicMock()
    session = AsyncMock()
    client.start_session.return_value = session
    session.start_transaction = AsyncMock()
    session.commit_transaction = AsyncMock()
    session.abort_transaction = AsyncMock()
    session.end_session = AsyncMock()
    return client


@pytest.fixture
def service(order_repo, menu_repo, publisher, mongo_client):
    return OrderService(
        order_repo=order_repo,
        menu_repo=menu_repo,
        publisher=publisher,
        mongo_client=mongo_client,
    )


def _make_order(**overrides):
    return OrderSchema(
        person=overrides.get(
            "person",
            OrderingPersonSchema(
                first_name="John", last_name="Doe", address="123 Main St", phone_number="555-1234"
            ),
        ),
        items=overrides.get(
            "items", [OrderedItemSchema(item_id="507f1f77bcf86cd799439011", quantity=2)]
        ),
    )


@pytest.mark.asyncio
async def test_create_order_success(service, menu_repo, order_repo, publisher):
    menu_item = MenuItemSchema(
        name="Burger", price=9.99, category="food", stock=10, id="507f1f77bcf86cd799439011"
    )
    menu_repo.get_by_id.return_value = menu_item
    menu_repo.decrement_stock.return_value = True
    order_repo.create.return_value = "order123"

    order = _make_order()
    result = await service.create_order_with_stock_check(order)

    assert result.success is True
    assert order.total_price == Decimal("19.98")
    assert order.id == "order123"
    publisher.publish_raw.assert_called()


@pytest.mark.asyncio
async def test_create_order_item_not_found(service, menu_repo):
    menu_repo.get_by_id.return_value = None

    order = _make_order()
    result = await service.create_order_with_stock_check(order)

    assert result.success is False
    assert "not found" in result.message


@pytest.mark.asyncio
async def test_create_order_insufficient_stock(service, menu_repo):
    menu_item = MenuItemSchema(
        name="Burger", price=9.99, category="food", stock=1, id="507f1f77bcf86cd799439011"
    )
    menu_repo.get_by_id.return_value = menu_item
    menu_repo.decrement_stock.return_value = False

    order = _make_order()
    result = await service.create_order_with_stock_check(order)

    assert result.success is False
    assert "stock" in result.message.lower()


@pytest.mark.asyncio
async def test_handle_status_update(service, order_repo, publisher):
    order_repo.update_status.return_value = True
    msg = SimpleNamespace(id="order123", status="preparing")

    await service.handle_status_update(msg)

    publisher.publish_raw.assert_called_once()
    call_kwargs = publisher.publish_raw.call_args
    assert call_kwargs.kwargs["event_type"] == "order.status_updated"
    assert call_kwargs.kwargs["correlation_id"] == "order123"
