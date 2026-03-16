import json
import logging
import time
from typing import Any, Awaitable, Callable, Generic, TypeVar

from pydantic import BaseModel
from redis import exceptions as redis_exc
from redis.asyncio import Redis

from shared.redis.envelope import MessageEnvelope
from shared.redis.metrics import STREAM_DLQ_TOTAL, STREAM_MESSAGE_DURATION, STREAM_MESSAGES_TOTAL

TMessage = TypeVar("TMessage", bound=BaseModel)

_PENDING_CLAIM_INTERVAL = 30_000  # ms — claim messages idle longer than this
_PENDING_CLAIM_BATCH = 50


class StreamConsumer(Generic[TMessage]):
    def __init__(
        self,
        *,
        redis: Redis,
        stream: str,
        group: str,
        consumer_name: str,
        message_type: type[TMessage],
        max_retries: int = 3,
        dlq_stream: str | None = "dead-letters",
    ) -> None:
        self._redis = redis
        self._stream = stream
        self._group = group
        self._consumer_name = consumer_name
        self._message_type = message_type
        self._max_retries = max_retries
        self._dlq_stream = dlq_stream
        self._claim_cursor: str = "0-0"

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

        claim_counter = 0
        while True:
            # Periodically reclaim orphaned pending messages
            claim_counter += 1
            if claim_counter % 6 == 0:  # every ~30s (6 * 5s block)
                await self._claim_pending(handler)

            if not (messages := await self._read_messages()):
                continue

            for _, entries in messages:
                for message_id, message_data in entries:
                    await self._process_message(message_id, message_data, handler)

    async def _process_message(
        self,
        message_id: bytes | str,
        message_data: dict[str, Any],
        handler: Callable[[TMessage], Awaitable[None]],
    ) -> None:
        raw_json = message_data.get("data", "{}")
        try:
            raw = json.loads(raw_json)

            # Support envelope format: unwrap payload if present
            if "payload" in raw and "event_type" in raw:
                envelope = MessageEnvelope.model_validate(raw)
                payload_data = envelope.payload
                correlation_id = envelope.correlation_id
                logging.info(
                    "[%s] Received `%s` event=%s correlation=%s",
                    self._stream,
                    message_id,
                    envelope.event_type,
                    correlation_id,
                )
            else:
                payload_data = raw
                correlation_id = raw.get("id", "")

            payload = self._message_type.model_validate(payload_data)
            start = time.monotonic()
            await handler(payload)
            duration = time.monotonic() - start

            await self._redis.xack(self._stream, self._group, message_id)
            STREAM_MESSAGES_TOTAL.labels(stream=self._stream, group=self._group, status="success").inc()
            STREAM_MESSAGE_DURATION.labels(stream=self._stream, group=self._group).observe(duration)
            logging.info(
                "ACKed %s from %s/%s (%.1fms, correlation=%s)",
                message_id,
                self._group,
                self._stream,
                duration * 1000,
                correlation_id,
            )
        except Exception as e:
            STREAM_MESSAGES_TOTAL.labels(stream=self._stream, group=self._group, status="error").inc()
            await self._handle_failure(message_id, message_data, e)

    async def _handle_failure(
        self,
        message_id: bytes | str,
        message_data: dict[str, Any],
        error: Exception,
    ) -> None:
        retry_key = f"{self._stream}:retries:{message_id}"
        retries = await self._redis.incr(retry_key)
        await self._redis.expire(retry_key, 3600)  # cleanup after 1h

        if retries >= self._max_retries:
            logging.error(
                "Message %s in %s/%s failed %d times, sending to DLQ: %s",
                message_id,
                self._group,
                self._stream,
                retries,
                error,
            )
            if self._dlq_stream:
                await self._send_to_dlq(message_id, message_data, str(error), retries)

            await self._redis.xack(self._stream, self._group, message_id)
            await self._redis.delete(retry_key)
        else:
            logging.warning(
                "Message %s in %s/%s failed (attempt %d/%d): %s",
                message_id,
                self._group,
                self._stream,
                retries,
                self._max_retries,
                error,
            )
            # Don't ack — message stays pending and will be reclaimed

    async def _send_to_dlq(
        self,
        message_id: bytes | str,
        message_data: dict[str, Any],
        error: str,
        retries: int,
    ) -> None:
        try:
            dlq_entry = json.dumps({
                "original_stream": self._stream,
                "original_group": self._group,
                "original_message_id": str(message_id),
                "data": message_data.get("data", ""),
                "error": error,
                "retries": retries,
                "timestamp": time.time(),
            })
            await self._redis.xadd(self._dlq_stream, {"data": dlq_entry})  # type: ignore[arg-type]
            STREAM_DLQ_TOTAL.labels(stream=self._stream, group=self._group).inc()
        except Exception as dlq_error:
            logging.error("Failed to send message to DLQ: %s", dlq_error)

    async def _claim_pending(self, handler: Callable[[TMessage], Awaitable[None]]) -> None:
        """Claim messages that have been pending too long (crashed consumers)."""
        try:
            claimed = await self._redis.xautoclaim(
                name=self._stream,
                groupname=self._group,
                consumername=self._consumer_name,
                min_idle_time=_PENDING_CLAIM_INTERVAL,
                start_id=self._claim_cursor,
                count=_PENDING_CLAIM_BATCH,
            )
            # xautoclaim returns (next_start_id, claimed_messages, deleted_ids)
            if claimed and len(claimed) > 1:
                self._claim_cursor = claimed[0] if claimed[0] != "0-0" else "0-0"
                messages = claimed[1]
                if messages:
                    logging.info("Claimed %d pending messages from %s", len(messages), self._stream)
                    for message_id, message_data in messages:
                        await self._process_message(message_id, message_data, handler)
        except redis_exc.ResponseError as e:
            logging.debug("xautoclaim not available or failed: %s", e)

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
