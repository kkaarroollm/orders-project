import json
import logging

from redis.asyncio import Redis

from src.interfaces import IRedisStreamPublisher


class RedisStreamPublisher(IRedisStreamPublisher):
    def __init__(self, redis: Redis):
        self._redis = redis

    async def publish(self, stream: str, data: dict) -> None:
        try:
            await self._redis.xadd(stream, {"data": json.dumps(data)})
            logging.info(f"Published to stream `{stream}`: {data}")
        except Exception as e:
            logging.error(f"Failed to publish to Redis stream `{stream}`: {e}")
