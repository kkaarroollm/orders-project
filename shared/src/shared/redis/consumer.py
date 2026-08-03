import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Generic, TypeVar

from redis import exceptions as redis_exc
from redis.asyncio import Redis

from shared.events.base import DomainEvent
from shared.redis.envelope import MessageEnvelope
from shared.redis.metrics import STREAM_DLQ_TOTAL, STREAM_MESSAGE_DURATION, STREAM_MESSAGES_TOTAL
from shared.tracing import consumer_span

TEvent = TypeVar("TEvent", bound=DomainEvent)

_PENDING_CLAIM_INTERVAL = 30_000  # ms — claim messages idle longer than this
_PENDING_CLAIM_BATCH = 50
_DLQ_MAXLEN = 10_000


@dataclass
class Route(Generic[TEvent]):
    """Binds one wire event type to the model and handler that own it."""

    event: type[TEvent]
    handler: Callable[[TEvent], Awaitable[None]]


class StreamConsumer:
    """Reads one stream and dispatches each message by its envelope event type.

    A single stream carries several event types (`orders-stream` carries both
    `order.created` and `order.status_updated`), so routing happens per message
    rather than per stream.
    """

    def __init__(  # noqa: PLR0913 — keyword-only consumer configuration
        self,
        *,
        redis: Redis,
        stream: str,
        group: str,
        consumer_name: str,
        routes: dict[str, Route[Any]],
        max_retries: int = 3,
        dlq_stream: str | None = "dead-letters",
        start_id: str = "0",
        noack: bool = False,
        reset_on_bind: bool = False,
        claim_pending: bool = True,
    ) -> None:
        self._redis = redis
        self._stream = stream
        self._group = group
        self._consumer_name = consumer_name
        self._routes = routes
        self._max_retries = max_retries
        self._dlq_stream = dlq_stream
        self._start_id = start_id
        self._noack = noack
        self._reset_on_bind = reset_on_bind
        self._reclaim_pending = claim_pending
        self._claim_cursor: str = "0-0"

    async def bind_group(self) -> None:
        try:
            await self._redis.xgroup_create(
                name=self._stream, groupname=self._group, id=self._start_id, mkstream=True
            )
            logging.info("Bound group `%s` to stream `%s`", self._group, self._stream)
        except redis_exc.ResponseError as e:
            if self._reset_on_bind:
                # The group belongs to this process alone, so discarding
                # everything from before it started is safe -- and required, or
                # a restart would replay stale statuses to fresh clients.
                await self._redis.xgroup_setid(self._stream, self._group, id=self._start_id)
                logging.info("Reset group `%s` on `%s` to %s", self._group, self._stream, self._start_id)
            else:
                logging.info("Binding group `%s` to stream `%s`: %s", self._group, self._stream, e)

    async def listen(self) -> None:
        await self.bind_group()
        logging.info(
            "Listening to `%s` as consumer `%s` in group `%s` for events: %s",
            self._stream,
            self._consumer_name,
            self._group,
            ", ".join(sorted(self._routes)) or "<none>",
        )

        claim_counter = 0
        while True:
            # Periodically reclaim orphaned pending messages
            claim_counter += 1
            if self._reclaim_pending and claim_counter % 6 == 0:  # every ~30s (6 * 5s block)
                await self._claim_pending()

            if not (messages := await self._read_messages()):
                continue

            for _, entries in messages:
                for message_id, message_data in entries:
                    await self._process_message(message_id, message_data)

    async def _process_message(
        self,
        message_id: bytes | str,
        message_data: dict[str, Any],
    ) -> None:
        raw_json = message_data.get("data", "{}")
        try:
            envelope = MessageEnvelope.model_validate(json.loads(raw_json))
            correlation_id = envelope.correlation_id

            route = self._routes.get(envelope.event_type)
            if route is None:
                # Streams are shared, so events this group does not handle are
                # normal traffic -- ack and move on rather than filling the DLQ.
                await self._skip(message_id, envelope.event_type)
                return

            logging.info(
                "[%s] Received `%s` event=%s correlation=%s",
                self._stream,
                message_id,
                envelope.event_type,
                correlation_id,
            )

            event = route.event.model_validate(envelope.payload)
            start = time.monotonic()
            with consumer_span(
                f"{self._stream} process",
                envelope.traceparent,
                **{
                    "messaging.system": "redis_streams",
                    "messaging.destination.name": self._stream,
                    "messaging.consumer.group.name": self._group,
                    "messaging.message.id": str(message_id),
                    "event.type": envelope.event_type,
                    "correlation.id": correlation_id,
                },
            ):
                await route.handler(event)
            duration = time.monotonic() - start

            if not self._noack:
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

    async def _skip(self, message_id: bytes | str, event_type: str) -> None:
        if not self._noack:
            await self._redis.xack(self._stream, self._group, message_id)
        STREAM_MESSAGES_TOTAL.labels(stream=self._stream, group=self._group, status="skipped").inc()
        logging.debug(
            "Skipped %s on %s/%s: no route for event `%s`",
            message_id,
            self._group,
            self._stream,
            event_type,
        )

    async def _handle_failure(
        self,
        message_id: bytes | str,
        message_data: dict[str, Any],
        error: Exception,
    ) -> None:
        if self._noack:
            # Nothing is pending, so there is nothing to retry. Redelivering a
            # live push to a client that has since gone is pointless anyway.
            logging.warning("Dropping %s on %s/%s: %s", message_id, self._group, self._stream, error)
            return

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
            await self._redis.xadd(
                self._dlq_stream,  # type: ignore[arg-type]
                {"data": dlq_entry},
                maxlen=_DLQ_MAXLEN,
                approximate=True,
            )
            STREAM_DLQ_TOTAL.labels(stream=self._stream, group=self._group).inc()
        except Exception as dlq_error:
            logging.error("Failed to send message to DLQ: %s", dlq_error)

    async def _claim_pending(self) -> None:
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
                        await self._process_message(message_id, message_data)
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
                noack=self._noack,
            )
        except redis_exc.ResponseError as e:
            logging.error("StreamConsumer._read_messages(): Error reading messages: %s", e)
            return []
