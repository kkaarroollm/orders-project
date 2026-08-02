import asyncio
import logging
import time
from datetime import UTC, datetime, timedelta
from typing import Any

from pymongo import ASCENDING
from pymongo.asynchronous.client_session import AsyncClientSession
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.errors import PyMongoError

from shared.events.base import DomainEvent
from shared.redis.publisher import StreamProducer

_RETENTION = timedelta(days=1)
_WATCH_TIMEOUT_MS = 1_000
_SWEEP_INTERVAL_SECONDS = 30.0
_SWEEP_BATCH = 100


class MongoOutbox:
    """Events staged inside the transaction that produced them.

    Writing the order and its event in one transaction removes the dual-write
    problem: a crash between the commit and the publish can no longer lose the
    event, because the event is *part of* the commit.
    """

    def __init__(self, collection: AsyncCollection) -> None:
        self._collection = collection

    async def ensure_indexes(self) -> None:
        # Drives the relay sweep; partial so it only spans unpublished rows.
        await self._collection.create_index(
            [("published_at", ASCENDING)],
            name="unpublished",
            partialFilterExpression={"published_at": None},
        )
        # Published rows are kept briefly for debugging, then expire.
        await self._collection.create_index("expires_at", expireAfterSeconds=0, name="ttl_expires_at")

    async def add(self, event: DomainEvent, session: AsyncClientSession, *, correlation_id: str = "") -> None:
        await self._collection.insert_one(
            {
                "stream": event.stream,
                "event_type": event.event_type,
                "event_id": event.event_id,
                "correlation_id": correlation_id or event.event_id,
                "payload": event.model_dump(mode="json"),
                "created_at": datetime.now(UTC),
                "published_at": None,
            },
            session=session,
        )

    async def unpublished(self, limit: int = _SWEEP_BATCH) -> list[dict[str, Any]]:
        cursor = self._collection.find({"published_at": None}).sort("_id", ASCENDING).limit(limit)
        return await cursor.to_list(length=limit)

    async def mark_published(self, doc_id: Any) -> None:
        now = datetime.now(UTC)
        await self._collection.update_one(
            {"_id": doc_id},
            {"$set": {"published_at": now, "expires_at": now + _RETENTION}},
        )

    def watch_inserts(self) -> Any:
        return self._collection.watch(
            pipeline=[{"$match": {"operationType": "insert"}}],
            max_await_time_ms=_WATCH_TIMEOUT_MS,
        )


class OutboxRelay:
    """Publishes staged events to Redis.

    A change stream gives near-immediate publishing; a periodic sweep is what
    makes it *correct*, covering a relay that was down, a publish that failed,
    and a resume token that aged out of the oplog. Republishing carries the
    original `event_id`, so consumer inboxes collapse the duplicate.
    """

    def __init__(
        self,
        *,
        outbox: MongoOutbox,
        producer: StreamProducer[Any],
        sweep_interval: float = _SWEEP_INTERVAL_SECONDS,
    ) -> None:
        self._outbox = outbox
        self._producer = producer
        self._sweep_interval = sweep_interval
        self._task: asyncio.Task[None] | None = None

    async def run(self) -> None:
        await self.sweep()
        while True:
            try:
                await self._watch()
            except PyMongoError as error:
                # Fall back to sweeping until the change stream recovers.
                logging.warning("Outbox change stream failed, sweeping instead: %s", error)
                await asyncio.sleep(1)
                await self.sweep()

    async def _watch(self) -> None:
        async with await self._outbox.watch_inserts() as stream:
            last_sweep = time.monotonic()
            while True:
                change = await stream.try_next()
                if change is None:
                    if time.monotonic() - last_sweep >= self._sweep_interval:
                        await self.sweep()
                        last_sweep = time.monotonic()
                    continue
                await self._publish(change["fullDocument"])

    async def sweep(self) -> int:
        published = 0
        for doc in await self._outbox.unpublished():
            await self._publish(doc)
            published += 1
        if published:
            logging.info("Outbox relay swept %d unpublished event(s)", published)
        return published

    async def _publish(self, doc: dict[str, Any]) -> None:
        await self._producer.publish_raw(
            doc["stream"],
            doc["payload"],
            event_type=doc["event_type"],
            correlation_id=doc.get("correlation_id", ""),
        )
        # Marked only after a successful publish, so a failure here means the
        # next sweep tries again rather than dropping the event.
        await self._outbox.mark_published(doc["_id"])

    def start(self) -> asyncio.Task[None]:
        self._task = asyncio.create_task(self.run())
        return self._task

    async def stop(self) -> None:
        if not self._task or self._task.done():
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
