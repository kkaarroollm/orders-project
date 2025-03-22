import asyncio
import json
import logging
from typing import Any, Awaitable, Callable

from redis import exceptions as redis_exc
from redis.asyncio import Redis

from src.interfaces import IRedisStreamConsumer


class RedisStreamConsumer(IRedisStreamConsumer):
    def __init__(self, *, redis: Redis, stream: str, group: str, consumer_name: str):
        self._redis = redis
        self._stream = stream
        self._group = group
        self._consumer_name = consumer_name

    async def bind_group(self) -> None:
        try:
            await self._redis.xgroup_create(name=self._stream, groupname=self._group, id="0", mkstream=True)
            logging.info(f"Bound group `{self._group}` to stream `{self._stream}`")
        except redis_exc.ResponseError as e:
            logging.info(f"Binding group `{self._group}` to stream `{self._stream}`: {e}")

    async def listen(self, handler: Callable[[dict], Awaitable[None]]) -> None:
        await self.bind_group()
        logging.info(f"Listening to `{self._stream}` as consumer `{self._consumer_name}` in group `{self._group}`")

        while True:
            if not (messages := await self._read_messages()):
                await asyncio.sleep(1)
                continue

            for _, entries in messages:
                for message_id, message_data in entries:
                    try:
                        payload = json.loads(message_data["data"])
                        await handler(payload)
                        await self._redis.xack(self._stream, self._group, message_id)
                        logging.debug(
                            f"ACKed message({message_id}) from a group({self._group}) in a stream({self._stream})"
                        )
                    except Exception as e:
                        logging.error(
                            f"Error message({message_id}) from a group({self._group}) in a stream({self._stream}): {e}"
                        )

    async def _read_messages(self, count: int = 10, block: int = 5000) -> Any:
        """Read a batch of messages from the stream."""
        try:
            return await self._redis.xreadgroup(
                groupname=self._group,
                consumername=self._consumer_name,
                streams={self._stream: ">"},
                count=count,
                block=block,
            )
        except redis_exc.ResponseError as e:
            logging.error(f"RedisStreamConsumer._read_messages(): Error reading messages: {e}")
            return []
