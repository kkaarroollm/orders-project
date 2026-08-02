import asyncio
from typing import Any
from unittest.mock import AsyncMock

import pytest

from shared.events.order import OrderStatusSimulated
from shared.redis.event_bus import EventBus


@pytest.fixture
def redis():
    client = AsyncMock()

    # Stand in for XREADGROUP's BLOCK: a mock that returns instantly would make
    # listen() spin without ever yielding, so cancellation could never land.
    async def blocking_read(**_: Any) -> list[Any]:
        await asyncio.sleep(0.01)
        return []

    client.xreadgroup.side_effect = blocking_read
    return client


async def _settle() -> None:
    await asyncio.sleep(0.05)


@pytest.mark.asyncio
async def test_bus_starts_healthy(redis):
    bus = EventBus(redis, group="test-group", on_consumer_failure=None)
    assert bus.healthy is True


@pytest.mark.asyncio
async def test_dead_consumer_marks_bus_unhealthy(redis):
    """A consumer that dies must be visible to the readiness probe."""
    failures: list[tuple[str, BaseException]] = []
    bus = EventBus(redis, group="test-group", on_consumer_failure=lambda g, e: failures.append((g, e)))
    redis.xgroup_create.side_effect = RuntimeError("redis is gone")

    bus.subscribe(OrderStatusSimulated, AsyncMock())
    await bus.start()
    await _settle()

    assert bus.healthy is False
    assert failures[0][0] == "test-group"
    assert str(failures[0][1]) == "redis is gone"


@pytest.mark.asyncio
async def test_stop_does_not_report_failure(redis):
    """Cancellation during shutdown is expected, not a consumer death."""
    failures: list[tuple[str, BaseException]] = []
    bus = EventBus(redis, group="test-group", on_consumer_failure=lambda g, e: failures.append((g, e)))

    bus.subscribe(OrderStatusSimulated, AsyncMock())
    await bus.start()
    await _settle()
    await asyncio.wait_for(bus.stop(), timeout=5)

    assert failures == []
    assert bus.healthy is True
