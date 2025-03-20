import json
import logging

from redis.asyncio import Redis

from src.schemas import CacheSchema
from src.websockets import ws_order_status_manager


class NotificationRepository:
    def __init__(self, redis_client: Redis):
        self._redis = redis_client

    async def set_order_status(self, order_id: str, message: dict, *, expire: int = 86400) -> None:
        key = f"order:{order_id}:status"
        await self._redis.hset(key, mapping=message)
        await self._redis.expire(key, expire)


    async def get_order_status(self, order_id: str) -> dict:
        key = f"order:{order_id}:status"
        return await self._redis.hgetall(key)

    async def subscribe_to_events(self, *channels: str) -> None:
        pubsub = self._redis.pubsub()
        await pubsub.subscribe(*channels)

        async for message in pubsub.listen():
            if message["type"] == "message":
                event_data = json.loads(message["data"])
                order_id = event_data.get("order_id") or event_data.get("id")
                cache_data = CacheSchema(order_id=order_id, status=event_data.get("status")).model_dump(mode="json")
                logging.info(f"📡 Received update for order {order_id}: {event_data.get("status")}")
                await ws_order_status_manager.broadcast(order_id, cache_data)
                await self.set_order_status(order_id, cache_data)
