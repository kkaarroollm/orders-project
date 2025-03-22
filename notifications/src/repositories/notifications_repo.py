from typing import Any

from redis.asyncio import Redis

from src.interfaces import INotificationRepository


class NotificationRepository(INotificationRepository):
    def __init__(self, redis_client: Redis):
        self._redis = redis_client

    async def set_order_status(self, order_id: str, message: dict, expire: int = 86400) -> None:
        key = f"order:{order_id}:status"
        await self._redis.hset(key, mapping=message)  # type: ignore[misc]
        await self._redis.expire(key, expire)

    async def get_order_status(self, order_id: str) -> dict[str, Any]:
        key = f"order:{order_id}:status"
        return dict(await self._redis.hgetall(key))  # type: ignore[misc]
