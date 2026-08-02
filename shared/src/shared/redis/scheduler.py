import asyncio
import json
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any

from redis.asyncio import Redis

# Pops only timers whose due time has passed, and only if this consumer wins the
# ZREM race. Atomic, so two replicas never fire the same timer.
_CLAIM_DUE = """
local due = redis.call('ZRANGEBYSCORE', KEYS[1], '-inf', ARGV[1], 'LIMIT', 0, tonumber(ARGV[2]))
if #due > 0 then
  redis.call('ZREM', KEYS[1], unpack(due))
end
return due
"""

_POLL_INTERVAL_SECONDS = 1.0
_CLAIM_BATCH = 50


class RedisScheduler:
    """Durable timers backed by a sorted set.

    An `asyncio.sleep` lives only in the process that started it, so a restart
    mid-simulation strands the order forever. A timer here survives restarts:
    whichever replica is running when it comes due fires it.
    """

    def __init__(self, redis: Redis, *, key: str = "scheduled-timers") -> None:
        self._redis = redis
        self._key = key
        self._claim = redis.register_script(_CLAIM_DUE)

    async def schedule(self, payload: dict[str, Any], *, delay_seconds: float) -> None:
        due_at = time.time() + delay_seconds
        # The payload is the member, so scheduling the same step twice is
        # naturally collapsed by the sorted set.
        await self._redis.zadd(self._key, {json.dumps(payload, sort_keys=True): due_at})
        logging.info("Scheduled %s in %.1fs", payload, delay_seconds)

    async def due(self) -> list[dict[str, Any]]:
        claimed = await self._claim(keys=[self._key], args=[time.time(), _CLAIM_BATCH])
        return [json.loads(item) for item in claimed]

    async def run(self, handler: Callable[[dict[str, Any]], Awaitable[None]]) -> None:
        logging.info("Scheduler polling `%s`", self._key)
        while True:
            for payload in await self.due():
                try:
                    await handler(payload)
                except Exception:
                    logging.exception("Scheduled handler failed for %s", payload)
            await asyncio.sleep(_POLL_INTERVAL_SECONDS)
