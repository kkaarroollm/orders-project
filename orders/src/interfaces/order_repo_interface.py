from typing import Protocol, runtime_checkable

from pymongo.asynchronous.client_session import AsyncClientSession

from src.schemas import OrderSchema, OrderStatus


@runtime_checkable
class OrderRepositoryProtocol(Protocol):
    async def create(self, data: OrderSchema, session: AsyncClientSession | None = None) -> str: ...
    async def get_by_id(self, id: str, session: AsyncClientSession | None = None) -> OrderSchema | None: ...
    async def update_status(self, order_id: str, new_status: OrderStatus, session: AsyncClientSession) -> bool: ...
