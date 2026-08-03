import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from pymongo.asynchronous.client_session import AsyncClientSession
from pymongo.asynchronous.collection import AsyncCollection

_RETENTION = timedelta(hours=24)


class IdempotencyStore:
    """Makes a retried request return its original result instead of acting twice.

    A client that times out and retries `POST /orders` would otherwise create a
    second order. The key is reserved inside the order's own transaction, so the
    reservation and the order commit together or not at all.
    """

    def __init__(self, collection: AsyncCollection) -> None:
        self._collection = collection

    async def ensure_indexes(self) -> None:
        await self._collection.create_index("key", unique=True, name="uniq_key")
        await self._collection.create_index("expires_at", expireAfterSeconds=0, name="ttl_expires_at")

    async def reserve(self, key: str, session: AsyncClientSession) -> None:
        """Claim a key. Raises `DuplicateKeyError` if it is already taken."""
        now = datetime.now(UTC)
        await self._collection.insert_one(
            {"key": key, "response": None, "created_at": now, "expires_at": now + _RETENTION},
            session=session,
        )

    async def complete(self, key: str, response: dict[str, Any]) -> None:
        await self._collection.update_one({"key": key}, {"$set": {"response": response}})
        logging.debug("Stored idempotent response for key %s", key)

    async def find(self, key: str) -> dict[str, Any] | None:
        return await self._collection.find_one({"key": key})
