"""Outbox atomicity against a real MongoDB replica set.

The guarantee is that the event is part of the order's transaction, which only
a real transaction can demonstrate. Requires `INTEGRATION_MONGO_URL`.
"""

import os
from unittest.mock import AsyncMock

import pytest
from pymongo import AsyncMongoClient
from shared.db.idempotency import IdempotencyStore
from shared.db.outbox import MongoOutbox, OutboxRelay

from src.repositories.menu_item_repo import MenuItemRepository
from src.repositories.order_repository import OrderRepository
from src.schemas import OrderedItemSchema, OrderingPersonSchema, OrderSchema, OrderStatus
from src.services.order_service import OrderService

MONGO_URL = os.environ.get("INTEGRATION_MONGO_URL")

pytestmark = pytest.mark.skipif(not MONGO_URL, reason="INTEGRATION_MONGO_URL not set")


@pytest.fixture
async def database():
    client: AsyncMongoClient = AsyncMongoClient(MONGO_URL)
    db = client["orders-integration-test"]
    for name in ("orders", "outbox", "menu_items", "idempotency_keys"):
        await db[name].delete_many({})
    yield db
    await client.close()


@pytest.fixture
async def menu_item_id(database):
    result = await database["menu_items"].insert_one(
        {"name": "Burger", "price": 10.0, "category": "food", "stock": 5}
    )
    return str(result.inserted_id)


@pytest.fixture
async def outbox(database):
    box = MongoOutbox(collection=database["outbox"])
    await box.ensure_indexes()
    return box


@pytest.fixture
async def idempotency(database):
    store = IdempotencyStore(collection=database["idempotency_keys"])
    await store.ensure_indexes()
    return store


@pytest.fixture
async def service(database, outbox, idempotency):
    return OrderService(
        order_repo=OrderRepository(collection=database["orders"]),
        menu_repo=MenuItemRepository(collection=database["menu_items"]),
        outbox=outbox,
        idempotency=idempotency,
        mongo_client=database.client,
    )


def _order(item_id: str, quantity: int = 1) -> OrderSchema:
    return OrderSchema(
        person=OrderingPersonSchema(
            first_name="John", last_name="Doe", address="123 Main St", phone_number="555-1234"
        ),
        items=[OrderedItemSchema(item_id=item_id, quantity=quantity)],
    )


@pytest.mark.asyncio
async def test_order_and_event_commit_together(service, database, menu_item_id):
    result = await service.create_order_with_stock_check(_order(menu_item_id))

    assert result.success is True
    assert await database["orders"].count_documents({}) == 1
    # order.created + order.simulate
    assert await database["outbox"].count_documents({"published_at": None}) == 2


@pytest.mark.asyncio
async def test_rejected_order_stages_no_event(service, database, menu_item_id):
    """The event must roll back with the order it describes."""
    result = await service.create_order_with_stock_check(_order(menu_item_id, quantity=99))

    assert result.success is False
    assert await database["orders"].count_documents({}) == 0
    assert await database["outbox"].count_documents({}) == 0
    assert (await database["menu_items"].find_one({}))["stock"] == 5


@pytest.mark.asyncio
async def test_relay_publishes_events_staged_before_it_started(service, database, outbox, menu_item_id):
    """The crash-after-commit case: the process died before publishing."""
    await service.create_order_with_stock_check(_order(menu_item_id))

    producer = AsyncMock()
    relay = OutboxRelay(outbox=outbox, producer=producer)

    assert await relay.sweep() == 2
    assert producer.publish_raw.await_count == 2
    assert await database["outbox"].count_documents({"published_at": None}) == 0


@pytest.mark.asyncio
async def test_status_cannot_move_backwards(service, database, menu_item_id):
    """A replayed `preparing` must not undo `out_for_delivery`."""
    order_id = (await service.create_order_with_stock_check(_order(menu_item_id))).order.id

    assert (await service.update_order_status(order_id, OrderStatus.PREPARING)).success
    assert (await service.update_order_status(order_id, OrderStatus.OUT_FOR_DELIVERY)).success
    assert not (await service.update_order_status(order_id, OrderStatus.PREPARING)).success

    stored = await database["orders"].find_one({})
    assert stored["status"] == "out_for_delivery"
    assert stored["version"] == 2


@pytest.mark.asyncio
async def test_skipping_a_status_is_rejected(service, database, menu_item_id):
    """`confirmed` -> `out_for_delivery` skips a step and must not apply."""
    order_id = (await service.create_order_with_stock_check(_order(menu_item_id))).order.id

    assert not (await service.update_order_status(order_id, OrderStatus.OUT_FOR_DELIVERY)).success
    assert (await database["orders"].find_one({}))["status"] == "confirmed"


@pytest.mark.asyncio
async def test_retry_with_the_same_key_creates_one_order(service, database, menu_item_id):
    """A client that times out and retries must not order twice."""
    first = await service.create_order_with_stock_check(_order(menu_item_id), "key-abc")
    second = await service.create_order_with_stock_check(_order(menu_item_id), "key-abc")

    assert first.order.id == second.order.id
    assert await database["orders"].count_documents({}) == 1
    assert (await database["menu_items"].find_one({}))["stock"] == 4


@pytest.mark.asyncio
async def test_different_keys_create_different_orders(service, database, menu_item_id):
    await service.create_order_with_stock_check(_order(menu_item_id), "key-abc")
    await service.create_order_with_stock_check(_order(menu_item_id), "key-xyz")

    assert await database["orders"].count_documents({}) == 2


@pytest.mark.asyncio
async def test_rejected_order_does_not_burn_its_key(service, database, menu_item_id):
    """The reservation rolls back with the order, so the key stays usable."""
    rejected = await service.create_order_with_stock_check(_order(menu_item_id, quantity=99), "key-abc")
    assert rejected.success is False
    assert await database["idempotency_keys"].count_documents({}) == 0

    accepted = await service.create_order_with_stock_check(_order(menu_item_id), "key-abc")
    assert accepted.success is True


@pytest.mark.asyncio
async def test_relay_does_not_republish_after_marking(service, outbox, menu_item_id):
    await service.create_order_with_stock_check(_order(menu_item_id))
    relay = OutboxRelay(outbox=outbox, producer=AsyncMock())

    await relay.sweep()

    assert await relay.sweep() == 0
