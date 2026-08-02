from unittest.mock import AsyncMock

import pytest

from shared.db.outbox import OutboxRelay


def _doc(doc_id: str = "1", event_id: str = "e1") -> dict:
    return {
        "_id": doc_id,
        "stream": "orders-stream",
        "event_type": "order.created.v1",
        "event_id": event_id,
        "correlation_id": "order123",
        "payload": {"id": "order123", "status": "confirmed", "event_id": event_id},
    }


@pytest.fixture
def outbox():
    box = AsyncMock()
    box.unpublished.return_value = []
    return box


@pytest.fixture
def producer():
    return AsyncMock()


@pytest.mark.asyncio
async def test_sweep_publishes_then_marks(outbox, producer):
    outbox.unpublished.return_value = [_doc()]
    relay = OutboxRelay(outbox=outbox, producer=producer)

    assert await relay.sweep() == 1

    producer.publish_raw.assert_awaited_once()
    assert producer.publish_raw.await_args.args[0] == "orders-stream"
    assert producer.publish_raw.await_args.kwargs["event_type"] == "order.created.v1"
    outbox.mark_published.assert_awaited_once_with("1")


@pytest.mark.asyncio
async def test_failed_publish_is_not_marked(outbox, producer):
    """A row stays unpublished so the next sweep retries it."""
    outbox.unpublished.return_value = [_doc()]
    producer.publish_raw.side_effect = ConnectionError("redis is down")
    relay = OutboxRelay(outbox=outbox, producer=producer)

    with pytest.raises(ConnectionError):
        await relay.sweep()

    outbox.mark_published.assert_not_awaited()


@pytest.mark.asyncio
async def test_republish_keeps_the_original_event_id(outbox, producer):
    """Consumer inboxes collapse the duplicate only if the id is stable."""
    outbox.unpublished.return_value = [_doc(event_id="stable-id")]
    relay = OutboxRelay(outbox=outbox, producer=producer)

    await relay.sweep()
    await relay.sweep()

    ids = [call.args[1]["event_id"] for call in producer.publish_raw.await_args_list]
    assert ids == ["stable-id", "stable-id"]


@pytest.mark.asyncio
async def test_sweep_is_a_noop_when_nothing_is_staged(outbox, producer):
    relay = OutboxRelay(outbox=outbox, producer=producer)

    assert await relay.sweep() == 0
    producer.publish_raw.assert_not_awaited()
