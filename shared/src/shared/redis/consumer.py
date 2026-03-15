import asyncio
import json
import logging
from typing import Any, Awaitable, Callable, Generic, TypeVar

from pydantic import BaseModel
from redis import exceptions as redis_exc
from redis.asyncio import Redis

TMessage = TypeVar("TMessage", bound=BaseModel)


class StreamConsumer(Generic[TMessage]):
    def __init__(
        self,
        *,
        redis: Redis,
        stream: str,
        group: str,
        consumer_name: str,
        message_type: type[TMessage],
    ) -> None:
        self._redis = redis
        self._stream = stream
        self._group = group
        self._consumer_name = consumer_name
        self._message_type = message_type

    async def bind_group(self) -> None:
        try:
            await self._redis.xgroup_create(
                name=self._stream, groupname=self._group, id="0", mkstream=True
            )
            logging.info("Bound group `%s` to stream `%s`", self._group, self._stream)
        except redis_exc.ResponseError as e:
            logging.info("Binding group `%s` to stream `%s`: %s", self._group, self._stream, e)

    async def listen(self, handler: Callable[[TMessage], Awaitable[None]]) -> None:
        await self.bind_group()
        logging.info(
            "Listening to `%s` as consumer `%s` in group `%s`",
            self._stream,
            self._consumer_name,
            self._group,
        )

        while True:
            if not (messages := await self._read_messages()):
                await asyncio.sleep(1)
                continue

            for _, entries in messages:
                for message_id, message_data in entries:
                    try:
                        raw = json.loads(message_data["data"])
                        payload = self._message_type.model_validate(raw)
                        logging.info("Received `%s` with data: %s", message_id, raw)
                        await handler(payload)
                        await self._redis.xack(self._stream, self._group, message_id)
                        logging.info(
                            "ACKed message(%s) from group(%s) in stream(%s)",
                            message_id,
                            self._group,
                            self._stream,
                        )
                    except Exception as e:
                        logging.error(
                            "Error message(%s) from group(%s) in stream(%s): %s",
                            message_id,
                            self._group,
                            self._stream,
                            e,
                        )

    async def _read_messages(self, count: int = 10, block: int = 5000) -> Any:
        try:
            return await self._redis.xreadgroup(
                groupname=self._group,
                consumername=self._consumer_name,
                streams={self._stream: ">"},
                count=count,
                block=block,
            )
        except redis_exc.ResponseError as e:
            logging.error("StreamConsumer._read_messages(): Error reading messages: %s", e)
            return []
