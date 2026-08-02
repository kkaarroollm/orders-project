"""Durable timers against a real Redis.

The atomic claim is a Lua script racing two consumers; a mock proves nothing
about it. Requires `INTEGRATION_REDIS_URL`.
"""

import asyncio
import os

import pytest
from redis.asyncio import Redis

from shared.redis.scheduler import RedisScheduler

REDIS_URL = os.environ.get("INTEGRATION_REDIS_URL", "")

pytestmark = pytest.mark.skipif(not REDIS_URL, reason="INTEGRATION_REDIS_URL not set")


@pytest.fixture
async def redis():
    client: Redis = Redis.from_url(REDIS_URL, decode_responses=True)
    await client.delete("test-timers")
    yield client
    await client.delete("test-timers")
    await client.aclose()


@pytest.fixture
def scheduler(redis):
    return RedisScheduler(redis, key="test-timers")


@pytest.mark.asyncio
async def test_timer_is_not_due_before_its_delay(scheduler):
    await scheduler.schedule({"entity_id": "order123", "step": 0}, delay_seconds=60)

    assert await scheduler.due() == []


@pytest.mark.asyncio
async def test_timer_fires_once_due(scheduler):
    await scheduler.schedule({"entity_id": "order123", "step": 0}, delay_seconds=0)

    due = await scheduler.due()

    assert [item["entity_id"] for item in due] == ["order123"]


@pytest.mark.asyncio
async def test_a_claimed_timer_is_not_returned_again(scheduler):
    """Claiming removes it, so a second poll finds nothing."""
    await scheduler.schedule({"entity_id": "order123", "step": 0}, delay_seconds=0)

    assert len(await scheduler.due()) == 1
    assert await scheduler.due() == []


@pytest.mark.asyncio
async def test_concurrent_consumers_each_get_a_timer_once(redis):
    """Two replicas polling together must not both fire the same timer."""
    first = RedisScheduler(redis, key="test-timers")
    second = RedisScheduler(redis, key="test-timers")
    for index in range(10):
        await first.schedule({"entity_id": f"order{index}", "step": 0}, delay_seconds=0)

    claimed = await asyncio.gather(first.due(), second.due())

    entity_ids = [item["entity_id"] for batch in claimed for item in batch]
    assert sorted(entity_ids) == sorted(f"order{index}" for index in range(10))
    assert len(entity_ids) == len(set(entity_ids))


@pytest.mark.asyncio
async def test_timers_survive_a_new_scheduler_instance(redis):
    """A restart must resume pending simulations rather than strand them."""
    await RedisScheduler(redis, key="test-timers").schedule({"entity_id": "order123"}, delay_seconds=0)

    restarted = RedisScheduler(redis, key="test-timers")

    assert len(await restarted.due()) == 1
