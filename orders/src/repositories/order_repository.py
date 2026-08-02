from bson import ObjectId
from pymongo import ReturnDocument
from pymongo.asynchronous.client_session import AsyncClientSession
from pymongo.asynchronous.collection import AsyncCollection
from shared.db.repository import MongoRepository

from src.schemas import ALLOWED_PREVIOUS, OrderSchema, OrderStatus


class OrderRepository(MongoRepository[OrderSchema]):
    def __init__(self, collection: AsyncCollection) -> None:
        super().__init__(collection, OrderSchema)

    async def advance_status(
        self, order_id: str, new_status: OrderStatus, session: AsyncClientSession
    ) -> OrderSchema | None:
        """Move an order forward, or do nothing.

        The allowed predecessors are part of the query, so an out-of-order or
        replayed event simply matches nothing. Returns the updated order (which
        carries `simulation`, needed by the event) or None if the transition
        was not legal from the order's current status.
        """
        allowed = ALLOWED_PREVIOUS.get(new_status, set())
        if not allowed:
            return None

        doc = await self._collection.find_one_and_update(
            {"_id": ObjectId(order_id), "status": {"$in": [status.value for status in allowed]}},
            {"$set": {"status": new_status.value}, "$inc": {"version": 1}},
            session=session,
            return_document=ReturnDocument.AFTER,
        )
        return self._model(**doc) if doc else None
