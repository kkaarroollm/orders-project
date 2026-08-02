"""Dedup against a real MongoDB replica set.

Mocks cannot prove this: the guarantee comes from a unique index aborting a
real transaction. Requires `INTEGRATION_MONGO_URL` (see the CI integration job).
"""

import os
from unittest.mock import AsyncMock

import pytest
from pymongo import AsyncMongoClient
from shared.db.inbox import MongoInbox
from shared.events.order import OrderStatusChanged

from src.repository import DeliveryRepository
from src.service import DeliveryService

MONGO_URL = os.environ.get("INTEGRATION_MONGO_URL")

pytestmark = pytest.mark.skipif(not MONGO_URL, reason="INTEGRATION_MONGO_URL not set")


@pytest.fixture
async def database():
    client: AsyncMongoClient = AsyncMongoClient(MONGO_URL)
    db = client["delivery-integration-test"]
    await db["deliveries"].delete_many({})
    await db["processed_events"].delete_many({})
    yield db
    await client.close()


@pytest.fixture
async def service(database):
    repo = DeliveryRepository(collection=database["deliveries"])
    await repo.ensure_indexes()

    inbox = MongoInbox(collection=database["processed_events"])
    await inbox.ensure_indexes()

    return DeliveryService(
        repo=repo,
        publisher=AsyncMock(),
        inbox=inbox,
        mongo_client=database.client,
    )


@pytest.mark.asyncio
async def test_same_event_delivered_twice_creates_one_delivery(service, database):
    event = OrderStatusChanged(id="order123", status="out_for_delivery")

    await service.handle_order(event)
    await service.handle_order(event)  # XAUTOCLAIM redelivery

    assert await database["deliveries"].count_documents({"order_id": "order123"}) == 1


@pytest.mark.asyncio
async def test_distinct_events_each_create_a_delivery(service, database):
    await service.handle_order(OrderStatusChanged(id="order123", status="out_for_delivery"))
    await service.handle_order(OrderStatusChanged(id="order456", status="out_for_delivery"))

    assert await database["deliveries"].count_documents({}) == 2


@pytest.mark.asyncio
async def test_duplicate_leaves_no_partial_write(service, database):
    """The aborted transaction must not leave an inbox row without a delivery."""
    event = OrderStatusChanged(id="order123", status="out_for_delivery")
    await service.handle_order(event)
    await service.handle_order(event)

    assert await database["processed_events"].count_documents({"event_id": event.event_id}) == 1
    assert await database["deliveries"].count_documents({}) == 1
