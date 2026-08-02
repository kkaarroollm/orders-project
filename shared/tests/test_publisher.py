import json
from unittest.mock import AsyncMock

import pytest

from shared.redis.publisher import StreamProducer


@pytest.fixture
def redis():
    return AsyncMock()


@pytest.mark.asyncio
async def test_publish_failure_propagates(redis):
    """A dropped event must not be reported as a successful publish."""
    redis.xadd.side_effect = ConnectionError("redis is down")
    producer: StreamProducer = StreamProducer(redis, source="test")

    with pytest.raises(ConnectionError):
        await producer.publish_raw("orders-stream", {"id": "order123"}, event_type="order.created")


@pytest.mark.asyncio
async def test_publish_trims_stream(redis):
    producer: StreamProducer = StreamProducer(redis, source="test", maxlen=1000)

    await producer.publish_raw("orders-stream", {"id": "order123"}, event_type="order.created")

    kwargs = redis.xadd.call_args.kwargs
    assert kwargs["maxlen"] == 1000
    assert kwargs["approximate"] is True


@pytest.mark.asyncio
async def test_publish_wraps_payload_in_envelope(redis):
    producer: StreamProducer = StreamProducer(redis, source="orders-service")

    await producer.publish_raw("orders-stream", {"id": "order123"}, event_type="order.created")

    envelope = json.loads(redis.xadd.call_args.args[1]["data"])
    assert envelope["event_type"] == "order.created"
    assert envelope["correlation_id"] == "order123"
    assert envelope["source"] == "orders-service"
    assert envelope["payload"] == {"id": "order123"}
