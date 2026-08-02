import logging
from datetime import UTC, datetime, timedelta

from pymongo import ASCENDING
from pymongo.asynchronous.client_session import AsyncClientSession
from pymongo.asynchronous.collection import AsyncCollection

_RETENTION = timedelta(days=7)


class MongoInbox:
    """Records which events a consumer group has already applied.

    Stream delivery is at-least-once: `XAUTOCLAIM` re-delivers anything left
    pending by a crashed consumer, and DLQ replay re-delivers deliberately.
    Recording the event id in the *same transaction* as the business write
    turns that into effectively-once -- either both land or neither does.
    """

    def __init__(self, collection: AsyncCollection) -> None:
        self._collection = collection

    async def ensure_indexes(self) -> None:
        await self._collection.create_index(
            [("group", ASCENDING), ("event_id", ASCENDING)],
            unique=True,
            name="uniq_group_event",
        )
        # Bounded growth: an event old enough to have fallen out of its stream
        # can no longer be redelivered, so its marker is dead weight.
        await self._collection.create_index("expires_at", expireAfterSeconds=0, name="ttl_expires_at")

    async def record(self, group: str, event_id: str, session: AsyncClientSession) -> None:
        """Mark an event as applied.

        Raises `DuplicateKeyError` if it was already applied. Callers let that
        propagate out of the transaction so the business write aborts with it.
        """
        await self._collection.insert_one(
            {
                "group": group,
                "event_id": event_id,
                "processed_at": datetime.now(UTC),
                "expires_at": datetime.now(UTC) + _RETENTION,
            },
            session=session,
        )
        logging.debug("Recorded event %s for group %s", event_id, group)
