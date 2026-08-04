import json
import logging

from redis.asyncio import Redis

from src.schemas import MenuItemSchema

_KEY = "menu:items"
# Short enough that the stock-refill CronJob, which writes MongoDB directly and
# emits no event, cannot leave the menu stale for long.
_TTL_SECONDS = 30


class MenuCache:
    """Caches the menu list, which is read on every page load and rarely changes."""

    def __init__(self, redis: Redis, ttl_seconds: int = _TTL_SECONDS) -> None:
        self._redis = redis
        self._ttl = ttl_seconds

    async def get(self) -> list[MenuItemSchema] | None:
        cached = await self._redis.get(_KEY)
        if not cached:
            return None
        return [MenuItemSchema.model_validate(item) for item in json.loads(cached)]

    async def set(self, items: list[MenuItemSchema]) -> None:
        payload = json.dumps([item.model_dump(mode="json") for item in items])
        await self._redis.set(_KEY, payload, ex=self._ttl)

    async def invalidate(self) -> None:
        """Drop the cache after stock moves, so the menu never shows sold-out items."""
        await self._redis.delete(_KEY)
        logging.debug("Menu cache invalidated")
