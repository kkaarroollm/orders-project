from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError
from shared.events.order import OrderStatusSimulated

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
def outbox():
    return AsyncMock()


@pytest.fixture
def idempotency():
    store = AsyncMock()
    store.find.return_value = None
    return store


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
def service(order_repo, menu_repo, outbox, idempotency, mongo_client):
    return OrderService(
        order_repo=order_repo,
        menu_repo=menu_repo,
        outbox=outbox,
        idempotency=idempotency,
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
        simulation=overrides.get("simulation", 1),
    )


@pytest.mark.asyncio
async def test_create_order_success(service, menu_repo, order_repo, outbox):
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

    staged = [call.args[0] for call in outbox.add.call_args_list]
    assert [type(event).__name__ for event in staged] == ["OrderCreated", "OrderSimulationRequested"]
    assert staged[0].event_type == "order.created.v1"
    # Staged inside the transaction, not published after it.
    session = service._mongo_client.start_session.return_value
    assert all(call.args[1] is session for call in outbox.add.call_args_list)


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
async def test_rejected_order_aborts_transaction(service, menu_repo, order_repo, mongo_client):
    """A later item failing must roll back the stock already decremented for earlier items."""
    in_stock = MenuItemSchema(name="Burger", price=9.99, category="food", stock=5, id="507f1f77bcf86cd799439011")
    sold_out = MenuItemSchema(name="Fries", price=3.50, category="food", stock=0, id="507f1f77bcf86cd799439012")
    menu_repo.get_by_id.side_effect = [in_stock, sold_out]
    menu_repo.decrement_stock.side_effect = [True, False]

    order = _make_order(
        items=[
            OrderedItemSchema(item_id="507f1f77bcf86cd799439011", quantity=1),
            OrderedItemSchema(item_id="507f1f77bcf86cd799439012", quantity=1),
        ]
    )
    result = await service.create_order_with_stock_check(order)

    session = mongo_client.start_session.return_value
    assert result.success is False
    session.abort_transaction.assert_awaited_once()
    session.commit_transaction.assert_not_awaited()
    order_repo.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_missing_item_aborts_transaction(service, menu_repo, mongo_client):
    menu_repo.get_by_id.return_value = None

    await service.create_order_with_stock_check(_make_order())

    session = mongo_client.start_session.return_value
    session.abort_transaction.assert_awaited_once()
    session.commit_transaction.assert_not_awaited()


@pytest.mark.asyncio
async def test_created_at_is_timezone_aware():
    assert _make_order().created_at.tzinfo is not None


@pytest.mark.parametrize("simulation", [-2, 2, 10_000])
def test_out_of_range_simulation_rejected(simulation):
    """`simulation` is client-supplied and drives server-side scheduling."""
    with pytest.raises(ValidationError):
        OrderSchema(
            person=OrderingPersonSchema(
                first_name="John", last_name="Doe", address="123 Main St", phone_number="555-1234"
            ),
            items=[OrderedItemSchema(item_id="507f1f77bcf86cd799439011", quantity=1)],
            simulation=simulation,
        )


@pytest.mark.asyncio
async def test_status_event_carries_the_orders_own_simulation_flag(service, order_repo, outbox):
    """`simulation: -1` must reach delivery, which decides whether to simulate.

    It used to fall back to the event model's default of 1, so an order that
    asked for no simulation got its delivery simulated anyway.
    """
    order_repo.advance_status.return_value = _make_order(simulation=-1)

    await service.handle_status_update(OrderStatusSimulated(id="order123", status="out_for_delivery"))

    assert outbox.add.call_args.args[0].simulation == -1


@pytest.mark.asyncio
async def test_illegal_transition_stages_no_event(service, order_repo, outbox):
    """Replayed or out-of-order transitions match nothing and are dropped."""
    order_repo.advance_status.return_value = None

    await service.handle_status_update(OrderStatusSimulated(id="order123", status="preparing"))

    outbox.add.assert_not_called()


@pytest.mark.asyncio
async def test_handle_status_update(service, order_repo, outbox):
    order_repo.advance_status.return_value = _make_order()

    await service.handle_status_update(OrderStatusSimulated(id="order123", status="preparing"))

    outbox.add.assert_called_once()
    event = outbox.add.call_args.args[0]
    assert event.event_type == "order.status_updated.v1"
    assert event.status == "preparing"
    assert outbox.add.call_args.kwargs["correlation_id"] == "order123"
