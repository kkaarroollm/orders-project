from pymongo.asynchronous.client_session import AsyncClientSession
from pymongo.asynchronous.collection import AsyncCollection
from shared.db.repository import MongoRepository

from src.schemas import OrderSchema, OrderStatus


class OrderRepository(MongoRepository[OrderSchema]):
    def __init__(self, collection: AsyncCollection) -> None:
        super().__init__(collection, OrderSchema)

    async def update_status(
        self, order_id: str, new_status: OrderStatus, session: AsyncClientSession
    ) -> bool:
        return await self.update_one(
            order_id,
            {"$set": {"status": new_status.value}},
            session=session,
        )
