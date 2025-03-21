import asyncio
import json
import logging
from typing import Any, AsyncGenerator

from redis.asyncio import Redis

from src.schemas import CacheSchema
from src.websockets import ws_order_status_manager


class NotificationRepository:
    def __init__(self, redis_client: Redis):
        self._redis = redis_client

    async def set_order_status(self, order_id: str, message: dict, *, expire: int = 86400) -> None:
        key = f"order:{order_id}:status"
        await self._redis.hset(key, mapping=message)  # type: ignore[misc]
        await self._redis.expire(key, expire)

    async def get_order_status(self, order_id: str) -> dict[str, Any]:
        key = f"order:{order_id}:status"
        result = await self._redis.hgetall(key)  # type: ignore[misc]
        return dict(result)

    async def get_last_stream_id(self, stream_name: str) -> str:
        return await self._redis.get(f"last_id:{stream_name}") or "0-0"

    async def read_streams(
        self, *stream_names: str, block: int = 5000, count: int = 10
    ) -> AsyncGenerator[tuple[str, str, dict], None]:
        last_ids = {stream: (await self.get_last_stream_id(stream)) for stream in stream_names}

        while True:
            try:
                if not (streams := await self._redis.xread(last_ids, block=block, count=count)):  # type: ignore
                    await asyncio.sleep(1)
                    continue

                for stream, messages in streams:
                    for message_id, message_data in messages:
                        yield stream, message_id, message_data

                        await self._redis.set(f"last_id:{stream}", message_id)
                        logging.info(f"🗑️ Deleted processed message {message_id} from {stream}")

            except Exception as e:
                logging.error(f"Error reading Redis streams {stream_names}: {e}")
                await asyncio.sleep(1)

    async def subscribe_to_events(self, *stream_names: str) -> None:
        async for stream, message_id, message_data in self.read_streams(*stream_names):
            try:
                event_data = json.loads(message_data["data"])
                order_id = event_data.get("order_id") or event_data.get("id")
                cache_data = CacheSchema(order_id=order_id, status=event_data.get("status")).model_dump(mode="json")
                logging.info(f"📡 Received update for order {order_id}: {event_data.get('status')}")
                await ws_order_status_manager.broadcast(order_id, cache_data)
                await self.set_order_status(order_id, cache_data)
            except Exception as e:
                logging.error(f"🚨 Error processing event from {stream}: {message_data}, error: {e}")
                continue
